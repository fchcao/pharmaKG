# 制药行业知识图谱本体Schema设计文档

**文档版本**: v2.0
**最后更新**: 2025-02-06
**状态**: 基于三轮访谈完成

---

## 目录

1. [文档概述](#一文档概述)
2. [核心设计原则](#二核心设计原则)
3. [实体层次结构](#三实体层次结构)
4. [关系类型定义](#四关系类型定义)
5. [属性定义](#五属性定义)
6. [跨域关联设计](#六跨域关联设计)
7. [标识符映射策略](#七标识符映射策略)
8. [数据源集成](#八数据源集成)
9. [实施指南](#九实施指南)

---

## 一、文档概述

### 1.1 目标与范围

本文档定义了制药行业全流程知识图谱的本体Schema，覆盖以下业务领域：

| 业务领域 | 覆盖范围 | 核心实体数 |
|---------|---------|-----------|
| **研究与发现 (R&D)** | 靶点发现、化合物筛选、构效关系、成药性评估 | 4大类 |
| **供应链管理** | 原料采购、生产制造、物流配送、短缺管理 | 4大类 |
| **监管合规** | 注册申报、药物警戒、合规检查、生命周期管理 | 4大类 |
| **临床试验** | 试验设计、受试者管理、数据采集、安全性监测 | 10+类 |

### 1.2 设计方法论

本Schema基于以下方法设计：

1. **三轮深度访谈**: 每个领域进行三轮访谈，共56个问题，71个关键决策
   - 第一轮: 业务领域梳理和核心实体识别
   - 第二轮: 待讨论问题深化和复杂场景设计
   - 第三轮: 技术选型和实施细节确认
2. **跨领域整合**: 识别跨领域关联需求，设计桥接关系
3. **混合策略**: 对复杂问题采用混合策略而非单一解决方案
4. **分层建模**: 按风险分层、按质量分层、按优先级分层
5. **时态支持**: 全生命周期时间戳和版本控制

### 1.3 技术栈选型（第三轮确认）

| 技术组件 | 选择方案 | 说明 |
|---------|---------|------|
| **图数据库** | Neo4j 5.x LTS | 成熟稳定，Cypher查询语言，支持Docker部署 |
| **本体语言** | Turtle + OWL + SHACL | Turtle用于数据存储，OWL用于推理，SHACL用于验证 |
| **部署方式** | Docker容器（autodl云服务器） | 自有云服务器，数据完全可控 |
| **查询语言** | Cypher + SPARQL | Cypher用于图查询，SPARQL用于RDF查询 |
| **推理引擎** | Neo4j内置 + OWL API | 基础推理用Neo4j，复杂推理用OWL API |

### 1.3 核心设计模式

```
┌─────────────────────────────────────────────────────────────┐
│                    制药KG核心设计模式                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  模式1: 多维分类体系 (Multi-dimensional Classification)       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 实体不是单一分类，而是同时属于多个分类维度             │   │
│  │ 示例: Compound                                      │   │
│  │   ├── 维度1: StructureType (SmallMolecule/Biologic) │   │
│  │   ├── 维度2: DevelopmentStage (Hit/Lead/PCC)        │   │
│  │   └── 维度3: TherapeuticArea (Oncology/CNS/CV)     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  模式2: 上下文依赖关系 (Context-dependent Relations)         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 关系携带丰富的上下文属性，而非简单连接                 │   │
│  │ 示例: Compound -[inhibits]-> Target                   │   │
│  │   ├── activity_value: 10.5 nM                        │   │
│  │   ├── activity_type: IC50                            │   │
│  │   ├── measured_in_assay: assay123                    │   │
│  │   ├── confidence_score: 0.85                         │   │
│  │   └── valid_from: 2024-01-01                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  模式3: 状态机建模 (State Machine Modeling)                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 实体状态通过状态机建模，支持转换规则和回退             │   │
│  │ 示例: Compound State Machine                         │   │
│  │   Hit ──[satisfies_criteria]──▶ Lead                 │   │
│  │   Lead ──[optimization_complete]─▶ PCC               │   │
│  │   PCC ──[tox_passed]─────────────▶ ClinicalCandidate │   │
│  │   Lead ──[failure+approval]───────▶ Hit (rollback)   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  模式4: 风险分层处理 (Risk Stratification)                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 按风险等级采用不同的处理策略                          │   │
│  │ 示例: 供应链追溯深度                                  │   │
│  │   ├── 高风险物料 → 5级追溯                            │   │
│  │   ├── 中风险物料 → 3级追溯                            │   │
│  │   └── 低风险物料 → 1级追溯                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、核心设计原则

### 2.1 五大核心原则

| 原则 | 描述 | 应用场景 |
|-----|------|---------|
| **渐进式复杂度管理** | 简单场景简单规则，复杂场景分层处理 | 全领域 |
| **上下文依赖建模** | 关系和属性依赖业务上下文 | 全领域 |
| **风险分层处理** | 按风险等级采用不同策略 | 供应链、监管、临床 |
| **多维度数据质量** | 完整性、准确性、一致性、时效性 | 临床、监管 |
| **全生命周期审计** | 数据变更、访问、决策全程可追溯 | 全领域 |

### 2.2 命名规范

```
实体命名规范:
├── PascalCase: Compound, Target, ClinicalTrial
├── 组合命名: SmallMolecule, RegulatoryAuthority
└── 缩写规范: API, PRO, DHT, RWE

关系命名规范:
├── 动词形式: inhibits, activates, treats, supplies
├── 动词_名词: has_activity, located_in, enrolls_in
├── 方向性: ──[:transitions_to]──▶ (单向)
└── 传递性标注: part_of (传递), interacts_with (非传递)

属性命名规范:
├── snake_case: activity_value, approval_date
├── 单位后缀: _value, _unit, _type
├── 布尔前缀: is_, has_, can_
└── 时间后缀: _date, _from, _until
```

### 2.3 建模约定

```turtle
# 约定1: 关系必须有方向性
# ✓ 正确
:Compound :inhibits :Target .

# ✗ 错误 (避免泛化关系)
:Compound :has_relationship :Target .

# 约定2: 关系应携带上下文属性
# ✓ 正确
:Compound :inhibits :Target ;
    :has_activity_value "10.5"^^xsd:float ;
    :has_activity_unit "nM"^^xsd:string ;
    :measured_in_assay :assay123 .

# 约定3: 多标识符设计
# ✓ 正确
:Compound
    :primary_id "InChIKey=XXXXX"^^xsd:string ;
    :secondary_id "PubChem_CID:12345"^^xsd:string ;
    :internal_id "CMP-001234"^^xsd:string .
```

---

## 三、实体层次结构

### 3.1 顶层实体分类

```
pharmaceutical:Entity (制药行业实体根类)
│
├── rdm:ResearchEntity (研究实体)
│   ├── Chemical
│   ├── Target
│   ├── Assay
│   └── Pathway
│
├── clinical:ClinicalEntity (临床实体)
│   ├── ClinicalTrial
│   ├── Subject
│   ├── InvestigationalSite
│   ├── Endpoint
│   ├── Investigator
│   └── AdverseEvent
│
├── supplychain:SupplyEntity (供应链实体)
│   ├── Manufacturer
│   ├── Supplier
│   ├── Material
│   └── SupplyEvent
│
└── regulatory:RegulatoryEntity (监管实体)
    ├── RegulatoryAuthority
    ├── RegulatorySubmission
    ├── SafetyEvent
    └── Inspection
```

### 3.2 R&D领域实体定义

#### 3.2.1 Compound (化合物)

```turtle
:Compound a owl:Class ;
    rdfs:label "Compound" ;
    rdfs:comment "化学实体，包括小分子、生物制剂等" ;

    # 核心属性
    :has_primary_id xsd:string ;
    :has_secondary_id xsd:string ;
    :has_internal_id xsd:string ;
    :has_smiles xsd:string ;
    :has_inchikey xsd:string ;
    :has_molecular_weight xsd:float ;
    :has_molecular_formula xsd:string ;

    # 多维分类 (通过关系实现)
    :has_structure_type :StructureType ;
    :has_development_stage :DevelopmentStage ;
    :has_therapeutic_area :TherapeuticArea ;

    # 状态管理
    :has_current_state :CompoundState ;
    :transitions_to :CompoundState .

# 结构类型
:StructureType a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:SmallMolecule :Biologic :Peptide
                  :Oligonucleotide :PROTAC :ADC)
    ] .

# 开发阶段
:DevelopmentStage a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:Hit :Lead :OptimizedLead
                  :PCC :ClinicalCandidate)
    ] .
```

#### 3.2.2 Target (靶点)

```turtle
:Target a owl:Class ;
    rdfs:label "Target" ;
    rdfs:comment "药物作用的生物靶点" ;

    # 核心属性
    :has_primary_id xsd:string ;  # UniProt Accession
    :has_secondary_id xsd:string ;  # Entrez, Ensembl
    :has_gene_symbol xsd:string ;   # HGNC Symbol
    :has_protein_name xsd:string ;
    :has_gene_sequence xsd:string ;
    :has_protein_sequence xsd:string ;

    # 多维分类
    :has_target_function :TargetFunction ;
    :has_druggability_stage :DruggabilityStage ;
    :has_gene_family :GeneFamily ;
    :has_subcellular_location :SubcellularLocation ;

    # 关系
    :associated_with :Disease ;
    :participates_in :Pathway .

# 靶点功能
:TargetFunction a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:Enzyme :Receptor :IonChannel
                  :Transporter :TranscriptionFactor
                  :StructuralProtein)
    ] .

# 成药性阶段
:DruggabilityStage a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:ValidatedTarget :ClinicalStageTarget
                  :ExploratoryTarget :UndruggableTarget)
    ] .
```

#### 3.2.3 Assay (实验)

```turtle
:Assay a owl:Class ;
    rdfs:label "Assay" ;
    rdfs:comment "生物化学或细胞学实验" ;

    # 核心属性
    :has_assay_id xsd:string ;
    :has_assay_name xsd:string ;
    :has_assay_type :AssayType ;
    :has_detection_method xsd:string ;
    :has_cell_line xsd:string ;
    :has_species xsd:string ;

    # BAO映射
    :maps_to_bao xsd:string ;  # BioAssay Ontology

    # 质量属性
    :has_reproducibility xsd:float ;
    :has_sample_size xsd:integer ;
    :has_data_source xsd:string .

# 实验类型
:AssayType a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:CellBased :Biochemical :InVivo
                  :ExVivo :HighThroughputScreening)
    ] .
