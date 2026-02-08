#!/usr/bin/env python3
#===========================================================
# 制药行业知识图谱 - 跨域关系推理引擎
# Pharmaceutical Knowledge Graph - Cross-Domain Relationship Inference Engine
#===========================================================
# 版本: v1.0
# 创建日期: 2025-02-08
#===========================================================
# 描述/Description:
# 该工具通过组合跨域模式来推断新的关系
# This tool infers new relationships by combining patterns across domains
#===========================================================

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import time

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database import Neo4jConnection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InferenceRuleType(Enum):
    """推理规则类型 / Inference Rule Type"""
    DRUG_REPURPOSING = "drug_repurposing"
    SAFETY_SIGNAL = "safety_signal"
    SUPPLY_CHAIN_RISK = "supply_chain_risk"
    COMPETITIVE_INTELLIGENCE = "competitive_intelligence"
    PATHWAY_DISCOVERY = "pathway_discovery"
    TRIAL_SUCCESS = "trial_success"


@dataclass
class InferenceRule:
    """推理规则定义 / Inference Rule Definition"""
    name: str
    description: str
    rule_type: InferenceRuleType
    cypher_pattern: str
    confidence_formula: str
    relationship_type: str
    relationship_direction: str  # "outgoing", "incoming", or "bidirectional"
    properties: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.name)


