# 供应链领域知识图谱访谈纪要 - 第二轮

**访谈日期**: 2025-02-04
**访谈领域**: 供应链管理 (Supply Chain)
**访谈类型**: 第二轮（针对待讨论问题）
**访谈状态**: 已完成

---

## 访谈问题与回答

### 问题1: 多级供应链（N-tier）的追溯深度

**Q1.1**: 对于多级供应链，追溯深度应该如何设定？

**回答**: **混合策略（3级基础 + 动态扩展）**

制药行业不能采用单一追溯深度，必须根据产品风险、监管要求和业务需求分层处理。

**追溯深度决策矩阵**:

```
┌─────────────────────────────────────────────────────────────────┐
│              制药供应链追溯深度决策矩阵                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  问题1: 产品类型？                                              │
│  ├─ 处方药（Rx）→ 3级追溯（到API制造商）                        │
│  ├─ 生物制品/疫苗 → N级追溯（到细胞库/培养基来源）               │
│  ├─ 仿制药 → 2级追溯（关键起始物料）                            │
│  └─ OTC/辅料 → 1级追溯（合规即可）                              │
│                                                                 │
│  问题2: 风险等级？（基于ICH Q9质量风险管理）                     │
│  ├─ 高风险（如无菌注射剂）→ N级追溯 + 实时监测                   │
│  ├─ 中风险（口服固体制剂）→ 3级追溯                             │
│  └─ 低风险（外用制剂）→ 2级追溯                                 │
│                                                                 │
│  问题3: 监管区域？                                              │
│  ├─ 美国 → DSCSA要求3级（到包装商）+ 序列化                    │
│  ├─ 欧盟 → EU FMD要求2级（到MAH）+ 反篡改                      │
│  └─ 中国 → NMPA要求"来源可查、去向可追"（实际3-4级）           │
│                                                                 │
│  问题4: 供应商关键性？                                          │
│  ├─ 单一来源API → N级追溯（地理溯源+替代方案）                  │
│  └─ 通用辅料 → 1级追溯                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Q1.2**: 什么情况下需要深入追溯？

**回答**: 四种情况都需要

1. **基于物料风险**: 如关键API、高风险物料
2. **基于供应商风险**: 如新供应商、单一来源供应商
3. **基于事件触发**: 如发生质量事件或短缺
4. **基于合规要求**: 如监管要求或客户要求

**设计决策**:
```turtle
# 追溯深度模型

# 基础追溯（默认3级）
:DrugProduct :has_traceability_depth :Tier3 .

# 动态追溯（根据条件扩展）
:DrugProduct
    :product_type "Biologic"^^xsd:string ;
    :risk_level "High"^^xsd:string ;
    :traceability_depth :Dynamic ;
    :traceability_to :CellBank ;
    :traceability_to :MediaSource .

# 追溯关系
:DrugProduct ──[:contains]──▶ :API
:API ──[:sourced_from]──▶ :APIManufacturer
:APIManufacturer ──[:imports_from]──▶ :APISupplier
:APISupplier ──[:located_in]──▶ :Country

# N级追溯（生物制品）
:DrugProduct ──[:derived_from]──▶ :CellBank
:CellBank ──[:sourced_from]──▶ :CellBankSupplier
:CellBankSupplier ──[:located_in]──▶ :Country

# 追溯查询
# 3级追溯
MATCH (d:DrugProduct)-[:contains]->(api:API)
MATCH (api)-[:sourced_from]->(m:APIManufacturer)
MATCH (m)-[:imports_from]->(s:APISupplier)
RETURN d.name, api.name, m.name, s.name, s.country

