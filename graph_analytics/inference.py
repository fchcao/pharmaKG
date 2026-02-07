#===========================================================
# PharmaKG - 关系推断
# Pharmaceutical Knowledge Graph - Relationship Inference
#===========================================================
# 版本: v1.0
# 描述: 基于图谱的关系推断和预测
#===========================================================

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class InferenceType(str, Enum):
    """推断类型"""
    DDI = "drug_drug_interaction"      # 药物-药物相互作用
    DDI_INDICATION = "drug_disease"      # 药物-疾病适应症
    TARGET_DISEASE = "target_disease"    # 靶点-疾病关联
    DRUG_REPURPOSING = "drug_repurposing" # 药物重定位
    ADVERSE_REACTION = "adverse_reaction" # 不良反应预测


@dataclass
class InferenceResult:
    """推断结果"""
    inference_type: InferenceType
    confidence: float
    entities: Tuple[str, str]
    predicted_relationship: str
    evidence: List[Dict[str, Any]]
    explanation: str
    metadata: Dict[str, Any]


class RelationshipInference:
    """
    关系推断基础类

    基于图结构推断新的关系
    """

    def __init__(self, neo4j_driver):
        """
        初始化关系推断器

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver

    def find_common_neighbors(
        self,
        entity1_id: str,
        entity2_id: str,
        neighbor_label: Optional[str] = None,
        relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        查找两个实体的共同邻居

        Args:
            entity1_id: 第一个实体 ID
            entity2_id: 第二个实体 ID
            neighbor_label: 邻居节点标签
            relationship_type: 关系类型

        Returns:
            共同邻居列表
        """
        rel_pattern = f"[:{relationship_type}]" if relationship_type else ""
        label_filter = f":{neighbor_label}" if neighbor_label else ""

        query = f"""
        MATCH (a {{primary_id: $entity1_id}})-{rel_pattern}]->(n{label_filter})<-[{rel_pattern}]-(b {{primary_id: $entity2_id}})
        RETURN DISTINCT n.primary_id as neighbor_id,
               n.name as neighbor_name,
               labels(n) as labels
        """

        with self.driver.session() as session:
            result = session.run(query, entity1_id=entity1_id, entity2_id=entity2_id)
            return [record.data() for record in result]

    def find_paths(
        self,
        entity1_id: str,
        entity2_id: str,
        max_length: int = 3,
        exclude_direct: bool = True
    ) -> List[Dict[str, Any]]:
        """
        查找两个实体之间的路径

        Args:
            entity1_id: 第一个实体 ID
            entity2_id: 第二个实体 ID
            max_length: 最大路径长度
            exclude_direct: 是否排除直接连接

        Returns:
            路径列表
        """
        min_length = 2 if exclude_direct else 1

        query = f"""
        MATCH path = (a {{primary_id: $entity1_id}})-[*{min_length}..{max_length}]-(b {{primary_id: $entity2_id}})
        RETURN [node in nodes(path) | {{
            id: node.primary_id,
            name: node.name,
            label: head(labels(node))
        }}] as nodes,
        [rel in relationships(path) | type(rel)] as relationships,
        length(path) as path_length
        ORDER BY path_length, path
        LIMIT 20
        """

        with self.driver.session() as session:
            result = session.run(query, entity1_id=entity1_id, entity2_id=entity2_id)
            return [record.data() for record in result]