```

#### 3.2.4 CompoundState (化合物状态)

```turtle
:CompoundState a owl:Class ;
    rdfs:label "CompoundState" ;
    rdfs:comment "化合物开发状态" ;

    :has_state_name xsd:string ;
    :has_state_description xsd:string ;
    :has_entry_date xsd:date ;
    :has_exit_date xsd:date .

# 状态转换规则
:StateTransitionRule a owl:Class ;
    :has_decision_gate_criteria xsd:string ;
    :requires_milestone :Milestone ;
    :requires_approval xsd:boolean ;
    :has_rollback_condition xsd:string ;
    :has_approval_workflow xsd:string .
```

### 3.3 临床领域实体定义

#### 3.3.1 ClinicalTrial (临床试验)

```turtle
:ClinicalTrial a owl:Class ;
    rdfs:label "ClinicalTrial" ;

    # 核心属性
    :has_trial_id xsd:string ;      # NCT Number
    :has_protocol_id xsd:string ;
    :has_trial_name xsd:string ;
    :has_trial_phase :TrialPhase ;
    :has_trial_type :TrialType ;
    :has_trial_design :TrialDesign ;

    # 多维分类
    :has_trial_purpose :TrialPurpose ;
    :has_regulatory_pathway :RegulatoryPathway ;
    :has_subject_population :SubjectPopulation ;
    :has_control_type :ControlType ;

    # 状态
    :has_trial_status :TrialStatus ;
    :has_start_date xsd:date ;
    :has_completion_date xsd:date ;
    :has_target_enrollment xsd:integer ;
    :has_actual_enrollment xsd:integer .

# 试验阶段
:TrialPhase a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:PhaseI :PhaseII :PhaseIII
                  :PhaseIV :PhaseIN)
    ] .

# 试验设计
:TrialDesign a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:RandomizedControlledTrial
                  :ObservationalStudy :RegistryStudy
                  :AdaptiveTrial :PragmaticTrial)
    ] .
```

#### 3.3.2 Subject (受试者)

```turtle
:Subject a owl:Class ;
    rdfs:label "Subject" ;
    rdfs:comment "临床试验受试者/参与者" ;

    # 核心属性
    :has_subject_id xsd:string ;
    :has_initials xsd:string ;
    :has_birth_year xsd:integer ;
    :has_gender xsd:string ;
    :has_race xsd:string ;
    :has_ethnicity xsd:string ;

    # 参与状态
    :has_enrollment_status :EnrollmentStatus ;
    :has_screening_status :ScreeningStatus ;
    :has_randomization_arm xsd:string ;
    :has_completion_status :CompletionStatus .

# 参与状态
:EnrollmentStatus a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:Screened :ScreenFailed :Enrolled
                  :Randomized :Treated :Completed
                  :Withdrawn :LostToFollowUp)
    ] .
```

#### 3.3.3 InvestigationalSite (研究中心)

```turtle
:InvestigationalSite a owl:Class ;
    rdfs:label "InvestigationalSite" ;

    # 核心属性
    :has_site_id xsd:string ;
    :has_site_name xsd:string ;
    :has_site_type :SiteType ;
    :has_site_tier :SiteTier ;
    :has_geographic_location xsd:string ;

    # 能力评估
    :has_capability_profile :SiteCapabilityProfile ;
    :has_performance_metrics :SitePerformanceMetrics ;
    :has_quality_metrics :SiteQualityMetrics .

# 中心类型
:SiteType a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:AcademicSite :CommunitySite
                  :SpecializedCenter :CRO)
    ] .

# 能力等级
:SiteTier a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:Tier1Site :Tier2Site :Tier3Site :NewSite)
    ] .
```

#### 3.3.4 Endpoint (终点指标)

```turtle
:Endpoint a owl:Class ;
    rdfs:label "Endpoint" ;

    # 核心属性
    :has_endpoint_id xsd:string ;
    :has_endpoint_name xsd:string ;
    :has_endpoint_type :EndpointType ;
    :has_data_type :DataType ;

    # 终点分类
    :is_primary_endpoint xsd:boolean ;
    :is_secondary_endpoint xsd:boolean ;
    :is_exploratory_endpoint xsd:boolean .

# 终点类型
:EndpointType a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:EfficacyEndpoint :SafetyEndpoint
                  :BiomarkerEndpoint :PatientReportedOutcome)
    ] .
```

### 3.4 供应链领域实体定义

#### 3.4.1 Supplier (供应商)

```turtle
:Supplier a owl:Class ;
    rdfs:label "Supplier" ;

    # 核心属性
    :has_supplier_id xsd:string ;
    :has_supplier_name xsd:string ;
    :has_duns_number xsd:string ;
    :has_supplier_type :SupplierType ;
    :has_collaboration_mode :CollaborationMode ;

    # 绩效评分
    :has_performance_tier xsd:string ;
    :has_quality_rating xsd:float ;
    :has_delivery_rating xsd:float ;
    :has_service_rating xsd:float ;

    # 认证状态
    :has_gmp_certification xsd:boolean ;
    :has_fda_approval xsd:boolean ;
    :has_certification_details :Certification .

# 供应商类型
:SupplierType a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:APISupplier :ExcipientSupplier
                  :PackagingSupplier :CDMO)
    ] .