class InferenceConfig:
    """推理配置 / Inference Configuration"""

    # Drug Repurposing Rule
    DRUG_REPURPOSING_RULE = InferenceRule(
        name="drug_repurposing_opportunity",
        description="Infer potential treatment opportunities when compound inhibits target associated with disease",
        rule_type=InferenceRuleType.DRUG_REPURPOSING,
        cypher_pattern="""
            MATCH (c:Compound)-[r1:INHIBITS|ACTIVATES|MODULATES]->(t:Target)
            MATCH (t)-[r2:ASSOCIATED_WITH_DISEASE|IMPLICATED_IN]->(d:Disease)
            WHERE NOT (c)-[:TREATS|POTENTIALLY_TREATS]->(d)
            AND r1.pchembl_value >= 6.0
            AND r2.confidence_score >= 0.7
        """,
        confidence_formula="(r1.pchembl_value / 10.0) * r2.confidence_score",
        relationship_type="POTENTIALLY_TREATS",
        relationship_direction="outgoing",
        properties={
            "inference_rule": "drug_repurposing_opportunity",
            "evidence_level": "D",
            "requires_clinical_validation": True
        }
    )

    # Safety Signal Detection Rule
    SAFETY_SIGNAL_RULE = InferenceRule(
        name="safety_signal_detection",
        description="Detect confirmed safety risks from multiple adverse events",
        rule_type=InferenceRuleType.SAFETY_SIGNAL,
        cypher_pattern="""
            MATCH (c:Compound)-[r1:HAS_SAFETY_SIGNAL]->(signal:SafetySignal)
            MATCH (c)-[r2:CAUSES_ADVERSE_EVENT]->(ae:AdverseEvent)
            WHERE ae.seriousness = 'serious'
            AND ae.condition_name = signal.condition_name
            WITH c, ae.condition_name, count(DISTINCT ae) as ae_count
            WHERE ae_count >= 3
        """,
        confidence_formula="min(0.95, 0.5 + (ae_count * 0.1))",
        relationship_type="CONFIRMED_RISK",
        relationship_direction="outgoing",
        properties={
            "inference_rule": "safety_signal_detection",
            "evidence_level": "C",
            "requires_monitoring": True
        }
    )

    # Supply Chain Risk Rule
    SUPPLY_CHAIN_RISK_RULE = InferenceRule(
        name="supply_chain_quality_risk",
        description="Identify potential quality issues from failed inspections",
        rule_type=InferenceRuleType.SUPPLY_CHAIN_RISK,
        cypher_pattern="""
            MATCH (m:Manufacturer)-[r1:OWNS|OPERATES]->(f:Facility)
            MATCH (f)-[r2:HAD_INSPECTION]->(i:Inspection)
            WHERE i.outcome = 'Fail'
            WITH m, f, count(DISTINCT i) as fail_count
            WHERE fail_count >= 2
        """,
        confidence_formula="min(0.9, 0.4 + (fail_count * 0.15))",
        relationship_type="POTENTIAL_QUALITY_ISSUE",
        relationship_direction="outgoing",
        properties={
            "inference_rule": "supply_chain_quality_risk",
            "evidence_level": "C",
            "requires_audit": True
        }
    )

    # Competitive Intelligence Rule
    COMPETITIVE_INTELLIGENCE_RULE = InferenceRule(
        name="competitive_analysis",
        description="Identify competing compounds targeting the same target",
        rule_type=InferenceRuleType.COMPETITIVE_INTELLIGENCE,
        cypher_pattern="""
            MATCH (c1:Compound)-[r1:INHIBITS|TARGETS]->(t:Target)
            MATCH (c2:Compound)-[r2:INHIBITS|TARGETS]->(t)
            WHERE c1.id < c2.id
            AND NOT (c1)-[:COMPETES_WITH]->(c2)
            AND r1.target_specificity >= 0.7
            AND r2.target_specificity >= 0.7
        """,
        confidence_formula="(r1.target_specificity + r2.target_specificity) / 2.0",
        relationship_type="COMPETES_WITH",
        relationship_direction="bidirectional",
        properties={
            "inference_rule": "competitive_analysis",
            "evidence_level": "B",
            "shared_target": True
        }
    )

    # Pathway-Based Drug Discovery Rule
    PATHWAY_DISCOVERY_RULE = InferenceRule(
        name="pathway_based_discovery",
        description="Infer treatment opportunities through pathway-disease associations",
        rule_type=InferenceRuleType.PATHWAY_DISCOVERY,
        cypher_pattern="""
            MATCH (c:Compound)-[r1:TARGETS|MODULATES]->(p:Pathway)
            MATCH (p)-[r2:DYSREGULATED_IN|IMPLICATED_IN]->(d:Disease)
            WHERE NOT (c)-[:TREATS|POTENTIALLY_TREATS]->(d)
            AND r2.pathway_dysregulation_score >= 0.6
        """,
        confidence_formula="r2.pathway_dysregulation_score * 0.8",
        relationship_type="POTENTIALLY_TREATS",
        relationship_direction="outgoing",
        properties={
            "inference_rule": "pathway_based_discovery",
            "evidence_level": "D",
            "mechanism": "pathway_modulation"
        }
    )

    # Clinical Trial Success Prediction Rule
    TRIAL_SUCCESS_RULE = InferenceRule(
        name="trial_success_prediction",
        description="Predict high probability of success for trials with validated targets",
        rule_type=InferenceRuleType.TRIAL_SUCCESS,
        cypher_pattern="""
            MATCH (t:ClinicalTrial)-[r1:TESTS]->(c:Compound)
            MATCH (c)-[r2:TARGETS]->(target:Target)
            MATCH (target)-[r3:HAS_CLINICAL_VALIDATION|VALIDATED_BY]->(v:Validation)
            WHERE t.phase IN ['Phase 2', 'Phase 3']
            AND v.validation_quality_score >= 0.7
        """,
        confidence_formula="(v.validation_quality_score + 0.2) * 0.9",
        relationship_type="HIGH_PROBABILITY_OF_SUCCESS",
        relationship_direction="outgoing",
        properties={
            "inference_rule": "trial_success_prediction",
            "evidence_level": "C",
            "predictive_model": "target_validation"
        }
    )

    @classmethod
    def get_all_rules(cls) -> List[InferenceRule]:
        """获取所有推理规则 / Get all inference rules"""
        return [
            cls.DRUG_REPURPOSING_RULE,
            cls.SAFETY_SIGNAL_RULE,
            cls.SUPPLY_CHAIN_RISK_RULE,
            cls.COMPETITIVE_INTELLIGENCE_RULE,
            cls.PATHWAY_DISCOVERY_RULE,
            cls.TRIAL_SUCCESS_RULE
        ]


