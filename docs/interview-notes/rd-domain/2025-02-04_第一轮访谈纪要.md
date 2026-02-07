# R&D领域知识图谱访谈纪要 - 第一轮

**访谈日期**: 2025-02-04
**访谈领域**: 研究与发现 (R&D)
**访谈状态**: 已完成

---

## 一、核心实体确认

用户确认R&D领域需要包含以下**四类核心实体**：

| 实体类别 | 包含内容 | 优先级 |
|---------|---------|-------|
| **化合物/药物类** | 小分子化合物、生物制剂、PROTAC、ADC等 | 高 |
| **靶点/生物分子类** | 基因、蛋白质、受体、酶等 | 高 |
| **实验/检测类** | 细胞实验、动物实验、生化实验等 | 高 |
| **功能/机制类** | 通路、生物过程、细胞组分等 | 高 |

**设计决策**：采用**全流程覆盖**策略，不预设优先级，四类实体同等重要。

---

## 二、核心业务流程

用户确认以下业务流程均需覆盖：

| 流程 | 描述 | 在KG中的体现 |
|-----|------|-------------|
| **靶点发现与验证** | 从靶点假设到验证的全流程 | Disease → Target → Validation Evidence |
| **化合物筛选与优化** | 从苗头化合物到先导化合物优化 | Hit → Lead → Optimization → PCC |
| **构效关系研究** | SAR、QSAR、分子对接等 | Chemical Structure ↔ Activity Data |
| **成药性评估** | 临床前候选化合物(PCC)确定 | ADME/Tox Properties ↔ Compound |

**设计决策**：业务流程通过**状态机**和**路径关系**在KG中建模。

---

## 三、核心痛点与KG解决方案

| 痛点 | KG解决方案 |
|-----|-----------|
| **靶点选择困难** | 多维证据聚合、靶点评分算法 |
| **数据孤岛问题** | 统一标识符、本体标准化 |
| **实验数据标准化** | BAO本体映射、实验元数据管理 |
| **转化率低** | 跨物种映射、 translational biomarkers |

---

## 四、实体分类体系设计

### 4.1 化合物分类（多维）

```
Compound (化合物)
├── 按结构类型分类:
│   ├── SmallMolecule (小分子)
│   ├── Biologic (生物制剂)
│   ├── Peptide (肽类)
│   ├── Oligonucleotide (寡核苷酸)
│   ├── PROTAC (蛋白降解嵌合体)
│   └── ADC (抗体药物偶联物)
│
├── 按开发阶段分类:
│   ├── Hit (苗头化合物)
│   ├── Lead (先导化合物)
│   ├── OptimizedLead (优化先导)
│   ├── PCC (临床前候选化合物)
│   └── ClinicalCandidate (临床候选)
│
└── 按治疗领域分类:
    ├── Oncology (肿瘤)
    ├── Cardiovascular (心血管)
    ├── CNS (中枢神经)
    └── ...
```

### 4.2 靶点分类（多维）

```
Target (靶点)
├── 按生物学功能分类:
│   ├── Enzyme (酶)
│   ├── Receptor (受体)
│   ├── IonChannel (离子通道)
│   ├── Transporter (转运体)
│   ├── TranscriptionFactor (转录因子)
│   └── StructuralProtein (结构蛋白)
│
├── 按成药性阶段分类:
│   ├── ValidatedTarget (已验证靶点)
│   ├── ClinicalStageTarget (临床阶段靶点)
│   ├── ExploratoryTarget (探索性靶点)
│   └── UndruggableTarget (不可成药靶点)
│
├── 按基因家族分类:
│   ├── Kinase (激酶家族)
│   ├── GPCR (GPCR家族)
│   ├── IonChannelFamily (离子通道家族)
│   └── ...
│
└── 按亚细胞定位分类:
    ├── MembraneProtein (膜蛋白)
    ├── CytoplasmicProtein (胞质蛋白)
    ├── NuclearProtein (核蛋白)
    └── SecretedProtein (分泌蛋白)
```

---

## 五、关系类型设计

### 5.1 化合物-靶点关系（精细化）

```
Compound ──[作用机制关系]──▶ Target
├── activates (激活)
│   ├── agonist (激动剂)
│   ├── partial_agonist (部分激动剂)
│   └── positive_modulator (正调节剂)
│
├── inhibits (抑制)
│   ├── antagonist (拮抗剂)
│   ├── inverse_agonist (反向激动剂)
│   ├── competitive_inhibitor (竞争性抑制剂)
│   ├── non_competitive_inhibitor (非竞争性抑制剂)
│   └── negative_modulator (负调节剂)
│
├── binds_to (结合)
│   ├── orthosteric (正构位点)
│   └── allosteric (变构位点)
│
├── regulates (调节)
│   ├── up_regulates (上调)
│   └── down_regulates (下调)
│
└── degrades (降解)
    └── via_proteolysis (蛋白降解途径)
```

### 5.2 带数值属性的关系