```

#### 3.4.2 Material (物料)

```turtle
:Material a owl:Class ;
    rdfs:label "Material" ;
    rdfs:comment "原料药、辅料、包装材料" ;

    # 核心属性
    :has_material_id xsd:string ;
    :has_material_name xsd:string ;
    :has_cas_number xsd:string ;
    :has_material_type :MaterialType ;
    :has_supply_stage :SupplyStage ;
    :has_control_level :ControlLevel ;

    # 质量规格
    :has_quality_specification xsd:string ;
    :has_storage_conditions xsd:string ;
    :has_shelf_life xsd:string .

# 物料类型
:MaterialType a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:API :Excipient :PackagingMaterial
                  :RawMaterial :Intermediate :BulkProduct)
    ] .
```

#### 3.4.3 SupplyEvent (供应事件)

```turtle
:SupplyEvent a owl:Class ;
    rdfs:label "SupplyEvent" ;

    # 核心属性
    :has_event_id xsd:string ;
    :has_event_type :EventType ;
    :has_event_severity xsd:string ;
    :has_start_date xsd:date ;
    :has_expected_resolution_date xsd:date ;
    :has_actual_resolution_date xsd:date .

# 事件类型
:EventType a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:ShortageEvent :QualityEvent
                  :LogisticsEvent :RegulatoryEvent)
    ] .
```

### 3.5 监管合规领域实体定义

#### 3.5.1 RegulatoryAuthority (监管机构)

```turtle
:RegulatoryAuthority a owl:Class ;
    rdfs:label "RegulatoryAuthority" ;

    # 核心属性
    :has_authority_id xsd:string ;
    :has_authority_name xsd:string ;
    :has_authority_region :Region ;
    :has_authority_scope :AuthorityScope ;
    :has_ich_membership xsd:boolean .

# 监管机构
:RegulatoryAuthority rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:FDA :NMPA :EMA :PMDA
                  :HealthCanada :TGA :MFDS)
    ] .
```

#### 3.5.2 RegulatorySubmission (监管申报)

```turtle
:RegulatorySubmission a owl:Class ;
    rdfs:label "RegulatorySubmission" ;

    # 核心属性
    :has_submission_id xsd:string ;
    :has_submission_type :SubmissionType ;
    :has_submission_stage :SubmissionStage ;
    :has_submission_number xsd:string ;
    :has_submission_date xsd:date ;

    # 申报状态
    :has_submission_status :SubmissionStatus ;
    :has_review_start_date xsd:date ;
    :has_review_clock_days xsd:integer ;
    :has_decision_date xsd:date .

# 申报类型
:SubmissionType a owl:Class ;
    rdfs:subClassOf [
        a owl:Class ;
        owl:oneOf (:IND :NDA :BLA :MAA
                  :GenericApplication :Supplement)
    ] .
```

#### 3.5.3 SafetyEvent (安全性事件)

```turtle
:SafetyEvent a owl:Class ;
    rdfs:label "SafetyEvent" ;

    # 核心属性
    :has_event_id xsd:string ;     # ICSR Case ID
    :has_event_type xsd:string ;
    :has_seriousness xsd:string ;
    :has_event_date xsd:date ;
    :has_onset_date xsd:date ;

    # 因果关系
    :has_causality_category xsd:string ;
    :has_expectedness xsd:string ;
    :has_outcome xsd:string ;

    # 报告信息
    :has_report_source :ReportSource ;
    :has_report_date xsd:date ;
    :has_reporting_deadline xsd:integer .
```

---

## 四、关系类型定义

### 4.1 关系设计原则

```
关系设计原则:
├── 语义明确: 使用精确的谓词，避免泛化
├── 方向性: 明确关系的方向
├── 属性丰富: 关系携带上下文属性
├── 证据溯源: 关系带来源和置信度
└── 时间标注: 关系带时间戳
```

### 4.2 R&D领域关系

```turtle
# 化合物-靶点作用关系
:inhibits a owl:ObjectProperty ;
    rdfs:domain :Compound ;
    rdfs:range :Target ;
    rdfs:subPropertyOf :acts_on .

:activates a owl:ObjectProperty ;
    rdfs:domain :Compound ;
    rdfs:range :Target ;
    rdfs:subPropertyOf :acts_on .

:binds_to a owl:ObjectProperty ;
    rdfs:domain :Compound ;
    rdfs:range :Target .

# 关系属性
:has_activity_value a owl:DatatypeProperty ;
    rdfs:domain :Activity ;
    rdfs:range xsd:float .

:has_activity_unit a owl:DatatypeProperty ;
    rdfs:domain :Activity ;
    rdfs:range xsd:string .

:has_activity_type a owl:DatatypeProperty ;
    rdfs:domain :Activity ;
    rdfs:range xsd:string ;  # IC50, EC50, Kd, Ki

:measured_in_assay a owl:ObjectProperty ;
    rdfs:domain :Activity ;
    rdfs:range :Assay .

# 靶点-疾病关系
:associated_with a owl:ObjectProperty ;
    rdfs:domain :Target ;
    rdfs:range :Disease .

# 靶点-通路关系
:participates_in a owl:ObjectProperty ;
    rdfs:domain :Target ;
    rdfs:range :Pathway .

# 化合物-疾病关系
:treats a owl:ObjectProperty ;
    rdfs:domain :Compound ;
    rdfs:range :Disease .

:prevents a owl:ObjectProperty ;
    rdfs:domain :Compound ;
    rdfs:range :Disease .
```

### 4.3 临床领域关系

```turtle
# 受试者-试验关系 (四维复杂性)
:enrolled_in a owl:ObjectProperty ;
    rdfs:domain :Subject ;
    rdfs:range :ClinicalTrial .

    # 维度1: 参与状态
    :enrollment_date xsd:date ;
    :screening_status xsd:string ;
    :informed_consent_obtained xsd:boolean ;
    :randomization_arm xsd:string .

    # 维度2: 符合性与依从性
    :inclusion_criteria_met xsd:boolean ;
    :exclusion_criteria_not_met xsd:string ;
    :protocol_compliance xsd:string ;
    :medication_compliance xsd:float ;
    :visit_attendance xsd:float .

    # 维度3: 数据贡献
    :data_type xsd:string ;
    :visit_data_count xsd:integer ;
    :data_quality_score xsd:string .

    # 维度4: 权益与合规
    :has_informed_consent xsd:boolean ;
    :has_compensation xsd:string ;
    :covered_by_insurance xsd:boolean .

# 试验-中心关系
:conducted_at a owl:ObjectProperty ;
    rdfs:domain :ClinicalTrial ;
    rdfs:range :InvestigationalSite .

    :site_role xsd:string ;  # LeadSite, ParticipatingSite
    :planned_enrollment xsd:integer ;
    :actual_enrollment xsd:integer .

# 不良事件关系
:experienced a owl:ObjectProperty ;
    rdfs:domain :Subject ;
    rdfs:range :AdverseEvent .

    :event_severity xsd:string ;
    :causality xsd:string ;
    :action_taken xsd:string ;
    :reported_date xsd:date .

# 终点关系
:has_primary_objective a owl:ObjectProperty ;
    rdfs:domain :ClinicalTrial ;
    rdfs:range :Endpoint .

:has_secondary_objective a owl:ObjectProperty ;
    rdfs:domain :ClinicalTrial ;
    rdfs:range :Endpoint .
```

### 4.4 供应链领域关系

```turtle
# 供应关系
:supplies a owl:ObjectProperty ;
    rdfs:domain :Supplier ;
    rdfs:range :Material .

    :supply_percentage xsd:float ;
    :contract_type xsd:string ;
    :delivery_terms xsd:string ;
    :quality_rating xsd:float .

# 生产关系
:produces a owl:ObjectProperty ;
    rdfs:domain :Manufacturer ;
    rdfs:range :Product .

    :capacity_volume xsd:float ;
    :lead_time xsd:integer ;
    :quality_rating xsd:float .