class CrossDomainInferenceEngine:
    """跨域关系推理引擎 / Cross-Domain Relationship Inference Engine"""

    def __init__(
        self,
        output_dir: Path,
        confidence_threshold: float = 0.5,
        dry_run: bool = False
    ):
        self.output_dir = output_dir
        self.confidence_threshold = confidence_threshold
        self.dry_run = dry_run

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Neo4j connection
        self.neo4j = Neo4jConnection()

        # Inference statistics
        self.stats = {
            "rules_executed": 0,
            "relationships_inferred": 0,
            "relationships_filtered": 0,
            "errors": [],
            "by_rule_type": {}
        }

        # Inference results storage
        self.inferred_relationships = []

    def execute_inference_rule(
        self,
        rule: InferenceRule,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """执行单个推理规则 / Execute a single inference rule"""
        logger.info(f"Executing rule: {rule.name}")
        logger.info(f"Description: {rule.description}")

        inferred = []

        try:
            # Build Cypher query
            query = f"""
                {rule.cypher_pattern}
                RETURN c, d, t, ae, f, fail_count, c1, c2, p, target, v,
                       r1, r2, r3
                {f'LIMIT {limit}' if limit else ''}
            """

            # Execute query
            result = self.neo4j.execute_query(query)

            logger.info(f"Found {len(result.records)} candidate patterns")

            # Process each result and calculate confidence
            for record in result.records:
                try:
                    inference = self._process_inference_record(record, rule)
                    if inference and inference["confidence"] >= self.confidence_threshold:
                        inferred.append(inference)
                        self.stats["relationships_inferred"] += 1
                    else:
                        self.stats["relationships_filtered"] += 1
                except Exception as e:
                    logger.warning(f"Error processing record: {str(e)}")
                    self.stats["errors"].append(str(e))

            # Update statistics
            self.stats["rules_executed"] += 1
            self.stats["by_rule_type"][rule.rule_type.value] = {
                "inferred": len(inferred),
                "filtered": self.stats["relationships_filtered"]
            }

            logger.info(f"Rule {rule.name}: {len(inferred)} relationships inferred")

        except Exception as e:
            logger.error(f"Error executing rule {rule.name}: {str(e)}")
            self.stats["errors"].append(f"{rule.name}: {str(e)}")

        return inferred

    def _process_inference_record(
        self,
        record: Dict,
        rule: InferenceRule
    ) -> Optional[Dict[str, Any]]:
        """处理推理记录 / Process inference record"""
        # Extract entities based on rule type
        if rule.rule_type == InferenceRuleType.DRUG_REPURPOSING:
            source_id = record.get("c", {}).get("id")
            target_id = record.get("d", {}).get("id")
            source_label = "Compound"
            target_label = "Disease"

            # Calculate confidence
            r1 = record.get("r1", {})
            r2 = record.get("r2", {})
            pchembl = r1.get("pchembl_value", 0)
            conf_score = r2.get("confidence_score", 0)
            confidence = round((pchembl / 10.0) * conf_score, 3)

            evidence = {
                "target_id": record.get("t", {}).get("id"),
                "pchembl_value": pchembl,
                "disease_association_confidence": conf_score
            }

        elif rule.rule_type == InferenceRuleType.SAFETY_SIGNAL:
            source_id = record.get("c", {}).get("id")
            target_id = record.get("condition_name")
            source_label = "Compound"
            target_label = "Condition"

            ae_count = record.get("ae_count", 0)
            confidence = round(min(0.95, 0.5 + (ae_count * 0.1)), 3)

            evidence = {
                "adverse_event_count": ae_count,
                "condition_name": target_id
            }

        elif rule.rule_type == InferenceRuleType.SUPPLY_CHAIN_RISK:
            source_id = record.get("m", {}).get("id")
            target_id = record.get("f", {}).get("id")
            source_label = "Manufacturer"
            target_label = "Facility"

            fail_count = record.get("fail_count", 0)
            confidence = round(min(0.9, 0.4 + (fail_count * 0.15)), 3)

            evidence = {
                "inspection_fail_count": fail_count
            }

        elif rule.rule_type == InferenceRuleType.COMPETITIVE_INTELLIGENCE:
            source_id = record.get("c1", {}).get("id")
            target_id = record.get("c2", {}).get("id")
            source_label = "Compound"
            target_label = "Compound"

            r1 = record.get("r1", {})
            r2 = record.get("r2", {})
            specificity1 = r1.get("target_specificity", 0)
            specificity2 = r2.get("target_specificity", 0)
            confidence = round((specificity1 + specificity2) / 2.0, 3)

            evidence = {
                "shared_target_id": record.get("t", {}).get("id"),
                "target_specificity_1": specificity1,
                "target_specificity_2": specificity2
            }

        elif rule.rule_type == InferenceRuleType.PATHWAY_DISCOVERY:
            source_id = record.get("c", {}).get("id")
            target_id = record.get("d", {}).get("id")
            source_label = "Compound"
            target_label = "Disease"

            r2 = record.get("r2", {})
            dysregulation_score = r2.get("pathway_dysregulation_score", 0)
            confidence = round(dysregulation_score * 0.8, 3)

            evidence = {
                "pathway_id": record.get("p", {}).get("id"),
                "dysregulation_score": dysregulation_score
            }

        elif rule.rule_type == InferenceRuleType.TRIAL_SUCCESS:
            source_id = record.get("t", {}).get("id")
            target_id = record.get("c", {}).get("id")
            source_label = "ClinicalTrial"
            target_label = "Compound"

            v = record.get("v", {})
            validation_score = v.get("validation_quality_score", 0)
            confidence = round((validation_score + 0.2) * 0.9, 3)

            evidence = {
                "target_id": record.get("target", {}).get("id"),
                "validation_score": validation_score
            }

        else:
            return None

        # Build inference object
        inference = {
            "rule_name": rule.name,
            "rule_type": rule.rule_type.value,
            "source_id": source_id,
            "source_label": source_label,
            "target_id": target_id,
            "target_label": target_label,
            "relationship_type": rule.relationship_type,
            "relationship_direction": rule.relationship_direction,
            "confidence": confidence,
            "evidence": evidence,
            "properties": rule.properties,
            "inferred_at": datetime.now().isoformat(),
            "evidence_trail": self._build_evidence_trail(record, rule)
        }

        return inference

    def _build_evidence_trail(
        self,
        record: Dict,
        rule: InferenceRule
    ) -> List[Dict[str, Any]]:
        """构建证据链 / Build evidence trail"""
        trail = []

        # Extract source relationships
        for key in ["r1", "r2", "r3"]:
            if key in record and record[key]:
                rel = record[key]
                trail.append({
                    "relationship": key,
                    "type": rel.get("type", "unknown"),
                    "source": rel.get("source", "unknown"),
                    "properties": {k: v for k, v in rel.items() if k != "elementId"}
                })

        return trail

    def execute_all_rules(
        self,
        rules: Optional[List[InferenceRule]] = None,
        limit_per_rule: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """执行所有推理规则 / Execute all inference rules"""
        logger.info("=" * 60)
        logger.info("Starting Cross-Domain Inference Pipeline")
        logger.info("=" * 60)

        start_time = time.time()

        # Get rules to execute
        if rules is None:
            rules = InferenceConfig.get_all_rules()

        logger.info(f"Executing {len(rules)} inference rules")
        logger.info(f"Confidence threshold: {self.confidence_threshold}")
        logger.info(f"Dry run: {self.dry_run}")

        # Execute each rule
        for rule in rules:
            try:
                inferred = self.execute_inference_rule(rule, limit=limit_per_rule)
                self.inferred_relationships.extend(inferred)
            except Exception as e:
                logger.error(f"Failed to execute rule {rule.name}: {str(e)}")
                self.stats["errors"].append(f"{rule.name}: {str(e)}")

        elapsed_time = time.time() - start_time

        logger.info("=" * 60)
        logger.info(f"Inference pipeline completed in {elapsed_time:.2f} seconds")
        logger.info(f"Total relationships inferred: {self.stats['relationships_inferred']}")
        logger.info(f"Total relationships filtered: {self.stats['relationships_filtered']}")
        logger.info(f"Errors encountered: {len(self.stats['errors'])}")
        logger.info("=" * 60)

        return self.inferred_relationships

    def generate_cypher_queries(self) -> Path:
        """生成Neo4j Cypher查询 / Generate Neo4j Cypher queries"""
        logger.info("Generating Neo4j Cypher queries...")

        output_file = self.output_dir / "inferred_relationships.cypher"

        queries = []
        queries.append("// ========================================")
        queries.append("// PharmaKG - Inferred Relationships")
        queries.append(f"// Generated: {datetime.now().isoformat()}")
        queries.append(f"// Confidence threshold: {self.confidence_threshold}")
        queries.append("// ========================================\n")

        # Group by relationship type
        by_type = {}
        for rel in self.inferred_relationships:
            rel_type = rel["relationship_type"]
            if rel_type not in by_type:
                by_type[rel_type] = []
            by_type[rel_type].append(rel)

        # Generate queries for each relationship type
        for rel_type, relationships in by_type.items():
            queries.append(f"\n// {rel_type} relationships ({len(relationships)} inferred)")

            for rel in relationships:
                source_label = rel["source_label"]
                target_label = rel["target_label"]
                source_id = rel["source_id"]
                target_id = rel["target_id"]
                confidence = rel["confidence"]
                properties = rel["properties"]
                evidence_trail = json.dumps(rel["evidence_trail"])

                # Build properties string
                props_str = ", ".join([
                    f"{k}: {json.dumps(v) if isinstance(v, (str, dict, list)) else v}"
                    for k, v in {
                        **properties,
                        "confidence": confidence,
                        "inferred_at": rel["inferred_at"],
                        "evidence_trail": evidence_trail
                    }.items()
                ])

                if rel["relationship_direction"] == "bidirectional":
                    queries.append(f"""
// {rel['rule_name']}: {source_id} <-> {target_id} (confidence: {confidence})
MATCH (a:{source_label} {{id: '{source_id}'}})
MATCH (b:{target_label} {{id: '{target_id}'}})
MERGE (a)-[r:{rel_type}]->(b)
ON CREATE SET r += {{{props_str}}}
MERGE (b)-[r2:{rel_type}]->(a)
ON CREATE SET r2 += {{{props_str}}};
""")
                else:
                    queries.append(f"""
// {rel['rule_name']}: {source_id} -> {target_id} (confidence: {confidence})
MATCH (a:{source_label} {{id: '{source_id}'}})
MATCH (b:{target_label} {{id: '{target_id}'}})
MERGE (a)-[r:{rel_type}]->(b)
ON CREATE SET r += {{{props_str}}};
""")

        # Write queries to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(queries))

        logger.info(f"Generated {output_file}")
        return output_file

    def generate_inference_summary(self) -> Dict:
        """生成推理汇总 / Generate inference summary"""
        # Group statistics by rule type
        by_rule = {}
        for rel in self.inferred_relationships:
            rule_name = rel["rule_name"]
            if rule_name not in by_rule:
                by_rule[rule_name] = {
                    "count": 0,
                    "avg_confidence": 0,
                    "min_confidence": 1,
                    "max_confidence": 0,
                    "relationship_type": rel["relationship_type"],
                    "rule_type": rel["rule_type"]
                }
            by_rule[rule_name]["count"] += 1
            conf = rel["confidence"]
            by_rule[rule_name]["avg_confidence"] += conf
            by_rule[rule_name]["min_confidence"] = min(by_rule[rule_name]["min_confidence"], conf)
            by_rule[rule_name]["max_confidence"] = max(by_rule[rule_name]["max_confidence"], conf)

        # Calculate averages
        for rule_name, stats in by_rule.items():
            if stats["count"] > 0:
                stats["avg_confidence"] = round(stats["avg_confidence"] / stats["count"], 3)

        summary = {
            "generated_at": datetime.now().isoformat(),
            "confidence_threshold": self.confidence_threshold,
            "dry_run": self.dry_run,
            "statistics": {
                "total_rules_executed": self.stats["rules_executed"],
                "total_relationships_inferred": self.stats["relationships_inferred"],
                "total_relationships_filtered": self.stats["relationships_filtered"],
                "total_errors": len(self.stats["errors"]),
                "errors": self.stats["errors"][:10]  # First 10 errors
            },
            "by_rule": by_rule,
            "by_relationship_type": self._summarize_by_relationship_type(),
            "confidence_distribution": self._calculate_confidence_distribution()
        }

        # Save summary to JSON
        summary_file = self.output_dir / "inference_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Generated summary: {summary_file}")
        return summary

    def _summarize_by_relationship_type(self) -> Dict[str, Any]:
        """按关系类型汇总 / Summarize by relationship type"""
        by_type = {}
        for rel in self.inferred_relationships:
            rel_type = rel["relationship_type"]
            if rel_type not in by_type:
                by_type[rel_type] = {
                    "count": 0,
                    "avg_confidence": 0,
                    "rule_types": set()
                }
            by_type[rel_type]["count"] += 1
            by_type[rel_type]["avg_confidence"] += rel["confidence"]
            by_type[rel_type]["rule_types"].add(rel["rule_type"])

        # Calculate averages and convert sets to lists
        for rel_type, stats in by_type.items():
            if stats["count"] > 0:
                stats["avg_confidence"] = round(stats["avg_confidence"] / stats["count"], 3)
            stats["rule_types"] = list(stats["rule_types"])

        return by_type

    def _calculate_confidence_distribution(self) -> Dict[str, int]:
        """计算置信度分布 / Calculate confidence distribution"""
        distribution = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0
        }

        for rel in self.inferred_relationships:
            conf = rel["confidence"]
            if conf < 0.2:
                distribution["0.0-0.2"] += 1
            elif conf < 0.4:
                distribution["0.2-0.4"] += 1
            elif conf < 0.6:
                distribution["0.4-0.6"] += 1
            elif conf < 0.8:
                distribution["0.6-0.8"] += 1
            else:
                distribution["0.8-1.0"] += 1

        return distribution

    def generate_report(self) -> Path:
        """生成可读报告 / Generate human-readable report"""
        logger.info("Generating inference report...")

        report_file = self.output_dir / "inference_report.md"

        summary = self.generate_inference_summary()

        report_lines = []
        report_lines.append("# Cross-Domain Relationship Inference Report")
        report_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**Confidence Threshold:** {self.confidence_threshold}")
        report_lines.append(f"**Dry Run:** {self.dry_run}")
        report_lines.append("\n---\n")

        # Summary
        report_lines.append("## Summary")
        report_lines.append(f"\n- **Rules Executed:** {summary['statistics']['total_rules_executed']}")
        report_lines.append(f"- **Relationships Inferred:** {summary['statistics']['total_relationships_inferred']}")
        report_lines.append(f"- **Relationships Filtered:** {summary['statistics']['total_relationships_filtered']}")
        report_lines.append(f"- **Errors:** {summary['statistics']['total_errors']}")

        # By Rule
        report_lines.append("\n## Results by Inference Rule\n")
        for rule_name, stats in summary["by_rule"].items():
            report_lines.append(f"### {rule_name}")
            report_lines.append(f"- **Relationship Type:** {stats['relationship_type']}")
            report_lines.append(f"- **Count:** {stats['count']}")
            report_lines.append(f"- **Avg Confidence:** {stats['avg_confidence']}")
            report_lines.append(f"- **Confidence Range:** {stats['min_confidence']:.3f} - {stats['max_confidence']:.3f}")
            report_lines.append("")

        # By Relationship Type
        report_lines.append("\n## Results by Relationship Type\n")
        for rel_type, stats in summary["by_relationship_type"].items():
            report_lines.append(f"### {rel_type}")
            report_lines.append(f"- **Count:** {stats['count']}")
            report_lines.append(f"- **Avg Confidence:** {stats['avg_confidence']}")
            report_lines.append(f"- **Inferred From:** {', '.join(stats['rule_types'])}")
            report_lines.append("")

        # Confidence Distribution
        report_lines.append("\n## Confidence Distribution\n")
        report_lines.append("| Range | Count |")
        report_lines.append("|-------|-------|")
        for range_key, count in summary["confidence_distribution"].items():
            report_lines.append(f"| {range_key} | {count} |")

        # Top Inferences
        report_lines.append("\n## Top Inferences (by confidence)\n")
        top_inferences = sorted(
            self.inferred_relationships,
            key=lambda x: x["confidence"],
            reverse=True
        )[:20]

        for i, rel in enumerate(top_inferences, 1):
            report_lines.append(f"{i}. **{rel['rule_name']}**")
            report_lines.append(f"   - {rel['source_label']} `{rel['source_id']}` -> {rel['target_label']} `{rel['target_id']}`")
            report_lines.append(f"   - Confidence: {rel['confidence']:.3f}")
            report_lines.append(f"   - Evidence: {json.dumps(rel['evidence'], ensure_ascii=False)}")
            report_lines.append("")

        # Errors
        if summary["statistics"]["total_errors"] > 0:
            report_lines.append("\n## Errors\n")
            for error in summary["statistics"]["errors"]:
                report_lines.append(f"- {error}")

        # Write report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        logger.info(f"Generated report: {report_file}")
        return report_file

    def run(
        self,
        rules: Optional[List[InferenceRule]] = None,
        limit_per_rule: Optional[int] = None,
        apply_to_neo4j: bool = False
    ) -> Dict:
        """运行推理流程 / Run inference pipeline"""
        logger.info("=" * 60)
        logger.info("Cross-Domain Relationship Inference Engine")
        logger.info("=" * 60)

        # Execute all rules
        self.execute_all_rules(rules, limit_per_rule)

        # Generate outputs
        self.generate_cypher_queries()
        summary = self.generate_inference_summary()
        self.generate_report()

        # Apply to Neo4j if requested
        if apply_to_neo4j and not self.dry_run:
            logger.info("Applying inferred relationships to Neo4j...")
            self._apply_to_neo4j()

        return summary

    def _apply_to_neo4j(self):
        """将推理关系应用到Neo4j / Apply inferred relationships to Neo4j"""
        cypher_file = self.output_dir / "inferred_relationships.cypher"

        if not cypher_file.exists():
            logger.warning("Cypher file not found, skipping Neo4j application")
            return

        # Read and execute Cypher file
        with open(cypher_file, 'r', encoding='utf-8') as f:
            cypher_content = f.read()

        # Split by semicolons and execute each query
        queries = [q.strip() for q in cypher_content.split(';') if q.strip() and not q.strip().startswith('//')]

        executed = 0
        errors = 0

        for query in queries:
            try:
                self.neo4j.execute_write(query)
                executed += 1
            except Exception as e:
                logger.warning(f"Error executing query: {str(e)}")
                errors += 1

        logger.info(f"Applied {executed} queries to Neo4j ({errors} errors)")