# 动态深度追溯
MATCH path = (d:DrugProduct)-[:sourced_from*1..N]->(source)
WHERE d.product_type = "Biologic"
RETURN path, length(path) as depth
```

---

### 问题2: 短缺事件的预测模型

**Q2.1**: 短缺事件的预测应该考虑哪些关键因素？

**回答**: 四类因素都需要考虑

1. **供应商内部指标**: 如产能利用率、库存水平、订单积压
2. **外部风险因素**: 如自然灾害、地缘政治、原材料短缺
3. **监管信号**: 如FDA警告信、进口预警、质量事件
4. **市场信号**: 如市场价格波动、需求激增、竞争态势

**Q2.2**: 预警系统应该如何设计风险等级？

**回答**: **混合模式**

结合分级和概率的风险评估方式。

**设计决策**:
```
短缺预测模型:

输入因素（四类）:
├── 供应商内部指标:
│   ├── capacity_utilization_rate (产能利用率)
│   ├── inventory_level (库存水平)
│   ├── backlog_days (订单积压天数)
│   └── on_time_delivery_rate (准时交付率)
│
├── 外部风险因素:
│   ├── natural_disaster_risk (自然灾害风险)
│   ├── geopolitical_risk (地缘政治风险)
│   ├── raw_material_shortage (原材料短缺)
│   └── logistics_disruption (物流中断)
│
├── 监管信号:
│   ├── fda_warning_letter (FDA警告信)
│   ├── import_alert (进口预警)
│   ├── quality_incident (质量事件)
│   └── compliance_status (合规状态)
│
└── 市场信号:
    ├── price_volatility (价格波动)
    ├── demand_surge (需求激增)
    └── competitor_status (竞争态势)

风险评分模型:
├── 概率评分（0-1）:
│   ├── shortgage_probability = f(内部指标 + 外部风险 + 监管信号 + 市场信号)
│   └── 使用机器学习模型（如逻辑回归、随机森林）
│
├── 风险等级（三级 + 概率）:
│   ├── 红色（高风险）: probability ≥ 0.7 OR 重大监管信号
│   ├── 黄色（中风险）: 0.3 ≤ probability < 0.7 OR 轻微监管信号
│   └── 绿色（低风险）: probability < 0.3 AND 无监管信号
│
└── 预警输出:
    ├── risk_level (风险等级)
    ├── probability_score (概率评分)
    ├── key_contributing_factors (主要贡献因素)
    ├── recommended_actions (建议行动)
    └── prediction_confidence (预测置信度)

预测关系设计:
:Supplier ──[:has_risk_indicator]──▶ :RiskIndicator
    ├── capacity_utilization "0.95"^^xsd:float
    ├── inventory_days_cover "15"^^xsd:float
    ├── backlog_days "30"^^xsd:float
    ├── fda_warning_letter "Yes"^^xsd:boolean
    └── risk_assessment_date "2024-02-04"^^xsd:date

:RiskIndicator ──[:predicted_shortage]──▶ :ShortagePrediction
    ├── shortage_probability "0.75"^^xsd:float
    ├── risk_level "Red"^^xsd:string
    ├── key_factors ["capacity_utilization", "fda_warning_letter"]
    ├── recommended_action "Find alternative supplier"
    └── prediction_confidence "0.82"^^xsd:float

:ShortagePrediction ──[:affects]──▶ :Material
    ├── material_name "API XYZ"^^xsd:string
    ├── impact_severity "High"^^xsd:string
    └── time_to_impact "2-3 months"^^xsd:string
