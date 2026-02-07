# R&D领域知识图谱访谈纪要 - 第二轮

**访谈日期**: 2025-02-04
**访谈领域**: 研究与发现 (R&D)
**访谈类型**: 第二轮（针对待讨论问题）
**访谈状态**: 已完成

---

## 访谈问题与回答

### 问题1: 化合物开发阶段的状态转换规则

**Q1.1**: 化合物从一个开发阶段进入下一个阶段的转换规则应该如何定义？

**回答**: **综合规则**

需要综合多种决策因素：
- **决策门控**: Hit→Lead需要满足活性、选择性、溶解性等标准
- **阶段依赖**: I期临床成功后才可进入II期
- **里程碑触发**: PCC确定后可开始GLP毒理研究
- **专家评审**: 综合多维度数据的集体决策

**Q1.2**: 化合物开发状态是否允许回退？

**回答**: **条件回退**

- 允许在特定情况下回退（如Lead重新优化）
- 需要记录回退原因
- 回退是异常情况，需要审批

**设计决策**:
```
CompoundStatus (状态机)
├── 正常转换:
│   ├── Hit ──[满足标准]──▶ Lead
│   ├── Lead ──[优化完成]──▶ PCC
│   └── PCC ──[毒理通过]──▶ ClinicalCandidate
│
├── 条件回退:
│   ├── Lead ──[优化失败+审批]──▶ Hit
│   ├── PCC ──[成药性失败+审批]──▶ Lead
│   └── ClinicalCandidate ──[临床失败+审批]──▶ PCC
│
└── 转换规则:
    ├── decision_gate (决策门控标准)
    ├── milestone_required (必需里程碑)
    ├── approval_required (审批要求)
    └── rollback_reason (回退原因)
```

---

### 问题2: 多维分类体系的组合爆炸问题

**Q2.1**: 当化合物有3种分类维度，每种维度有5个值时，如何避免创建125个子类？

**回答**: **按需创建 + 分面分类**

**策略组合**:
1. **按需创建**: 只创建常用的组合类，其他通过查询动态组合
2. **分面分类**: 采用分面搜索（faceted search）模式

**Q2.2**: 用户通常如何查询化合物？

**回答**: **全部支持**

需要支持多种查询方式：
- 按单一维度过滤
- 按多维度组合查询
- 按相似度查询

**设计决策**:
```
化合物分类策略:

方案A: 分面分类 (Faceted Classification)
├── 维度1: StructureType
│   └── 值: SmallMolecule, Biologic, Peptide...
├── 维度2: DevelopmentStage
│   └── 值: Hit, Lead, PCC, ClinicalCandidate
└── 维度3: TherapeuticArea
    └── 值: Oncology, Cardiovascular, CNS...

查询实现:
├── 单一维度: ?StructureType=SmallMolecule
├── 组合查询: ?StructureType=SmallMolecule&DevelopmentStage=PCC
├── 分面导航: 逐步细化过滤条件
└── 相似度: 找出与Compound X相似的化合物

方案B: 按需创建预定义类
├── 高频组合: 创建如OncologyPCC类
├── 中频组合: 通过视图或查询定义
└── 低频组合: 动态查询

示例本体设计:
:Compound a :StructureType ;
    :DevelopmentStage :Lead ;
    :TherapeuticArea :Oncology .

# 预定义高频组合
:OncologyPCC rdfs:subClassOf [
    a owl:Class ;
    owl:intersectionOf (
        :Compound :DevelopmentStage :PCC
        :Compound :TherapeuticArea :Oncology
    )
] .
```

---

### 问题3: 活性数据的不确定性表示

**Q3.1**: 活性数据中的不确定性主要来自哪些方面？

**回答**: 全部来源都需要考虑

1. **实验重复性误差**: 如标准差、置信区间、变异系数
2. **方法学差异**: 如不同实验方法/条件的结果差异
3. **专家判断的主观性**: 如"可能相关"这种模糊判断
4. **数据不完整**: 如数据缺失、插值结果

**Q3.2**: 在KG中应该如何表示这种不确定性？

**回答**: 全部表示方式都需要支持

1. **数值 ± 误差范围**: 如10.5 ± 2.3 nM
2. **置信区间**: 如90%置信区间
3. **置信度等级**: 如高/中/低置信度评分
4. **概率分布**: 概率分布表示