class DrugDrugInteractionPredictor(RelationshipInference):
    """
    药物-药物相互作用预测器

    基于以下方法预测 DDI：
    - 共享靶点 (Shared Targets)
    - 通路重叠 (Pathway Overlap)
    - 结构相似性 (Structural Similarity)
    - 图嵌入相似度 (Graph Embedding Similarity)
    """

    def predict_interaction(
        self,
        drug1_id: str,
        drug2_id: str,
        methods: Optional[List[str]] = None
    ) -> InferenceResult:
        """
        预测两个药物之间的相互作用

        Args:
            drug1_id: 第一个药物 ID
            drug2_id: 第二个药物 ID
            methods: 使用的预测方法列表

        Returns:
            推断结果
        """
        if methods is None:
            methods = ["shared_targets", "pathway_overlap", "structural_similarity"]

        evidence = []
        confidence_scores = []

        # 检查是否已有已知的相互作用
        existing = self._check_existing_interaction(drug1_id, drug2_id)
        if existing:
            return InferenceResult(
                inference_type=InferenceType.DDI,
                confidence=1.0,
                entities=(drug1_id, drug2_id),
                predicted_relationship="KNOWN_INTERACTION",
                evidence=[{"type": "database", "source": "existing"}],
                explanation=f"Known drug-drug interaction between {drug1_id} and {drug2_id}",
                metadata=existing
            )

        # 共享靶点方法
        if "shared_targets" in methods:
            shared_targets = self._find_shared_targets(drug1_id, drug2_id)
            if shared_targets:
                evidence.append({
                    "type": "shared_targets",
                    "targets": shared_targets,
                    "count": len(shared_targets)
                })
                # 共享靶点越多，相互作用可能性越高
                confidence_scores.append(min(len(shared_targets) * 0.2, 1.0))

        # 通路重叠方法
        if "pathway_overlap" in methods:
            pathway_overlap = self._find_pathway_overlap(drug1_id, drug2_id)
            if pathway_overlap:
                evidence.append({
                    "type": "pathway_overlap",
                    "pathways": pathway_overlap,
                    "count": len(pathway_overlap)
                })
                confidence_scores.append(0.6)

        # 结构相似性方法
        if "structural_similarity" in methods:
            sim = self._calculate_structural_similarity(drug1_id, drug2_id)
            if sim and sim > 0.7:
                evidence.append({
                    "type": "structural_similarity",
                    "similarity": sim
                })
                confidence_scores.append(sim * 0.8)

        # 计算总体置信度
        confidence = 0.0
        if confidence_scores:
            confidence = max(confidence_scores)  # 取最高分数

        # 生成解释
        explanation = self._generate_ddi_explanation(drug1_id, drug2_id, evidence)

        return InferenceResult(
            inference_type=InferenceType.DDI,
            confidence=confidence,
            entities=(drug1_id, drug2_id),
            predicted_relationship="POTENTIAL_INTERACTION",
            evidence=evidence,
            explanation=explanation,
            metadata={
                "methods_used": methods,
                "evidence_count": len(evidence)
            }
        )

    def _check_existing_interaction(
        self,
        drug1_id: str,
        drug2_id: str
    ) -> Optional[Dict[str, Any]]:
        """检查是否已有已知的相互作用"""
        query = """
        MATCH (d1:Compound {primary_id: $drug1_id})-[r:INTERACTS_WITH]-(d2:Compound {primary_id: $drug2_id})
        RETURN r.interaction_type as interaction_type,
               r.severity as severity,
               r.description as description
        LIMIT 1
        """

        with self.driver.session() as session:
            result = session.run(query, drug1_id=drug1_id, drug2_id=drug2_id)
            return result.single()

    def _find_shared_targets(
        self,
        drug1_id: str,
        drug2_id: str
    ) -> List[Dict[str, Any]]:
        """查找共享的靶点"""
        query = """
        MATCH (d1:Compound {primary_id: $drug1_id})-[:TARGETS]->(t:Target)<-[:TARGETS]-(d2:Compound {primary_id: $drug2_id})
        RETURN DISTINCT t.primary_id as target_id,
               t.name as target_name,
               t.gene_symbol as gene_symbol
        """

        with self.driver.session() as session:
            result = session.run(query, drug1_id=drug1_id, drug2_id=drug2_id)
            return [record.data() for record in result]

    def _find_pathway_overlap(
        self,
        drug1_id: str,
        drug2_id: str
    ) -> List[Dict[str, Any]]:
        """查找通路重叠"""
        query = """
        MATCH (d1:Compound {primary_id: $drug1_id})-[:TARGETS]->(:Target)-[:PARTICIPATES_IN]->(p:Pathway)<-[:PARTICIPATES_IN]-(:Target)<-[:TARGETS]-(d2:Compound {primary_id: $drug2_id})
        RETURN DISTINCT p.primary_id as pathway_id,
               p.name as pathway_name
        """

        with self.driver.session() as session:
            result = session.run(query, drug1_id=drug1_id, drug2_id=drug2_id)
            return [record.data() for record in result]

    def _calculate_structural_similarity(
        self,
        drug1_id: str,
        drug2_id: str
    ) -> Optional[float]:
        """计算结构相似度（基于指纹）"""
        # 简化实现：使用共享的化学子结构
        query = """
        MATCH (d1:Compound {primary_id: $drug1_id}), (d2:Compound {primary_id: $drug2_id})
        WHERE d1.molecular_formula = d2.molecular_formula
           OR d1.inchikey[0..7] = d2.inchikey[0..7]
        RETURN CASE WHEN d1.inchikey[0..14] = d2.inchikey[0..14] THEN 1.0
                    WHEN d1.inchikey[0..7] = d2.inchikey[0..7] THEN 0.8
                    ELSE 0.5 END as similarity
        """

        with self.driver.session() as session:
            result = session.run(query, drug1_id=drug1_id, drug2_id=drug2_id)
            record = result.single()
            return record["similarity"] if record else None

    def _generate_ddi_explanation(
        self,
        drug1_id: str,
        drug2_id: str,
        evidence: List[Dict[str, Any]]
    ) -> str:
        """生成 DDI 预测解释"""
        if not evidence:
            return f"Insufficient evidence to predict interaction between {drug1_id} and {drug2_id}"

        parts = []
        for ev in evidence:
            if ev["type"] == "shared_targets":
                parts.append(f"share {ev['count']} target(s)")
            elif ev["type"] == "pathway_overlap":
                parts.append(f"have {ev['count']} overlapping pathway(s)")
            elif ev["type"] == "structural_similarity":
                parts.append(f"have {ev['similarity']:.2f} structural similarity")

        return f"{drug1_id} and {drug2_id} " + " and ".join(parts)