# 短缺影响关系
:affects a owl:ObjectProperty ;
    rdfs:domain :ShortageEvent ;
    rdfs:range :Drug .

    :severity xsd:string ;
    :expected_duration xsd:string ;
    :affected_markets xsd:string .

:caused_by a owl:ObjectProperty ;
    rdfs:domain :ShortageEvent ;
    rdfs:range :Cause .

    :quality_issue xsd:string ;
    :capacity_constraint xsd:string ;
    :logistics_disruption xsd:string .

# 传播关系
:propagates_to a owl:ObjectProperty ;
    rdfs:domain :ShortageEvent ;
    rdfs:range :ShortageEvent .

    :propagation_path xsd:string ;
    :propagation_delay xsd:integer .
```

### 4.5 监管合规领域关系

```turtle
# 申报关系
:submits a owl:ObjectProperty ;
    rdfs:domain :Company ;
    rdfs:range :RegulatorySubmission .

    :submission_type xsd:string ;
    :submission_date xsd:date ;
    :submission_number xsd:string .

:submitted_to a owl:ObjectProperty ;
    rdfs:domain :RegulatorySubmission ;
    rdfs:range :RegulatoryAuthority .

    :jurisdiction xsd:string ;
    :review_process xsd:string .

# 审批决策关系
:makes_decision a owl:ObjectProperty ;
    rdfs:domain :RegulatoryAuthority ;
    rdfs:range :RegulatorySubmission .

    :decision_type xsd:string ;  # Approval, CRL, Refusal
    :decision_date xsd:date ;
    :approval_number xsd:string ;
    :conditions_attached xsd:string .

# 安全性事件关系
:experienced a owl:ObjectProperty ;
    rdfs:domain :Patient ;
    rdfs:range :SafetyEvent .

:associated_with a owl:ObjectProperty ;
    rdfs:domain :SafetyEvent ;
    rdfs:range :DrugProduct .

    :suspect_product xsd:string ;
    :indication xsd:string ;
    :dose xsd:string ;
    :duration xsd:string .

:assessed_by a owl:ObjectProperty ;
    rdfs:domain :SafetyEvent ;
    rdfs:range :CausalityAssessment .

    :causality_category xsd:string ;
    :confidence_score xsd:float .

# 检查关系
:inspected_by a owl:ObjectProperty ;
    rdfs:domain :Facility ;
    rdfs:range :Inspection .

:results_in a owl:ObjectProperty ;
    rdfs:domain :Inspection ;
    rdfs:range :InspectionFinding .

    :finding_category xsd:string ;  # Critical, Major, Minor
    :description xsd:string .

:requires_action a owl:ObjectProperty ;
    rdfs:domain :InspectionFinding ;
    rdfs:range :CAPA .
```

---

## 五、属性定义

### 5.1 属性分类体系

```
属性分类:
├── 核心标识属性 (Primary Identification)
│   ├── *_id (主标识符)
│   ├── *_name (名称)
│   └── *_code (编码)
│
├── 分类属性 (Classification)
│   ├── *_type (类型)
│   ├── *_stage (阶段)
│   ├── *_category (类别)
│   └── *_class (分类)
│
├── 描述属性 (Description)
│   ├── *_description (描述)
│   ├── *_definition (定义)
│   └── *_comment (注释)
│
├── 数值属性 (Numerical)
│   ├── *_value (数值)
│   ├── *_unit (单位)
│   ├── *_score (评分)
│   └── *_percentage (百分比)
│
├── 时间属性 (Temporal)
│   ├── *_date (日期)
│   ├── *_from (开始时间)
│   ├── *_until (结束时间)
│   └── *_timestamp (时间戳)
│
└── 质量属性 (Quality)
    ├── *_confidence (置信度)
    ├── *_completeness (完整性)
    ├── *_accuracy (准确性)
    └── *_reliability (可靠性)
```

### 5.2 核心数据类型

```turtle
# 基础数据类型
:xsd:string
:xsd:integer
:xsd:float
:xsd:boolean
:xsd:date
:xsd:dateTime
:xsd:decimal

# 扩展数据类型
:iri a rdfs:Datatype ;  # 国际资源标识符
:curie a rdfs:Datatype ; # 紧凑URI (如:GO:0008150)
:smiles a rdfs:Datatype ; # SMILES化学结构式
:inchikey a rdfs:Datatype ; # InChIKey
```

### 5.3 属性约束定义

```turtle
# 基数性约束
:has_activity_value a owl:DatatypeProperty ;
    rdfs:domain :Activity ;
    rdfs:range xsd:float ;
    owl:cardinality "1"^^xsd:nonNegativeInteger .  # 必填

:has_secondary_id a owl:DatatypeProperty ;
    rdfs:domain :Compound ;
    rdfs:range xsd:string ;
    owl:minCardinality "0"^^xsd:nonNegativeInteger ;  # 可选
    owl:maxCardinality "10"^^xsd:nonNegativeInteger . # 最多10个

# 值域约束
:development_stage a owl:ObjectProperty ;
    rdfs:domain :Compound ;
    rdfs:range [
        a owl:Class ;
        owl:oneOf (:Hit :Lead :OptimizedLead :PCC :ClinicalCandidate)
    ] .

# 正则表达式约束
:has_inchikey a owl:DatatypeProperty ;
    rdfs:domain :Compound ;
    rdfs:range xsd:string ;
    rdfs:comment "Must match InChIKey format: [A-Z]{14}-[A-Z]{10}-[A-Z]" .
```

---

## 六、跨域关联设计

### 6.1 跨领域关联策略

| 关联类型 | 关联强度 | 关联方式 | 应用场景 |
|---------|---------|---------|---------|
| **R&D ↔ 监管合规** | 🔴 深度关联 | 实体级关联 | 安全性信号、证据链、风险评估 |
| **R&D ↔ 供应链** | 🟡 部分关联 | 属性级关联 | API供应商、工艺转移 |
| **供应链 ↔ 监管合规** | 🟡 部分关联 | 属性级关联 | 供应商资质、短缺报告 |
| **R&D ↔ 临床** | 🔴 深度关联 | 实体级关联 | 靶点验证、生物标志物、安全性 |
| **临床 ↔ 监管合规** | 🔴 深度关联 | 实体级关联 | 申报证据、安全性数据 |
| **临床 ↔ 供应链** | 🟢 轻度关联 | 引用级关联 | 试验药品供应 |

### 6.2 跨领域桥接关系

```turtle
# R&D ↔ 监管合规
:Target :has_safety_signal ──▶ :SafetyEvent
    ├── :mechanism_based xsd:boolean
    ├── :off_target xsd:boolean
    └── :identified_in_preclinical xsd:boolean

:Compound :becomes ──▶ :RegulatoryDrugProduct
    ├── :formulation_change xsd:string
    ├── :manufacturing_change xsd:string
    └── :regulatory_pathway xsd:string

:ClinicalTrial :generates_evidence_for ──▶ :RegulatorySubmission
    ├── :evidence_type xsd:string
    ├── :study_reference xsd:string
    └── :weight_in_submission xsd:float

# R&D ↔ 供应链
:Compound(API) :sourced_from ──▶ :Supplier
    ├── :supply_percentage xsd:float
    ├── :contract_type xsd:string
    └── :quality_rating xsd:float

:PCC :requires_manufacturing ──▶ :Manufacturer
    ├── :capacity_requirement xsd:string
    ├── :technology_transfer xsd:boolean
    └── :timeline_months xsd:integer

# R&D ↔ 临床
:Target :validated_in ──▶ :ClinicalTrial
    ├── :validation_type xsd:string
    ├── :biomarker_used xsd:boolean
    └── :validation_status xsd:string

:Biomarker :used_as_endpoint ──▶ :Endpoint
    ├── :endpoint_type xsd:string
    ├── :correlation_with_survival xsd:string
    └── :regulatory_acceptance xsd:string