```

---

### 问题3: 供应商动态评分更新频率

**Q3.1**: 供应商绩效评分的更新频率应该如何设定？

**回答**: **分层频率（混合策略）**

单一频率无法满足所有指标的特性需求。采用风险分层+指标特性的双维决策框架。

**分层频率决策框架**:

```
┌─────────────────────────────────────────────────────────────────┐
│              供应商绩效评分更新频率矩阵                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  维度1：指标类型（数据特性）                                     │
│  ├─ 实时/近实时指标 → 每次交易后更新（自动化）                   │
│  │   └─ 交期准时率、订单确认时间、发票匹配                       │
│  ├─ 短期指标 → 每日/每周批量                                    │
│  │   └─ 库存周转、响应时间、服务工单解决                         │
│  ├─ 中期指标 → 每月/每季度                                      │
│  │   └─ 质量合格率、投诉率、审计发现                             │
│  └─ 长期指标 → 每半年/每年                                      │
│      └─ 财务稳定性、战略规划匹配度、创新能力                     │
│                                                                 │
│  维度2：供应商风险等级（业务影响）                               │
│  ├─ 高风险供应商 → 所有指标频率提升一级                          │
│  ├─ 中风险供应商 → 标准频率                                     │
│  └─ 低风险供应商 → 长期指标可延长周期                            │
│                                                                 │
│  维度3：事件触发（异常响应）                                     │
│  └─ 任何等级供应商发生重大事件 → 立即更新并冻结采购              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Q3.2**: 不同评分维度的更新频率应该如何区分？

**回答**: 按维度特性区分

1. **交付维度（高频）**: 如准时交付率、交期一致性
2. **质量维度（中频）**: 如批次合格率、OOS率
3. **成本维度（低频）**: 如价格竞争力、付款条件
4. **战略维度（低频）**: 如财务稳定性、合规认证

**设计决策**:
```turtle
# 供应商绩效评分模型

# 评分维度定义（带更新频率）
:SupplierPerformanceScore
    ├── delivery维度（高频）
    │   ├── on_time_delivery_rate
    │   │   ├── update_frequency :PerTransaction
    │   │   └── calculation_window :Rolling30Days
    │   ├── lead_time_consistency
    │   │   ├── update_frequency :Weekly
    │   │   └── calculation_window :Rolling90Days
    │   └── order_confirmation_time
    │       ├── update_frequency :PerTransaction
    │       └── calculation_window :Rolling7Days
    │
    ├── quality维度（中频）
    │   ├── batch_acceptance_rate
    │   │   ├── update_frequency :Monthly
    │   │   └── calculation_window :Rolling6Months
    │   ├── oos_incident_rate
    │   │   ├── update_frequency :Monthly
    │   │   └── calculation_window :Rolling12Months
    │   └── complaint_rate
    │       ├── update_frequency :Quarterly
    │       └── calculation_window :Rolling12Months
    │
    ├── cost维度（低频）
    │   ├── unit_price_competitiveness
    │   │   ├── update_frequency :Quarterly
    │   │   └── benchmark_market :Regional
    │   └── payment_terms
    │       ├── update_frequency :SemiAnnually
    │       └── contract_based :true
    │
    └── strategic维度（低频）
        ├── financial_stability
        │   ├── update_frequency :Annually
        │   └── data_source :CreditReport
        ├── certification_status
        │   ├── update_frequency :EventDriven
        │   └── trigger :CertificationChange
        └── innovation_capability
            ├── update_frequency :Annually
            └── assessment_method :ExpertReview

# 风险调整频率
:Supplier ──[:has_risk_level]──▶ :RiskLevel
    ├── risk_level "High"^^xsd:string
    └── frequency_multiplier "1.5"^^xsd:float

# 高风险供应商频率调整
:SupplierPerformanceScore
    :base_update_frequency :Monthly ;
    :adjusted_frequency :[
        :frequency_period "Weekly" ;
        :applies_when "HighRiskSupplier"
    ]

# 事件触发更新
:Supplier ──[:experienced_event]──▶ :SupplyEvent
    ├── event_type "QualityIncident"^^xsd:string
    ├── event_severity "Major"^^xsd:string
    ├── event_date "2024-02-04"^^xsd:date
    └── triggers_immediate_update :true

:SupplyEvent ──[:triggers_update]──▶ :ScoreUpdate
    ├── update_type "Immediate"^^xsd:string
    ├── freeze_procurement :true
    └── requires_review :true

# 评分历史追踪
:Supplier ──[:has_score_history]──▶ :ScoreHistory
    ├── score_date "2024-02-04"^^xsd:date
    ├── overall_score "85.5"^^xsd:float
    ├── delivery_score "90.2"^^xsd:float
    ├── quality_score "88.1"^^xsd:float
    └── cost_score "78.3"^^xsd:float

# 时序评分查询
MATCH (s:Supplier)-[r:has_score_history]->(sh:ScoreHistory)
WHERE s.id = "SupplierX"
  AND sh.score_date >= date("2023-01-01")
RETURN sh.score_date, sh.overall_score, sh.delivery_score, sh.quality_score
ORDER BY sh.score_date DESC
```