def main():
    """主函数 / Main function"""
    parser = argparse.ArgumentParser(
        description="Infer Cross-Domain Relationships for PharmaKG"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/root/autodl-tmp/pj-pharmaKG/data/validated"),
        help="Path to output directory"
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.5,
        help="Minimum confidence threshold for inferred relationships (0.0-1.0)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (don't apply to Neo4j)"
    )
    parser.add_argument(
        "--apply-to-neo4j",
        action="store_true",
        help="Apply inferred relationships to Neo4j database"
    )
    parser.add_argument(
        "--limit-per-rule",
        type=int,
        default=None,
        help="Limit number of inferences per rule"
    )
    parser.add_argument(
        "--rules",
        type=str,
        nargs="+",
        choices=[
            "drug_repurposing",
            "safety_signal",
            "supply_chain_risk",
            "competitive_intelligence",
            "pathway_discovery",
            "trial_success"
        ],
        default=None,
        help="Specific rules to execute (default: all)"
    )

    args = parser.parse_args()

    # Create engine instance
    engine = CrossDomainInferenceEngine(
        output_dir=args.output_dir,
        confidence_threshold=args.confidence_threshold,
        dry_run=args.dry_run
    )

    # Select rules to execute
    rules = None
    if args.rules:
        all_rules = InferenceConfig.get_all_rules()
        rule_map = {r.rule_type.value: r for r in all_rules}
        rules = [rule_map[rule] for rule in args.rules if rule in rule_map]

    # Run inference
    summary = engine.run(
        rules=rules,
        limit_per_rule=args.limit_per_rule,
        apply_to_neo4j=args.apply_to_neo4j
    )

    # Print summary
    print("\n" + "=" * 60)
    print("INFERENCE SUMMARY")
    print("=" * 60)
    print(f"Rules Executed: {summary['statistics']['total_rules_executed']}")
    print(f"Relationships Inferred: {summary['statistics']['total_relationships_inferred']}")
    print(f"Relationships Filtered: {summary['statistics']['total_relationships_filtered']}")
    print(f"Errors: {summary['statistics']['total_errors']}")
    print("\nResults by Rule:")
    for rule_name, stats in summary["by_rule"].items():
        print(f"  - {rule_name}: {stats['count']} (avg confidence: {stats['avg_confidence']})")
    print("=" * 60)


if __name__ == "__main__":
    main()
