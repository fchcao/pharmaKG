# 监管合规领域知识图谱访谈纪要 - 第一轮

**访谈日期**: 2025-02-04
**访谈领域**: 监管合规 (Regulatory Compliance)
**访谈状态**: 已完成

---

## 一、核心实体确认

用户确认监管合规领域需要包含以下**四类核心实体**：

| 实体类别 | 包含内容 | 优先级 |
|---------|---------|-------|
| **监管机构** | FDA、NMPA、EMA、PMDA等 | 高 |
| **监管申报** | IND、NDA、BLA、MAA等 | 高 |
| **临床试验/研究** | I-IV期临床试验、上市后研究 | 高 |
| **安全性事件** | AE、SAE、SUSAR、ADR等 | 高 |

---

## 二、核心业务流程

| 流程 | 描述 | 在KG中的体现 |
|-----|------|-------------|
| **注册申报流程** | 从临床试验申请到批准的全流程 | Submission → Review → Approval → Labeling |
| **药物警戒流程** | 不良反应收集、评估、报告 | AE Collection → Causality Assessment → Reporting |
| **合规检查流程** | GMP、GCP、GVP等检查与合规 | Inspection → Findings → CAPA → Status |
| **生命周期管理** | 产品标签、说明书、宣传材料审核 | Post-approval Changes → Supplements → Renewals |

---

## 三、核心痛点与KG解决方案

| 痛点 | KG解决方案 |
|-----|-----------|
| **法规复杂性** | 多地区法规本体化、规则引擎 |
| **数据整合难题** | 统一安全数据模型、标准化术语 |
| **时限压力** | 自动化报告、预警系统 |
| **变更管理** | 法规变更跟踪、影响分析 |

---

## 四、实体分类体系设计

### 4.1 监管机构分类

```
RegulatoryAuthority (监管机构)
├── 按地区分类:
│   ├── NorthAmerica (北美)
│   │   ├── FDA (美国食品药品监督管理局)
│   │   ├── HealthCanada (加拿大卫生部)
│   │   └── COFEPRIS (墨西哥联邦卫生风险防护委员会)
│   ├── Europe (欧洲)
│   │   ├── EMA (欧洲药品管理局)
│   │   └── NationalAuthorities (各国监管机构)
│   ├── AsiaPacific (亚太)
│   │   ├── NMPA (中国国家药品监督管理局)
│   │   ├── PMDA (日本药品医疗器械局)
│   │   ├── MFDS (韩国食品医药品安全处)
│   │   └── TGA (澳大利亚治疗商品管理局)
│   └── OtherRegions (其他地区)
│
├── 按监管范围分类:
│   ├── DrugAuthority (药品监管)
│   ├── DeviceAuthority (器械监管)
│   ├── BiologicsAuthority (生物制品监管)
│   └── CombinationProductAuthority (组合产品监管)
│
└── 按合作框架分类:
    ├── ICHMember (ICH成员)
    ├── ICHObserver (ICH观察员)
    └── NonMember (非成员)
```

### 4.2 监管申报分类（多维）

```
RegulatorySubmission (监管申报)
├── 按申报类型分类:
│   ├── IND (Investigational New Drug)
│   │   ├── OriginalIND
│   │   ├── Amendment
│   │   └── AnnualReport
│   ├── NDA (New Drug Application)
│   │   ├── 505(b)(1) (含新分子实体)
│   │   └── 505(b)(2) (含已批准活性成分)
│   ├── BLA (Biologics License Application)
│   ├── MAA (Marketing Authorization Application)
│   └── GenericApplication (仿制药申请)
│
├── 按申报阶段分类:
│   ├── InitialSubmission (初始申报)
│   ├── Supplement (补充申报)
│   │   ├── PAS (Prior Approval Supplement)
│   │   ├── CBE (Changes Being Effected)
│   │   └── AnnualReport (年度报告)
│   └── Renewal (续期申报)
│
├── 按申报地区分类:
│   ├── USSubmission (美国申报)
│   ├── EUSubmission (欧盟申报)
│   ├── ChinaSubmission (中国申报)
│   └── JapanSubmission (日本申报)
│
└── 按治疗领域分类:
    ├── Oncology (肿瘤)
    ├── Cardiovascular (心血管)
    ├── CNS (中枢神经)
    └── ...
```

### 4.3 安全性事件分类

