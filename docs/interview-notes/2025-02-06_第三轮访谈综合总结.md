# 制药行业知识图谱Interview - 第三轮综合总结

**访谈日期**: 2025-02-06
**访谈类型**: 第三轮（针对待最终确认问题）
**访谈状态**: 已完成

---

## 第三轮访谈概览

| 领域 | 待确认问题数 | 关键决策数 | 复杂度评估 |
|-----|-------------|-----------|-----------|
| **跨领域共性** | 3 | 3 | 中 |
| **R&D** | 3 | 3 | 中 |
| **供应链** | 3 | 3 | 中 |
| **监管合规** | 3 | 3 | 中 |
| **临床试验** | 5 | 5 | 中 |

---

## 一、跨领域共性问题决策

### 1.1 图数据库选型

**决策**: **Neo4j（成熟稳定）**

| 选择维度 | 说明 |
|---------|------|
| **成熟度** | 市场占有率最高，社区支持丰富 |
| **查询语言** | Cypher查询语言，SQL-like易于学习 |
| **企业功能** | 完整的企业级功能（监控、备份、安全） |
| **部署方式** | 支持Docker容器部署，适合autodl云服务器 |
| **成本考虑** | 社区版免费，企业版按需购买 |

**技术规格建议**:
```
推荐配置:
├── 版本: Neo4j 5.x LTS
├── 部署: Docker容器  【切记不能用Docker部署，因为我现在用的 autodl 云服务 （ https://www.autodl.com/docs/ ），因为这个环境本身就是一个 docker 容器环境，不能在嵌套一个 docker 了。】
├── 内存: 16GB+ (生产环境32GB+)
├── 存储: SSD 2TB+
├── CPU: 8核+ (生产环境16核+)
└── 集群: 单机起步，后期可扩展为集群
```

### 1.2 本体语言选择

**决策**: **组合使用（Turtle + OWL）**

| 场景 | 选择 | 理由 |
|-----|------|------|
| **数据存储/交换** | RDF/Turtle | W3C标准，易于理解和交换 |
| **规则定义** | OWL | 强大的推理能力，支持复杂约束 |
| **数据验证** | SHACL | 图数据约束验证语言 |

**实施策略**:
```turtle
# 数据存储: 使用Turtle
@prefix pharma: <http://pharma-kg.org/ontology/> .
pharma:Compound a pharma:ChemicalEntity ;
    pharma:has_inchikey "XXXXXXXXXXXXX" .

# 规则定义: 使用OWL
pharma:Compound rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty pharma:inhibits ;
    owl:someValuesFrom pharma:Target
] .

# 数据验证: 使用SHACL
pharma:CompoundShape a sh:NodeShape ;
    sh:property [
        sh:path pharma:has_inchikey ;
        sh:datatype xsd:string ;
        sh:minLength 25 ;
        sh:maxLength 27
    ] .
```

### 1.3 部署方式

**决策**: **自有云服务器（autodl）**

| 部署模式 | 说明 |
|---------|------|
| **云服务器** | 使用autodl租用的云服务器 |
| **容器化部署** | Docker + Docker Compose |
| **数据安全** | 数据存储在自有服务器，完全可控 |
| **扩展性** | 后期可根据需求垂直/水平扩展 |

**架构设计**:
```
┌─────────────────────────────────────────────────┐
│                  autodl云服务器                   │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │           Docker容器层                      │  │
│  │  ┌─────────────┐  ┌─────────────┐         │  │
│  │  │   Neo4j     │  │  API服务    │         │  │
│  │  │   容器      │  │   容器      │         │  │
│  │  └─────────────┘  └─────────────┘         │  │
│  │  ┌─────────────┐  ┌─────────────┐         │  │
│  │  │  前端界面    │  │  ETL服务    │         │  │
│  │  │   容器      │  │   容器      │         │  │
│  │  └─────────────┘  └─────────────┘         │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │           持久化存储层                      │  │
│  │  ┌─────────────┐  ┌─────────────┐         │  │
│  │  │  数据卷     │  │  备份卷     │         │  │
│  │  └─────────────┘  └─────────────┘         │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 二、R&D领域决策

### 2.1 活性数据不确定性表示

**决策**: **分场景决定**

| 场景类别 | 表示方式 | 理由 |
|---------|---------|------|
| **关键实验** | 概率分布存储 | 临床前毒理、安全药理等关键决策需要完整不确定性信息 |
| **常规筛选** | 简单表示 | 高通量筛选用误差范围、置信区间即可 |
| **专家判断** | 置信度等级 | 使用High/Medium/Low等级表示 |

**Schema实现**:
```turtle
# 关键实验: 存储完整概率分布
:CriticalAssay
    :has_activity_value "10.5"^^xsd:float ;
    :has_distribution_type "Normal"^^xsd:string ;
    :has_distribution_mean "10.5"^^xsd:float ;
    :has_distribution_std "2.3"^^xsd:float ;
    :has_distribution_confidence "0.95"^^xsd:float .

