#===========================================================
# PharmaKG ETL - Neo4j 批量加载器
# Pharmaceutical Knowledge Graph - Neo4j Batch Loader
#===========================================================
# 版本: v1.0
# 描述: 批量加载节点和关系到 Neo4j
#===========================================================

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from threading import Lock

try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

from .cypher_builder import CypherBuilder


logger = logging.getLogger(__name__)


class Neo4jBatchLoader:
    """
    Neo4j 批量加载器

    功能：
    - 批量节点加载（使用 UNWIND 优化）
    - 批量关系加载
    - 事务管理
    - 错误恢复
    - 约束创建
    """

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
        batch_size: int = 500,
        timeout: int = 300,
        max_retries: int = 3,
        dry_run: bool = False
    ):
        """
        初始化批量加载器

        Args:
            uri: Neo4j 连接 URI
            user: 用户名
            password: 密码
            database: 数据库名称
            batch_size: 批量大小
            timeout: 查询超时时间（秒）
            max_retries: 最大重试次数
            dry_run: 试运行模式
        """
        if not NEO4J_AVAILABLE:
            raise ImportError("neo4j package is required. Install with: pip install neo4j")

        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.batch_size = batch_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.dry_run = dry_run

        self._driver: Optional[Driver] = None
        self._lock = Lock()

        # 统计信息
        self.stats = {
            "nodes_loaded": 0,
            "relationships_loaded": 0,
            "errors": 0,
            "batches_processed": 0
        }

    def _get_driver(self) -> Driver:
        """获取数据库驱动"""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60,
                connection_timeout=30,
                max_transaction_retry_time=30
            )
        return self._driver

    def close(self):
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def load_nodes(
        self,
        label: str,
        records: List[Dict],
        merge_key: str,
        additional_props: Optional[Dict[str, Any]] = None,
        create_constraints: bool = True
    ) -> int:
        """
        批量加载节点

        Args:
            label: 节点标签
            records: 记录列表
            merge_key: 合并键字段
            additional_props: 额外的属性（添加到所有节点）
            create_constraints: 是否创建唯一约束

        Returns:
            加载的节点数量
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would load {len(records)} {label} nodes")
            return len(records)

        if not records:
            logger.warning(f"No records to load for label {label}")
            return 0

        # 创建约束
        if create_constraints:
            self._ensure_unique_constraint(label, merge_key)

        # 分批处理
        total_loaded = 0
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            loaded = self._load_node_batch(label, batch, merge_key, additional_props)
            total_loaded += loaded

        self.stats["nodes_loaded"] += total_loaded
        self.stats["batches_processed"] += (len(records) + self.batch_size - 1) // self.batch_size

        return total_loaded

    def _load_node_batch(
        self,
        label: str,
        batch: List[Dict],
        merge_key: str,
        additional_props: Optional[Dict[str, Any]]
    ) -> int:
        """加载节点批次"""
        # 添加额外属性
        if additional_props:
            batch = [
                {**record, **additional_props}
                for record in batch
            ]

        # 生成 Cypher
        query, params = CypherBuilder.unwind_merge_nodes(
            label=label,
            merge_key=merge_key,
            batch_var="batch"
        )

        # 执行查询
        try:
            result = self._execute_query(query, {"batch": batch})
            return result[0].get("nodes_created", len(batch))
        except Exception as e:
            logger.error(f"Failed to load node batch: {e}")
            self.stats["errors"] += 1
            return 0

    def load_relationships(
        self,
        from_label: str,
        from_key: str,
        to_label: str,
        to_key: str,
        rel_type: str,
        records: List[Dict],
        rel_properties: Optional[Dict[str, Any]] = None,
        merge: bool = True
    ) -> int:
        """
        批量加载关系

        Args:
            from_label: 起始节点标签
            from_key: 起始节点键字段
            to_label: 目标节点标签
            to_key: 目标节点键字段
            rel_type: 关系类型
            records: 记录列表（包含 from_id, to_id, 可选的 props）
            rel_properties: 关系属性模板
            merge: 是否使用 MERGE（否则使用 CREATE）

        Returns:
            加载的关系数量
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would load {len(records)} {rel_type} relationships")
            return len(records)

        if not records:
            logger.warning(f"No relationships to load for type {rel_type}")
            return 0

        # 分批处理
        total_loaded = 0
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            loaded = self._load_relationship_batch(
                from_label, from_key, to_label, to_key, rel_type,
                batch, rel_properties, merge
            )
            total_loaded += loaded

        self.stats["relationships_loaded"] += total_loaded

        return total_loaded

    def _load_relationship_batch(
        self,
        from_label: str,
        from_key: str,
        to_label: str,
        to_key: str,
        rel_type: str,
        batch: List[Dict],
        rel_properties: Optional[Dict[str, Any]],
        merge: bool
    ) -> int:
        """加载关系批次"""
        # 构建关系数据
        relationships = []
        for record in batch:
            rel_data = {
                "from_id": record.get("from_id"),
                "to_id": record.get("to_id")
            }

            # 添加关系属性
            props = rel_properties.copy() if rel_properties else {}
            if "props" in record:
                props.update(record["props"])
            elif "properties" in record:
                props.update(record["properties"])

            if props:
                rel_data["properties"] = props

            relationships.append(rel_data)

        # 生成 Cypher
        query = CypherBuilder.unwind_create_relationships(
            from_label=from_label,
            from_key=from_key,
            to_label=to_label,
            to_key=to_key,
            rel_type=rel_type,
            batch_var="batch",
            merge=merge
        )

        # 执行查询
        try:
            result = self._execute_query(query, {"batch": relationships})
            return result[0].get("relationships_created", len(batch))
        except Exception as e:
            logger.error(f"Failed to load relationship batch: {e}")
            self.stats["errors"] += 1
            return 0

    def create_constraint(
        self,
        label: str,
        property_key: str,
        constraint_type: str = "unique"
    ) -> bool:
        """
        创建约束

        Args:
            label: 节点标签
            property_key: 属性键
            constraint_type: 约束类型 (unique, exists)

        Returns:
            是否成功
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would create {constraint_type} constraint on {label}.{property_key}")
            return True

        constraint_name = f"{label.lower()}_{property_key}_{constraint_type}"

        if constraint_type == "unique":
            query = (
                f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.{property_key} IS UNIQUE"
            )
        elif constraint_type == "exists":
            query = (
                f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.{property_key} IS NOT NULL"
            )
        else:
            logger.error(f"Unknown constraint type: {constraint_type}")
            return False

        try:
            self._execute_query(query, {})
            logger.info(f"Created {constraint_type} constraint on {label}.{property_key}")
            return True
        except Exception as e:
            logger.warning(f"Failed to create constraint: {e}")
            return False

    def _ensure_unique_constraint(self, label: str, property_key: str):
        """确保唯一约束存在"""
        self.create_constraint(label, property_key, "unique")

    def _execute_query(
        self,
        query: str,
        params: Dict[str, Any]
    ) -> List[Dict]:
        """
        执行 Cypher 查询

        Args:
            query: Cypher 查询语句
            params: 查询参数

        Returns:
            查询结果
        """
        driver = self._get_driver()

        for attempt in range(self.max_retries):
            try:
                with driver.session(database=self.database) as session:
                    result = session.run(query, params, timeout=self.timeout)
                    return [record.data() for record in result]

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Query failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    raise

    def execute_cypher(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        执行自定义 Cypher 查询

        Args:
            query: Cypher 查询语句
            params: 查询参数

        Returns:
            查询结果
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute query:\n{query}")
            return []

        return self._execute_query(query, params or {})

    def begin_transaction(self):
        """
        开始事务

        Returns:
            事务对象
        """
        driver = self._get_driver()
        session = driver.session(database=self.database)
        return session.begin_transaction()

    def get_stats(self) -> Dict[str, int]:
        """获取加载统计"""
        return self.stats.copy()

    def reset_stats(self):
        """重置统计"""
        self.stats = {
            "nodes_loaded": 0,
            "relationships_loaded": 0,
            "errors": 0,
            "batches_processed": 0
        }

    def test_connection(self) -> bool:
        """
        测试数据库连接

        Returns:
            连接是否成功
        """
        try:
            result = self._execute_query("RETURN 1 as test", {})
            return result and result[0].get("test") == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def count_nodes(self, label: str) -> int:
        """
        统计节点数量

        Args:
            label: 节点标签

        Returns:
            节点数量
        """
        if self.dry_run:
            return 0

        query = f"MATCH (n:{label}) RETURN count(n) as count"
        result = self._execute_query(query, {})
        return result[0].get("count", 0)

    def count_relationships(
        self,
        from_label: Optional[str] = None,
        rel_type: Optional[str] = None,
        to_label: Optional[str] = None
    ) -> int:
        """
        统计关系数量

        Args:
            from_label: 起始节点标签
            rel_type: 关系类型
            to_label: 目标节点标签

        Returns:
            关系数量
        """
        if self.dry_run:
            return 0

        # 构建查询
        parts = []
        if from_label:
            parts.append(f"(a:{from_label})")
        else:
            parts.append("(a)")

        if rel_type:
            parts.append(f"-[r:{rel_type}]->")
        else:
            parts.append("-[r]->")

        if to_label:
            parts.append(f"(b:{to_label})")
        else:
            parts.append("(b)")

        pattern = "".join(parts)
        query = f"MATCH {pattern} RETURN count(r) as count"
        result = self._execute_query(query, {})
        return result[0].get("count", 0)

    def clear_database(self, confirm: bool = False) -> bool:
        """
        清空数据库

        Args:
            confirm: 确认标志（必须为 True）

        Returns:
            是否成功
        """
        if not confirm:
            logger.warning("Database clear not confirmed (use confirm=True)")
            return False

        if self.dry_run:
            logger.info("[DRY RUN] Would clear database")
            return True

        query = "MATCH (n) DETACH DELETE n"
        try:
            self._execute_query(query, {})
            logger.info("Database cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return False