**设计决策**:
```turtle
# 基础表示
:compoundX :inhibits :targetY ;
    :has_activity_value "10.5"^^xsd:float ;
    :has_activity_unit "nM"^^xsd:string ;
    :has_activity_type "IC50"^^xsd:string .

# 不确定性表示（多种方式并行）

# 方式1: 误差范围
:compoundX :inhibits :targetY ;
    :has_activity_value "10.5"^^xsd:float ;
    :has_std_error "2.3"^^xsd:float ;
    :has_std_deviation "2.3"^^xsd:float .

# 方式2: 置信区间
:compoundX :inhibits :targetY ;
    :has_ci_90_lower "8.2"^^xsd:float ;
    :has_ci_90_upper "12.8"^^xsd:float .

# 方式3: 置信度等级
:compoundX :inhibits :targetY ;
    :has_confidence_level "High"^^xsd:string ;
    :has_confidence_score "0.85"^^xsd:float .

# 方式4: 概率分布（对于复杂情况）
:compoundX :inhibits :targetY ;
    :has_distribution_type "Normal"^^xsd:string ;
    :has_distribution_mean "10.5"^^xsd:float ;
    :has_distribution_std "2.3"^^xsd:float .

# 方法学差异表示
:compoundX :inhibits :targetY ;
    :measured_in_assay :assay123 ;
    :assay_methodology "Fluorescence"^^xsd:string ;
    :assay_reliability_score "0.9"^^xsd:float .

# 主观性表示（专家判断）
:targetY :associated_with :diseaseZ ;
    :has_evidence_level "Possible"^^xsd:string ;
    :expert_confidence "Medium"^^xsd:string ;
    :assessment_method "ExpertConsensus"^^xsd:string .

# 数据完整性
:compoundX :inhibits :targetY ;
    :data_completeness "Complete"^^xsd:string ;
    :data_quality_score "0.8"^^xsd:float ;
    :missing_data_handling "Imputed"^^xsd:string .
```

---

### 问题4: 负面结果（Inactive数据）的处理

**Q4.1**: 将负面结果纳入KG的价值和挑战？

**回答**: 既有价值也有挑战

**价值**:
- **节约研发成本**: 避免重复测试无效化合物
- **完善构效关系**: 帮助理解SAR边界

**挑战**:
- **存储负担**: 数据量太大，增加存储成本
- **偏差问题**: 影响数据质量统计

**Q4.2**: 对于大量的阴性数据，应该如何存储？

**回答**: **混合策略**

采用分层次的存储策略：
1. **策略3（聚合存储）为主**: 通过计数统计存储
2. **策略2（选择性存储）为辅**: 只存储重要或代表性的阴性数据
3. **策略4（外部链接）为支撑**: 使用外部链接
4. **策略1（完整存储）仅用于极少量高价值DCM**: 完整存储

**设计决策**:
```
阴性数据存储策略:

层次1: 聚合存储（主要方式）
├── 存储统计信息
│   ├── total_tested (测试总数)
│   ├── active_count (活性数量)
│   ├── inactive_count (无活性数量)
│   └── hit_rate (命中率)
│
├── 示例:
    :TargetA -[:tested_against]→ :CompoundSeriesX
    :total_tested 1000
    :active_count 5
    :inactive_count 995
    :hit_rate 0.005

层次2: 选择性存储（辅助方式）
├── 存储有代表性的阴性数据
│   ├── SAR边界化合物
│   ├── 与活性化合物结构相似的阴性化合物
│   ├── 高质量实验的阴性数据
│   └── 历史重要项目的阴性数据
│
├── 选择标准:
    :NegativeResult
    ├── is_representative : true  # 具有代表性
    ├── similarity_to_active_gt : 0.7  # 与活性化合物相似度>0.7
    ├── data_quality_score_gte : 0.8  # 数据质量>=0.8
    └── project_importance : "High"  # 高价值项目

层次3: 外部链接（支撑方式）
├── KG中存储summary和链接
│   ├── external_storage_location (外部存储位置)
│   ├── summary_statistics (汇总统计)
│   └── query_interface (查询接口)
│
├── 示例:
    :CompoundX -[:has_negative_data]→ :ExternalDataset
    :external_location "s3://bucket/path/to/data"
    :record_count 50000
    :query_api "https://api.example.com/query"

层次4: 完整存储（极少数高价值DCM）
├── 存储完整的阴性三元组
│   ├── 每个阴性结果都是一条记录
│   ├── 用于关键决策的化合物
│   └── 数据完整的长期项目
│
├── DCM (Data of Critical Importance)标记:
    :NegativeResult
    ├── is_dcm : true
    ├── complete_stored : true
    └── retention_policy : "Permanent"

查询模式:
# 聚合查询
MATCH (t:Target)-[r:tested_against]->(series:CompoundSeries)
WHERE series.project_id = "ProjectX"
RETURN t.name,
       r.total_tested,
       r.active_count,
       r.hit_rate

# 选择性阴性数据查询
MATCH (c:Compound)-[r:acts_on]->(t:Target)
WHERE r.activity = "inactive"
  AND r.is_representative = true
  AND c.similarity_to_active > 0.7
RETURN c, r

# 外部数据查询
MATCH (c:Compound)-[r:has_negative_data]->(ext:ExternalDataset)
RETURN c.name, ext.summary_statistics, ext.query_api
```

