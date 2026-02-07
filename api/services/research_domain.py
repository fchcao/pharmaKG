#===========================================================
# 制药行业知识图谱 - R&D 领域查询服务
# Pharmaceutical Knowledge Graph - R&D Domain Query Service
#===========================================================
# 版本: v1.0
# 创建日期: 2025-02-06
#===========================================================

from typing import List, Optional, Any
import logging

from .database import get_db

logger = logging.getLogger(__name__)


class ResearchDomainService:
    """R&D领域查询服务"""

    def __init__(self):
        self.db = get_db()

    def count_compounds(self) -> int:
        """统计化合物数量"""
        query = """
        MATCH (c:Compound)
        RETURN count(c) AS count
        """
        result = self.db.execute_query(query)
        return result.records[0]["count"] if result.records else 0

    def count_targets(self) -> int:
        """统计靶点数量"""
        query = """
        MATCH (t:Target)
        RETURN count(t) AS count
        """
        result = self.db.execute_query(query)
        return result.records[0]["count"] if result.records else 0

    def get_compound_by_id(self, compound_id: str) -> dict:
        """根据ID获取化合物"""
        query = """
        MATCH (c:Compound {primary_id: $compound_id})
        OPTIONAL MATCH (c)-[:HAS_DEVELOPMENT_STAGE]->(ds:DevelopmentStage)
        OPTIONAL MATCH (c)-[:HAS_STRUCTURE_TYPE]->(st:StructureType)
        RETURN c.primary_id AS primary_id,
               c.name AS name,
               c.smiles AS smiles,
               c.inchikey AS inchikey,
               c.molecular_weight AS molecular_weight,
               c.logp AS logp,
               c.hbond_donors AS hbond_donors,
               c.hbond_acceptors AS hbond_acceptors,
               c.rotatable_bonds AS rotatable_bonds,
               ds.name AS development_stage,
               st.name AS structure_type
        """
        result = self.db.execute_query(query, {"compound_id": compound_id})
        return result.records[0] if result.records else {}

    def search_compounds(self, params: dict) -> List[dict]:
        """搜索化合物"""
        conditions = []
        parameters = {}

        if params.get("name"):
            conditions.append("c.name CONTAINS $name")
            parameters["name"] = params["name"]

        if params.get("min_molecular_weight"):
            conditions.append("c.molecular_weight >= $min_mw")
            parameters["min_mw"] = params["min_molecular_weight"]

        if params.get("max_molecular_weight"):
            conditions.append("c.molecular_weight <= $max_mw")
            parameters["max_mw"] = params["max_molecular_weight"]

        if params.get("development_stage"):
            conditions.append("c.development_stage = $stage")
            parameters["stage"] = params["development_stage"]

        if params.get("is_approved") is not None:
            conditions.append("c.is_approved_drug = $is_approved")
            parameters["is_approved"] = params["is_approved"]

        where_clause = " AND ".join(conditions) if conditions else "true"

        query = f"""
        MATCH (c:Compound)-[:HAS_DEVELOPMENT_STAGE]->(ds:DevelopmentStage)
        WHERE {where_clause}
        RETURN c.primary_id AS primary_id,
               c.name AS name,
               c.smiles AS smiles,
               c.inchikey AS inchikey,
               c.molecular_weight AS molecular_weight,
               c.logp AS logp,
               c.is_approved_drug AS is_approved,
               ds.name AS development_stage
        ORDER BY c.name
        LIMIT $limit
        SKIP $offset
        """

        page = params.get("page", 1)
        page_size = params.get("page_size", 20)

        result = self.db.execute_query(query, {
            **parameters,
            "limit": page_size,
            "offset": (page - 1) * page_size
        })

        return result.records

    def get_compound_targets(self, compound_id: str) -> List[dict]:
        """获取化合物的靶点"""
        query = """
        MATCH (c:Compound {primary_id: $compound_id})-[r:INHIBITS|ACTIVATES|BINDS_TO]->(t:Target)-[:HAS_TARGET_TYPE]->(tt:TargetType)
        RETURN t.primary_id AS primary_id,
               t.name AS name,
               t.gene_symbol AS gene_symbol,
               t.uniprot_id AS uniprot_id,
               tt.name AS target_type,
               type(r) AS relationship_type,
               r.ic50 AS ic50,
               r.ic50_unit AS ic50_unit
        ORDER BY t.name
        """
        result = self.db.execute_query(query, {"compound_id": compound_id})
        return result.records

    def get_target_compounds(self, target_id: str) -> List[dict]:
        """获取靶点的化合物"""
        query = """
        MATCH (t:Target {primary_id: $target_id})<[r:INHIBITS|ACTIVATES|BINDS_TO]-(c:Compound)-[:HAS_DEVELOPMENT_STAGE]->(ds:DevelopmentStage)
        RETURN c.primary_id AS primary_id,
               c.name AS name,
               c.smiles AS smiles,
               c.molecular_weight AS molecular_weight,
               ds.name AS development_stage,
               type(r) AS relationship_type,
               r.ic50 AS ic50,
               r.ic50_unit AS ic50_unit
        ORDER BY r.ic50
        """
        result = self.db.execute_query(query, {"target_id": target_id})
        return result.records

    def get_assays_by_compound(self, compound_id: str) -> List[dict]:
        """获取化合物的实验"""
        query = """
        MATCH (c:Compound {primary_id: $compound_id})<-[:TESTS_COMPOUND]-(a:Assay)-[:HAS_ASSAY_TYPE]->(at:AssayType)
        OPTIONAL MATCH (a)-[:MEASURES]->(t:Target)
        RETURN a.assay_id AS assay_id,
               a.name AS assay_name,
               at.name AS assay_type,
               a.detection_method AS detection_method,
               a.cell_line AS cell_line,
               t.name AS target_name
        ORDER BY a.name
        """
        result = self.db.execute_query(query, {"compound_id": compound_id})
        return result.records

    def get_pathway_targets(self, pathway_id: str) -> List[dict]:
        """获取通路的靶点"""
        query = """
        MATCH (p:Pathway {primary_id: $pathway_id})-[:INCLUDES_TARGET]->(t:Target)-[:HAS_TARGET_TYPE]->(tt:TargetType)
        RETURN t.primary_id AS primary_id,
               t.name AS name,
               t.gene_symbol AS gene_symbol,
               tt.name AS target_type
        ORDER BY t.name
        """
        result = self.db.execute_query(query, {"pathway_id": pathway_id})
        return result.records

    def get_disease_targets(self, disease_name: str) -> List[dict]:
        """获取疾病相关的靶点"""
        query = """
        MATCH (d:Condition {condition_name: $disease_name})<-[:HAS_TARGET_ASSOCIATION]-(t:Target)-[:HAS_TARGET_TYPE]->(tt:TargetType)
        RETURN t.primary_id AS primary_id,
               t.name AS name,
               t.gene_symbol AS gene_symbol,
               tt.name AS target_type
        ORDER BY tt.name, t.name
        """
        result = self.db.execute_query(query, {"disease_name": disease_name})
        return result.records

    def get_pathway_by_disease(self, disease_name: str) -> List[dict]:
        """获取疾病相关通路"""
        query = """
        MATCH (d:Condition {condition_name: $disease_name})<-[:RELATED_TO_DISEASE]-(p:Pathway)-[:HAS_PATHWAY_TYPE]->(pt:PathwayType)
        RETURN p.primary_id AS primary_id,
               p.name AS name,
               pt.name AS pathway_type,
               p.organism AS organism
        ORDER BY p.name
        """
        result = self.db.execute_query(query, {"disease_name": disease_name})
        return result.records

    def get_sar_data(self, compound_id: str) -> List[dict]:
        """获取化合物的SAR数据"""
        query = """
        MATCH (c:Compound {primary_id: $compound_id})-[:HAS_SAR_DATA]->(sar:SARData)-[:LINKS_TARGET]->(t:Target)
        RETURN c.primary_id AS compound_id,
               c.name AS compound_name,
               t.name AS target_name,
               sar.activity_value AS activity_value,
               sar.activity_unit AS activity_unit,
               sar.measurement_type AS measurement_type
        ORDER BY sar.activity_value
        """
        result = self.db.execute_query(query, {"compound_id": compound_id})
        return result.records