---

### 问题4: 跨国供应链法规差异处理

**Q4.1**: 跨国供应链的法规差异主要体现在哪些方面？

**回答**: 四个方面

1. **认证互认**: 如GMP、GDP等认证的互认
2. **进口管制**: 如进口许可证、监管备案要求
3. **贸易合规**: 如原产地规则、关税分类
4. **特殊监管**: 如数据隐私、出口管制

**Q4.2**: 在KG中应该如何处理这些法规差异？

**回答**: **混合策略（通用+扩展 + 映射转换 + 条件分区）**

**三层模型架构**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    跨国法规知识图谱架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  第1层：通用核心层（Global Core）                                │
│  ├── 实体：Compound, Supplier, Facility, Regulation              │
│  ├── 关系：produces, regulates, certifies, imports               │
│  └── 属性：name, identifier, dateCreated（跨法规通用）           │
│                                                                 │
│  第2层：法规扩展层（Regulatory Extensions）                      │
│  ├── 美国扩展：FDA_Registration, DEA_License, 483_Observation    │
│  ├── 欧盟扩展：EMA_MarketingAuth, QP_Release, GMP_Certificate    │
│  ├── 中国扩展：NMPA_Registration, ImportLicense, 口岸检验         │
│  └── 扩展通过 rdf:type 或 subclass 链接到核心层                  │
│                                                                 │
│  第3层：映射转换层（Mapping & Transformation）                   │
│  ├── 概念映射：FDA_Registration ≡ NMPA_Registration（功能等价）   │
│  ├── 标准转换：GMP_US → GMP_EU 差异标注                          │
│  └── 合规路径：多法规同时合规的决策逻辑                          │
│                                                                 │
│  特殊场景：分区存储（Federation）                                │
│  └── 数据本地化要求（如中国人类遗传资源）→ 独立分区+联邦查询       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**设计决策**:
```turtle
# 第1层：通用核心层
:Manufacturer a :Entity ;
    :name "Manufacturer ABC"^^xsd:string ;
    :global_id "MFR-12345"^^xsd:string ;
    :country "Global"^^xsd:string .

:Regulation a :GlobalRegulation ;
    :name "GMP"^^xsd:string ;
    :regulation_type "QualityStandard"^^xsd:string .

:Facility ──[:complies_with]──▶ :Regulation

# 第2层：法规扩展层
# 美国扩展
:Facility ──[:has_us_extension]──▶ :USFacilityExtension
    ├── fei_number "12345678901234"^^xsd:string ;
    ├── dea_registration "AB1234567"^^xsd:string ;
    ├── fda_483_status "NAI"^^xsd:string ;
    └── last_fda_inspection "2023-06-15"^^xsd:date .

# 欧盟扩展
:Facility ──[:has_eu_extension]──▶ :EUFacilityExtension
    ├── eudra_ct_number "EU-CT-2024-12345"^^xsd:string ;
    ├── qp_release_available "Yes"^^xsd:boolean ;
    ├── gmp_certificate_number "EU-GMP-1234"^^xsd:string ;
    └── qp_name "Dr. John Smith"^^xsd:string .

# 中国扩展
:Facility ──[:has_cn_extension]──▶ :CNFacilityExtension
    ├── nmpa_license "京20180001"^^xsd:string ;
    ├── import_license "进2024-001"^^xsd:string ;
    ├── port_inspection_required "Yes"^^xsd:boolean ;
    └── designated_ports ["北京", "上海", "广州"] .

# 第3层：映射转换层
# 认证互认映射
:GMPCertificate ──[:has_mutual_recognition]──▶ :RegulatoryAuthority
    ├── certificate_type "GMP"^^xsd:string ;
    ├── issuing_authority "FDA"^^xsd:string ;
    ├── recognized_by "EMA"^^xsd:boolean ;
    ├── recognition_scope "Manufacture of APIs"^^xsd:string ;
    └── equivalence_note "Substantially equivalent"^^xsd:string .

# 贸易合规映射
:Product ──[:has_trade_classification]──▶ :TradeClassification
    ├── hs_code_us "3004.90"^^xsd:string ;
    ├── hs_code_eu "3004.90"^^xsd:string ;
    ├── hs_code_cn "3004.90"^^xsd:string ;
    ├── origin_rule_us "35% CHVF"^^xsd:string ;
    ├── origin_rule_eu "Substantial Transformation"^^xsd:string ;
    └── origin_rule_cn "完全获得"^^xsd:string .

# 进口管制映射
:Material ──[:requires_import_license]──▶ :ImportLicense
    ├── material_name "API XYZ"^^xsd:string ;
    ├── target_region "US"^^xsd:string ;
    ├── license_type "DEA Certificate"^^xsd:string ;
    ├── license_number "ABC123"^^xsd:string ;
    ├── expiry_date "2025-12-31"^^xsd:date ;
    └── renewal_required "Yes"^^xsd:boolean .

# 合规路径查询
# 查询：某产品在美国、欧盟、中国的合规要求
MATCH (p:Product)-[:has_trade_classification]->(tc:TradeClassification)
MATCH (p)-[:contains]->(m:Material)
MATCH (m)-[:requires_import_license]->(il:ImportLicense)
RETURN p.name,
       tc.hs_code_us, tc.hs_code_eu, tc.hs_code_cn,
       il.license_type, il.target_region, il.license_number

# 认证互认查询
MATCH (f:Facility)-[:complies_with]->(cert:GMPCertificate)
MATCH (cert)-[:has_mutual_recognition]->(ra:RegulatoryAuthority)
WHERE cert.issuing_authority = "FDA"
  AND cert.recognized_by = "EMA"
RETURN f.name, cert.certificate_type, ra.name
```