---

### 问题5: 时间维度处理

**Q5.1**: 化合物的结构变更（如盐型、晶型变化）应该如何处理？

**回答**: **混合策略**

- 关键变更保留版本
- 小变更不保留版本

**Q5.2**: KG中的哪些元素需要时间戳？

**回答**: **全部级别**都需要

1. **实体级别**: 实体的创建/修改时间
2. **关系级别**: 关系的生效时间
3. **属性级别**: 属性值的时间序列
4. **事件级别**: 事件发生时间

**设计决策**:
```
时间维度建模:

实体版本化:
├── 关键变更触发新版本:
│   ├── 化学结构变化（盐型、晶型）
│   ├── 开发阶段重大变化
│   └── 关键属性变化
│
├── 版本表示:
    :Compoundv1 :has_version :Compoundv2
    :Compoundv1
        :version_number "1"^^xsd:integer ;
        :structure_smiles "CCO" ;
        :salt_form "FreeBase" ;
        :valid_from "2024-01-01"^^xsd:date ;
        :valid_until "2024-06-15"^^xsd:date .

    :Compoundv2
        :version_number "2"^^xsd:integer ;
        :structure_smiles "CCO.Cl" ;
        :salt_form "Hydrochloride" ;
        :valid_from "2024-06-15"^^xsd:date ;
        :valid_until "..."^^xsd:date ;
        :derived_from :Compoundv1 .

├── 小变更（不创建版本）:
    :Compound
        :current_salt_form "Hydrochloride"^^xsd:string ;
        :salt_form_history [
            "FreeBase"^^xsd:string ;
            :from "2024-01-01"^^xsd:date ;
            :to "2024-06-15"^^xsd:date
        ]

关系时间戳:
├── 关系的生效时间:
    :compoundX :inhibits :targetY ;
        :relationship_valid_from "2024-01-01"^^xsd:date ;
        :relationship_valid_until "..."^^xsd:date ;
        :evidence_reported_date "2023-12-15"^^xsd:date .

    # 时间切片查询
    MATCH (c:Compound)-[r:inhibits]->(t:Target)
    WHERE date("2024-06-01") >= r.relationship_valid_from
      AND date("2024-06-01") <= r.relationship_valid_until
    RETURN c, t, r

属性时间序列:
├── 属性值随时间变化:
    :compoundX :has_activity [
        :value "10.5"^^xsd:float ;
        :measured_date "2024-01-15"^^xsd:date ;
        :assay_version "v1.0"^^xsd:string
    ], [
        :value "8.2"^^xsd:float ;
        :measured_date "2024-06-20"^^xsd:date ;
        :assay_version "v2.0"^^xsd:string
    ] .

事件时间戳:
├── 事件发生时间:
    :AssayEvent123
        :event_type "BiochemicalAssay"^^xsd:string ;
        :event_start_time "2024-01-15T09:00:00"^^xsd:dateTime ;
        :event_end_time "2024-01-15T17:00:00"^^xsd:dateTime ;
        :event_created_at "2024-01-15T18:30:00"^^xsd:dateTime .

时态查询模式:
# 历史状态查询
MATCH (c:Compound)-[r:inhibits]->(t:Target)
WHERE r.relationship_valid_from <= date("2024-03-01")
  AND (r.relationship_valid_until >= date("2024-03-01") OR r.relationship_valid_until IS NULL)
RETURN c, t, r

# 时间序列查询
MATCH (c:Compound)-[r:has_activity_timeseries]->(t:Target)
WHERE r.measured_date >= date("2024-01-01")
  AND r.measured_date <= date("2024-12-31")
RETURN c.name, t.name,
       [r_in in collect(r) | r_in.value] as values,
       [r_in in collect(r) | r_in.measured_date] as dates
ORDER BY dates ASC

# 变更历史查询
MATCH (c:Compound)-[:has_version*]->(version:Compound)
WHERE version.valid_from <= date("2024-12-31")
RETURN version.version_number,
       version.structure_smiles,
       version.salt_form,
       version.valid_from,
       version.valid_until
ORDER BY version.valid_from ASC
```