# 临床 ↔ 监管合规
:ClinicalTrial :supports_submission ──▶ :RegulatorySubmission
    ├── :study_phase xsd:string
    ├── :study_design xsd:string
    └── :key_evidence xsd:boolean

:Subject :experienced ──▶ :SafetyEvent
    ├── :trial_context xsd:string
    ├── :treatment_arm xsd:string
    └── :causality_assessment xsd:string

# 临床 ↔ 供应链
:ClinicalTrial :requires_supply ──▶ :Material
    ├── :drug_product xsd:string
    ├── :estimated_quantity xsd:float
    └── :supply_timeline xsd:string
```

### 6.3 跨领域查询示例

```cypher
// 查询1: R&D靶点 → 临床验证 → 监管安全性信号
MATCH (t:Target)-[:validated_in]->(ct:ClinicalTrial)
MATCH (t)-[:has_safety_signal]->(se:SafetyEvent)
WHERE t.target_id = "TARGET-123"
RETURN t.name, ct.protocol_id, se.event_type, se.causality

// 查询2: 化合物API → 供应商 → 监管资质
MATCH (c:Compound)-[:sourced_from]->(s:Supplier)
MATCH (s)-[:has_certification]->(cert:Certification)
MATCH (cert)-[:mutual_recognition_in]->(ra:RegulatoryAuthority)
WHERE c.development_stage = "PCC"
RETURN c.name, s.name, cert.certification_type, ra.name

// 查询3: 临床试验 → 证据支持 → 监管申报 → 审批决策
MATCH (ct:ClinicalTrial)-[:supports_submission]->(rs:RegulatorySubmission)
MATCH (ra:RegulatoryAuthority)-[:makes_decision]->(rs)
WHERE ct.protocol_id = "PROTOCOL-123"
RETURN ct.protocol_id, rs.submission_type, ra.name,
       rs.decision_type, rs.decision_date

// 查询4: 供应链短缺 → 受影响试验 → 监管报告
MATCH (se:ShortageEvent)-[:affects]->(m:Material)
MATCH (ct:ClinicalTrial)-[:requires_supply]->(m)
MATCH (ct)-[:affected_shortage_reported_to]->(ra:RegulatoryAuthority)
WHERE se.severity = "Critical"
RETURN se.event_id, m.material_name, ct.protocol_id, ra.name
```

---

## 七、标识符映射策略

### 7.1 标识符设计原则

```
标识符设计原则:
├── 持久化: 使用公认的标准标识符
├── 唯一性: 全局唯一标识
├── 可解析: 可通过标识符解析到实体
├── 多映射: 支持多种标识符系统
└── 可追溯: 标识符带来源和时间戳
```

### 7.2 跨领域标识符映射

```
┌─────────────────────────────────────────────────────────────┐
│                   标识符映射服务体系                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Compound (化合物)                                           │
│  ├── 主标识符: InChIKey (IUPAC标准)                          │
│  ├── 次要标识符:                                             │
│  │   ├── PubChem CID (美国)                                 │
│  │   ├── ChEMBL ID (欧洲)                                   │
│  │   ├── DrugBank ID (加拿大)                               │
│  │   └── ChemSpider ID (皇家化学会)                          │
│  ├── 监管标识符:                                             │
│  │   ├── UNII (FDA)                                         │
│  │   └── CAS Number (化学文摘社)                            │
│  └── 内部标识符: 公司内部化合物编号                            │
│                                                              │
│  Target (靶点/蛋白)                                          │
│  ├── 主标识符: UniProt Accession                             │
│  ├── 次要标识符:                                             │
│  │   ├── Entrez Gene ID (NCBI)                              │
│  │   ├── Ensembl ID (EBI)                                   │
│  │   └── RefSeq ID (NCBI)                                   │
│  ├── 基因符号: HGNC Symbol                                   │
│  └── 内部标识符: 公司内部靶点编号                              │
│                                                              │
│  Disease (疾病)                                              │
│  ├── 主标识符: MONDO ID (统一医学本体)                        │
│  ├── 次要标识符:                                             │
│  │   ├── DOID (疾病本体)                                     │
│  │   ├── ICD-10 (国际疾病分类)                               │
│  │   ├── SNOMED-CT (系统医学临床术语集)                       │
│  │   └── MedDRA (监管活动医学词典)                           │
│  └── 俗名映射                                                │
│                                                              │
│  ClinicalTrial (临床试验)                                    │
│  ├── 主标识符: NCT Number (ClinicalTrials.gov)               │
│  ├── 次要标识符:                                             │
│  │   ├── EudraCT (欧盟)                                     │
│  │   ├── ChiCTR (中国)                                      │
│  │   ├── JCTN (日本)                                        │
│  │   └── CTRI (印度)                                        │
│  └── 内部标识符: 公司内部试验编号                              │
│                                                              │
│  RegulatorySubmission (监管申报)                             │
│  ├── FDA: NDA/BLA Number (e.g., NDA 123456)                 │
│  ├── EMA: EudraCT Number (e.g., 2024-123456-12)             │
│  ├── NMPA: 申报编号 (e.g., CXSL2400XXX)                     │
│  └── PMDA: 申請編號 (e.g., 申請番号)                         │
│                                                              │
│  Company/Manufacturer (公司/制造商)                          │
│  ├── 主标识符: DUNS Number (邓白氏编码)                       │
│  ├── 次要标识符:                                             │
│  │   ├── FEI Code (FDA设施标识符)                            │
│  │   ├── GLN (全球位置号码)                                  │
│  │   └── VAT Number (增值税号)                              │
│  └── 内部标识符: 供应商主数据编号                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 标识符服务接口

```turtle
# 标识符映射实体
:IdentifierMapping a owl:Class ;
    :has_entity_type xsd:string ;
    :has_primary_identifier xsd:string ;
    :has_secondary_identifier xsd:string ;
    :has_identifier_system xsd:string ;
    :has_mapping_source xsd:string ;
    :has_mapping_confidence xsd:float ;
    :has_last_updated xsd:date .

# 标识符系统
:IdentifierSystem a owl:Class ;
    :has_system_name xsd:string ;
    :has_system_prefix xsd:string ;
    :has_system_url xsd:anyURI ;
    :has_resolution_service xsd:anyURI .
```

---

## 八、数据源集成

### 8.1 数据源优先级矩阵

| 领域 | 优先级1 | 优先级2 | 优先级3 | 优先级4 |
|-----|--------|--------|--------|--------|
| **R&D** | 本体/知识库 | 公共数据库 | 内部数据 | 文献/专利 |
| **临床** | 内部业务系统 | 公共注册库 | 医院数据源 | 试验文档 |
| **供应链** | 内部业务系统 | 公共/监管数据 | 行业数据 | 实时信息 |
| **监管** | 公共数据库 | 监管机构数据 | 内部系统 | 文献/病例 |

### 8.2 核心数据源清单