# 常规筛选: 简单表示
:HTSAssay
    :has_activity_value "10.5"^^xsd:float ;
    :has_std_error "2.3"^^xsd:float ;
    :has_ci_90_lower "8.2"^^xsd:float ;
    :has_ci_90_upper "12.8"^^xsd:float .

# 专家判断: 置信度等级
:ExpertAssessment
    :has_evidence_level "Possible"^^xsd:string ;
    :expert_confidence "Medium"^^xsd:string ;
    :assessment_method "ExpertConsensus"^^xsd:string .
```

### 2.2 阴性数据外部链接性能保证

**决策**: **预建立索引**

| 策略 | 说明 |
|-----|------|
| **索引策略** | 在外部数据集上预先建立B+树或Hash索引 |
| **元数据存储** | 在KG中存储外部数据的元数据和统计信息 |
| **查询路由** | 查询时先访问元数据，确定是否需要访问外部数据 |
| **性能监控** | 监控外部查询响应时间，优化热点数据 |

**Schema设计**:
```turtle
:ExternalDataset
    :external_location "s3://bucket/path/to/data"^^xsd:string ;
    :summary_statistics {
        "total_count": 50000,
        "active_count": 150,
        "hit_rate": 0.003
    } ;
    :indexed_by :BTreeIndex ;
    :index_fields ["compound_id", "target_id", "activity_type"] ;
    :query_api "https://api.example.com/query"^^xsd:anyURI ;
    :estimated_query_time "100-500ms"^^xsd:string .

:QueryPerformance
    :external_query_cache_enabled :true ;
    :cache_ttl "3600"^^xsd:integer ;  # 1小时
    :cache_hit_rate "0.75"^^xsd:float .
```

### 2.3 化合物版本控制

**决策**: **需要Git-like的分支功能**

| 功能需求 | 说明 |
|---------|------|
| **并行分支** | 支持创建特性分支、实验分支，支持并行开发 |
| **分支合并** | 支持分支合并，冲突检测和解决 |
| **版本历史** | 完整的版本历史记录，可追溯任何历史版本 |
| **标签管理** | 支持为重要版本打标签（如v1.0-release） |

**Schema设计**:
```turtle
:CompoundVersion
    :version_number "1.2.3"^^xsd:string ;
    :branch_name "feature-optimization"^^xsd:string ;
    :parent_version "1.2.2"^^xsd:string ;
    :commit_message "Improved metabolic stability"^^xsd:string ;
    :committed_by "User123"^^xsd:string ;
    :committed_at "2024-01-15T10:30:00"^^xsd:dateTime .

:VersionBranch
    :branch_name "main"^^xsd:string ;
    :branch_type "main"^^xsd:string ;  # main, feature, release, hotfix
    :created_at "2024-01-01T00:00:00"^^xsd:dateTime ;
    :created_by "User456"^^xsd:string ;
    :is_merged :true ;
    :merged_into "main"^^xsd:string ;
    :merged_at "2024-02-01T00:00:00"^^xsd:dateTime .

# 分支合并
:MergeCommit
    :merge_from "feature-branch"^^xsd:string ;
    :merge_into "main"^^xsd:string ;
    :merge_strategy "three-way"^^xsd:string ;
    :conflict_resolved :true ;
    :merge_commit_id "abc123"^^xsd:string .
```

---

## 三、供应链领域决策

### 3.1 ML模型训练数据来源

**决策**: **混合数据源（内部为主+外部为辅）**

| 数据源 | 权重 | 用途 |
|-------|------|------|
| **内部历史数据** | 70% | 公司特定的短缺、供应、库存数据 |
| **外部行业数据** | 30% | FDA短缺公告、行业报告等公开数据 |
| **迁移学习** | 结合 | 内部数据预训练，外部数据微调 |

**数据源清单**:
```
内部数据源:
├── 历史短缺记录 (5年)
├── 供应商交付绩效
├── 库存周转数据
├── 生产计划数据
└── 质量事件记录