---

## 设计决策汇总

| 问题 | 决策 | 实施复杂度 |
|-----|------|-----------|
| 状态转换规则 | 综合规则（门控+依赖+里程碑） | 中 |
| 状态回退 | 条件回退（需审批+记录原因） | 中 |
| 多维分类 | 分面分类+按需创建 | 低 |
| 查询支持 | 全部支持（单维+组合+相似度） | 中 |
| 不确定性表示 | 多种方式并行（误差+置信区间+等级+分布） | 高 |
| 阴性数据 | 混合策略（聚合+选择+外部+少量完整） | 高 |
| 化合物版本 | 混合策略（关键变更版本化） | 中 |
| 时间戳 | 全级别支持（实体+关系+属性+事件） | 高 |

---

## 新增的实体和关系定义

### 新增实体

```
# 状态转换相关
:StateTransitionRule
    ├── :decision_gate_criteria
    ├── :milestone_required
    ├── :approval_required
    └── :rollback_condition

:Facet (分面)
    ├── :facet_name
    ├── :facet_values
    └── :facet_priority

# 不确定性相关
:UncertaintyModel
    ├── :uncertainty_type (Error/CI/Level/Distribution)
    ├── :uncertainty_parameters
    └── :confidence_methodology

# 阴性数据相关
:AggregateResult
    ├── :total_count
    ├── :active_count
    ├── :inactive_count
    └── :hit_rate

:RepresentativeNegativeResult
    ├── :is_representative
    ├── :selection_criteria
    └── :data_quality_score

:ExternalDataset
    ├── :external_location
    ├── :summary_statistics
    ├── :record_count
    └── :query_api

# 版本控制相关
:CompoundVersion
    ├── :version_number
    ├── :valid_from
    ├── :valid_until
    ├── :derived_from
    └── :change_type

# 时间相关
:TimeInterval
    ├── :start
    ├── :end
    └── :duration

:TimeSeriesData
    ├── :timestamp
    ├── :value
    └── :metadata
```

### 新增关系

```
# 状态转换
:Compound ──[:has_current_state]──▶ :CompoundState
:CompoundState ──[:can_transition_to]──▶ :CompoundState
:CompoundState ──[:transition_rule]──▶ :StateTransitionRule

# 分面分类
:Compound ──[:has_facet]──▶ :Facet
:Facet ──[:has_facet_value]──▶ :FacetValue

# 不确定性
:Activity ──[:has_uncertainty]──▶ :UncertaintyModel
:UncertaintyModel ──[:derived_by]──▶ :Methodology

# 阴性数据
:Target ──[:tested_against]──▶ :CompoundSeries
:CompoundSeries ──[:has_aggregate_result]──▶ :AggregateResult
:Compound ──[:has_negative_data]──▶ :ExternalDataset
:NegativeResult ──[:is_representative_of]──▶ :CompoundSeries

# 版本控制
:Compound ──[:has_version]──▶ :CompoundVersion
:CompoundVersion ──[:derived_from]──▶ :CompoundVersion
:Compound ──[:has_property_history]──▶ :PropertyValueHistory

# 时间相关
:Entity ──[:valid_from]──▶ xsd:dateTime
:Entity ──[:valid_until]──▶ xsd:dateTime
:Relationship ──[:effective_date]──▶ xsd:dateTime
:Property ──[:measured_at]──▶ xsd:dateTime
```

---

## 待实施事项

### 高优先级
- [ ] 实现状态机模型和转换规则
- [ ] 设计分面分类查询接口
- [ ] 实现不确定性数据的多种表示方式
- [ ] 建立阴性数据的聚合和选择策略

### 中优先级
- [ ] 实现化合物版本控制
- [ ] 建立时态查询模式
- [ ] 设计外部数据链接机制
- [ ] 实现时间序列数据存储

### 低优先级
- [ ] 优化版本回退的历史追溯
- [ ] 建立数据质量评分体系
- [ ] 实现概率分布的高级查询

---

## 下一步行动

- [x] R&D领域第二轮访谈完成
- [ ] 供应链领域第二轮访谈
- [ ] 监管合规领域第二轮访谈
- [ ] 生成完整R&D领域Schema设计文档
- [ ] 整合三个领域的第二轮访谈结果

---

**访谈纪要版本**: v2.0
**最后更新**: 2025-02-04
