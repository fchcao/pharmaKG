#===========================================================
# PharmaKG - 推理引擎
# Pharmaceutical Knowledge Graph - Reasoning Engine
#===========================================================
# 版本: v1.0
# 描述: 知识图谱推理引擎
#===========================================================

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class ReasoningType(str, Enum):
    """推理类型"""
    DEDUCTIVE = "deductive"      # 演绎推理
    INDUCTIVE = "inductive"        # 归纳推理
    ABDUCTIVE = "abductive"        # 溯因推理
    ANALOGY = "analogy"            # 类比推理
    RULE_BASED = "rule_based"      # 基于规则


@dataclass
class ReasoningResult:
    """推理结果"""
    reasoning_type: ReasoningType
    conclusion: str
    confidence: float
    premises: List[str]
    rules: List[str]
    evidence: List[Dict[str, Any]]
    explanation: str


class KnowledgeGraphReasoner:
    """
    知识图谱推理器

    基于图结构和规则进行推理
    """

    def __init__(self, neo4j_driver):
        """
        初始化推理器

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver
        self.rules = self._load_default_rules()

    def _load_default_rules(self) -> Dict[str, Any]:
        """加载默认推理规则"""
        return {
            "drug_efficacy": [
                {
                    "name": "target_mechanism",
                    "condition": "drug_targets_disease_pathway",
                    "conclusion": "drug_may_treat_disease",
                    "confidence": 0.7
                },
                {
                    "name": "similar_drug_success",
                    "condition": "similar_drug_treats_disease",
                    "conclusion": "drug_may_treat_disease",
                    "confidence": 0.6
                }
            ],
            "safety": [
                {
                    "name": "target_safety_issue",
                    "condition": "drug_targets_high_risk_target",
                    "conclusion": "drug_may_have_safety_concern",
                    "confidence": 0.6
                },
                {
                    "name": "ddi_risk",
                    "condition": "drugs_share_target",
                    "conclusion": "potential_drug_drug_interaction",
                    "confidence": 0.5
                }
            ],
            "trial_success": [
                {
                    "name": "phase_progression",
                    "condition": "drug_succeeded_in_earlier_phase",
                    "conclusion": "likely_to_succeed_in_later_phase",
                    "confidence": 0.7
                },
                {
                    "name": "biomarker_positive",
                    "condition": "trial_has_positive_biomarker",
                    "conclusion": "higher_success_probability",
                    "confidence": 0.6
                }
            ]
        }

    def deductive_reasoning(
        self,
        facts: List[Dict[str, Any]],
        query: str
    ) -> List[ReasoningResult]:
        """
        演绎推理

        从一般性规则推导具体结论

        Args:
            facts: 已知事实列表
            query: 推理查询

        Returns:
            推理结果列表
        """
        results = []

        # 规则：如果药物作用于疾病的靶点，则可能治疗该疾病
        if "treat" in query.lower() or "efficacy" in query.lower():
            for fact in facts:
                drug_id = fact.get("drug_id")
                disease_id = fact.get("disease_id")

                if drug_id and disease_id:
                    # 检查药物是否靶向疾病相关靶点
                    if self._check_target_association(drug_id, disease_id):
                        results.append(ReasoningResult(
                            reasoning_type=ReasoningType.DEDUCTIVE,
                            conclusion=f"{drug_id} may treat {disease_id}",
                            confidence=0.7,
                            premises=[f"{drug_id} targets disease-associated targets"],
                            rules=["target_mechanism"],
                            evidence=[fact],
                            explanation=f"Based on target mechanism, {drug_id} may treat {disease_id}"
                        ))

        return results

    def inductive_reasoning(
        self,
        observations: List[Dict[str, Any]],
        entity_id: str
    ) -> List[ReasoningResult]:
        """
        归纳推理

        从具体观察推导一般性结论

        Args:
            observations: 观察列表
            entity_id: 实体 ID

        Returns:
            推理结果列表
        """
        results = []

        # 观察模式：同一靶点的药物往往有相似疗效
        target_drugs = defaultdict(list)

        for obs in observations:
            target_id = obs.get("target_id")
            drug_id = obs.get("drug_id")
            outcome = obs.get("outcome")

            if target_id and drug_id and outcome:
                target_drugs[target_id].append((drug_id, outcome))

        # 分析模式
        for target_id, drugs in target_drugs.items():
            if len(drugs) >= 3:
                successful = [d for d, o in drugs if o == "success"]
                success_rate = len(successful) / len(drugs)

                if success_rate > 0.6:
                    results.append(ReasoningResult(
                        reasoning_type=ReasoningType.INDUCTIVE,
                        conclusion=f"Drugs targeting {target_id} show {success_rate:.1%} success rate",
                        confidence=min(success_rate + 0.1, 1.0),
                        premises=[f"Observed {len(drugs)} drugs targeting {target_id}"],
                        rules=["pattern_induction"],
                        evidence=[{"target_id": target_id, "drugs": drugs}],
                        explanation=f"Based on observed patterns, {target_id} is a promising target"
                    ))

        return results

    def abductive_reasoning(
        self,
        observation: Dict[str, Any],
        possible_explanations: int = 5
    ) -> List[ReasoningResult]:
        """
        溯因推理

        从观察推断最可能的原因

        Args:
            observation: 观察到的现象
            possible_explanations: 返回解释数量

        Returns:
            推理结果列表（按似然性排序）
        """
        results = []

        # 示例：观察到药物不良反应，推断可能原因
        if "adverse_event" in observation:
            drug_id = observation.get("drug_id")
            event_type = observation.get("event_type")

            if drug_id and event_type:
                # 可能原因1：靶点相关副作用
                target_cause = self._infer_target_cause(drug_id, event_type)
                if target_cause:
                    results.append(target_cause)

                # 可能原因2：药物相互作用
                ddi_cause = self._infer_ddi_cause(drug_id, event_type)
                if ddi_cause:
                    results.append(ddi_cause)

                # 可能原因3：剂量相关
                dose_cause = self._infer_dose_cause(event_type)
                if dose_cause:
                    results.append(dose_cause)

        # 按置信度排序
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results[:possible_explanations]

    def _infer_target_cause(
        self,
        drug_id: str,
        event_type: str
    ) -> Optional[ReasoningResult]:
        """推断靶点相关原因"""
        query = """
        MATCH (d:Compound {primary_id: $drug_id})-[:TARGETS]->(t:Target)-[:ASSOCIATED_WITH]->(ae:AdverseEvent {name: $event_type})
        RETURN t.primary_id as target_id, t.name as target_name
        LIMIT 1
        """

        with self.driver.session() as session:
            try:
                result = session.run(query, drug_id=drug_id, event_type=event_type)
                record = result.single()
                if record:
                    return ReasoningResult(
                        reasoning_type=ReasoningType.ABDUCTIVE,
                        conclusion=f"Adverse event may be caused by target {record['target_id']}",
                        confidence=0.7,
                        premises=[f"{drug_id} targets {record['target_id']}"],
                        rules=["target_safety_association"],
                        evidence=[{"target_id": record["target_id"]}],
                        explanation=f"Target {record['target_name']} is associated with {event_type}"
                    )
            except Exception:
                pass

        return None

    def _infer_ddi_cause(
        self,
        drug_id: str,
        event_type: str
    ) -> Optional[ReasoningResult]:
        """推断药物相互作用原因"""
        return None  # 简化实现

    def _infer_dose_cause(
        self,
        event_type: str
    ) -> Optional[ReasoningResult]:
        """推断剂量相关原因"""
        return None  # 简化实现

    def analogy_reasoning(
        self,
        source_case: Dict[str, Any],
        target_entities: List[str]
    ) -> List[ReasoningResult]:
        """
        类比推理

        基于相似案例进行推理

        Args:
            source_case: 源案例
            target_entities: 目标实体列表

        Returns:
            推理结果列表
        """
        results = []

        # 示例：已知药物A成功治疗疾病X，药物B与A相似，推断B可能也有效
        source_drug = source_case.get("drug_id")
        disease = source_case.get("disease_id")
        outcome = source_case.get("outcome")

        if source_drug and disease and outcome == "success":
            # 找到相似的药物
            query = """
            MATCH (d1:Compound {primary_id: $drug_id})
            MATCH (d1)-[:TARGETS]->(t:Target)<-[:TARGETS]-(d2:Compound)
            WHERE d1.inchikey[0..7] = d2.inchikey[0..7]
            RETURN DISTINCT d2.primary_id as similar_drug, d2.name as drug_name
            LIMIT 5
            """

            with self.driver.session() as session:
                try:
                    result = session.run(query, drug_id=source_drug)
                    similar_drugs = [record.data() for record in result]
                except Exception:
                    similar_drugs = []

            for drug in similar_drugs:
                drug_id = drug["similar_drug"]
                results.append(ReasoningResult(
                    reasoning_type=ReasoningType.ANALOGY,
                    conclusion=f"{drug_id} may be effective against {disease}",
                    confidence=0.6,
                    premises=[
                        f"{source_drug} is effective against {disease}",
                        f"{drug_id} is structurally similar to {source_drug}"
                    ],
                    rules=["structural_analogy"],
                    evidence=[{"source_case": source_case, "similar_drug": drug_id}],
                    explanation=f"Based on structural similarity to {source_drug}"
                ))

        return results

    def rule_based_reasoning(
        self,
        context: Dict[str, Any],
        rule_category: Optional[str] = None
    ) -> List[ReasoningResult]:
        """
        基于规则的推理

        使用预定义规则进行推理

        Args:
            context: 上下文信息
            rule_category: 规则类别

        Returns:
            推理结果列表
        """
        results = []

        # 应用相关规则
        for category, rules in self.rules.items():
            if rule_category and category != rule_category:
                continue

            for rule in rules:
                if self._evaluate_rule_condition(rule["condition"], context):
                    results.append(ReasoningResult(
                        reasoning_type=ReasoningType.RULE_BASED,
                        conclusion=rule["conclusion"],
                        confidence=rule["confidence"],
                        premises=[context],
                        rules=[rule["name"]],
                        evidence=[{"rule": rule["name"]}],
                        explanation=f"Rule '{rule['name']}' triggered"
                    ))

        return results

    def _check_target_association(self, drug_id: str, disease_id: str) -> bool:
        """检查药物是否靶向疾病相关靶点"""
        query = """
        MATCH (d:Compound {primary_id: $drug_id})-[:TARGETS]->(t:Target)-[:ASSOCIATED_WITH]->(dis:Disease {primary_id: $disease_id})
        RETURN count(t) > 0
        """

        with self.driver.session() as session:
            result = session.run(query, drug_id=drug_id, disease_id=disease_id)
            return result.single()[0] if result else False

    def _evaluate_rule_condition(
        self,
        condition: str,
        context: Dict[str, Any]
    ) -> bool:
        """评估规则条件"""
        # 简化实现：基于关键字符串匹配
        condition_lower = condition.lower()

        if "target" in condition_lower and "disease" in condition_lower:
            drug_id = context.get("drug_id")
            disease_id = context.get("disease_id")
            if drug_id and disease_id:
                return self._check_target_association(drug_id, disease_id)

        return False


class PathBasedReasoner:
    """
    基于路径的推理器

    通过分析图中的路径进行推理
    """

    def __init__(self, neo4j_driver):
        """
        初始化路径推理器

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver

    def find_explanation_paths(
        self,
        entity1_id: str,
        entity2_id: str,
        max_length: int = 4
    ) -> List[Dict[str, Any]]:
        """
        查找解释路径

        找到两个实体之间的有意义路径，用于解释它们之间的关系

        Args:
            entity1_id: 第一个实体 ID
            entity2_id: 第二个实体 ID
            max_length: 最大路径长度

        Returns:
            路径列表
        """
        query = f"""
        MATCH path = (a {{primary_id: $entity1_id}})-[*1..{max_length}]-(b {{primary_id: $entity2_id}})
        RETURN [node in nodes(path) | node.primary_id] as nodes,
               [rel in relationships(path) | type(rel)] as relationships,
               length(path) as path_length
        ORDER BY path_length
        LIMIT 10
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                entity1_id=entity1_id,
                entity2_id=entity2_id
            )
            return [record.data() for record in result]

    def explain_relationship(
        self,
        entity1_id: str,
        entity2_id: str,
        relationship_type: Optional[str] = None
    ) -> List[str]:
        """
        解释两个实体之间的关系

        Args:
            entity1_id: 第一个实体 ID
            entity2_id: 第二个实体 ID
            relationship_type: 关系类型

        Returns:
            解释列表
        """
        explanations = []

        # 查找共同邻居
        common_neighbors = self._find_common_neighbors(entity1_id, entity2_id)
        if common_neighbors:
            explanations.append(
                f"Both entities are connected through {len(common_neighbors)} common neighbor(s)"
            )

        # 查找中介实体
        mediator_paths = self._find_mediator_paths(entity1_id, entity2_id)
        if mediator_paths:
            explanations.append(
                f"Connected through {len(mediator_paths)} mediator path(s)"
            )

        # 查找路径模式
        paths = self.find_explanation_paths(entity1_id, entity2_id)
        if paths:
            explanations.append(f"Found {len(paths)} connection path(s)")

        return explanations

    def _find_common_neighbors(
        self,
        entity1_id: str,
        entity2_id: str
    ) -> List[str]:
        """查找共同邻居"""
        query = """
        MATCH (a {primary_id: $entity1_id})-->(neighbor)<--(b {primary_id: $entity2_id})
        RETURN DISTINCT neighbor.primary_id as neighbor_id
        LIMIT 10
        """

        with self.driver.session() as session:
            result = session.run(query, entity1_id=entity1_id, entity2_id=entity2_id)
            return [record["neighbor_id"] for record in result]

    def _find_mediator_paths(
        self,
        entity1_id: str,
        entity2_id: str
    ) -> List[Dict[str, Any]]:
        """查找中介路径"""
        query = """
        MATCH path = (a {primary_id: $entity1_id})-[*2..3]-(b {primary_id: $entity2_id})
        WITH path, [n in nodes(path) | n.primary_id][1..-1] as mediators
        RETURN mediators, length(path) as path_length
        ORDER BY path_length
        LIMIT 5
        """

        with self.driver.session() as session:
            result = session.run(query, entity1_id=entity1_id, entity2_id=entity2_id)
            return [record.data() for record in result]


class RuleEngine:
    """
    规则引擎

    管理和执行推理规则
    """

    def __init__(self, neo4j_driver):
        """
        初始化规则引擎

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver
        self.rules: Dict[str, Dict[str, Any]] = {}

    def add_rule(
        self,
        rule_id: str,
        name: str,
        condition: str,
        action: str,
        confidence: float = 1.0
    ):
        """
        添加规则

        Args:
            rule_id: 规则 ID
            name: 规则名称
            condition: 条件（Cypher 表达式）
            action: 动作（Cypher 语句）
            confidence: 置信度
        """
        self.rules[rule_id] = {
            "name": name,
            "condition": condition,
            "action": action,
            "confidence": confidence
        }

    def execute_rules(
        self,
        context: Dict[str, Any],
        rule_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行规则

        Args:
            context: 上下文参数
            rule_ids: 要执行的规则 ID 列表（None 表示全部）

        Returns:
            执行结果
        """
        results = []

        rules_to_execute = (
            [(rid, r) for rid, r in self.rules.items() if rule_ids is None or rid in rule_ids]
        )

        for rule_id, rule in rules_to_execute:
            try:
                # 检查条件
                if self._evaluate_condition(rule["condition"], context):
                    # 执行动作
                    action_result = self._execute_action(rule["action"], context)

                    results.append({
                        "rule_id": rule_id,
                        "rule_name": rule["name"],
                        "confidence": rule["confidence"],
                        "result": action_result
                    })

            except Exception as e:
                logger.warning(f"Rule {rule_id} execution failed: {e}")

        return results

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """评估条件"""
        # 简化实现：使用 Cypher 查询
        query = condition

        # 替换上下文变量
        for key, value in context.items():
            query = query.replace(f"${key}", str(value))

        try:
            with self.driver.session() as session:
                result = session.run(query)
                return result.single()[0] if result else False
        except Exception:
            return False

    def _execute_action(self, action: str, context: Dict[str, Any]) -> Any:
        """执行动作"""
        query = action

        for key, value in context.items():
            query = query.replace(f"${key}", str(value))

        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]


class ExplainabilityEngine:
    """
    可解释性引擎

    提供推理结果的解释
    """

    def __init__(self, neo4j_driver):
        """
        初始化可解释性引擎

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver
        self.path_reasoner = PathBasedReasoner(neo4j_driver)

    def explain_prediction(
        self,
        prediction: Any,
        entity_ids: List[str]
    ) -> Dict[str, Any]:
        """
        解释预测结果

        Args:
            prediction: 预测结果
            entity_ids: 相关实体 ID 列表

        Returns:
            解释信息
        """
        explanation = {
            "prediction": prediction,
            "explanations": [],
            "supporting_evidence": [],
            "confidence_factors": []
        }

        # 查找实体之间的解释路径
        if len(entity_ids) >= 2:
            for i in range(len(entity_ids) - 1):
                paths = self.path_reasoner.find_explanation_paths(
                    entity_ids[i],
                    entity_ids[i + 1]
                )

                for path in paths:
                    explanation["explanations"].append({
                        "type": "path",
                        "path": path["nodes"],
                        "relationships": path["relationships"]
                    })

        return explanation

    def generate_natural_language_explanation(
        self,
        reasoning_result: Any
    ) -> str:
        """
        生成自然语言解释

        Args:
            reasoning_result: 推理结果

        Returns:
            自然语言解释
        """
        if hasattr(reasoning_result, "explanation"):
            return reasoning_result.explanation

        # 通用解释生成
        return "This prediction is based on knowledge graph reasoning using multiple evidence sources."