外部数据源:
├── FDA Drug Shortages API
├── ASHP短缺公告
├── EUDRAF短缺信息
├── 行业协会报告
└── 新闻与社交媒体
```

### 3.2 跨国法规时间差处理

**决策**: **地区独立管理**

| 策略 | 说明 |
|-----|------|
| **地区独立** | 各地区独立管理，按当地法规生效时间执行 |
| **法规映射** | 建立法规映射表，追踪各地区法规差异 |
| **本地化团队** | 各地区配备本地化团队，处理当地法规事务 |

**Schema设计**:
```turtle
:RegionalRegulation
    :region "EuropeanUnion"^^xsd:string ;
    :regulation_id "EU-GMP-2024"^^xsd:string ;
    :effective_date "2024-06-01"^^xsd:date ;
    :transition_period "6 months"^^xsd:string ;
    :local_requirements xsd:string ;
    :mutual_recognition_with :RegulatoryAuthority .

:RegulatoryComplianceStatus
    :region "China"^^xsd:string ;
    :compliant_as_of "2024-05-01"^^xsd:date ;
    :non_compliant_in "UnitedStates"^^xsd:string ;
    :reason "Different GLP requirements"^^xsd:string .
```

### 3.3 敏感信息权限控制

**决策**: **最小权限原则**

| 原则 | 说明 |
|-----|------|
| **按需授权** | 严格按业务需要授权，不授予不必要的权限 |
| **审批流程** | 敏感信息访问需要审批，记录访问原因和期限 |
| **审计日志** | 完整记录所有敏感信息访问，定期审计 |
| **数据脱敏** | 非必要情况下，优先使用脱敏数据 |

**Schema设计**:
```turtle
:SensitiveData
    :data_sensitivity_level "High"^^xsd:string ;
    :requires_approval :true ;
    :approval_workflow :AccessApprovalWorkflow ;
    :default_access_denied :true .

:AccessRequest
    :requester "User123"^^xsd:string ;
    :requested_data "Supplier_Pricing"^^xsd:string ;
    :business_justification "Vendor evaluation"^^xsd:string ;
    :access_duration "7 days"^^xsd:string ;
    :approval_status "Pending"^^xsd:string ;
    :approved_by "Manager456"^^xsd:string ;
    :access_granted :false .

:DataAccessLog
    :access_time "2024-01-15T10:30:00"^^xsd:dateTime ;
    :user "User123"^^xsd:string ;
    :data_accessed "Supplier_Pricing"^^xsd:string ;
    :access_purpose "Vendor evaluation"^^xsd:string ;
    :approval_reference "REQ-001"^^xsd:string .
```

---

## 四、监管合规领域决策

### 4.1 假阳性过载避免

**决策**: **多维度阈值动态调整**

| 维度 | 阈值调整因子 | 示例 |
|-----|------------|------|
| **产品风险** | 高风险产品 → 更低阈值 | 新分子实体 vs 仿制药 |
| **监管状态** | 审评中 → 更低阈值 | NDA审评中 vs 已上市 |
| **历史表现** | 不良事件多 → 更高阈值 | 已知安全性问题 vs 安全记录良好 |
| **报告质量** | 高质量报告 → 更低阈值 | 临床试验报告 vs 自发报告 |

**Schema设计**:
```turtle
:SafetySignalDetection
    :product_risk_level "High"^^xsd:string ;
    :regulatory_status "UnderReview"^^xsd:string ;
    :historical_performance "Poor"^^xsd:string ;
    :report_quality_score "0.9"^^xsd:float ;

    :detection_threshold {
        "base_threshold": 3,
        "risk_factor": 0.5,  # 高风险降低阈值
        "status_factor": 0.7,  # 审评中降低阈值
        "history_factor": 1.5,  # 历史差提高阈值
        "quality_factor": 0.8,  # 高质量降低阈值
        "final_threshold": 0.63  # 综合计算
    } .