```
SafetyEvent (安全性事件)
├── 按严重程度分类:
│   ├── SAE (Serious Adverse Event)
│   │   ├── Death (死亡)
│   │   ├── LifeThreatening (危及生命)
│   │   ├── Hospitalization (住院)
│   │   ├── Disability (残疾)
│   │   └── CongenitalAnomaly (先天异常)
│   └── AE (Adverse Event - 非严重)
│
├── 按因果关系分类:
│   ├── Related (相关)
│   ├── PossiblyRelated (可能相关)
│   ├── Unrelated (不相关)
│   └── Unclassifiable (无法分类)
│
├── 按预期性分类:
│   ├── Expected (预期)
│   └── Unexpected (非预期)
│
├── 按报告来源分类:
│   ├── SpontaneousReport (自发报告)
│   ├── ClinicalTrial (临床试验)
│   ├── Literature (文献)
│   ├── Registry (登记研究)
│   └── SocialMedia (社交媒体)
│
└── 按报告时限分类:
    ├── ImmediateReport (立即报告，7/15天)
    ├── PeriodicReport (定期报告)
    └── FollowUpReport (随访报告)
```

### 4.4 检查/稽查分类

```
Inspection (检查/稽查)
├── 按检查类型分类:
│   ├── GMPInspection (GMP检查)
│   ├── GCPInspection (GCP稽查)
│   ├── GLPInspection (GLP检查)
│   └── GVPInspection (GVP检查)
│
├── 按检查发起方分类:
│   ├── RegulatoryInspection (监管机构检查)
│   ├── SponsorAudit (申办方稽查)
│   └── ThirdPartyAudit (第三方审计)
│
├── 按检查结果分类:
│   ├── NAI (No Action Indicated)
│   ├── VAI (Voluntary Action Indicated)
│   └── OAI (Official Action Indicated)
│
└── 按检查范围分类:
    ├── RoutineInspection (常规检查)
    ├── ForCauseInspection (有因检查)
    └── PreApprovalInspection (批准前检查)
```

---

## 五、关系类型设计

### 5.1 申报流程关系

```
Company ──[submits]────────────────▶ Submission
    ├── submission_type (申报类型)
    ├── submission_date (申报日期)
    └── submission_number (申报编号)

Submission ──[submitted_to]─────────▶ RegulatoryAuthority
    ├── jurisdiction (管辖范围)
    └── review_process (审评流程)

Submission ──[contains]─────────────▶ DrugProduct
    ├── product_name (产品名称)
    └── dosage_form (剂型)

Submission ──[includes_study]───────▶ ClinicalTrial
    ├── study_id (研究编号)
    └── study_phase (研究阶段)
```

### 5.2 审批决策关系

```
RegulatoryAuthority ──[reviews]─────▶ Submission
    ├── review_start_date (审评开始日期)
    ├── review_clock_days (审评天数)
    └── review_cycle_number (审评轮次)

RegulatoryAuthority ──[makes_decision]▶ Submission
    ├── decision_type (决策类型)
    │   ├── Approval (批准)
    │   ├── CompleteResponse (CRL - 完全回应信)
    │   ├── Withdrawal (撤回)
    │   └── Refusal (拒绝)
    ├── decision_date (决策日期)
    ├── approval_number (批准文号)
    └── conditions_attached (附加条件)

Submission ──[requires]─────────────▶ PostMarketingCommitment
    ├── commitment_type (承诺类型)
    ├── due_date (截止日期)
    └── status (状态)
```

### 5.3 安全性事件关系

```
Patient ──[experienced]────────────▶ SafetyEvent
    ├── event_date (事件日期)
    ├── onset_date (发作日期)
    └── outcome (结局)

SafetyEvent ──[associated_with]────▶ DrugProduct
    ├── suspect_product (疑似产品)
    ├── indication (适应症)
    ├── dose (剂量)
    └── duration (用药时长)

SafetyEvent ──[assessed_by]─────────▶ CausalityAssessment
    ├── assessor (评估者)
    ├── algorithm (算法)
    ├── causality_category (因果类别)
    └── confidence_score (置信度)

SafetyEvent ──[reported_via]────────▶ ReportSource
    ├── source_type (来源类型)
    ├── reporter_qualification (报告人资质)
    └── report_date (报告日期)

SafetyEvent ──[requires_reporting]──▶ RegulatoryReport
    ├── report_type (报告类型)
    ├── deadline_days (截止天数)
    ├── submission_date (提交日期)
    └── reference_number (编号)
```

### 5.4 检查关系

