#===========================================================
# PharmaKG - 预测器
# Pharmaceutical Knowledge Graph - Predictors
#===========================================================
# 版本: v1.0
# 描述: 特定领域预测模型
#===========================================================

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class PredictionType(str, Enum):
    """预测类型"""
    DRUG_REPURPOSING = "drug_repurposing"
    ADVERSE_REACTION = "adverse_reaction"
    TRIAL_OUTCOME = "trial_outcome"
    DRUG_EFFICACY = "drug_efficacy"


@dataclass
class PredictionResult:
    """预测结果"""
    prediction_type: PredictionType
    prediction: Any
    confidence: float
    evidence: List[Dict[str, Any]]
    explanation: str
    metadata: Dict[str, Any]


class DrugRepurposingPredictor:
    """
    药物重定位预测器

    预测现有药物的新适应症
    """

    def __init__(self, neo4j_driver):
        """
        初始化药物重定位预测器

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver

    def predict_for_disease(
        self,
        disease_id: str,
        top_k: int = 20,
        min_phase: int = 2
    ) -> List[PredictionResult]:
        """
        为指定疾病预测药物重定位机会

        Args:
            disease_id: 疾病 ID
            top_k: 返回前 K 个结果
            min_phase: 最小临床试验阶段

        Returns:
            预测结果列表
        """
        # 方法1: 基于靶点关联
        target_based = self._target_based_prediction(disease_id, min_phase)

        # 方法2: 基于相似药物
        similarity_based = self._similarity_based_prediction(disease_id, min_phase)

        # 方法3: 基于通路
        pathway_based = self._pathway_based_prediction(disease_id, min_phase)

        # 合并和排序结果
        all_predictions = {}

        for pred in target_based + similarity_based + pathway_based:
            drug_id = pred.metadata["drug_id"]
            if drug_id not in all_predictions:
                all_predictions[drug_id] = pred
            else:
                # 合并证据
                all_predictions[drug_id].evidence.extend(pred.evidence)
                # 更新置信度（取最大值）
                all_predictions[drug_id].confidence = max(
                    all_predictions[drug_id].confidence,
                    pred.confidence
                )

        # 按置信度排序
        sorted_predictions = sorted(
            all_predictions.values(),
            key=lambda x: x.confidence,
            reverse=True
        )

        return sorted_predictions[:top_k]

    def _target_based_prediction(
        self,
        disease_id: str,
        min_phase: int
    ) -> List[PredictionResult]:
        """基于靶点的预测"""
        query = """
        MATCH (d:Disease {primary_id: $disease_id})<-[:ASSOCIATED_WITH]-(t:Target)<-[:TARGETS]-(drug:Compound)
        WHERE NOT (drug)-[:TREATS]->(d:Disease {primary_id: $disease_id})
        RETURN DISTINCT drug.primary_id as drug_id, drug.name as drug_name,
               t.primary_id as target_id, t.name as target_name
        """

        with self.driver.session() as session:
            result = session.run(query, disease_id=disease_id)
            records = [record.data() for record in result]

        predictions = []
        for record in records:
            predictions.append(PredictionResult(
                prediction_type=PredictionType.DRUG_REPURPOSING,
                prediction=record["drug_id"],
                confidence=0.7,
                evidence=[{
                    "type": "target_association",
                    "target_id": record["target_id"],
                    "target_name": record["target_name"]
                }],
                explanation=f"Targets {record['target_name']}, which is associated with disease",
                metadata={
                    "drug_id": record["drug_id"],
                    "drug_name": record["drug_name"],
                    "method": "target_based"
                }
            ))

        return predictions

    def _similarity_based_prediction(
        self,
        disease_id: str,
        min_phase: int
    ) -> List[PredictionResult]:
        """基于相似药物的预测"""
        query = """
        // 获取已知治疗该疾病的药物
        MATCH (known_drug:Compound)-[:TREATS]->(d:Disease {primary_id: $disease_id})

        // 找到与已知药物共享靶点的药物
        MATCH (known_drug)-[:TARGETS]->(t:Target)<-[:TARGETS]-(candidate:Compound)
        WHERE NOT (candidate)-[:TREATS]->(d:Disease {primary_id: $disease_id})

        WITH candidate, count(DISTINCT t) as shared_targets
        RETURN candidate.primary_id as drug_id, candidate.name as drug_name,
               shared_targets, collect(DISTINCT t.name) as target_names
        ORDER BY shared_targets DESC
        LIMIT 20
        """

        with self.driver.session() as session:
            result = session.run(query, disease_id=disease_id)
            records = [record.data() for record in result]

        predictions = []
        for record in records:
            confidence = min(0.5 + record["shared_targets"] * 0.1, 0.95)

            predictions.append(PredictionResult(
                prediction_type=PredictionType.DRUG_REPURPOSING,
                prediction=record["drug_id"],
                confidence=confidence,
                evidence=[{
                    "type": "similar_drug",
                    "shared_targets": record["shared_targets"],
                    "target_names": record["target_names"]
                }],
                explanation=f"Shares {record['shared_targets']} target(s) with drugs treating disease",
                metadata={
                    "drug_id": record["drug_id"],
                    "drug_name": record["drug_name"],
                    "method": "similarity_based"
                }
            ))

        return predictions

    def _pathway_based_prediction(
        self,
        disease_id: str,
        min_phase: int
    ) -> List[PredictionResult]:
        """基于通路的预测"""
        query = """
        // 获取疾病相关通路
        MATCH (d:Disease {primary_id: $disease_id})<-[:INVOLVED_IN]-(p:Pathway)

        // 找到作用于这些通路的药物
        MATCH (drug:Compound)-[:TARGETS]->(:Target)-[:PARTICIPATES_IN]->(p)
        WHERE NOT (drug)-[:TREATS]->(d:Disease {primary_id: $disease_id})

        RETURN DISTINCT drug.primary_id as drug_id, drug.name as drug_name,
               count(DISTINCT p) as pathway_count
        ORDER BY pathway_count DESC
        LIMIT 20
        """

        with self.driver.session() as session:
            result = session.run(query, disease_id=disease_id)
            records = [record.data() for record in result]

        predictions = []
        for record in records:
            confidence = min(0.4 + record["pathway_count"] * 0.15, 0.9)

            predictions.append(PredictionResult(
                prediction_type=PredictionType.DRUG_REPURPOSING,
                prediction=record["drug_id"],
                confidence=confidence,
                evidence=[{
                    "type": "pathway_association",
                    "pathway_count": record["pathway_count"]
                }],
                explanation=f"Acts on {record['pathway_count']} disease-relevant pathway(s)",
                metadata={
                    "drug_id": record["drug_id"],
                    "drug_name": record["drug_name"],
                    "method": "pathway_based"
                }
            ))

        return predictions


class AdverseReactionPredictor:
    """
    不良反应预测器

    预测药物可能的不良反应
    """

    def __init__(self, neo4j_driver):
        """
        初始化不良反应预测器

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver

    def predict_for_drug(
        self,
        drug_id: str,
        top_k: int = 10
    ) -> List[PredictionResult]:
        """
        预测药物可能的不良反应

        Args:
            drug_id: 药物 ID
            top_k: 返回前 K 个结果

        Returns:
            预测结果列表
        """
        predictions = []

        # 方法1: 基于靶点不良反应
        target_based = self._predict_by_targets(drug_id)

        # 方法2: 基于结构相似药物的不良反应
        similarity_based = self._predict_by_similarity(drug_id)

        # 方法3: 基于药物类别
        class_based = self._predict_by_class(drug_id)

        # 合并结果
        all_reactions = {}

        for pred in target_based + similarity_based + class_based:
            reaction = pred.prediction
            if reaction not in all_reactions:
                all_reactions[reaction] = pred
            else:
                # 合并证据，更新置信度
                all_reactions[reaction].evidence.extend(pred.evidence)
                all_reactions[reaction].confidence = max(
                    all_reactions[reaction].confidence,
                    pred.confidence
                )

        # 排序
        sorted_predictions = sorted(
            all_reactions.values(),
            key=lambda x: x.confidence,
            reverse=True
        )

        return sorted_predictions[:top_k]

    def _predict_by_targets(
        self,
        drug_id: str
    ) -> List[PredictionResult]:
        """基于靶点预测"""
        query = """
        MATCH (drug:Compound {primary_id: $drug_id})-[:TARGETS]->(t:Target)
        MATCH (other:Compound)-[:TARGETS]->(t)
        MATCH (other)-[:CAUSES]->(ae:AdverseEvent)
        RETURN DISTINCT ae.primary_id as event_id, ae.name as event_name,
               ae.severity as severity, count(*) as frequency
        ORDER BY frequency DESC
        LIMIT 10
        """

        with self.driver.session() as session:
            try:
                result = session.run(query, drug_id=drug_id)
                records = [record.data() for record in result]
            except Exception:
                # AdverseEvent 节点可能不存在
                return []

        predictions = []
        for record in records:
            predictions.append(PredictionResult(
                prediction_type=PredictionType.ADVERSE_REACTION,
                prediction=record["event_name"],
                confidence=min(0.3 + record["frequency"] * 0.1, 0.8),
                evidence=[{
                    "type": "target_based",
                    "frequency": record["frequency"]
                }],
                explanation=f"Observed in drugs sharing target(s)",
                metadata={
                    "severity": record.get("severity"),
                    "method": "target_based"
                }
            ))

        return predictions

    def _predict_by_similarity(
        self,
        drug_id: str
    ) -> List[PredictionResult]:
        """基于结构相似性预测"""
        # 获取结构相似的药物
        query = """
        MATCH (d:Compound {primary_id: $drug_id})
        MATCH (d)-[:TARGETS]->(t:Target)<-[:TARGETS]-(similar:Compound)
        WHERE d.inchikey[0..7] = similar.inchikey[0..7]
        RETURN similar.primary_id as drug_id, similar.name as drug_name
        LIMIT 10
        """

        with self.driver.session() as session:
            try:
                result = session.run(query, drug_id=drug_id)
                similar_drugs = [record.data() for record in result]
            except Exception:
                return []

        # 这里可以查询这些药物的不良反应
        # 简化实现
        predictions = []

        for drug in similar_drugs[:3]:
            predictions.append(PredictionResult(
                prediction_type=PredictionType.ADVERSE_REACTION,
                prediction="Unknown",
                confidence=0.4,
                evidence=[{
                    "type": "similarity_based",
                    "similar_drug": drug["drug_name"]
                }],
                explanation=f"Similar to {drug['drug_name']}",
                metadata={"method": "similarity_based"}
            ))

        return predictions

    def _predict_by_class(
        self,
        drug_id: str
    ) -> List[PredictionResult]:
        """基于药物类别预测"""
        query = """
        MATCH (d:Compound {primary_id: $drug_id})
        OPTIONAL MATCH (d)-[:IN_CLASS]->(dc:DrugClass)
        RETURN dc.name as class_name
        """

        with self.driver.session() as session:
            try:
                result = session.run(query, drug_id=drug_id)
                record = result.single()
                if not record or not record["class_name"]:
                    return []
                class_name = record["class_name"]
            except Exception:
                return []

        # 基于类别的已知不良反应
        # 简化实现
        return []


