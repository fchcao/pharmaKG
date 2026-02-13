#===========================================================
# 制药行业知识图谱 - 搜索服务
# Pharmaceutical Knowledge Graph - Search Service
#===========================================================
# 版本: v1.0
# 创建日期: 2025-02-08
# 描述: 全文搜索、模糊搜索和建议功能
#===========================================================

from typing import List, Optional, Any, Dict
import logging
from datetime import datetime

from ..database import get_db

logger = logging.getLogger(__name__)


class SearchService:
    """搜索服务 - 提供全文搜索、模糊搜索和建议功能"""

    def __init__(self):
        self.db = get_db()

    def create_fulltext_indexes(self) -> Dict[str, Any]:
        """创建全文搜索索引"""
        indexes_created = []
        errors = []

        # 定义需要索引的节点和属性
        index_configs = [
            {
                "name": "entity_fulltext",
                "label": "Compound",
                "properties": ["name", "primary_id", "smiles"]
            },
            {
                "name": "target_fulltext",
                "label": "Target",
                "properties": ["name", "primary_id", "gene_symbol", "gene_name", "uniprot_id"]
            },
            {
                "name": "pathway_fulltext",
                "label": "Pathway",
                "properties": ["name", "primary_id", "kegg_id"]
            },
            {
                "name": "trial_fulltext",
                "label": "ClinicalTrial",
                "properties": ["title", "trial_id", "condition"]
            },
            {
                "name": "manufacturer_fulltext",
                "label": "Manufacturer",
                "properties": ["name", "manufacturer_id", "city", "country"]
            },
            {
                "name": "drug_fulltext",
                "label": "DrugProduct",
                "properties": ["name", "primary_id", "active_ingredient"]
            }
        ]

        for config in index_configs:
            try:
                # 首先删除已存在的索引（如果存在）
                drop_query = f"CALL db.index.fulltext.drop('{config['name']}') IF EXISTS"
                self.db.execute_query(drop_query)

                # 创建新索引
                create_query = f"""
                CALL db.index.fulltext.createNodeIndex(
                    '{config['name']}',
                    ['{config['label']}'],
                    {config['properties']}
                )
                """
                self.db.execute_query(create_query)
                indexes_created.append(config['name'])
                logger.info(f"Created fulltext index: {config['name']}")
            except Exception as e:
                error_msg = f"Failed to create index {config['name']}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        return {
            "success": len(indexes_created) > 0,
            "indexes_created": indexes_created,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }

    def list_fulltext_indexes(self) -> List[Dict[str, Any]]:
        """列出所有全文搜索索引"""
        # Neo4j 5.x 使用 SHOW INDEXES 命令
        query = "SHOW INDEXES WHERE type = 'FULLTEXT' YIELD name, labelsOrTypes, properties"
        try:
            result = self.db.execute_query(query)

            # Convert to list of dicts for compatibility
            indexes = []
            for record in result.records:
                indexes.append({
                    'name': record.get('name'),
                    'labelsOrTypes': record.get('labelsOrTypes', []),
                    'properties': record.get('properties', [])
                })
            return indexes
        except Exception as e:
            logger.warning(f"Failed to list fulltext indexes using SHOW INDEXES: {str(e)}")
            # Fallback: try the old procedure
            try:
                query = "CALL db.index.fulltext.listAvailableIndexes() YIELD name"
                result = self.db.execute_query(query)
                indexes = []
                for record in result.records:
                    indexes.append({
                        'name': record.get('name'),
                        'labelsOrTypes': [],
                        'properties': []
                    })
                return indexes
            except Exception as e2:
                logger.warning(f"Failed to list fulltext indexes using listAvailableIndexes: {str(e2)}")
                return []

    def fulltext_search(
        self,
        query_text: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 20,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        全文搜索

        Args:
            query_text: 搜索查询文本
            entity_types: 实体类型过滤 (例如: ['Compound', 'Target'])
            limit: 返回结果数量限制
            skip: 跳过结果数量

        Returns:
            包含搜索结果和元数据的字典
        """
        if not query_text or len(query_text.strip()) == 0:
            return {
                "results": [],
                "total": 0,
                "query": query_text,
                "entity_types": entity_types,
                "message": "Empty query provided"
            }

        # 获取可用的全文索引
        try:
            available_indexes = self.list_fulltext_indexes()
            index_names = [idx['name'] for idx in available_indexes] if available_indexes else []
        except Exception as e:
            logger.warning(f"Failed to list fulltext indexes: {str(e)}")
            index_names = []

        if not index_names:
            logger.warning("No fulltext indexes available - falling back to basic search")
            # Fallback: use simple Cypher query with CONTAINS
            return self._fallback_search(query_text, entity_types, limit, skip)

        # 如果指定了实体类型，过滤索引
        if entity_types:
            filtered_indexes = []
            for idx in available_indexes:
                labels = idx.get('labelsOrTypes', [])
                if any(label in entity_types for label in labels):
                    filtered_indexes.append(idx['name'])
            index_names = filtered_indexes if filtered_indexes else index_names

        results = []
        total_count = 0

        # 在每个索引中搜索
        for index_name in index_names:
            try:
                search_query = f"""
                CALL db.index.fulltext.queryNodes('{index_name}', $query_text)
                YIELD node, score
                RETURN labels(node)[0] AS entity_type,
                       elementId(node) AS element_id,
                       node.primary_id AS primary_id,
                       node.name AS name,
                       score
                ORDER BY score DESC
                LIMIT $limit
                """
                result = self.db.execute_query(search_query, {
                    "query_text": query_text,
                    "limit": limit
                })

                for record in result.records:
                    results.append({
                        "entity_type": record.get("entity_type", "Unknown"),
                        "element_id": record.get("element_id"),
                        "primary_id": record.get("primary_id"),
                        "name": record.get("name"),
                        "score": record.get("score", 0.0),
                        "index_name": index_name
                    })
                    total_count += 1
            except Exception as e:
                logger.error(f"Error searching index {index_name}: {str(e)}")

        # 按分数排序并应用分页
        results.sort(key=lambda x: x['score'], reverse=True)
        paginated_results = results[skip:skip + limit]

        return {
            "results": paginated_results,
            "total": len(results),
            "returned": len(paginated_results),
            "query": query_text,
            "entity_types": entity_types,
            "skip": skip,
            "limit": limit
        }

    def _fallback_search(
        self,
        query_text: str,
        entity_types: Optional[List[str]],
        limit: int,
        skip: int
    ) -> Dict[str, Any]:
        """Fallback search using simple Cypher CONTAINS query"""
        entity_filter = ""
        if entity_types:
            entity_filter = " AND " + " OR ".join([f"n:{et}" for et in entity_types])

        query = f"""
        MATCH (n)
        WHERE n.name IS NOT NULL
          AND n.name CONTAINS $query_text
          {entity_filter}
        RETURN labels(n)[0] AS entity_type,
               elementId(n) AS element_id,
               n.primary_id AS primary_id,
               n.name AS name,
               1.0 AS score
        ORDER BY n.name
        SKIP $skip
        LIMIT $limit
        """

        result = self.db.execute_query(query, {
            "query_text": query_text,
            "skip": skip,
            "limit": limit
        })

        results = []
        for record in result.records:
            results.append({
                "entity_type": record.get("entity_type", "Unknown"),
                "element_id": record.get("element_id"),
                "primary_id": record.get("primary_id"),
                "name": record.get("name"),
                "score": record.get("score", 0.0),
                "index_name": "fallback"
            })

        # Get total count
        count_query = f"""
        MATCH (n)
        WHERE n.name IS NOT NULL
          AND n.name CONTAINS $query_text
          {entity_filter}
        RETURN count(n) AS total
        """
        count_result = self.db.execute_query(count_query, {"query_text": query_text})
        total = count_result.records[0]["total"] if count_result.records else 0

        return {
            "results": results,
            "total": total,
            "returned": len(results),
            "query": query_text,
            "entity_types": entity_types,
            "skip": skip,
            "limit": limit,
            "method": "CONTAINS_FALLBACK"
        }

    def fuzzy_search(
        self,
        query_text: str,
        entity_type: str,
        search_field: str = "name",
        max_distance: int = 2,
        limit: int = 20,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        模糊搜索 (使用 Levenshtein 距离)

        Args:
            query_text: 搜索查询文本
            entity_type: 实体类型 (例如: 'Compound', 'Target')
            search_field: 搜索字段
            max_distance: 最大编辑距离 (0-4)
            limit: 返回结果数量限制
            skip: 跳过结果数量

        Returns:
            包含模糊搜索结果的字典
        """
        if not query_text or len(query_text.strip()) == 0:
            return {
                "results": [],
                "total": 0,
                "query": query_text,
                "entity_type": entity_type,
                "message": "Empty query provided"
            }

        # 检查 APOC 是否可用
        try:
            apoc_check = self.db.execute_query("RETURN apoc.version() AS version LIMIT 1")
            if not apoc_check.records:
                logger.warning("APOC library not available")
                return {
                    "results": [],
                    "total": 0,
                    "query": query_text,
                    "entity_type": entity_type,
                    "message": "APOC library not available for fuzzy search"
                }
        except Exception as e:
            logger.warning(f"APOC check failed: {str(e)}")
            # 如果没有 APOC，使用 CONTAINS 作为后备
            fallback_query = f"""
            MATCH (n:{entity_type})
            WHERE n.{search_field} IS NOT NULL
              AND n.{search_field} CONTAINS $query_text
            RETURN labels(n)[0] AS entity_type,
                   elementId(n) AS element_id,
                   n.primary_id AS primary_id,
                   n.{search_field} AS {search_field},
                   1.0 AS similarity
            ORDER BY {search_field}
            SKIP $skip
            LIMIT $limit
            """
            result = self.db.execute_query(fallback_query, {
                "query_text": query_text,
                "skip": skip,
                "limit": limit
            })

            results = []
            for record in result.records:
                results.append({
                    "entity_type": record.get("entity_type", entity_type),
                    "element_id": record.get("element_id"),
                    "primary_id": record.get("primary_id"),
                    search_field: record.get(search_field),
                    "similarity": 1.0,
                    "method": "CONTAINS_FALLBACK"
                })

            # 获取总数
            count_query = f"""
            MATCH (n:{entity_type})
            WHERE n.{search_field} IS NOT NULL
              AND n.{search_field} CONTAINS $query_text
            RETURN count(n) AS total
            """
            count_result = self.db.execute_query(count_query, {"query_text": query_text})
            total = count_result.records[0]["total"] if count_result.records else 0

            return {
                "results": results,
                "total": total,
                "returned": len(results),
                "query": query_text,
                "entity_type": entity_type,
                "search_field": search_field,
                "skip": skip,
                "limit": limit,
                "method": "CONTAINS_FALLBACK"
            }

        # 使用 APOC 进行模糊搜索
        search_query = f"""
        MATCH (n:{entity_type})
        WHERE n.{search_field} IS NOT NULL
        WITH n, apoc.text.distance(n.{search_field}, $query_text) AS distance
        WHERE distance <= $max_distance
        RETURN labels(n)[0] AS entity_type,
               elementId(n) AS element_id,
               n.primary_id AS primary_id,
               n.{search_field} AS {search_field},
               distance,
               (1.0 - (distance * 1.0 / length($query_text))) AS similarity
        ORDER BY distance, similarity DESC
        SKIP $skip
        LIMIT $limit
        """

        result = self.db.execute_query(search_query, {
            "query_text": query_text,
            "max_distance": max_distance,
            "skip": skip,
            "limit": limit
        })

        results = []
        for record in result.records:
            results.append({
                "entity_type": record.get("entity_type", entity_type),
                "element_id": record.get("element_id"),
                "primary_id": record.get("primary_id"),
                search_field: record.get(search_field),
                "distance": record.get("distance", 0),
                "similarity": record.get("similarity", 0.0),
                "method": "APOC_LEVENSHTEIN"
            })

        # 获取总数
        count_query = f"""
        MATCH (n:{entity_type})
        WHERE n.{search_field} IS NOT NULL
        WITH n, apoc.text.distance(n.{search_field}, $query_text) AS distance
        WHERE distance <= $max_distance
        RETURN count(n) AS total
        """
        count_result = self.db.execute_query(count_query, {
            "query_text": query_text,
            "max_distance": max_distance
        })
        total = count_result.records[0]["total"] if count_result.records else 0

        return {
            "results": results,
            "total": total,
            "returned": len(results),
            "query": query_text,
            "entity_type": entity_type,
            "search_field": search_field,
            "max_distance": max_distance,
            "skip": skip,
            "limit": limit,
            "method": "APOC_LEVENSHTEIN"
        }

    def get_suggestions(
        self,
        prefix: str,
        entity_type: str,
        search_field: str = "name",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        获取搜索建议 (自动完成)

        Args:
            prefix: 搜索前缀
            entity_type: 实体类型
            search_field: 搜索字段
            limit: 返回建议数量

        Returns:
            包含搜索建议的字典
        """
        if not prefix or len(prefix.strip()) == 0:
            return {
                "suggestions": [],
                "total": 0,
                "prefix": prefix,
                "entity_type": entity_type
            }

        query = f"""
        MATCH (n:{entity_type})
        WHERE n.{search_field} IS NOT NULL
          AND toLower(n.{search_field}) STARTS WITH toLower($prefix)
        RETURN DISTINCT n.{search_field} AS suggestion,
               count(*) AS frequency
        ORDER BY frequency DESC, suggestion
        LIMIT $limit
        """

        result = self.db.execute_query(query, {
            "prefix": prefix,
            "limit": limit
        })

        suggestions = []
        for record in result.records:
            suggestions.append({
                "text": record.get("suggestion"),
                "frequency": record.get("frequency", 0)
            })

        return {
            "suggestions": suggestions,
            "total": len(suggestions),
            "prefix": prefix,
            "entity_type": entity_type,
            "search_field": search_field
        }

    def aggregate_search(
        self,
        query_text: str,
        group_by: str = "entity_type",
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        聚合搜索 - 按指定维度分组统计搜索结果

        Args:
            query_text: 搜索查询文本
            group_by: 分组维度 ('entity_type', 'domain')
            limit: 每组最大结果数

        Returns:
            包含聚合搜索结果的字典
        """
        if not query_text or len(query_text.strip()) == 0:
            return {
                "groups": [],
                "total": 0,
                "query": query_text,
                "group_by": group_by
            }

        # 获取全文搜索结果
        fulltext_result = self.fulltext_search(query_text, limit=limit)

        if group_by == "entity_type":
            # 按实体类型分组
            groups = {}
            for result in fulltext_result.get("results", []):
                entity_type = result.get("entity_type", "Unknown")
                if entity_type not in groups:
                    groups[entity_type] = {
                        "entity_type": entity_type,
                        "count": 0,
                        "results": []
                    }
                groups[entity_type]["count"] += 1
                if len(groups[entity_type]["results"]) < limit:
                    groups[entity_type]["results"].append(result)

            return {
                "groups": list(groups.values()),
                "total_groups": len(groups),
                "total_results": fulltext_result.get("total", 0),
                "query": query_text,
                "group_by": group_by
            }

        elif group_by == "domain":
            # 按业务领域分组
            domain_mapping = {
                "Compound": "R&D",
                "Target": "R&D",
                "Pathway": "R&D",
                "Assay": "R&D",
                "ClinicalTrial": "Clinical",
                "Subject": "Clinical",
                "AdverseEvent": "Clinical",
                "Intervention": "Clinical",
                "Manufacturer": "Supply Chain",
                "DrugShortage": "Supply Chain",
                "DrugProduct": "Supply Chain",
                "Facility": "Supply Chain",
                "Submission": "Regulatory",
                "Approval": "Regulatory",
                "Inspection": "Regulatory",
                "ComplianceAction": "Regulatory"
            }

            groups = {}
            for result in fulltext_result.get("results", []):
                entity_type = result.get("entity_type", "Unknown")
                domain = domain_mapping.get(entity_type, "Other")

                if domain not in groups:
                    groups[domain] = {
                        "domain": domain,
                        "count": 0,
                        "entity_types": {},
                        "results": []
                    }

                groups[domain]["count"] += 1

                if entity_type not in groups[domain]["entity_types"]:
                    groups[domain]["entity_types"][entity_type] = 0
                groups[domain]["entity_types"][entity_type] += 1

                if len(groups[domain]["results"]) < limit:
                    groups[domain]["results"].append(result)

            # 转换 entity_types 为列表格式
            for domain in groups.values():
                domain["entity_types"] = [
                    {"type": k, "count": v}
                    for k, v in domain["entity_types"].items()
                ]

            return {
                "groups": list(groups.values()),
                "total_groups": len(groups),
                "total_results": fulltext_result.get("total", 0),
                "query": query_text,
                "group_by": group_by
            }

        else:
            return {
                "groups": [],
                "total": 0,
                "query": query_text,
                "group_by": group_by,
                "message": f"Invalid group_by parameter: {group_by}"
            }

    def multi_entity_search(
        self,
        query_text: str,
        entity_config: List[Dict[str, Any]],
        limit_per_entity: int = 10
    ) -> Dict[str, Any]:
        """
        多实体搜索 - 在多个实体类型中搜索

        Args:
            query_text: 搜索查询文本
            entity_config: 实体配置列表，每个配置包含 entity_type 和 search_field
            limit_per_entity: 每个实体类型的最大结果数

        Returns:
            包含多实体搜索结果的字典
        """
        if not query_text or len(query_text.strip()) == 0:
            return {
                "results": {},
                "total": 0,
                "query": query_text
            }

        all_results = {}
        total_count = 0

        for config in entity_config:
            entity_type = config.get("entity_type")
            search_field = config.get("search_field", "name")

            if not entity_type:
                continue

            try:
                # 使用模糊搜索获取结果
                result = self.fuzzy_search(
                    query_text=query_text,
                    entity_type=entity_type,
                    search_field=search_field,
                    limit=limit_per_entity,
                    skip=0
                )

                if result.get("results"):
                    all_results[entity_type] = {
                        "entity_type": entity_type,
                        "search_field": search_field,
                        "count": len(result["results"]),
                        "results": result["results"]
                    }
                    total_count += len(result["results"])

            except Exception as e:
                logger.error(f"Error searching entity type {entity_type}: {str(e)}")

        return {
            "results": all_results,
            "total_entities": len(all_results),
            "total_results": total_count,
            "query": query_text
        }