```
Facility ──[inspected_by]──────────▶ Inspection
    ├── inspection_type (检查类型)
    ├── inspection_start_date (开始日期)
    └── inspection_end_date (结束日期)

Inspector ──[conducts]─────────────▶ Inspection
    ├── inspector_name (检查员姓名)
    └── inspector_role (检查员角色)

Inspection ──[results_in]──────────▶ InspectionFinding
    ├── finding_category (发现类别)
    │   ├── Critical (关键缺陷)
    │   ├── Major (主要缺陷)
    │   └── Minor (次要缺陷)
    ├── description (描述)
    └── reference_regulation (引用法规)

InspectionFinding ──[requires_action]─▶ CAPA (Corrective and Preventive Action)
    ├── action_type (行动类型)
    ├── responsible_party (责任方)
    ├── due_date (截止日期)
    └── status (状态)
```

### 5.5 与R&D的关联关系

```
R&D Compound ──[becomes]────────────▶ RegulatoryDrugProduct
    ├── formulation_change (处方变更)
    └── manufacturing_change (生产工艺变更)

R&D Target ──[has_safety_signal]───▶ SafetyEvent
    ├── mechanism_based (机制相关)
    └── off_target (脱靶效应)

ClinicalTrial ──[generates_evidence]▶ Submission
    ├── evidence_type (证据类型)
    └── study_reference (研究引用)

PreclinicalStudy ──[identifies_risk]─▶ SafetyConcern
    ├── animal_species (动物种属)
    └── risk_level (风险等级)
```

---

## 六、典型查询场景

### 6.1 注册状态追踪

```cypher
// 查询: 追踪产品在各地区的注册状态和历史
MATCH (d:DrugProduct {name: "Drug X"})
MATCH (d)<-[:contains]-(s:RegulatorySubmission)
MATCH (s)-[:submitted_to]->(ra:RegulatoryAuthority)
MATCH (ra)-[:makes_decision]->(dec:Decision)
RETURN ra.name, s.submission_type, s.submission_date,
       dec.decision_type, dec.decision_date, dec.approval_number
ORDER BY s.submission_date DESC
```

### 6.2 安全性信号检测

```cypher
// 查询: 分析产品安全性信号和趋势
MATCH (se:SafetyEvent)-[:associated_with]->(d:DrugProduct {name: "Drug X"})
MATCH (se)-[:assessed_by]->(ca:CausalityAssessment)
WHERE ca.causality_category IN ["Related", "PossiblyRelated"]
WITH se, se.event_type as eventType, count(se) as eventCount
WHERE eventCount > 3
RETURN eventType, eventCount,
       collect(se.s seriousness)[0..5] as examples
ORDER BY eventCount DESC
```

### 6.3 合规监控

```cypher
// 查询: 监控合规要求和法规变更
MATCH (ra:RegulatoryAuthority)-[:issues]->(r:Regulation)
WHERE r.effective_date > date("2024-01-01")
MATCH (r)-[:applies_to]->(dt:DrugType)
MATCH (d:DrugProduct)-[:has_type]->(dt)
RETURN ra.name, r.regulation_type, r.effective_date,
       d.name as affected_products
ORDER BY r.effective_date DESC
```

### 6.4 报告生成

```cypher
// 查询: 生成监管报告汇总
MATCH (d:DrugProduct {name: "Drug X"})<-[:associated_with]-(se:SafetyEvent)
MATCH (se)-[:reported_via]->(rr:RegulatoryReport)
MATCH (rr)-[:submitted_to]->(ra:RegulatoryAuthority)
WITH ra, rr.report_type, count(rr) as reportCount
RETURN ra.name, rr.report_type, reportCount
ORDER BY reportCount DESC
```

### 6.5 R&D-Regulatory关联查询

```cypher
// 查询: 靶点相关安全性信号追踪到R&D阶段
MATCH (t:Target)-[:studied_in]->(s:Study)
MATCH (s)-[:identifies_risk]->(sc:SafetyConcern)
MATCH (sc)-[:manifests_as]->(se:SafetyEvent)
WHERE se.event_type = "Liver Toxicity"
RETURN t.name, s.study_type, sc.risk_level, count(se) as eventCount
```

---

## 七、数据源与优先级