```

### 4.2 RWE数据隐私保护

**决策**: **混合方案（去标识化+联邦学习）**

| 技术 | 应用场景 | 说明 |
|-----|---------|------|
| **数据去标识化** | 数据源头 | 移除个人身份信息（姓名、地址等） |
| **联邦学习** | 模型训练 | 在不传输原始数据的情况下进行模型训练 |
| **差分隐私** | 结果发布 | 添加噪声保护个体隐私 |
| **可信执行环境** | 敏感计算 | 在隔离环境中处理敏感数据 |

**Schema设计**:
```turtle
:RWEDataDeIdentification
    :method_type ["Pseudonymization", "KAnonymity"]^^xsd:string ;
    :removed_fields ["Name", "Address", "SSN"]^^xsd:string ;
    :kept_fields ["AgeGroup", "Region", "Gender"]^^xsd:string ;
    :re_identification_risk "Low"^^xsd:string ;
    :privacy_budget "0.1"^^xsd:float .  # 差分隐私预算

:FederatedLearningSetup
    :model_type "LogisticRegression"^^xsd:string ;
    :data_stays_local :true ;
    :only_gradients_shared :true ;
    :aggregation_server "secure-aggregation.com"^^xsd:anyURI ;
    :privacy_preserving "DifferentialPrivacy"^^xsd:string .
```

### 4.3 法规变更间接影响量化

**决策**: **混合方法（图传播+专家评估）**

| 步骤 | 方法 | 输出 |
|-----|------|------|
| **第1步** | 图传播算法 | 基础影响评分（0-100） |
| **第2步** | 专家评估调整 | 调整后评分，考虑复杂因素 |
| **第3步** | 综合分析 | 最终影响评级（低/中/高） |

**算法设计**:
```cypher
// 图传播算法基础
MATCH (rc:RegulatoryChange)-[:affects]->(direct:Entity)
WITH rc, direct, 100 as impact_score

// 1度传播
MATCH (direct)-[:related_to*1..2]->(indirect:Entity)
WHERE NOT (rc)-[:affects]->(indirect)
WITH direct, indirect, impact_score * 0.5 as decayed_score

// 专家调整因子
SET indirect.impact_score = decayed_score * expert_adjustment_factor

// 结果聚合
RETURN indirect.entity_type, indirect.impact_score
```

---

## 五、临床领域决策

### 5.1 DHT设备验证与质量平衡

**决策**: **分层验证**

| 设备风险等级 | 验证要求 | 验证内容 |
|-------------|---------|---------|
| **高风险** | 完整验证 | 分析验证+临床验证+性能验证 |
| **中风险** | 标准验证 | 分析验证+基本性能验证 |
| **低风险** | 简化验证 | 厂商认证+文献支持 |

**风险等级判定**:
```
高风险场景:
├── 关键临床终点测量
├── 用药剂量调整依据
└── 安全性监测

中风险场景:
├── 辅助终点测量
├── 生活质量评估
└── 依从性监测

低风险场景:
├── 活动量监测
├── 睡眠质量追踪
└── 基础生命体征
```

### 5.2 适应性试验方案变更处理

**决策**: **综合方案（1+2+3）**

| 变更类型 | 处理方式 | 说明 |
|---------|---------|------|
| **重大变更** | 重新知情同意 | 影响风险-受益比的变更需要重新同意 |
| **轻微变更** | 通知+可选退出 | 不影响核心权益的变更只需通知 |
| **持续沟通** | 透明化管理 | 及时与受试者沟通变更内容和原因 |

**变更分类标准**:
```turtle
:ProtocolChange
    :change_id "ADAPT-001"^^xsd:string ;
    :change_type "DroppedArmC"^^xsd:string ;
    :change_severity "Major"^^xsd:string ;

    # 变更影响评估
    :affects_risk_benefit :true ;
    :affects_investigational_product :false ;
    :affects_procedures :true ;

    # 处理方式
    :requires_re_consent :true ;
    :requires_notification :true ;
    :allows_opt_out :true ;

    # 受试者沟通
    :communication_method "InPerson + Written"^^xsd:string ;
    :communication_timeline "At least 2 weeks before implementation"^^xsd:string .
```

### 5.3 伴随诊断供应链管理

**决策**: **混合方案（中心为主+本地为备）**

| 策略 | 说明 |
|-----|------|
| **中心实验室** | 主要检测场所，统一质量控制 |
| **本地实验室** | 备用检测场所，作为中心实验室的补充 |
| **检测网络** | 建立多个认证实验室网络，分散风险 |

**供应链设计**:
```turtle
:CompanionDiagnosticSupply
    :primary_lab :CentralLab ;
    :backup_labs [:LocalLab1, :LocalLab2] ;
    :lab_network :CDxLabNetwork ;

    :quality_control "Standardized"^^xsd:string ;
    :sample_shipping "ColdChain"^^xsd:string ;
    :turnaround_time "7-10 days"^^xsd:string ;
    :redundancy_level "High"^^xsd:string .