---

### 问题5: 敏感商业信息的权限控制

**Q5.1**: 哪些类型的供应链数据属于敏感商业信息？

**回答**: 四类都是

1. **定价与合同**: 如单价、合同条款、折扣信息
2. **技术机密**: 如配方、工艺参数、质量标准
3. **战略信息**: 如供应商评估报告、谈判记录
4. **运营数据**: 如供应量、库存水平

**Q5.2**: 权限控制应该采用什么机制？

**回答**: 全部机制都需要

1. **基于角色(RBAC)**: 不同角色不同权限
2. **基于供应商**: 不同供应商数据不同权限
3. **基于数据级别**: 高敏感数据需要审批才能访问
4. **审计日志**: 记录所有数据访问历史

**设计决策**:
```turtle
# 敏感数据分类
:SensitiveDataType
    ├── PricingAndContracting (定价与合同)
    │   ├── unit_price (单价)
    │   ├── contract_terms (合同条款)
    │   ├── discount_schedule (折扣表)
    │   └── payment_terms (付款条件)
    │
    ├── TechnicalConfidential (技术机密)
    │   ├── formulation (配方)
    │   ├── process_parameters (工艺参数)
    │   ├── quality_specifications (质量标准)
    │   └── manufacturing_process (制造工艺)
    │
    ├── StrategicInformation (战略信息)
    │   ├── supplier_assessment_report (供应商评估报告)
    │   ├── negotiation_records (谈判记录)
    │   ├── alternative_supplier_list (备选供应商)
    │   └── sourcing_strategy (采购策略)
    │
    └── OperationalData (运营数据)
        ├── supply_volume (供应量)
        ├── inventory_level (库存水平)
        ├── demand_forecast (需求预测)
        └── production_schedule (生产计划)

# 权限控制模型

# 1. 基于角色（RBAC）
:Role
    ├── ProcurementOfficer (采购员)
    │   ├── can_access :PricingAndContracting
    │   ├── can_access :OperationalData
    │   └── cannot_access :StrategicInformation
    │
    ├── FinanceManager (财务经理)
    │   ├── can_access :PricingAndContracting
    │   ├── can_access :StrategicInformation
    │   └── cannot_access :TechnicalConfidential
    │
    ├── QualityManager (质量经理)
    │   ├── can_access :TechnicalConfidential
    │   ├── can_access :OperationalData
    │   └── cannot_access :PricingAndContracting
    │
    └── SeniorManagement (高级管理层)
        ├── can_access_all :true
        └── approval_required :HighSensitivityData

# 2. 基于供应商
:Supplier ──[:has_sensitivity_level]──▶ :SensitivityLevel
    ├── level "High"^^xsd:string  # 竞争敏感供应商
    ├── level "Medium"^^xsd:string  # 常规供应商
    └── level "Low"^^xsd:string  # 公开信息供应商

:Data ──[:belongs_to_supplier]──▶ :Supplier
    :supplier_id "SupplierX"^^xsd:string ;
    :access_restriction [
        :requires_role "ProcurementOfficer"^^xsd:string ;
        :requires_approval :true ;
        :min_sensitivity_level "Medium"^^xsd:string
    ] .

# 3. 基于数据级别
:DataClassification
    ├── Public (公开数据)
    │   ├── access_level :AllUsers
    │   └── approval_required :false
    │
    ├── Internal (内部数据)
    │   ├── access_level :AuthorizedEmployees
    │   └── approval_required :false
    │
    ├── Confidential (机密数据)
    │   ├── access_level :RoleBased
    │   └── approval_required :false
    │
    └── HighlyConfidential (高度机密)
        ├── access_level :ApprovalRequired
        └── approval_required :true

# 4. 审计日志
:DataAccess ──[:logged_in]──▶ :AuditLog
    ├── user_id "user123"^^xsd:string ;
    ├── user_role "ProcurementOfficer"^^xsd:string ;
    ├── accessed_data "unit_price"^^xsd:string ;
    ├── supplier_id "SupplierX"^^xsd:string ;
    ├── access_time "2024-02-04T10:30:00"^^xsd:dateTime ;
    ├── access_purpose "PriceNegotiation"^^xsd:string ;
    └── access_granted :true .

# 敏感数据访问控制
# 示例：访问定价数据
:DataPoint
    a :PricingAndContracting ;
    :data_id "price_supplierX_2024"^^xsd:string ;
    :supplier_id "SupplierX"^^xsd:string ;
    :classification :Confidential ;
    :allowed_roles ["ProcurementOfficer", "FinanceManager", "SeniorManagement"] ;
    :requires_approval :false ;
    :audit_required :true .

# 查询权限检查
MATCH (u:User {id: "user123"})-[:has_role]->(r:Role)
MATCH (d:DataPoint {id: "price_supplierX_2024"})
WHERE r.name IN d.allowed_roles
RETURN u.id, d.data_id, "Access Granted"

# 审计查询
MATCH (u:User)-[a:logged_in]->(al:AuditLog)
WHERE u.id = "user123"
  AND al.access_time >= datetime("2024-02-01T00:00:00")
RETURN al.access_time, al.accessed_data, al.access_purpose, al.access_granted
ORDER BY al.access_time DESC
```