```
R&D数据源:
├── 本体/知识库:
│   ├── Gene Ontology (GO)
│   ├── Reactome (通路)
│   ├── KEGG (通路)
│   ├── ChEBI (化学实体)
│   └── BioAssay Ontology (BAO)
├── 公共数据库:
│   ├── ChEMBL (活性数据)
│   ├── PubChem (化合物)
│   ├── DrugBank (药物)
│   ├── UniProt (蛋白)
│   └── ClinVar (临床变异)
├── 内部数据:
│   └── 内部实验数据库
└── 文献/专利:
    └── PubMed, 专利数据库

临床数据源:
├── 内部业务系统:
│   ├── CTMS (临床试验管理系统)
│   ├── EDC (电子数据采集)
│   ├── eConsent (电子知情同意)
│   └── RTSM (随机化与试验供应管理)
├── 公共注册库:
│   ├── ClinicalTrials.gov
│   ├── ChiCTR (中国)
│   ├── EudraCT (欧盟)
│   └── JCTN (日本)
├── 医院数据源:
│   ├── EHR/EMR (电子健康记录)
│   ├── HIS (医院信息系统)
│   └── LIS (实验室信息系统)
└── 试验文档:
    └── ICF, CRF, Protocol

供应链数据源:
├── 内部业务系统:
│   ├── ERP (企业资源计划)
│   ├── SCM (供应链管理)
│   └── MES (制造执行系统)
├── 公共/监管数据:
│   ├── FDA Drug Shortages
│   ├── EUDRAF (欧盟)
│   └── NMPA短缺公告
├── 行业数据:
│   └── Pharma publications, Market reports
└── 实时信息:
    └── News feeds, Social media, Alerts

监管数据源:
├── 公共数据库:
│   ├── ClinicalTrials.gov
│   ├── Drugs@FDA
│   ├── EMA欧几里得数据库
│   └── FAERS (不良事件报告系统)
├── 监管机构数据:
│   ├── FDA AA database
│   ├── EudraCT
│   └── CDE药物临床试验登记平台
├── 内部系统:
│   ├── Argus (安全性数据库)
│   ├── Arisg (安全性数据库)
│   └── RIM (注册信息管理)
└── 文献/病例报告:
    └── PubMed, Case reports
```

### 8.3 数据质量框架

```turtle
# 数据质量模型
:DataQuality a owl:Class ;
    :has_completeness_score xsd:float ;
    :has_accuracy_score xsd:float ;
    :has_consistency_score xsd:float ;
    :has_timeliness_score xsd:float ;
    :has_overall_quality xsd:string ;
    :has_quality_issues xsd:string .

# 质量维度定义
:Completeness a owl:Class ;
    :has_missing_data_rate xsd:float ;
    :has_required_fields_filled xsd:float ;
    :has_optional_fields_filled xsd:float .

:Accuracy a owl:Class ;
    :has_validation_passed xsd:boolean ;
    :has_source_consistency xsd:float ;
    :has_error_rate xsd:float .

:Consistency a owl:Class ;
    :has_cross_field_consistency xsd:float ;
    :has_cross_record_consistency xsd:float ;
    :has_temporal_consistency xsd:float .

:Timeliness a owl:Class ;
    :has_data_latency xsd:string ;
    :has_update_frequency xsd:string ;
    :has_last_update_date xsd:date .
```

---

## 九、实施指南

### 9.1 分阶段实施路线图

#### Phase 1: 核心基础 (3个月)

```
优先级 P0:
├── R&D核心实体
│   ├── Compound多维分类
│   ├── Target多维分类
│   └── 核心关系 (inhibits, activates, associated_with)
│
├── 临床核心实体
│   ├── ClinicalTrial多维分类
│   ├── Subject基础建模
│   ├── InvestigationalSite
│   └── 四维Subject-Trial关系
│
├── 供应链核心实体
│   ├── 3级基础追溯模型
│   ├── Supplier基础评分
│   └── Material分类
│
├── 监管核心实体
│   ├── RegulatoryAuthority
│   ├── RegulatorySubmission基础分类
│   └── 基础RBAC权限控制
│
└── 跨域核心
    ├── 标识符映射服务
    └── 桥接关系定义
```

#### Phase 2: 增强功能 (3-6个月)

```
优先级 P1:
├── R&D增强
│   ├── 不确定性数据表示
│   ├── 阴性数据聚合存储
│   └── 状态机模型
│
├── 临床增强
│   ├── RWE数据整合接口
│   ├── HTA四层证据链
│   ├── PRO数据标准化
│   └── 四维数据质量框架
│
├── 供应链增强
│   ├── 动态追溯深度模型
│   ├── 短缺预测基础框架
│   └── 供应商风险分层
│
├── 监管增强
│   ├── 信号检测综合阈值
│   ├── 影响分析预筛选+图遍历
│   └── RWE场景权重
│
└── 跨域增强
    ├── R&D-监管深度关联
    └── R&D-临床深度关联
```

#### Phase 3: 高级功能 (6-12个月)

```
优先级 P2:
├── R&D高级
│   ├── 化合物版本控制
│   ├── 时态查询完整支持
│   └── 概率分布高级查询
│
├── 临床高级
│   ├── 适应性试验版本控制
│   ├── DHT数据分层整合
│   ├── 生物标志物分层模型
│   └── 跨境数据传输合规框架
│
├── 供应链高级
│   ├── 短缺预测ML模型
│   ├── 跨国法规三层模型
│   └── 供应链智能预警
│
├── 监管高级
│   ├── RWE数据整合平台
│   ├── 场景权重动态决策
│   └── 自动化影响分析
│
└── 跨域高级
    ├── 完整审计日志系统
    └── 跨域高级查询引擎
```

### 9.2 技术栈选型建议

```
图数据库选型:
├── 推荐: Neo4j
│   ├── 成熟稳定
│   ├── Cypher查询语言
│   ├── 丰富社区支持
│   └── 企业级功能
│
├── 备选: AWS Neptune
│   ├── 云原生
│   ├── 支持Gremlin/SPARQL
│   ├── 无需运维
│   └── 按需付费

本体语言:
├── RDF/Turtle: 标准格式，易于交换
├── OWL: 推理能力，复杂约束
└── SHACL: 数据验证规则

查询语言:
├── Cypher (Neo4j)
├── Gremlin (图遍历)
├── SPARQL (RDF查询)
└── GraphQL (API查询)

数据集成:
├── ETL工具: Apache NiFi, Talend
├── 虚拟化: Denodo, Dremio
└── API: REST, GraphQL
```

### 9.3 查询模式库

```cypher
// Q1: 靶点发现查询
// 给定疾病，找潜在靶点和化合物
MATCH (d:Disease {name: "Disease X"})-[:associated_with]->(t:Target)
MATCH (c:Compound)-[r:inhibits|activates]->(t)
WHERE c.development_stage IN ["PCC", "ClinicalCandidate"]
  AND r.activity_value < 100  # nM
RETURN t.name, t.druggability_stage,
       c.name, r.activity_type, r.activity_value
ORDER BY r.activity_value ASC

// Q2: 供应链追溯查询
// 给定药品，追溯所有原料供应商
MATCH (d:Drug)-[:contains]->(api:API)
MATCH (api)-[:sourced_from]->(s:Supplier)
WHERE d.name = "Drug X"
RETURN d.name, api.name, s.name, s.country,
       s.supply_percentage, s.quality_rating

// Q3: 安全性信号检测
// 分析产品安全性信号和趋势
MATCH (se:SafetyEvent)-[:associated_with]->(d:DrugProduct)
MATCH (se)-[:assessed_by]->(ca:CausalityAssessment)
WHERE d.name = "Drug X"
  AND ca.causality_category IN ["Related", "PossiblyRelated"]
WITH se.event_type as eventType, count(se) as eventCount
WHERE eventCount > 3
RETURN eventType, eventCount
ORDER BY eventCount DESC

// Q4: 临床试验进度监控
MATCH (ct:ClinicalTrial)-[:conducted_at]->(s:InvestigationalSite)
WHERE ct.protocol_id = "PROTOCOL-123"
RETURN ct.protocol_id, s.site_name,
       count{(s)<-[:enrolled_in]-()} as enrolled_count,
       s.quality_metrics,
       s.enrollment_percentage
ORDER BY enrolled_count DESC

// Q5: 跨域查询: R&D靶点 → 临床 → 监管
MATCH (t:Target)-[:validated_in]->(ct:ClinicalTrial)
MATCH (ct)-[:supports_submission]->(rs:RegulatorySubmission)
MATCH (ra:RegulatoryAuthority)-[:makes_decision]->(rs)
WHERE t.target_id = "TARGET-123"
RETURN t.name, ct.protocol_id, rs.submission_type,
       ra.name, rs.decision_type, rs.decision_date

// Q6: 时态查询: 化合物历史状态
MATCH (c:Compound)-[:has_version*]->(version:Compound)
WHERE c.compound_id = "COMPOUND-123"
  AND version.valid_from <= date("2024-12-31")
RETURN version.version_number, version.structure_smiles,
       version.salt_form, version.valid_from, version.valid_until
ORDER BY version.valid_from ASC
```