| 数据源类型 | 优先级 | 主要用途 | 示例 |
|-----------|-------|---------|------|
| **公共数据库** | 1 | 临床试验、药物信息 | ClinicalTrials.gov, Drugs@FDA |
| **监管机构数据** | 2 | 审评决定、法规公告 | FDA AA database, EudraCT |
| **内部系统** | 3 | PV数据、注册管理 | Argus, Arisg, RIM |
| **文献/病例报告** | 4 | 安全信号发现 | PubMed, Case reports |

### 标识符映射策略

```
RegulatorySubmission标识符:
├── FDA: NDA/BLA Number (e.g., NDA 123456)
├── EMA: EudraCT Number (e.g., 2024-123456-12)
├── NMPA: 申报编号 (e.g., CXSL2400XXX)
└── 内部: 申报项目编号

SafetyEvent标识符:
├── ICSR: Case ID (CIOMS I格式)
├── 局部报告编号
└── 内部事件编号

DrugProduct标识符:
├── FDA: UNII (Unique Ingredient Identifier)
├── EMA: Product Number (e.g., EU/1/00/000/001)
├── NMPA: 批准文号 (e.g., 国药准字H20240001)
└── 内部: 产品代码
```

---

## 八、与R&D数据关联

**关联策略**：**需要关联**，深度整合

| 关联场景 | R&D实体 | 监管实体 | 关联方式 |
|---------|--------|---------|---------|
| **靶点安全性** | Target | SafetyEvent | Target.safety_signal |
| **成药性评估** | Compound | Submission | Compound.regulatory_pathway |
| **临床证据** | ClinicalTrial | Submission | Study.evidence_for |
| **机制相关风险** | Mechanism | SafetyConcern | Mechanism.safety_risk |

**设计决策**：
- 监管合规与R&D需要**深度关联**
- 主要关联点：**安全性信号**、**证据链**、**风险评估**
- 支持：靶点选择决策、化合物优化、临床设计

---

## 九、核心指标体系

### 9.1 申报效率指标

```
SubmissionEfficiency
├── timeliness (时效性)
│   ├── submission_to_approval_days (申报到批准天数)
│   ├── cycle_time (审评周期)
│   └── on_time_submission_rate (按时申报率)
│
├── success_rate (成功率)
│   ├── first_cycle_approval_rate (首轮批准率)
│   ├── complete_response_rate (CRL率)
│   └── withdrawal_rate (撤回率)
│
└── quality (质量)
    ├── review_cycle_number (审评轮次)
    ├── information_request_count (信息请求次数)
    └── meeting_frequency (会议频率)
```

### 9.2 安全性监测指标

```
SafetyMonitoring
├── reporting_timeliness (报告时效)
│   ├── serious_report_within_7days (7天内报告率)
│   ├── non_serious_report_within_15days (15天内报告率)
│   └── follow_up_report_rate (随访报告率)
│
├── signal_detection (信号检测)
│   ├── pbrer_signal_count (PBRER信号数)
│   ├── aem_signal_count (AEM信号数)
│   └── emerging_signal_count (新发信号数)
│
└── causality_assessment (因果评估)
    ├── related_case_rate (相关病例率)
    ├── positive_rechallenge_rate (再激发阳性率)
    └── dechallenge_rate (去激发率)
```

### 9.3 合规状态指标

```
ComplianceStatus
├── inspection_status (检查状态)
│   ├── oai_facility_count (OAI设施数)
│   ├── vai_facility_count (VAI设施数)
│   └── nai_facility_count (NAI设施数)
│
├── capa_status (CAPA状态)
│   ├── open_critical_capa (开放关键CAPA数)
│   ├── overdue_capa_count (逾期CAPA数)
│   └── closed_on_time_capa_rate (按时关闭CAPA率)
│
└── commitment_status (承诺状态)
    ├── overdue_pmc_count (逾期PMC数)
    ├── pending_pmc_count (待完成PMC数)
    └── pmc_completion_rate (PMC完成率)
```

---

## 十、待讨论问题

1. [ ] 多地区**同步申报**的优先级策略如何定义？
2. [ ] 安全性信号的**自动检测**阈值如何设定？
3. [ ] 监管变更的**影响分析**范围如何确定？
4. [ ] **RWE数据**在安全性评估中的权重如何确定？
5. [ ] 敏感审评信息的**访问权限**如何控制？

---

## 十一、下一步行动

- [x] 监管合规领域第一轮访谈完成
- [ ] 生成监管合规领域Schema设计文档
- [ ] 开始第二轮访谈（针对待讨论问题）
- [ ] 整合三个领域的Schema设计

---

**访谈纪要版本**: v1.0
**最后更新**: 2025-02-04