---

## 设计决策汇总

| 问题 | 决策 | 实施复杂度 |
|-----|------|-----------|
| 追溯深度 | 混合策略（3级基础+动态扩展） | 中 |
| 追溯触发 | 多条件触发（风险+供应商+事件+合规） | 中 |
| 短缺预测 | 四类因素+混合风险模式 | 高 |
| 评分更新 | 分层频率（风险+指标特性+事件触发） | 高 |
| 法规差异 | 三层模型（核心+扩展+映射） | 高 |
| 权限控制 | 多维控制（RBAC+供应商+级别+审计） | 高 |

---

## 新增的实体和关系定义

### 新增实体

```
# 追溯相关
:TraceabilityConfig
    ├── :default_depth
    ├── :max_depth
    ├── :product_type
    └── :risk_level

:DynamicTraceability
    ├── :trace_to
    ├── :condition
    └── :depth

# 预测相关
:RiskIndicator
    ├── :indicator_type
    ├── :value
    ├── :threshold
    └── :status

:ShortagePrediction
    ├── :shortage_probability
    ├── :risk_level
    ├── :key_factors
    └── :confidence_score

# 评分相关
:SupplierPerformanceScore
    ├── :delivery_score
    ├── :quality_score
    ├── :cost_score
    └── :strategic_score

:ScoreHistory
    ├── :score_date
    ├── :overall_score
    └── :dimension_scores

# 法规相关
:RegulatoryExtension
    ├── :region
    ├── :local_requirements
    └── :extensions

:MutualRecognition
    ├── :issuing_authority
    ├── :recognizing_authority
    └── :scope

# 权限相关
:SensitiveDataType
    ├── :data_type
    ├── :classification
    └── :access_level

:DataClassification
    ├── :level
    ├── :access_rules
    └── :approval_required

:AuditLog
    ├── :user_id
    ├── :accessed_data
    ├── :access_time
    └── :access_purpose
```