### 9.4 验证与测试计划

```
验证层次:
├── Schema验证
│   ├── 语法验证 (Turtle/OWL)
│   ├── 语义验证 (推理检查)
│   └── 约束验证 (SHACL)
│
├── 数据验证
│   ├── 标识符唯一性
│   ├── 关系完整性
│   └── 属性值域
│
└── 查询验证
    ├── 查询性能
    ├── 结果准确性
    └── 边界条件

测试场景:
├── 单元测试
│   ├── 实体创建
│   ├── 关系建立
│   └── 属性赋值
│
├── 集成测试
│   ├── 数据导入
│   ├── 跨域查询
│   └── 标识符映射
│
└── 性能测试
    ├── 查询响应时间
    ├── 图遍历效率
    └── 并发访问
```

---

## 附录A: 完整实体类清单

### A.1 R&D实体类 (20+)

```
核心实体:
├── Compound
├── Target
├── Assay
├── Pathway
├── Disease

状态实体:
├── CompoundState
├── StateTransitionRule
├── Milestone

分类实体:
├── StructureType
├── DevelopmentStage
├── TherapeuticArea
├── TargetFunction
├── DruggabilityStage
├── GeneFamily
├── AssayType

不确定性实体:
├── UncertaintyModel
├── ConfidenceMethodology

阴性数据实体:
├── AggregateResult
├── RepresentativeNegativeResult
├── ExternalDataset

版本控制实体:
├── CompoundVersion
├── TimeInterval
```

### A.2 临床实体类 (30+)

```
核心实体:
├── ClinicalTrial
├── Subject
├── InvestigationalSite
├── Endpoint
├── Investigator
├── AdverseEvent
├── ProtocolDesign

分类实体:
├── TrialPhase
├── TrialType
├── TrialDesign
├── TrialPurpose
├── SiteType
├── SiteTier
├── EndpointType
├── EnrollmentStatus

数据质量实体:
├── DataQuality
├── DataQualityRule
├── SiteQualityMetrics
├── TrialQualityMetrics

RWE/PRO实体:
├── RWESource
├── RWEComparator
├── HTAEvidenceChain
├── DHTDevice
├── DHTValidation
├── PROInstrument

适应性设计实体:
├── ProtocolVersion
├── AdaptiveDecisionRule
├── TrialTermination
├── TrialFailureLesson

隐私合规实体:
├── RegionalDataRegulation
├── DataDeIdentification
├── SubjectPrivacyPreference

资源管理实体:
├── SiteCapabilityProfile
├── TrialSupplyChain
├── CRAssignment

生物标志物实体:
├── Biomarker
├── BiomarkerTestResult
├── EnrichmentDesign
```

### A.3 供应链实体类 (20+)

```
核心实体:
├── Supplier
├── Manufacturer
├── Material
├── SupplyEvent

分类实体:
├── SupplierType
├── MaterialType
├── SupplyStage
├── ControlLevel
├── EventType

追溯实体:
├── TraceabilityConfig
├── TraceabilityPath

风险预测实体:
├── RiskIndicator
├── ShortagePrediction

合规实体:
├── Certification
├── ComplianceRecord

性能实体:
├── SupplierPerformance
├── RiskAssessment
```

### A.4 监管合规实体类 (20+)

```
核心实体:
├── RegulatoryAuthority
├── RegulatorySubmission
├── SafetyEvent
├── Inspection

分类实体:
├── SubmissionType
├── SubmissionStage
├── SubmissionStatus
├── AuthorityScope

决策实体:
├── Decision
├── DecisionCriteria
├── SynchronizationStrategy

信号检测实体:
├── SafetySignalType
├── SignalDetection
├── SafetyAlert

RWE实体:
├── RWEDataSource
├── UsageScenario
├── RWEEvidence

变更管理实体:
├── RegulatoryChange
├── ImpactAnalysis

检查实体:
├── InspectionFinding
├── CAPA

权限实体:
├── AccessRequest
├── RegulatoryRole
```

---

## 附录B: 关系类型清单

### B.1 R&D关系 (15+)

```
作用机制:
├── inhibits (抑制)
├── activates (激活)
├── binds_to (结合)
├── regulates (调节)
└── degrades (降解)

疾病关联:
├── associated_with (关联)
├── treats (治疗)
└── prevents (预防)

通路参与:
└── participates_in (参与)

实验关系:
├── measured_in_assay (在实验中测量)
└── has_activity_value (活性值)

状态转换:
├── transitions_to (转换到)
├── can_rollback_to (可回退到)
└── transition_rule (转换规则)

分类关系:
├── has_structure_type
├── has_development_stage
└── has_therapeutic_area

不确定性:
└── has_uncertainty (不确定性)

阴性数据:
├── tested_against (测试过)
├── has_aggregate (聚合)
└── has_external_data (外部数据)
```

### B.2 临床关系 (25+)

```
受试者-试验:
├── enrolled_in (入组)
├── transitions_to (状态转换)
├── withdraws_from (退出)
├── has_compliance_status (依从状态)
├── has_adherence (依从性)
├── has_protocol_deviation (方案偏离)
├── contributes_data_to (贡献数据)
├── has_informed_consent (知情同意)
├── has_compensation (补偿)
└── covered_by_insurance (保险覆盖)

试验-中心:
├── conducted_at (在...进行)
├── has_principal_investigator (主要研究者)
├── has_site_coordinator (中心协调员)
├── has_capabilities (能力)
└── has_performance_metrics (绩效指标)

试验关系:
├── designed_by (设计者)
├── has_primary_objective (主要目标)
├── has_secondary_objective (次要目标)
├── has_inclusion_criteria (入排标准)
├── has_exclusion_criteria (排除标准)
└── requires_monitoring_by (监察者)

安全性:
├── experienced (经历)
├── assessed_by (评估者)
├── requires_reporting (需要报告)
└── reported_via (通过...报告)

数据质量:
└── has_quality (质量)

RWE整合:
├── has_rwe_comparator (RWE对照)
└── includes_evidence (包含证据)

适应性设计:
├── has_version (有版本)
└── based_on_rule (基于规则)

生物标志物:
├── has_biomarker_status (生物标志物状态)
├── used_as_endpoint (用作终点)
└── targets_biomarker (靶向标志物)

跨境合规:
├── subject_to_regulation (受法规约束)
└── has_privacy_preference (隐私偏好)
```

### B.3 供应链关系 (20+)

```
基础关系:
├── supplies (供应)
├── produces (生产)
├── stores (存储)
└── transports (运输)

能力关系:
├── has_production_capability (生产能力)
├── has_certification (认证)
└── collaboration_mode (合作模式)

短缺事件:
├── affects (影响)
├── caused_by (由...导致)
├── impacts (冲击)
└── propagates_to (传播到)

追溯关系:
├── contains (包含)
├── sourced_from (来源)
├── provides_to (提供给)
├── manufactures_at (在...制造)
└── dynamic_trace_to (动态追溯)

风险关系:
├── has_risk_indicator (风险指标)
├── predicts_shortage (预测短缺)
└── has_regional_extension (地区扩展)

合规关系:
├── mutual_recognition_in (互认于)
└── compliance_status (合规状态)
```

### B.4 监管关系 (20+)

```
申报关系:
├── submits (提交)
├── submitted_to (提交给)
├── contains (包含)
└── includes_study (包含研究)

审批决策:
├── reviews (审评)
├── makes_decision (做决策)
├── requires (要求)
└── has_priority_score (优先级评分)

安全性事件:
├── experienced (经历)
├── associated_with (关联)
├── assessed_by (被评估)
├── reported_via (通过...报告)
└── requires_reporting (需要报告)

检查关系:
├── inspected_by (被...检查)
├── conducts (执行)
├── results_in (导致)
└── requires_action (需要行动)

RWE整合:
├── weighted_by_scenario (按场景加权)
└── applies_to (应用于)

变更影响:
├── affects (影响)
└── requires_compliance_action (需要合规行动)

权限关系:
├── has_role (有角色)
├── has_members (有成员)
├── accessible_by_role (可被角色访问)
├── accessible_in_project (可在项目中访问)
├── requires_access_request (需要访问请求)
└── logged_in (记录于)
```