:Lab
    :lab_id "LAB-001"^^xsd:string ;
    :lab_type "Central"^^xsd:string ;
    :certification ["CLIA", "CAP", "ISO15189"]^^xsd:string ;
    :capacity "1000 samples/month"^^xsd:string ;
    :geographic_coverage "Global"^^xsd:string .
```

### 5.4 跨境数据传输平衡

**决策**: **分区处理（敏感本地+非敏感可跨境）**

| 数据类别 | 处理方式 | 示例 |
|---------|---------|------|
| **敏感数据** | 本地处理，只传输结果 | 基因组数据、详细病历 |
| **去标识化数据** | 可跨境传输 | 聚合统计数据 |
| **公开数据** | 可跨境传输 | 已发表研究结果 |

**分区策略**:
```turtle
:DataPartition
    :data_category "GenomicData"^^xsd:string ;
    :sensitivity_level "High"^^xsd:string ;
    :storage_location "Local"^^xsd:string ;
    :cross_border_allowed :false ;
    :can_transfer_result :true ;
    :result_aggregation "SummaryStatistics"^^xsd:string .

:DataPartition
    :data_category "Demographics"^^xsd:string ;
    :sensitivity_level "Medium"^^xsd:string ;
    :storage_location "Local"^^xsd:string ;
    :cross_border_allowed :true ;
    :de_identification_required :true ;
    :transfer_method "API"^^xsd:string .
```

### 5.5 受试者招募AI匹配

**决策**: **精确优先（不漏掉合适的受试者）**

| 策略 | 说明 |
|-----|------|
| **召回保证** | 使用较低的阈值，宁可多推荐 |
| **人工筛选** | 推荐的候选人需要人工二次筛选确认 |
| **反馈学习** | 根据人工筛选结果持续优化模型 |

**匹配算法**:
```turtle
:SubjectMatchingAlgorithm
    :strategy "PrecisionPriority"^^xsd:string ;

    :threshold_config {
        "primary_threshold": 0.85,  # 高阈值
        "secondary_threshold": 0.70,  # 中阈值
        "include_marginal": true,    # 包含边缘候选
        "human_review_required": true
    } .

:CandidateRecommendation
    :subject_id "SUB-001"^^xsd:string ;
    :trial_id "NCT-12345"^^xsd:string ;
    :matching_score "0.78"^^xsd:float ;
    :matching_category "Marginal"^^xsd:string ;
    :human_review_status "Pending"^^xsd:string ;
    :review_outcome "Included"^^xsd:string .
```

---

## 六、实施影响分析

### 6.1 Schema设计调整

基于第三轮访谈决策，需要对Schema进行以下调整：

| 调整项 | 原设计 | 新设计 | 影响 |
|-------|-------|-------|------|
| **图数据库** | 未确定 | Neo4j 5.x | 技术栈明确 |
| **本体语言** | 未确定 | Turtle + OWL + SHACL | 分层明确 |
| **不确定性表示** | 单一方式 | 分场景决定 | 更灵活 |
| **外部数据** | 未确定 | 预索引 + 缓存 | 性能优化 |
| **版本控制** | 简单历史 | Git-like分支 | 功能增强 |
| **ML训练** | 未确定 | 混合数据源 | 数据源明确 |
| **权限控制** | 基础RBAC | 最小权限+审批 | 安全增强 |
| **假阳性** | 未确定 | 多维度阈值 | 算法优化 |
| **DHT验证** | 未确定 | 分层验证 | 成本优化 |

### 6.2 实施优先级调整

| 优先级 | 原计划 | 调整后 | 原因 |
|-------|-------|-------|------|
| P0 | 基础实体 | 基础实体+不确定性 | 不确定性是分场景，需要提前支持 |
| P0 | 基础关系 | 基础关系+版本控制 | Git-like分支需要基础架构支持 |
| P1 | RWE整合 | RWE整合+联邦学习 | 混合方案需要更复杂架构 |
| P1 | 信号检测 | 信号检测+多维度阈值 | 多维度阈值需要算法优化 |
| P2 | 版本控制 | (已升级到P0/P1) | 用户明确需要 |

### 6.3 新增功能需求

基于第三轮访谈，新增以下功能需求：

```
新增功能清单:
├── 技术架构
│   ├── Neo4j容器化部署方案
│   ├── Turtle/OWL/SHACL分层架构
│   └── 混合数据源集成框架
│
├── R&D领域
│   ├── 分场景不确定性表示引擎
│   ├── 外部数据索引服务
│   └── Git-like版本控制系统
│
├── 供应链领域
│   ├── 混合数据源ML训练管道
│   ├── 地区独立法规管理系统
│   └── 最小权限审批工作流
│
├── 监管合规领域
│   ├── 多维度阈值动态调整引擎
│   ├── 联邦学习框架集成
│   └── 图传播+专家评估混合算法
│
└── 临床领域
    ├── DHT分层验证系统
    ├── 综合方案变更管理系统
    ├── 中心+本地混合检测网络
    ├── 数据分区跨境传输管理
    └── 精确优先AI匹配系统