### 新增关系

```
# 追溯关系
:DrugProduct ──[:has_traceability_config]──▶ :TraceabilityConfig
:DrugProduct ──[:dynamic_trace_to]──▶ :Entity

# 预测关系
:Supplier ──[:has_risk_indicator]──▶ :RiskIndicator
:RiskIndicator ──[:predicted_shortage]──▶ :ShortagePrediction
:ShortagePrediction ──[:affects]──▶ :Material

# 评分关系
:Supplier ──[:has_current_score]──▶ :SupplierPerformanceScore
:Supplier ──[:has_score_history]──▶ :ScoreHistory
:SupplyEvent ──[:triggers_update]──▶ :ScoreUpdate

# 法规关系
:Facility ──[:has_regional_extension]──▶ :RegulatoryExtension
:GMPCertificate ──[:has_mutual_recognition]──▶ :RegulatoryAuthority

# 权限关系
:User ──[:has_role]──▶ :Role
:Role ──[:can_access]──▶ :SensitiveDataType
:DataPoint ──[:has_classification]──▶ :DataClassification
:DataAccess ──[:logged_in]──▶ :AuditLog
```

---

## 待实施事项

### 高优先级
- [ ] 实现动态追溯深度模型
- [ ] 建立短缺预测框架
- [ ] 设计分层评分更新机制
- [ ] 实现三层法规模型

### 中优先级
- [ ] 建立风险调整频率机制
- [ ] 实现多法规合规路径查询
- [ ] 设计RBAC权限控制模型
- [ ] 建立审计日志系统

### 低优先级
- [ ] 优化N级追溯查询性能
- [ ] 建立预测模型训练pipeline
- [ ] 实现细粒度权限控制
- [ ] 建立合规决策支持系统

---

## 下一步行动

- [x] 供应链领域第二轮访谈完成
- [ ] 监管合规领域第二轮访谈
- [ ] 生成完整供应链领域Schema设计文档
- [ ] 整合三个领域的第二轮访谈结果

---

**访谈纪要版本**: v2.0
**最后更新**: 2025-02-04