class DrugDiseasePredictor(RelationshipInference):
    """
    药物-疾病预测器

    预测：
    - 药物适应症 (Drug Indications)
    - 药物重定位 (Drug Repurposing)
    - 疾病治疗推荐
    """

    def predict_indication(
        self,
        drug_id: str,
        disease_id: str,
        max_path_length: int = 3
    ) -> InferenceResult:
        """
        预测药物对疾病的适应症

        Args:
            drug_id: 药物 ID
            disease_id: 疾病 ID
            max_path_length: 最大路径长度

        Returns:
            推断结果
        """
        evidence = []
        confidence_scores = []

        # 检查是否已有已知适应症
        existing = self._check_existing_indication(drug_id, disease_id)
        if existing:
            return InferenceResult(
                inference_type=InferenceType.DDI_INDICATION,
                confidence=1.0,
                entities=(drug_id, disease_id),
                predicted_relationship="KNOWN_INDICATION",
                evidence=[{"type": "database", "source": "existing"}],
                explanation=f"Known indication of {drug_id} for {disease_id}",
                metadata=existing
            )

        # 查找药物-靶点-疾病路径
        target_disease_paths = self._find_target_disease_paths(drug_id, disease_id)
        if target_disease_paths:
            evidence.append({
                "type": "target_disease_association",
                "paths": target_disease_paths[:5],  # 最多5条
                "count": len(target_disease_paths)
            })
            confidence_scores.append(min(len(target_disease_paths) * 0.15, 0.9))

        # 查找相似药物的适应症
        similar_drugs = self._find_similar_drugs_with_indication(drug_id, disease_id)
        if similar_drugs:
            evidence.append({
                "type": "similar_drug_indications",
                "drugs": similar_drugs[:5],
                "count": len(similar_drugs)
            })
            confidence_scores.append(0.7)

        # 查找共享通路
        pathway_paths = self._find_pathway_paths(drug_id, disease_id)
        if pathway_paths:
            evidence.append({
                "type": "pathway_association",
                "pathways": pathway_paths,
                "count": len(pathway_paths)
            })
            confidence_scores.append(0.5)

        # 计算总体置信度
        confidence = max(confidence_scores) if confidence_scores else 0.0

        return InferenceResult(
            inference_type=InferenceType.DDI_INDICATION,
            confidence=confidence,
            entities=(drug_id, disease_id),
            predicted_relationship="POTENTIAL_INDICATION" if confidence > 0.3 else "UNLIKELY_INDICATION",
            evidence=evidence,
            explanation=self._generate_indication_explanation(drug_id, disease_id, evidence),
            metadata={
                "evidence_count": len(evidence),
                "path_length": max_path_length
            }
        )

    def _check_existing_indication(
        self,
        drug_id: str,
        disease_id: str
    ) -> Optional[Dict[str, Any]]:
        """检查是否已有已知适应症"""
        query = """
        MATCH (d:Compound {primary_id: $drug_id})-[r:TREATS]->(dis:Disease {primary_id: $disease_id})
        RETURN r.phase as phase,
               r.status as status,
               r.evidence_level as evidence_level
        LIMIT 1
        """

        with self.driver.session() as session:
            result = session.run(query, drug_id=drug_id, disease_id=disease_id)
            return result.single()

    def _find_target_disease_paths(
        self,
        drug_id: str,
        disease_id: str
    ) -> List[Dict[str, Any]]:
        """查找药物-靶点-疾病路径"""
        query = """
        MATCH path = (d:Compound {primary_id: $drug_id})-[:TARGETS]->(t:Target)-[:ASSOCIATED_WITH]->(dis:Disease {primary_id: $disease_id})
        RETURN t.primary_id as target_id,
               t.name as target_name,
               [rel in relationships(path) | type(rel)] as relationship_types
        """

        with self.driver.session() as session:
            result = session.run(query, drug_id=drug_id, disease_id=disease_id)
            return [record.data() for record in result]

    def _find_similar_drugs_with_indication(
        self,
        drug_id: str,
        disease_id: str
    ) -> List[Dict[str, Any]]:
        """查找有相似适应症的药物"""
        # 首先获取药物的结构特征
        query = """
        MATCH (d:Compound {primary_id: $drug_id})
        OPTIONAL MATCH (d)-[:TARGETS]->(t:Target)
        WITH d, collect(DISTINCT t.primary_id) as targets
        MATCH (similar:Compound)-[:TARGETS]->(t:Target)
        WHERE t.primary_id IN targets AND similar.primary_id <> $drug_id
        WITH similar, count(DISTINCT t) as shared_targets
        WHERE shared_targets >= 2
        MATCH (similar)-[:TREATS]->(dis:Disease {primary_id: $disease_id})
        RETURN similar.primary_id as drug_id,
               similar.name as drug_name,
               shared_targets
        ORDER BY shared_targets DESC
        LIMIT 10
        """

        with self.driver.session() as session:
            result = session.run(query, drug_id=drug_id, disease_id=disease_id)
            return [record.data() for record in result]

    def _find_pathway_paths(
        self,
        drug_id: str,
        disease_id: str
    ) -> List[Dict[str, Any]]:
        """查找通路关联路径"""
        query = """
        MATCH (d:Compound {primary_id: $drug_id})-[:TARGETS]->(:Target)-[:PARTICIPATES_IN]->(p:Pathway)<-[:INVOLVED_IN]-(dis:Disease {primary_id: $disease_id})
        RETURN DISTINCT p.primary_id as pathway_id,
               p.name as pathway_name
        """

        with self.driver.session() as session:
            result = session.run(query, drug_id=drug_id, disease_id=disease_id)
            return [record.data() for record in result]

    def _generate_indication_explanation(
        self,
        drug_id: str,
        disease_id: str,
        evidence: List[Dict[str, Any]]
    ) -> str:
        """生成适应症预测解释"""
        if not evidence:
            return f"Insufficient evidence to predict {drug_id} for {disease_id}"

        parts = []
        for ev in evidence:
            if ev["type"] == "target_disease_association":
                parts.append(f"targets linked to disease ({ev['count']} association(s))")
            elif ev["type"] == "similar_drug_indications":
                parts.append(f"similar to drugs treating disease ({ev['count']} drug(s))")
            elif ev["type"] == "pathway_association":
                parts.append(f"shares disease-relevant pathways ({ev['count']} pathway(s))")

        return f"{drug_id} may treat {disease_id}: " + "; ".join(parts)