```turtle
# 示例三元组
:compoundX :inhibits :targetY ;
    :has_activity_value "10.5"^^xsd:float ;
    :has_activity_unit "nM"^^xsd:string ;
    :has_activity_type "IC50"^^xsd:string ;
    :measured_in_assay :assay123 ;
    :has_confidence_score "0.85"^^xsd:float ;
    :measured_in_cell_line "HEK293"^^xsd:string ;
    :measured_in_species "Human"^^xsd:string .
```

### 5.3 上下文依赖关系

```
Activity (活性数据)
├── 实验条件:
│   ├── cell_line (细胞系)
│   ├── species (物种)
│   ├── expression_system (表达系统)
│   ├── temperature (温度)
│   └── ph_value (pH值)
│
├── 时间维度:
│   ├── incubation_time (孵育时间)
│   ├── time_point测定时间点
│   └── kinetics (动力学参数)
│
└── 数据质量:
    ├── reproducibility (重现性)
    ├── sample_size (样本量)
    └── data_source (数据来源)
```

---

## 六、典型查询场景

### 6.1 靶点发现查询

```cypher
// 查询: 给定疾病D，找潜在靶点和化合物
MATCH (d:Disease {name: "Disease X"})-[:associated_with]->(t:Target)
MATCH (c:Compound)-[:acts_on]->(t)
WHERE c.development_stage IN ["PCC", "ClinicalCandidate"]
RETURN t, c, c.activity_value
ORDER BY c.activity_value ASC
```

### 6.2 作用机制查询

```cypher
// 查询: 给定化合物C，找其作用靶点和通路
MATCH (c:Compound {id: "C"})-[:r]->(t:Target)
MATCH (t)-[:participates_in]->(p:Pathway)
RETURN c, r, t, p
```

### 6.3 构效关系查询

```cypher
// 查询: 分析化合物结构变化与活性变化关系
MATCH (c1:Compound)-[:similar_to]->(c2:Compound)
MATCH (c1)-[a1:acts_on]->(t:Target)
MATCH (c2)-[a2:acts_on]->(t)
RETURN c1.smiles, c1.activity_value, c2.smiles, c2.activity_value
```

### 6.4 活性对比查询

```cypher
// 查询: 比较不同化合物在相同靶点上的活性数据
MATCH (c:Compound)-[a:acts_on]->(t:Target {id: "Target Y"})
WHERE a.measured_in_cell_line = "HEK293"
RETURN c.name, a.activity_value, a.activity_type
ORDER BY a.activity_value ASC
```

---

## 七、数据源与优先级

| 数据源类型 | 优先级 | 主要用途 | 本体参考 |
|-----------|-------|---------|---------|
| **本体/知识库** | 1 | 语义标准化、关系推理 | GO, Reactome, KEGG, ChEBI |
| **公共数据库** | 2 | 活性数据、化合物信息 | ChEMBL, PubChem, DrugBank |
| **内部数据** | 3 | 项目专有数据、保密信息 | 内部实验数据库 |
| **文献/专利** | 4 | 文本挖掘、证据发现 | PubMed,专利数据库 |

### 标识符映射策略

```
Compound标识符:
├── 主标识符: InChIKey (标准化)
├── 次要标识符: PubChem CID, ChEMBL ID
└── 内部标识符: 公司内部编号

Target标识符:
├── 主标识符: UniProt Accession
├── 次要标识符: Entrez Gene ID, Ensembl ID
└── 基因符号: HGNC Symbol

Disease标识符:
├── 主标识符: MONDO ID
├── 次要标识符: DOID, ICD-10, SNOMED-CT
└── 俗名映射
```

---

## 八、与真实世界证据(RWE)整合

**整合策略**：**部分整合**，在特定场景下关联

| 整合场景 | 整合方式 | 实体关联 |
|---------|---------|---------|
| **药物重定位** | R&D化合物 ↔ RWE药物 | Compound.equivalent_to |
| **靶点验证** | R&D靶点 ↔ RWE生物标志物 | Target.biomarker_for |
| **转化研究** | 动物模型 ↔ 人体数据 | Model.translates_to |

**设计决策**：R&D和RWE保持独立KG，通过**桥接实体**和**映射表**实现按需整合。

---

## 九、待讨论问题

1. [ ] 化合物开发阶段的**状态转换规则**如何定义？
2. [ ] 多维分类体系如何**避免组合爆炸**？
3. [ ] 活性数据的**不确定性**如何表示和传播？
4. [ ] 负面结果（inactive数据）是否纳入KG？
5. [ ] 时间维度（如化合物历史版本）如何处理？

---

## 十、下一步行动

- [x] R&D领域第一轮访谈完成
- [ ] 生成R&D领域Schema设计文档
- [ ] 开始供应链领域访谈
- [ ] 开始监管合规领域访谈
- [ ] R&D领域第二轮访谈（针对待讨论问题）

---

**访谈纪要版本**: v1.0
**最后更新**: 2025-02-04