```

---

## 七、待实施事项更新

### 7.1 立即行动（Phase 1）

- [x] 三轮访谈全部完成
- [x] 技术栈选型确认（Neo4j + Turtle/OWL/SHACL）
- [ ] 部署方案设计（autodl云服务器 + Docker）
- [ ] 数据源清单确认（混合数据源）
- [ ] 分场景不确定性模型设计
- [ ] 版本控制架构设计
- [ ] 权限控制流程设计

### 7.2 短期计划（Phase 2）

- [ ] Neo4j环境搭建（autodl服务器）
- [ ] Turtle/OWL/SHACL分层实现
- [ ] 外部数据索引服务开发
- [ ] Git-like版本控制原型
- [ ] 多维度阈值算法实现
- [ ] 联邦学习技术预研

### 7.3 中期计划（Phase 3）

- [ ] 混合数据源ML管道
- [ ] DHT分层验证系统
- [ ] 适应性试验综合管理
- [ ] 数据分区跨境传输
- [ ] 完整审计日志系统

---

## 八、文件清单更新

```
docs/interview-notes/
├── 2025-02-04_第一轮访谈综合总结.md
├── 2025-02-04_第二轮访谈综合总结.md
├── 2025-02-06_第三轮访谈综合总结.md (本文件)
├── rd-domain/
│   ├── 2025-02-04_第一轮访谈纪要.md
│   └── 2025-02-04_第二轮访谈纪要.md
├── clinical-domain/
│   ├── 2025-02-04_第一轮访谈纪要.md
│   └── 2025-02-04_第二轮访谈纪要.md
├── supply-chain/
│   ├── 2025-02-04_第一轮访谈纪要.md
│   └── 2025-02-04_第二轮访谈纪要.md
└── regulatory/
    ├── 2025-02-04_第一轮访谈纪要.md
    └── 2025-02-04_第二轮访谈纪要.md
```

---

## 九、三轮访谈核心指标对比

| 指标 | 第一轮 | 第二轮 | 第三轮 | 累计 |
|-----|-------|-------|-------|------|
| 访谈问题数 | 12 | 27 | 17 | 56 |
| 决策制定数 | 12 | 42 | 17 | 71 |
| 新增实体类 | 0 | ~60 | ~10 | ~70 |
| 新增关系类型 | 0 | ~40 | ~5 | ~45 |
| 待确认问题 | 0 | 17 | 0 | ✅全部解决 |
| 设计原则 | 5 | 5 | 深化 | 稳定 |
| 复杂度评估 | 中 | 高 | 高 | 稳定 |

---

## 十、最终交付物清单

### 10.1 访谈文档

- [x] 第一轮访谈综合总结
- [x] 第二轮访谈综合总结
- [x] 第三轮访谈综合总结
- [x] R&D领域访谈纪要（2轮）
- [x] 临床领域访谈纪要（2轮）
- [x] 供应链领域访谈纪要（2轮）
- [x] 监管合规领域访谈纪要（2轮）

### 10.2 Schema设计文档

- [x] 制药行业知识图谱Schema设计文档
- [x] 实施路线图

### 10.3 待生成文档

- [ ] 技术架构详细设计文档
- [ ] 数据源详细评估报告
- [ ] 数据ETL流程设计文档
- [ ] API接口设计文档
- [ ] 部署运维手册

---

**访谈纪要版本**: v3.0
**最后更新**: 2025-02-06
**访谈状态**: ✅ 全部完成

---

*第三轮访谈针对前两轮待确认的17个问题进行了深入讨论，所有问题均已得到明确决策。至此，制药行业知识图谱项目的访谈阶段全部完成，可以进入技术实施阶段。*