class ClinicalTrialOutcomePredictor:
    """
    临床试验结果预测器

    预测临床试验的可能结果
    """

    def __init__(self, neo4j_driver):
        """
        初始化试验结果预测器

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver

    def predict_trial_outcome(
        self,
        trial_id: str
    ) -> PredictionResult:
        """
        预测试验结果

        Args:
            trial_id: 试验 ID

        Returns:
            预测结果
        """
        # 获取试验信息
        trial_info = self._get_trial_info(trial_id)
        if not trial_info:
            return PredictionResult(
                prediction_type=PredictionType.TRIAL_OUTCOME,
                prediction="UNKNOWN",
                confidence=0.0,
                evidence=[],
                explanation="Trial not found",
                metadata={}
            )

        # 计算预测特征
        features = self._extract_trial_features(trial_info)

        # 基于历史数据预测
        prediction = self._predict_from_features(features)

        return prediction

    def _get_trial_info(self, trial_id: str) -> Optional[Dict[str, Any]]:
        """获取试验信息"""
        query = """
        MATCH (t:ClinicalTrial {primary_id: $trial_id})
        RETURN t.phase as phase, t.enrollment as enrollment,
               t.conditions as conditions, t.interventions as interventions
        """

        with self.driver.session() as session:
            result = session.run(query, trial_id=trial_id)
            return result.single()

    def _extract_trial_features(self, trial_info: Dict[str, Any]) -> Dict[str, Any]:
        """提取试验特征"""
        features = {}

        # 阶段
        phase = trial_info.get("phase", "")
        features["phase"] = phase
        features["phase_numeric"] = self._parse_phase(phase)

        # 招募人数
        enrollment = trial_info.get("enrollment")
        features["enrollment"] = enrollment or 0
        features["enrollment_log"] = np.log1p(enrollment or 1)

        # 疾病数量
        conditions = trial_info.get("conditions", [])
        features["num_conditions"] = len(conditions) if conditions else 0

        # 干预措施数量
        interventions = trial_info.get("interventions", [])
        features["num_interventions"] = len(interventions) if interventions else 0

        return features

    def _parse_phase(self, phase: str) -> int:
        """解析试验阶段"""
        phase_mapping = {
            "Phase 1": 1,
            "Phase 2": 2,
            "Phase 3": 3,
            "Phase 4": 4,
            "Early Phase 1": 0.5
        }

        return phase_mapping.get(phase, 0)

    def _predict_from_features(self, features: Dict[str, Any]) -> PredictionResult:
        """基于特征预测"""
        # 简化预测逻辑
        phase = features["phase_numeric"]
        enrollment = features["enrollment"]

        # 基于阶段的基础成功率
        phase_success_rate = {
            1: 0.70,
            2: 0.50,
            3: 0.60,
            4: 0.85
        }

        base_success = phase_success_rate.get(phase, 0.5)

        # 招募人数调整
        if enrollment > 0:
            if enrollment < 50:
                base_success *= 0.9
            elif enrollment > 500:
                base_success *= 1.05

        # 限制在合理范围
        base_success = max(0.2, min(0.95, base_success))

        return PredictionResult(
            prediction_type=PredictionType.TRIAL_OUTCOME,
            prediction="POSITIVE" if base_success > 0.5 else "NEGATIVE",
            confidence=0.5 + abs(base_success - 0.5),
            evidence=[{
                "type": "phase_based",
                "phase": features["phase"],
                "enrollment": enrollment
            }],
            explanation=f"Predicted success probability: {base_success:.2%}",
            metadata={
                "success_probability": base_success,
                "features": features
            }
        )


class DrugEfficacyPredictor:
    """
    药物疗效预测器

    预测药物对特定疾病的疗效
    """

    def __init__(self, neo4j_driver):
        """
        初始化疗效预测器

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver

    def predict_efficacy(
        self,
        drug_id: str,
        disease_id: str
    ) -> PredictionResult:
        """
        预测药物对疾病的疗效

        Args:
            drug_id: 药物 ID
            disease_id: 疾病 ID

        Returns:
            预测结果
        """
        # 收集证据
        evidence = []
        confidence_scores = []

        # 证据1: 靶点关联强度
        target_score = self._assess_target_association(drug_id, disease_id)
        if target_score > 0:
            evidence.append({
                "type": "target_association",
                "score": target_score
            })
            confidence_scores.append(target_score)

        # 证据2: 相似药物疗效
        similarity_score = self._assess_similar_drug_efficacy(drug_id, disease_id)
        if similarity_score > 0:
            evidence.append({
                "type": "similar_drug_efficacy",
                "score": similarity_score
            })
            confidence_scores.append(similarity_score)

        # 证据3: 通路覆盖
        pathway_score = self._assess_pathway_coverage(drug_id, disease_id)
        if pathway_score > 0:
            evidence.append({
                "type": "pathway_coverage",
                "score": pathway_score
            })
            confidence_scores.append(pathway_score)

        # 综合预测
        overall_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        efficacy_prediction = "HIGH" if overall_confidence > 0.7 else "MODERATE" if overall_confidence > 0.4 else "LOW"

        return PredictionResult(
            prediction_type=PredictionType.DRUG_EFFICACY,
            prediction=efficacy_prediction,
            confidence=overall_confidence,
            evidence=evidence,
            explanation=f"Predicted efficacy: {efficacy_prediction} (confidence: {overall_confidence:.2%})",
            metadata={
                "drug_id": drug_id,
                "disease_id": disease_id,
                "efficacy_score": overall_confidence
            }
        )

    def _assess_target_association(
        self,
        drug_id: str,
        disease_id: str
    ) -> float:
        """评估靶点关联强度"""
        query = """
        MATCH (d:Compound {primary_id: $drug_id})-[:TARGETS]->(t:Target)-[:ASSOCIATED_WITH]->(dis:Disease {primary_id: $disease_id})
        WITH count(DISTINCT t) as target_count
        RETURN target_count
        """

        with self.driver.session() as session:
            try:
                result = session.run(query, drug_id=drug_id, disease_id=disease_id)
                record = result.single()
                if record:
                    # 每个靶点贡献0.3的置信度，最高0.9
                    return min(record["target_count"] * 0.3, 0.9)
            except Exception:
                pass

        return 0.0

    def _assess_similar_drug_efficacy(
        self,
        drug_id: str,
        disease_id: str
    ) -> float:
        """评估相似药物疗效"""
        query = """
        MATCH (d:Compound {primary_id: $drug_id})-[:TARGETS]->(t:Target)<-[:TARGETS]-(similar:Compound)-[:TREATS]->(dis:Disease {primary_id: $disease_id})
        WITH count(DISTINCT similar) as similar_count
        RETURN similar_count
        """

        with self.driver.session() as session:
            try:
                result = session.run(query, drug_id=drug_id, disease_id=disease_id)
                record = result.single()
                if record:
                    # 每个相似药物贡献0.25的置信度
                    return min(record["similar_count"] * 0.25, 0.8)
            except Exception:
                pass

        return 0.0

    def _assess_pathway_coverage(
        self,
        drug_id: str,
        disease_id: str
    ) -> float:
        """评估通路覆盖"""
        query = """
        MATCH (d:Compound {primary_id: $drug_id})-[:TARGETS]->(:Target)-[:PARTICIPATES_IN]->(p:Pathway)<-[:INVOLVED_IN]-(dis:Disease {primary_id: $disease_id})
        RETURN count(DISTINCT p) as pathway_count
        """

        with self.driver.session() as session:
            try:
                result = session.run(query, drug_id=drug_id, disease_id=disease_id)
                record = result.single()
                if record:
                    # 每个通路贡献0.2的置信度
                    return min(record["pathway_count"] * 0.2, 0.7)
            except Exception:
                pass

        return 0.0
