#===========================================================
# PharmaKG ETL - Cypher 查询构建器
# Pharmaceutical Knowledge Graph - Cypher Query Builder
#===========================================================
# 版本: v1.0
# 描述: 动态构建 Cypher 查询语句
#===========================================================

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


logger = logging.getLogger(__name__)


class CypherBuilder:
    """
    Cypher 查询构建器

    提供静态方法用于构建常见的 Cypher 查询模式
    """

    @staticmethod
    def create_node(
        label: str,
        props: Dict[str, Any]
    ) -> str:
        """
        创建节点查询

        Args:
            label: 节点标签
            props: 属性字典

        Returns:
            Cypher 查询语句
        """
        props_str = CypherBuilder._format_properties(props)
        return f"CREATE (n:{label} {props_str})"

    @staticmethod
    def merge_node(
        label: str,
        match_props: Dict[str, Any],
        set_props: Optional[Dict[str, Any]] = None,
        on_create_set: Optional[Dict[str, Any]] = None,
        on_match_set: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        合并节点查询

        Args:
            label: 节点标签
            match_props: 匹配属性
            set_props: 设置属性（无论创建或匹配）
            on_create_set: 创建时设置的属性
            on_match_set: 匹配时设置的属性

        Returns:
            Cypher 查询语句
        """
        match_str = CypherBuilder._format_properties(match_props)
        query = f"MERGE (n:{label} {match_str})"

        if set_props:
            set_str = CypherBuilder._format_properties(set_props)
            query += f"\nSET n += {set_str}"

        if on_create_set:
            create_str = CypherBuilder._format_properties(on_create_set)
            query += f"\nON CREATE SET n += {create_str}"

        if on_match_set:
            match_str = CypherBuilder._format_properties(on_match_set)
            query += f"\nON MATCH SET n += {match_str}"

        return query

    @staticmethod
    def unwind_create_nodes(
        label: str,
        batch_var: str = "batch",
        merge: bool = True,
        merge_key: str = "primary_id"
    ) -> str:
        """
        使用 UNWIND 批量创建节点

        Args:
            label: 节点标签
            batch_var: 批次变量名
            merge: 是否使用 MERGE
            merge_key: 合并键

        Returns:
            Cypher 查询语句
        """
        keyword = "MERGE" if merge else "CREATE"

        query = f"""
UNWIND ${batch_var} AS row
{keyword} (n:{label} {{{merge_key}: row.{merge_key}}})
SET n += row
WITH count(*) as nodes_created
RETURN nodes_created
"""
        return query.strip()

    @staticmethod
    def unwind_merge_nodes(
        label: str,
        merge_key: str,
        batch_var: str = "batch"
    ) -> Tuple[str, str]:
        """
        使用 UNWIND 批量合并节点（返回查询和参数）

        Args:
            label: 节点标签
            merge_key: 合并键字段
            batch_var: 批次变量名

        Returns:
            (查询语句, 参数键名)
        """
        query = f"""
UNWIND ${batch_var} AS row
MERGE (n:{label} {{{merge_key}: row.{merge_key}}})
SET n += row
WITH count(*) as nodes_created
RETURN nodes_created
"""
        return query.strip(), batch_var

    @staticmethod
    def unwind_create_relationships(
        from_label: str,
        from_key: str,
        to_label: str,
        to_key: str,
        rel_type: str,
        batch_var: str = "batch",
        merge: bool = True
    ) -> str:
        """
        使用 UNWIND 批量创建关系

        Args:
            from_label: 起始节点标签
            from_key: 起始节点键字段
            to_label: 目标节点标签
            to_key: 目标节点键字段
            rel_type: 关系类型
            batch_var: 批次变量名
            merge: 是否使用 MERGE

        Returns:
            Cypher 查询语句
        """
        keyword = "MERGE" if merge else "CREATE"

        query = f"""
UNWIND ${batch_var} AS row
MATCH (from:{from_label} {{{from_key}: row.from_id}})
MATCH (to:{to_label} {{{to_key}: row.to_id}})
{keyword} (from)-[r:{rel_type}]->(to)
"""
        # 添加关系属性
        query += """
WITH row, r
WHERE row.properties IS NOT NULL
SET r += row.properties
"""

        query += """
WITH count(*) as relationships_created
RETURN relationships_created
"""
        return query.strip()

    @staticmethod
    def create_relationship(
        from_label: str,
        from_props: Dict[str, Any],
        to_label: str,
        to_props: Dict[str, Any],
        rel_type: str,
        rel_props: Optional[Dict[str, Any]] = None,
        merge: bool = False
    ) -> str:
        """
        创建关系查询

        Args:
            from_label: 起始节点标签
            from_props: 起始节点匹配属性
            to_label: 目标节点标签
            to_props: 目标节点匹配属性
            rel_type: 关系类型
            rel_props: 关系属性
            merge: 是否使用 MERGE

        Returns:
            Cypher 查询语句
        """
        from_str = CypherBuilder._format_properties(from_props)
        to_str = CypherBuilder._format_properties(to_props)
        keyword = "MERGE" if merge else "CREATE"

        query = f"""
MATCH (from:{from_label} {from_str})
MATCH (to:{to_label} {to_str})
{keyword} (from)-[r:{rel_type}]->(to)
"""

        if rel_props:
            props_str = CypherBuilder._format_properties(rel_props)
            query += f"SET r += {props_str}"

        return query.strip()

    @staticmethod
    def match_nodes(
        label: str,
        props: Optional[Dict[str, Any]] = None,
        where_clause: Optional[str] = None
    ) -> str:
        """
        匹配节点查询

        Args:
            label: 节点标签
            props: 属性匹配
            where_clause: WHERE 子句

        Returns:
            Cypher 查询语句
        """
        query = f"MATCH (n:{label}"

        if props:
            query += " " + CypherBuilder._format_properties(props)

        query += ")"

        if where_clause:
            query += f"\nWHERE {where_clause}"

        return query + "\nRETURN n"

    @staticmethod
    def match_relationships(
        from_label: Optional[str] = None,
        rel_type: Optional[str] = None,
        to_label: Optional[str] = None,
        where_clause: Optional[str] = None,
        return_clause: str = "from, to, r"
    ) -> str:
        """
        匹配关系查询

        Args:
            from_label: 起始节点标签
            rel_type: 关系类型
            to_label: 目标节点标签
            where_clause: WHERE 子句
            return_clause: RETURN 子句

        Returns:
            Cypher 查询语句
        """
        # 构建模式
        from_part = f"(from:{from_label})" if from_label else "(from)"
        to_part = f"(to:{to_label})" if to_label else "(to)"

        if rel_type:
            rel_part = f"-[r:{rel_type}]->"
        else:
            rel_part = "-[r]->"

        query = f"MATCH {from_part}{rel_part}{to_part}"

        if where_clause:
            query += f"\nWHERE {where_clause}"

        query += f"\nRETURN {return_clause}"

        return query

    @staticmethod
    def update_node(
        label: str,
        match_props: Dict[str, Any],
        set_props: Dict[str, Any]
    ) -> str:
        """
        更新节点查询

        Args:
            label: 节点标签
            match_props: 匹配属性
            set_props: 设置属性

        Returns:
            Cypher 查询语句
        """
        match_str = CypherBuilder._format_properties(match_props)
        set_str = CypherBuilder._format_properties(set_props)

        return f"""
MATCH (n:{label} {match_str})
SET n += {set_str}
RETURN n
""".strip()

    @staticmethod
    def delete_nodes(
        label: str,
        props: Optional[Dict[str, Any]] = None,
        detach: bool = True
    ) -> str:
        """
        删除节点查询

        Args:
            label: 节点标签
            props: 匹配属性
            detach: 是否分离关系

        Returns:
            Cypher 查询语句
        """
        keyword = "DETACH DELETE" if detach else "DELETE"

        query = f"MATCH (n:{label}"

        if props:
            query += " " + CypherBuilder._format_properties(props)

        query += f")\n{keyword} n"

        return query

    @staticmethod
    def count_nodes(
        label: str,
        where_clause: Optional[str] = None
    ) -> str:
        """
        统计节点查询

        Args:
            label: 节点标签
            where_clause: WHERE 子句

        Returns:
            Cypher 查询语句
        """
        query = f"MATCH (n:{label})"

        if where_clause:
            query += f"\nWHERE {where_clause}"

        query += "\nRETURN count(n) as count"

        return query

    @staticmethod
    def batch_create_constraints(
        constraints: List[Tuple[str, str, str]]
    ) -> str:
        """
        批量创建约束

        Args:
            constraints: 约束列表 [(label, property, type)]

        Returns:
            Cypher 查询语句
        """
        queries = []

        for label, prop, constraint_type in constraints:
            constraint_name = f"{label.lower()}_{prop}_{constraint_type}"

            if constraint_type == "unique":
                query = (
                    f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                    f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
                )
            elif constraint_type == "exists":
                query = (
                    f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                    f"FOR (n:{label}) REQUIRE n.{prop} IS NOT NULL"
                )
            else:
                continue

            queries.append(query)

        return "\n".join(queries)

    @staticmethod
    def _format_properties(props: Dict[str, Any]) -> str:
        """
        格式化属性为 Cypher 格式

        Args:
            props: 属性字典

        Returns:
            格式化的属性字符串
        """
        if not props:
            return "{}"

        items = []
        for key, value in props.items():
            formatted_value = CypherBuilder._format_value(value)
            items.append(f"{key}: {formatted_value}")

        return "{" + ", ".join(items) + "}"

    @staticmethod
    def _format_value(value: Any) -> str:
        """
        格式化值为 Cypher 格式

        Args:
            value: 值

        Returns:
            格式化的值
        """
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # 转义特殊字符
            escaped = value.replace("\\", "\\\\").replace("'", "\\'")
            return f"'{escaped}'"
        elif isinstance(value, list):
            items = [CypherBuilder._format_value(v) for v in value]
            return "[" + ", ".join(items) + "]"
        elif isinstance(value, dict):
            return CypherBuilder._format_properties(value)
        elif isinstance(value, datetime):
            return f"datetime('{value.isoformat()}')"
        else:
            # 其他类型转为字符串
            escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
            return f"'{escaped}'"

    @staticmethod
    def build_parameterized_query(
        query_template: str,
        params: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        构建参数化查询

        Args:
            query_template: 查询模板（使用 $param 格式）
            params: 参数字典

        Returns:
            (查询语句, 参数字典)
        """
        # 清理参数值
        clean_params = {}
        for key, value in params.items():
            if value is not None:
                clean_params[key] = value

        return query_template, clean_params

    @staticmethod
    def create_index(
        label: str,
        property_key: str,
        index_name: Optional[str] = None
    ) -> str:
        """
        创建索引

        Args:
            label: 节点标签
            property_key: 属性键
            index_name: 索引名称（可选）

        Returns:
            Cypher 查询语句
        """
        if index_name is None:
            index_name = f"{label.lower()}_{property_key}_index"

        return (
            f"CREATE INDEX {index_name} IF NOT EXISTS "
            f"FOR (n:{label}) ON (n.{property_key})"
        )

    @staticmethod
    def full_text_search(
        label: str,
        search_field: str,
        search_term: str,
        return_props: Optional[List[str]] = None
    ) -> str:
        """
        全文搜索查询

        Args:
            label: 节点标签
            search_field: 搜索字段
            search_term: 搜索词
            return_props: 返回属性列表

        Returns:
            Cypher 查询语句
        """
        return_clause = "n"
        if return_props:
            return_clause = ", ".join([f"n.{p}" for p in return_props])

        return f"""
CALL db.index.fulltext.queryNodes('{label}_{search_field}_index', '{search_term}') YIELD node, score
RETURN node, score
LIMIT 100
""".strip()

    @staticmethod
    def shortest_path(
        from_label: str,
        from_props: Dict[str, Any],
        to_label: str,
        to_props: Dict[str, Any],
        max_depth: int = 5,
        relationship_types: Optional[List[str]] = None
    ) -> str:
        """
        最短路径查询

        Args:
            from_label: 起始节点标签
            from_props: 起始节点属性
            to_label: 目标节点标签
            to_props: 目标节点属性
            max_depth: 最大深度
            relationship_types: 允许的关系类型

        Returns:
            Cypher 查询语句
        """
        from_str = CypherBuilder._format_properties(from_props)
        to_str = CypherBuilder._format_properties(to_props)

        rel_pattern = ""
        if relationship_types:
            rel_pattern = "|" + "|".join(relationship_types)

        return f"""
MATCH (from:{label} {from_str}), (to:{to_label} {to_str})
MATCH path = shortestPath((from)-[*1..{max_depth}{rel_pattern}]-(to))
RETURN path, length(path) as path_length
LIMIT 10
""".strip()
