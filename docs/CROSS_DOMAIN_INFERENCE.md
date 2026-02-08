# 制药行业知识图谱 - 跨域关系推理引擎文档
# Pharmaceutical Knowledge Graph - Cross-Domain Relationship Inference Engine Documentation

版本 / Version: v1.0
日期 / Date: 2025-02-08

---

## 目录 / Table of Contents

1. [概述 / Overview](#概述--overview)
2. [推理规则 / Inference Rules](#推理规则--inference-rules)
3. [架构设计 / Architecture Design](#架构设计--architecture-design)
4. [使用指南 / Usage Guide](#使用指南--usage-guide)
5. [置信度计算 / Confidence Calculation](#置信度计算--confidence-calculation)
6. [证据链追踪 / Evidence Trail Tracking](#证据链追踪--evidence-trail-tracking)
7. [Neo4j集成 / Neo4j Integration](#neo4j集成--neo4j-integration)
8. [性能优化 / Performance Optimization](#性能优化--performance-optimization)
9. [故障排查 / Troubleshooting](#故障排查--troubleshooting)

---

## 概述 / Overview

### 功能 / Purpose

跨域关系推理引擎（Cross-Domain Relationship Inference Engine）通过组合跨域模式来推断新的关系，发现隐藏的关联和洞察，为药物研发、临床试验、供应链管理和合规监管提供智能支持。

The Cross-Domain Relationship Inference Engine infers new relationships by combining patterns across domains, discovering hidden associations and insights to provide intelligent support for drug discovery, clinical trials, supply chain management, and regulatory compliance.

### 核心功能 / Core Features

- **多规则推理引擎**：支持6大类推理规则，覆盖药物重定位、安全信号检测等场景
- **智能置信度计算**：基于证据强度自动计算推理置信度
- **证据链追踪**：完整记录推理路径和证据来源
- **可配置阈值**：支持设置置信度阈值过滤低质量推理
- **Neo4j原生集成**：直接生成Cypher查询，无缝集成到知识图谱
- **批量处理**：高效的批量推理处理能力

### 推理场景 / Inference Scenarios

1. **药物重定位机会** / Drug Repurposing Opportunities
2. **安全信号检测** / Safety Signal Detection
3. **供应链风险评估** / Supply Chain Risk Assessment
4. **竞争情报分析** / Competitive Intelligence Analysis
5. **通路发现** / Pathway-Based Discovery
6. **试验成功预测** / Clinical Trial Success Prediction

---

## 推理规则 / Inference Rules

### 1. 药物重定位机会 / Drug Repurposing Opportunities

**规则名称 / Rule Name:** `drug_repurposing_opportunity`

**场景 / Scenario:**
当化合物抑制某个靶标，而该靶标与某种疾病相关时，推断该化合物可能治疗该疾病。

**Cypher模式 / Cypher Pattern:**
```cypher
MATCH (c:Compound)-[r1:INHIBITS|ACTIVATES|MODULATES]->(t:Target)
MATCH (t)-[r2:ASSOCIATED_WITH_DISEASE|IMPLICATED_IN]->(d:Disease)
WHERE NOT (c)-[:TREATS|POTENTIALLY_TREATS]->(d)
AND r1.pchembl_value >= 6.0
AND r2.confidence_score >= 0.7
```

**置信度公式 / Confidence Formula:**
```
confidence = (r1.pchembl_value / 10.0) * r2.confidence_score
```

**创建的关系 / Relationship Created:**
- **类型 / Type:** `POTENTIALLY_TREATS`
- **方向 / Direction:** Compound → Disease
- **属性 / Properties:**
  - `inference_rule`: "drug_repurposing_opportunity"
  - `evidence_level`: "D" (推断 / Inferred)
  - `requires_clinical_validation`: true

**示例 / Example:**
```
阿司匹林 (INHIBITS) → PTGS1 (COX-1)
PTGS1 (ASSOCIATED_WITH_DISEASE) → 结肠癌
推断: 阿司匹林 (POTENTIALLY_TREATS) → 结肠癌
置信度: 0.6 (7.5/10 * 0.8)
```

### 2. 安全信号检测 / Safety Signal Detection

**规则名称 / Rule Name:** `safety_signal_detection`

**场景 / Scenario:**
当化合物存在安全信号，且针对相同病症有多个严重不良事件报告时，确认该风险。

**Cypher模式 / Cypher Pattern:**
```cypher
MATCH (c:Compound)-[r1:HAS_SAFETY_SIGNAL]->(signal:SafetySignal)
MATCH (c)-[r2:CAUSES_ADVERSE_EVENT]->(ae:AdverseEvent)
WHERE ae.seriousness = 'serious'
AND ae.condition_name = signal.condition_name
WITH c, ae.condition_name, count(DISTINCT ae) as ae_count
WHERE ae_count >= 3
```

**置信度公式 / Confidence Formula:**
```
confidence = min(0.95, 0.5 + (ae_count * 0.1))
```

**创建的关系 / Relationship Created:**
- **类型 / Type:** `CONFIRMED_RISK`
- **方向 / Direction:** Compound → Condition
- **属性 / Properties:**
  - `inference_rule`: "safety_signal_detection"
  - `evidence_level`: "C" (临床证据 / Clinical Evidence)
  - `requires_monitoring`: true

### 3. 供应链风险评估 / Supply Chain Risk Assessment

**规则名称 / Rule Name:** `supply_chain_quality_risk`

**场景 / Scenario:**
当制造商拥有的设施有多次检查失败记录时，识别潜在质量问题。

**Cypher模式 / Cypher Pattern:**
```cypher
MATCH (m:Manufacturer)-[r1:OWNS|OPERATES]->(f:Facility)
MATCH (f)-[r2:HAD_INSPECTION]->(i:Inspection)
WHERE i.outcome = 'Fail'
WITH m, f, count(DISTINCT i) as fail_count
WHERE fail_count >= 2
```

**置信度公式 / Confidence Formula:**
```
confidence = min(0.9, 0.4 + (fail_count * 0.15))
```

**创建的关系 / Relationship Created:**
- **类型 / Type:** `POTENTIAL_QUALITY_ISSUE`
- **方向 / Direction:** Manufacturer → Facility
- **属性 / Properties:**
  - `inference_rule`: "supply_chain_quality_risk"
  - `evidence_level`: "C"
  - `requires_audit`: true

### 4. 竞争情报分析 / Competitive Intelligence Analysis

**规则名称 / Rule Name:** `competitive_analysis`

**场景 / Scenario:**
当两个化合物抑制相同靶标时，推断它们存在竞争关系。

**Cypher模式 / Cypher Pattern:**
```cypher
MATCH (c1:Compound)-[r1:INHIBITS|TARGETS]->(t:Target)
MATCH (c2:Compound)-[r2:INHIBITS|TARGETS]->(t)
WHERE c1.id < c2.id
AND NOT (c1)-[:COMPETES_WITH]->(c2)
AND r1.target_specificity >= 0.7
AND r2.target_specificity >= 0.7
```

**置信度公式 / Confidence Formula:**
```
confidence = (r1.target_specificity + r2.target_specificity) / 2.0
```

**创建的关系 / Relationship Created:**
- **类型 / Type:** `COMPETES_WITH`
- **方向 / Direction:** Compound ↔ Compound (双向 / Bidirectional)
- **属性 / Properties:**
  - `inference_rule`: "competitive_analysis"
  - `evidence_level`: "B" (计算证据 / Computational Evidence)
  - `shared_target`: true

### 5. 通路发现 / Pathway-Based Discovery

**规则名称 / Rule Name:** `pathway_based_discovery`

**场景 / Scenario:**
当化合物靶向某通路，而该通路在某种疾病中失调时，推断治疗机会。

**Cypher模式 / Cypher Pattern:**
```cypher
MATCH (c:Compound)-[r1:TARGETS|MODULATES]->(p:Pathway)
MATCH (p)-[r2:DYSREGULATED_IN|IMPLICATED_IN]->(d:Disease)
WHERE NOT (c)-[:TREATS|POTENTIALLY_TREATS]->(d)
AND r2.pathway_dysregulation_score >= 0.6
```

**置信度公式 / Confidence Formula:**
```
confidence = r2.pathway_dysregulation_score * 0.8
```

**创建的关系 / Relationship Created:**
- **类型 / Type:** `POTENTIALLY_TREATS`
- **方向 / Direction:** Compound → Disease
- **属性 / Properties:**
  - `inference_rule`: "pathway_based_discovery"
  - `evidence_level`: "D"
  - `mechanism`: "pathway_modulation"

### 6. 试验成功预测 / Clinical Trial Success Prediction

**规则名称 / Rule Name:** `trial_success_prediction`

**场景 / Scenario:**
当临床试验测试的化合物靶向已临床验证的靶标时，预测高成功概率。

**Cypher模式 / Cypher Pattern:**
```cypher
MATCH (t:ClinicalTrial)-[r1:TESTS]->(c:Compound)
MATCH (c)-[r2:TARGETS]->(target:Target)
MATCH (target)-[r3:HAS_CLINICAL_VALIDATION|VALIDATED_BY]->(v:Validation)
WHERE t.phase IN ['Phase 2', 'Phase 3']
AND v.validation_quality_score >= 0.7
```

**置信度公式 / Confidence Formula:**
```
confidence = (v.validation_quality_score + 0.2) * 0.9
```

**创建的关系 / Relationship Created:**
- **类型 / Type:** `HIGH_PROBABILITY_OF_SUCCESS`
- **方向 / Direction:** ClinicalTrial → Compound
- **属性 / Properties:**
  - `inference_rule`: "trial_success_prediction"
  - `evidence_level`: "C"
  - `predictive_model`: "target_validation"

---

## 架构设计 / Architecture Design

### 系统组件 / System Components

```
┌─────────────────────────────────────────────────────────────┐
│          Cross-Domain Inference Engine                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Rule        │  │  Inference   │  │  Output      │      │
│  │  Executor    │  │  Processor   │  │  Generator   │      │
│  │              │  │              │  │              │      │
│  │  - Cypher    │  │  - Pattern   │  │  - Cypher    │      │
│  │    Queries   │  │    Matching  │  │    Queries   │      │
│  │  - Result    │  │  - Confidence│  │  - Summary   │      │
│  │    Parsing   │  │    Calc      │  │  - Reports   │      │
│  │  - Evidence  │  │  - Evidence  │  │              │      │
│  │    Trail     │  │    Trail     │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Inference Rule Engine                  │    │
│  │  - Rule Registry                                    │    │
│  │  - Pattern Matching                                 │    │
│  │  - Confidence Calculation                           │    │
│  │  - Evidence Aggregation                             │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 处理流程 / Processing Flow

1. **规则执行阶段 / Rule Execution Phase**
   - 执行Cypher查询获取候选模式
   - 解析查询结果
   - 收集证据信息

2. **推理处理阶段 / Inference Processing Phase**
   - 应用置信度公式
   - 过滤低于阈值的结果
   - 构建证据链

3. **输出生成阶段 / Output Generation Phase**
   - 生成Neo4j Cypher查询
   - 生成统计摘要
   - 生成人类可读报告

---

## 使用指南 / Usage Guide

### 基本用法 / Basic Usage

```bash
# 激活conda环境
conda activate pharmakg-api

# 运行所有推理规则
python3 -m tools.infer_cross_domain_relationships \
    --output-dir /root/autodl-tmp/pj-pharmaKG/data/validated \
    --confidence-threshold 0.5 \
    --dry-run
```

### 命令行参数 / Command Line Arguments

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--output-dir` | 输出目录 | `data/validated` |
| `--confidence-threshold` | 最小置信度阈值 | 0.5 |
| `--dry-run` | 干运行模式（不应用到Neo4j） | False |
| `--apply-to-neo4j` | 应用推理关系到Neo4j | False |
| `--limit-per-rule` | 每个规则的限制数量 | None |
| `--rules` | 指定要执行的规则 | 全部 |

### 执行特定规则 / Execute Specific Rules

```bash
# 仅执行药物重定位和安全信号检测规则
python3 -m tools.infer_cross_domain_relationships \
    --rules drug_repurposing safety_signal \
    --confidence-threshold 0.7
```

### 应用到Neo4j / Apply to Neo4j

```bash
# 生成查询并应用到Neo4j
python3 -m tools.infer_cross_domain_relationships \
    --apply-to-neo4j \
    --confidence-threshold 0.6
```

---

## 置信度计算 / Confidence Calculation

### 置信度级别 / Confidence Levels

| 级别 | 范围 | 描述 | 证据类型 |
|------|------|------|----------|
| A | 0.9-1.0 | 非常高 | 临床验证 |
| B | 0.7-0.9 | 高 | 计算证据 |
| C | 0.5-0.7 | 中等 | 统计关联 |
| D | 0.3-0.5 | 低 | 推断关联 |
| E | 0.0-0.3 | 非常低 | 弱关联 |

### 置信度公式详解 / Confidence Formula Details

#### 1. 药物重定位置信度

**因素 / Factors:**
- 化合物活性强度（pchembl_value）
- 靶标-疾病关联强度（confidence_score）

**公式 / Formula:**
```python
confidence = (pchembl_value / 10.0) * target_disease_confidence

# 示例 / Example
# pchembl_value = 7.5 (强活性)
# confidence_score = 0.8 (强关联)
# confidence = 0.75 * 0.8 = 0.6 (中等置信度)
```

#### 2. 安全信号置信度

**因素 / Factors:**
- 严重不良事件数量（ae_count）

**公式 / Formula:**
```python
confidence = min(0.95, 0.5 + (ae_count * 0.1))

# 示例 / Example
# ae_count = 5
# confidence = min(0.95, 0.5 + 0.5) = 0.95 (非常高置信度)
```

#### 3. 竞争情报置信度

**因素 / Factors:**
- 靶标特异性（target_specificity）

**公式 / Formula:**
```python
confidence = (specificity_1 + specificity_2) / 2.0

# 示例 / Example
# specificity_1 = 0.8 (高特异性)
# specificity_2 = 0.9 (非常高特异性)
# confidence = 0.85 (高置信度)
```

---

## 证据链追踪 / Evidence Trail Tracking

### 证据链结构 / Evidence Trail Structure

```json
{
  "evidence_trail": [
    {
      "relationship": "r1",
      "type": "INHIBITS",
      "source": "ChEMBL",
      "properties": {
        "pchembl_value": 7.5,
        "assay_type": "Biochemical"
      }
    },
    {
      "relationship": "r2",
      "type": "ASSOCIATED_WITH_DISEASE",
      "source": "DisGeNET",
      "properties": {
        "confidence_score": 0.8,
        "evidence_count": 15
      }
    }
  ]
}
```

### 证据来源 / Evidence Sources

| 来源 | 可信度 | 描述 |
|------|--------|------|
| ClinicalTrials.gov | A | 临床试验数据 |
| ChEMBL | A | 生物活性数据 |
| FDA | A | 监管机构数据 |
| DisGeNET | B | 疾病-基因关联 |
| STRING | B | 蛋白质相互作用 |
| GO Annotation | C | 基因本体论 |

### 证据级别 / Evidence Levels

| 级别 | 描述 | 何时使用 |
|------|------|----------|
| A | 实验验证 / 实验室或临床证据 | 直接实验数据 |
| B | 计算证据 / 统计或生物信息学分析 | 预测或关联分析 |
| C | 临床观察 / 病例报告或上市后监测 | 真实世界证据 |
| D | 推断证据 / 基于逻辑推断 | 知识图谱推理 |
| E | 弱证据 / 间接或低质量证据 | 文本挖掘或假设 |

---

## Neo4j集成 / Neo4j Integration

### 推理关系创建 / Creating Inferred Relationships

#### 单向关系 / Unidirectional Relationship

```cypher
MATCH (c:Compound {id: 'COMPOUND:123'})
MATCH (d:Disease {id: 'DISEASE:456'})
MERGE (c)-[r:POTENTIALLY_TREATS]->(d)
ON CREATE SET r += {
    inference_rule: "drug_repurposing_opportunity",
    evidence_level: "D",
    confidence: 0.6,
    inferred_at: datetime(),
    evidence_trail: "[...]",
    requires_clinical_validation: true
};
```

#### 双向关系 / Bidirectional Relationship

```cypher
MATCH (c1:Compound {id: 'COMPOUND:123'})
MATCH (c2:Compound {id: 'COMPOUND:456'})
MERGE (c1)-[r1:COMPETES_WITH]->(c2)
ON CREATE SET r1 += {
    inference_rule: "competitive_analysis",
    evidence_level: "B",
    confidence: 0.85,
    inferred_at: datetime(),
    shared_target: true
};
MERGE (c2)-[r2:COMPETES_WITH]->(c1)
ON CREATE SET r2 += {
    inference_rule: "competitive_analysis",
    evidence_level: "B",
    confidence: 0.85,
    inferred_at: datetime(),
    shared_target: true
};
```

### 查询推理关系 / Querying Inferred Relationships

#### 按置信度查询 / Query by Confidence

```cypher
MATCH (a)-[r]->(b)
WHERE r.confidence >= 0.7
AND r.evidence_level IN ['A', 'B', 'C']
RETURN a, r, b
ORDER BY r.confidence DESC;
```

#### 按规则类型查询 / Query by Rule Type

```cypher
MATCH (c:Compound)-[r:POTENTIALLY_TREATS]->(d:Disease)
WHERE r.inference_rule = 'drug_repurposing_opportunity'
RETURN c.name, d.name, r.confidence
ORDER BY r.confidence DESC
LIMIT 20;
```

#### 获取证据链 / Get Evidence Trail

```cypher
MATCH (c:Compound)-[r:POTENTIALLY_TREATS]->(d:Disease)
WHERE c.id = 'COMPOUND:123'
RETURN r.evidence_trail AS evidence;
```

---

## 性能优化 / Performance Optimization

### 批量处理 / Batch Processing

**默认批处理 / Default Batching:**
- 每个规则独立执行
- 结果在内存中聚合
- 批量写入Neo4j

**优化建议 / Optimization Recommendations:**

1. **限制结果数量 / Limit Results**
   ```bash
   --limit-per-rule 1000
   ```

2. **选择特定规则 / Select Specific Rules**
   ```bash
   --rules drug_repurposing safety_signal
   ```

3. **调整置信度阈值 / Adjust Confidence Threshold**
   ```bash
   --confidence-threshold 0.7
   ```

### 查询优化 / Query Optimization

#### 索引建议 / Index Recommendations

```cypher
// 创建复合索引
CREATE INDEX compound_inchikey IF NOT EXISTS
FOR (c:Compound) ON (c.inchikey);

CREATE INDEX target_uniprot IF NOT EXISTS
FOR (t:Target) ON (t.uniprot_id);

CREATE INDEX disease_mondo IF NOT EXISTS
FOR (d:Disease) ON (d.mondo_id);

// 创建关系索引
CREATE INDEX rel_inhibits_pchembl IF NOT EXISTS
FOR ()-[r:INHIBITS]->() ON (r.pchembl_value);

CREATE INDEX rel_associated_confidence IF NOT EXISTS
FOR ()-[r:ASSOCIATED_WITH_DISEASE]->() ON (r.confidence_score);
```

#### 查询计划分析 / Query Plan Analysis

```cypher
// 分析查询执行计划
EXPLAIN
MATCH (c:Compound)-[r1:INHIBITS]->(t:Target)
MATCH (t)-[r2:ASSOCIATED_WITH_DISEASE]->(d:Disease)
WHERE r1.pchembl_value >= 6.0
AND r2.confidence_score >= 0.7
RETURN c, d, r1, r2;
```

---

## 故障排查 / Troubleshooting

### 常见问题 / Common Issues

#### 1. 没有找到推理结果 / No Inference Results Found

**可能原因 / Possible Causes:**
- 数据库中没有所需的关系类型
- 置信度阈值设置过高
- Cypher查询条件过于严格

**解决方案 / Solutions:**
```bash
# 降低置信度阈值
--confidence-threshold 0.3

# 检查数据库中的关系
MATCH ()-[r:INHIBITS]->()
RETURN count(r);

# 查看规则执行日志
--verbose
```

#### 2. Neo4j连接错误 / Neo4j Connection Error

**症状 / Symptom:**
```
ServiceUnavailable: Unable to connect to bolt://localhost:7687
```

**解决方案 / Solutions:**
```bash
# 检查Neo4j是否运行
systemctl status neo4j

# 验证连接
python3 -c "from api.database import Neo4jConnection; db = Neo4jConnection(); print(db.verify_connection())"

# 检查配置
cat api/.env | grep NEO4J
```

#### 3. 置信度计算错误 / Confidence Calculation Error

**症状 / Symptom:**
```
KeyError: 'pchembl_value'
```

**解决方案 / Solutions:**
- 检查关系中是否存在所需属性
- 使用COALESCE提供默认值
- 更新Cypher查询模式

```cypher
// 使用COALESCE处理缺失值
COALESCE(r.pchembl_value, 0) AS pchembl_value
```

### 调试技巧 / Debugging Tips

#### 启用详细日志 / Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或者设置特定日志级别
logging.getLogger('tools.infer_cross_domain_relationships').setLevel(logging.DEBUG)
```

#### 查看推理摘要 / View Inference Summary

```bash
# 查看JSON摘要
cat data/validated/inference_summary.json | jq '.statistics'

# 查看按规则分类的统计
cat data/validated/inference_summary.json | jq '.by_rule'

# 查看置信度分布
cat data/validated/inference_summary.json | jq '.confidence_distribution'
```

#### 检查生成的Cypher查询 / Inspect Generated Cypher

```bash
# 查看生成的查询
head -100 data/validated/inferred_relationships.cypher

# 验证查询语法
cypher-shell -a bolt://localhost:7687 -u neo4j -p password < data/validated/inferred_relationships.cypher
```

---

## 附录 / Appendix

### A. 推理规则配置 / Inference Rule Configuration

**添加自定义规则 / Adding Custom Rules:**

```python
custom_rule = InferenceRule(
    name="my_custom_rule",
    description="Custom inference rule",
    rule_type=InferenceRuleType.CUSTOM,
    cypher_pattern="""
        MATCH (a:Entity1)-[r1:REL1]->(b:Entity2)
        WHERE r1.property >= threshold
    """,
    confidence_formula="r1.property * 0.5",
    relationship_type="INFERRED_REL",
    relationship_direction="outgoing",
    properties={
        "inference_rule": "my_custom_rule",
        "evidence_level": "D"
    }
)
```

### B. 置信度阈值建议 / Confidence Threshold Recommendations

| 用途 | 建议阈值 | 说明 |
|------|----------|------|
| 药物重定位筛选 | ≥0.6 | 平衡召回率和精确度 |
| 安全信号监测 | ≥0.7 | 高置信度以避免误报 |
| 竞争情报分析 | ≥0.5 | 可接受较低置信度 |
| 供应链风险评估 | ≥0.8 | 高置信度以确保准确性 |
| 通路发现 | ≥0.5 | 探索性分析 |
| 试验成功预测 | ≥0.7 | 支持决策制定 |

### C. 性能基准 / Performance Benchmarks

| 数据规模 | 推理时间 | 内存使用 | 说明 |
|----------|----------|----------|------|
| 1K 实体 | <1分钟 | <100MB | 小规模测试 |
| 10K 实体 | 2-5分钟 | 100-500MB | 中等规模 |
| 100K 实体 | 15-30分钟 | 500MB-2GB | 大规模处理 |
| 1M+ 实体 | 1-3小时 | 2-8GB | 生产环境 |

---

## 参考资料 / References

1. **知识图谱推理技术 / Knowledge Graph Reasoning:**
   - Link Prediction in Knowledge Graphs
   - Path-Based Reasoning Methods
   - Embedding-Based Inference

2. **制药行业应用 / Pharmaceutical Applications:**
   - Drug Repurposing: A Review
   - Pharmacovigilance and Knowledge Graphs
   - Clinical Trial Prediction Models

3. **Neo4j最佳实践 / Neo4j Best Practices:**
   - Cypher Query Tuning
   - Indexing Strategies
   - Batch Processing Patterns

---

**文档版本 / Document Version:** v1.0
**最后更新 / Last Updated:** 2025-02-08
**维护者 / Maintainer:** PharmaKG Development Team
