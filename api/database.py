#===========================================================
# 制药行业知识图谱 - Neo4j数据库连接
# Pharmaceutical Knowledge Graph - Neo4j Database Connection
#===========================================================
# 版本: v1.0
# 创建日期: 2025-02-06
#===========================================================

from typing import Optional, Any, List
from contextlib import contextmanager
import logging

from neo4j import GraphDatabase, Driver, AsyncGraphDatabase
from neo4j import ManagedTransaction
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)


class QueryResult(BaseModel):
    """查询结果模型"""
    records: List[dict[str, Any]]
    summary: dict[str, Any]
    query: str
    parameters: dict[str, Any]


class Neo4jConnection:
    """Neo4j连接管理器"""

    def __init__(self):
        self._driver: Optional[Driver] = None

    def connect(self) -> Driver:
        """建立连接"""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            logger.info(f"Connected to Neo4j at {settings.NEO4J_URI}")
        return self._driver

    def close(self):
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    @contextmanager
    def session(self):
        """创建会话上下文管理器"""
        driver = self.connect()
        session = driver.session(database=settings.NEO4J_DATABASE)
        try:
            yield session
        finally:
            session.close()

    def execute_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        fetch_size: Optional[int] = None
    ) -> QueryResult:
        """执行Cypher查询"""
        parameters = parameters or {}
        records = []
        summary = {}

        try:
            with self.session() as session:
                result = session.run(query, parameters)

                # 获取记录
                for record in result:
                    records.append(record.data())

                # 获取查询摘要
                summary = result.consume().counters

            logger.info(f"Query executed successfully. Records: {len(records)}")

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

        return QueryResult(
            records=records,
            summary=summary,
            query=query,
            parameters=parameters
        )

    def execute_write(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None
    ) -> QueryResult:
        """执行写操作"""
        parameters = parameters or {}
        records = []
        summary = {}

        try:
            with self.session() as session:
                result = session.run(query, parameters)

                for record in result:
                    records.append(record.data())

                summary = result.consume().counters

            logger.info(f"Write query executed successfully. Records affected: {summary.get('updates', 0)}")

        except Exception as e:
            logger.error(f"Write query execution failed: {str(e)}")
            raise

        return QueryResult(
            records=records,
            summary=summary,
            query=query,
            parameters=parameters
        )

    def verify_connection(self) -> bool:
        """验证连接状态"""
        try:
            with self.session() as session:
                result = session.run("RETURN 1 AS test")
                record = result.single()
                return record["test"] == 1
        except Exception as e:
            logger.error(f"Connection verification failed: {str(e)}")
            return False


# 全局连接实例
_db_connection: Optional[Neo4jConnection] = None


def get_db() -> Neo4jConnection:
    """获取数据库连接实例"""
    global _db_connection
    if _db_connection is None:
        _db_connection = Neo4jConnection()
    return _db_connection


async def close_db():
    """关闭数据库连接"""
    global _db_connection
    if _db_connection:
        _db_connection.close()
        _db_connection = None