class TargetDiseasePredictor(RelationshipInference):
    """
    靶点-疾病预测器

    预测靶点与疾病的关联
    """

    def predict_association(
        self,
        target_id: str,
        disease_id: str
    ) -> InferenceResult:
        """
        预测靶点与疾病的关联

        Args:
            target_id: 靶点 ID
            disease_id: 疾病 ID

        Returns:
            推断结果
        """
        evidence = []
        confidence_scores = []

        # 检查是否已有已知关联
        existing = self._check_existing_association(target_id, disease_id)
        if existing:
            return InferenceResult(
                inference_type=InferenceType.TARGET_DISEASE,
                confidence=1.0,
                entities=(target_id, disease_id),
                predicted_relationship="KNOWN_ASSOCIATION",
                evidence=[{"type": "database", "source": "existing"}],
                explanation=f"Known association between {target_id} and {disease_id}",
                metadata=existing
            )

        # 查找关联疾病的药物
        drug_paths = self._find_drug_paths(target_id, disease_id)
        if drug_paths:
            evidence.append({
                "type": "drug_mediates_association",
                "drugs": drug_paths,
                "count": len(drug_paths)
            })
            confidence_scores.append(min(len(drug_paths) * 0.25, 0.8))

        # 查找通路关联
        pathway_associations = self._find_pathway_associations(target_id, disease_id)
        if pathway_associations:
            evidence.append({
                "type": "pathway_association",
                "pathways": pathway_associations,
                "count": len(pathway_associations)
            })
            confidence_scores.append(0.6)

        # 查找基因本体关联
        go_associations = self._find_go_associations(target_id, disease_id)
        if go_associations:
            evidence.append({
                "type": "gene_ontology_association",
                "terms": go_associations,
                "count": len(go_associations)
            })
            confidence_scores.append(0.5)

        confidence = max(confidence_scores) if confidence_scores else 0.0

        return InferenceResult(
            inference_type=InferenceType.TARGET_DISEASE,
            confidence=confidence,
            entities=(target_id, disease_id),
            predicted_relationship="POTENTIAL_ASSOCIATION" if confidence > 0.3 else "UNLIKELY_ASSOCIATION",
            evidence=evidence,
            explanation=self._generate_association_explanation(target_id, disease_id, evidence),
            metadata={"evidence_count": len(evidence)}
        )

    def _check_existing_association(
        self,
        target_id: str,
        disease_id: str
    ) -> Optional[Dict[str, Any]]:
        """检查是否已有已知关联"""
        query = """
        MATCH (t:Target {primary_id: $target_id})-[r:ASSOCIATED_WITH]->(d:Disease {primary_id: $disease_id})
        RETURN r.association_type as association_type,
               r.evidence_count as evidence_count,
               r.confidence as confidence
        LIMIT 1
        """

        with self.driver.session() as session:
            result = session.run(query, target_id=target_id, disease_id=disease_id)
            return result.single()

    def _find_drug_paths(
        self,
        target_id: str,
        disease_id: str
    ) -> List[Dict[str, Any]]:
        """查找药物介导的关联"""
        query = """
        MATCH (t:Target {primary_id: $target_id})<-[:TARGETS]-(d:Compound)-[:TREATS]->(dis:Disease {primary_id: $disease_id})
        RETURN DISTINCT d.primary_id as drug_id,
               d.name as drug_name,
               d.approved as is_approved
        """

        with self.driver.session() as session:
            result = session.run(query, target_id=target_id, disease_id=disease_id)
            return [record.data() for record in result]

    def _find_pathway_associations(
        self,
        target_id: str,
        disease_id: str
    ) -> List[Dict[str, Any]]:
        """查找通路关联"""
        query = """
        MATCH (t:Target {primary_id: $target_id})-[:PARTICIPATES_IN]->(p:Pathway)<-[:INVOLVED_IN]-(d:Disease {primary_id: $disease_id})
        RETURN DISTINCT p.primary_id as pathway_id,
               p.name as pathway_name
        """

        with self.driver.session() as session:
            result = session.run(query, target_id=target_id, disease_id=disease_id)
            return [record.data() for record in result]

    def _find_go_associations(
        self,
        target_id: str,
        disease_id: str
    ) -> List[Dict[str, Any]]:
        """查找基因本体关联"""
        # 简化实现：通过共同注释
        query = """
        MATCH (t:Target {primary_id: $target_id})-[:HAS_ANNOTATION]->(go:GOTerm)<-[:HAS_ANNOTATION]-(:Target)-[:ASSOCIATED_WITH]->(d:Disease {primary_id: $disease_id})
        RETURN DISTINCT go.primary_id as go_id,
               go.name as go_name,
               go.namespace as namespace
        LIMIT 20
        """

        with self.driver.session() as session:
            result = session.run(query, target_id=target_id, disease_id=disease_id)
            return [record.data() for record in result]

    def _generate_association_explanation(
        self,
        target_id: str,
        disease_id: str,
        evidence: List[Dict[str, Any]]
    ) -> str:
        """生成关联预测解释"""
        if not evidence:
            return f"Insufficient evidence to predict association between {target_id} and {disease_id}"

        parts = []
        for ev in evidence:
            if ev["type"] == "drug_mediates_association":
                parts.append(f"targeted by drugs treating disease ({ev['count']} drug(s))")
            elif ev["type"] == "pathway_association":
                parts.append(f"shares disease-relevant pathways ({ev['count']} pathway(s))")
            elif ev["type"] == "gene_ontology_association":
                parts.append(f"shares functional annotations ({ev['count']} term(s))")

        return f"{target_id} may be associated with {disease_id}: " + "; ".join(parts)