### B.5 跨域桥接关系 (10+)

```
R&D ↔ 监管:
├── Target ──[:has_safety_signal]──▶ SafetyEvent
├── Compound ──[:becomes]──▶ RegulatoryDrugProduct
└── ClinicalTrial ──[:generates_evidence]──▶ RegulatorySubmission

R&D ↔ 供应链:
├── Compound ──[:sourced_from]──▶ Supplier
└── PCC ──[:requires_manufacturing]──▶ Manufacturer

R&D ↔ 临床:
├── Target ──[:validated_in]──▶ ClinicalTrial
├── Biomarker ──[:used_as_endpoint]──▶ Endpoint
└── Compound ──[:has_safety_profile]──▶ AdverseEvent

临床 ↔ 监管:
├── ClinicalTrial ──[:supports_submission]──▶ RegulatorySubmission
└── Subject ──[:experienced]──▶ SafetyEvent

临床 ↔ 供应链:
└── ClinicalTrial ──[:requires_supply]──▶ Material

供应链 ↔ 监管:
├── Manufacturer ──[:has_certification]──▶ Certification
└── ShortageEvent ──[:reported_to]──▶ RegulatoryAuthority
```

---

## 附录C: 查询示例库

### C.1 靶点发现与验证

```cypher
// 查找给定疾病的潜在靶点和化合物
MATCH (d:Disease {name: "Non-Small Cell Lung Cancer"})-[:associated_with]->(t:Target)
MATCH (c:Compound)-[r:inhibits|activates]->(t)
WHERE t.druggability_stage IN ["ValidatedTarget", "ClinicalStageTarget"]
  AND c.development_stage IN ["PCC", "ClinicalCandidate"]
  AND r.activity_value < 50
RETURN t.name, t.target_function, t.druggability_stage,
       c.name, r.activity_type, r.activity_value, r.measured_in_assay
ORDER BY r.activity_value ASC
LIMIT 20

// 查询靶点的临床验证状态
MATCH (t:Target)-[:validated_in]->(ct:ClinicalTrial)
MATCH (ct)-[:has_phase]->(phase:TrialPhase)
WHERE t.target_id = "EGFR"
RETURN t.name, ct.protocol_id, ct.trial_phase,
       ct.start_date, ct.status
ORDER BY ct.start_date DESC
```

### C.2 供应链风险分析

```cypher
// 供应链风险评估
MATCH (d:Drug)-[:contains]->(api:API)
MATCH (api)-[:sourced_from]->(s:Supplier)
MATCH (s)-[:has_risk_indicator]->(ri:RiskIndicator)
WHERE d.name = "Critical Drug X"
  AND s.supply_percentage > 30
RETURN d.name, api.name, s.name, s.country,
       s.supply_percentage, ri.risk_level, ri.risk_trend,
       ri.indicator_type, ri.value, ri.threshold
ORDER BY s.supply_percentage DESC, ri.risk_level DESC

// 短缺影响分析
MATCH (se:ShortageEvent {severity: "Critical"})-[:affects]->(d:Drug)
MATCH (d)-[:prescribed_for]->(disease:Disease)
MATCH (se)-[:propagates_to*1..3]->(downstream:ShortageEvent)
RETURN se.event_id, d.name, disease.name,
       se.start_date, se.expected_resolution_date,
       count(DISTINCT downstream) as downstream_impacts
ORDER BY se.start_date DESC
```

### C.3 监管合规分析

```cypher
// 全球注册状态追踪
MATCH (d:DrugProduct {name: "Drug Y"})<-[:contains]-(s:RegulatorySubmission)
MATCH (s)-[:submitted_to]->(ra:RegulatoryAuthority)
OPTIONAL MATCH (ra)-[:makes_decision]->(dec:Decision)
WHERE dec.decision_date >= date("2023-01-01")
RETURN ra.name, ra.authority_region,
       s.submission_type, s.submission_date,
       dec.decision_type, dec.decision_date, dec.approval_number
ORDER BY s.submission_date DESC

// 安全性信号检测
MATCH (se:SafetyEvent)-[:associated_with]->(d:DrugProduct)
MATCH (se)-[:assessed_by]->(ca:CausalityAssessment)
MATCH (d)-[:approved_in]->(ra:RegulatoryAuthority)
WHERE d.name = "Drug Z"
  AND se.event_date >= date("2023-01-01")
  AND ca.causality_category IN ["Related", "PossiblyRelated"]
WITH se.event_type as eventType, count(se) as eventCount, ra.name
WHERE eventCount > 2
RETURN eventType, eventCount, ra.name
ORDER BY eventCount DESC
```

### C.4 临床试验分析

```cypher
// 多中心试验进度分析
MATCH (ct:ClinicalTrial {protocol_id: "PROTOCOL-123"})-[:conducted_at]->(s:InvestigationalSite)
MATCH (s)-[:has_performance_metrics]->(spm:SitePerformanceMetrics)
RETURN s.site_name, s.site_tier, s.country,
       spm.enrollment_rate, spm.actual_enrollment, spm.target_enrollment,
       spm.protocol_compliance_score, spm.data_quality_score
ORDER BY spm.actual_enrollment DESC

// 受试者依从性分析
MATCH (ct:ClinicalTrial {protocol_id: "PROTOCOL-123"})<-[:enrolled_in]-(sub:Subject)
MATCH (sub)-[:has_adherence]->(adh:AdherenceLevel)
MATCH (sub)-[:has_protocol_deviation]->(pd:ProtocolDeviation)
RETURN sub.subject_id, adh.medication_compliance, adh.visit_attendance,
       adh.overall_adherence, count(pd) as deviation_count
ORDER BY adh.medication_compliance ASC, deviation_count DESC
```

### C.5 跨领域综合查询

```cypher
// R&D靶点 → 临床验证 → 监管安全性信号
MATCH (t:Target)-[:validated_in]->(ct:ClinicalTrial)
MATCH (t)-[:has_safety_signal]->(se:SafetyEvent)
MATCH (se)-[:assessed_by]->(ca:CausalityAssessment)
MATCH (ct)-[:supports_submission]->(rs:RegulatorySubmission)
MATCH (rs)-[:submitted_to]->(ra:RegulatoryAuthority)
WHERE t.target_id = "TARGET-123"
  AND ca.causality_category IN ["Related", "PossiblyRelated"]
RETURN t.name, ct.protocol_id, ct.trial_phase,
       se.event_type, se.event_date,
       rs.submission_type, ra.name
ORDER BY se.event_date DESC

// 化合物API → 供应商 → 监管资质 → 短缺风险
MATCH (c:Compound)-[:sourced_from]->(s:Supplier)
MATCH (s)-[:has_certification]->(cert:Certification)
MATCH (s)-[:has_risk_indicator]->(ri:RiskIndicator)
OPTIONAL MATCH (s)-[:involved_in_shortage]->(se:ShortageEvent)
WHERE c.development_stage IN ["PCC", "ClinicalCandidate"]
  AND c.material_type = "API"
RETURN c.name, s.name, s.country,
       cert.certification_type, cert.status,
       ri.risk_level, ri.value,
       se.event_id, se.severity
ORDER BY ri.risk_level DESC, c.name
```

---

**文档版本**: v1.0
**最后更新**: 2025-02-06
**下次更新**: 根据第三轮访谈结果更新

---

*本文档基于四领域两轮访谈（R&D、供应链、监管合规、临床试验）共计27个问题、42个关键决策的分析结果编制而成。*
