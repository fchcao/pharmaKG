# 制药行业知识图谱 - 核心实体定义

## 实体分类层次结构

```
pharmaceutical:Entity (抽象根类)
│
├── rdm:ResearchEntity (研究实体)
│   ├── Chemical
│   ├── Target (Gene/Protein)
│   ├── Pathway
│   └── Assay
│
├── clinical:ClinicalEntity (临床实体)
│   ├── ClinicalTrial
│   ├── Patient
│   ├── Intervention
│   └── Outcome
│
├── manufacturing:ManufacturingEntity (生产实体)
│   ├── Manufacturer
│   ├── Supplier
│   ├── API
│   └── Facility
│
├── regulatory:RegulatoryEntity (监管实体)
│   ├── RegulatoryAgency
│   ├── Submission
│   ├── Approval
│   └── AdverseEvent
│
├── commercial:CommercialEntity (商业实体)
│   ├── Market
│   ├── Pricing
│   ├── Reimbursement
│   └── Sales
│
└── supplychain:SupplyChainEntity (供应链实体)
    ├── Distribution
    ├── Inventory
    ├── Shortage
    └── Logistics
```

---

## 一、研究实体 (rdm:ResearchEntity)

### 1.1 Chemical (化学物质/药物)

**定义**: 具有明确分子结构的化学实体，包括药物、先导化合物、代谢产物等。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| chemical_id | IRI | ✓ | 唯一标识符 | CHEBI:27732 |
| name | String | ✓ | 化学名称 | "Aspirin" |
| inchikey | String | ✓ | InChIKey (主标识符) | "BSYNRYMUTXBXSQ-UHFFFAOYSA-N" |
| smiles | String | ○ | SMILES表示 | "CC(=O)OC1=CC=CC=C1C(=O)O" |
| formula | String | ○ | 分子式 | "C9H8O4" |
| molecular_weight | Float | ○ | 分子量 | 180.16 |
| drug_status | Enum | ○ | 药物状态 | approved/experimental/withdrawn |

**标准参考**:
- ChEBI (Chemical Entities of Biological Interest)
- PubChem
- ChEMBL

---

### 1.2 Target (靶点 - 基因/蛋白)

**定义**: 药物作用的生物分子靶点，包括蛋白质、基因、RNA等。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| target_id | IRI | ✓ | 唯一标识符 | UniProt:P12345 |
| name | String | ✓ | 靶点名称 | "COX-1" |
| symbol | String | ✓ | 基因符号 | "PTGS1" |
| target_type | Enum | ✓ | 靶点类型 | protein/gene/rna |
| organism | String | ○ | 物种 | "Homo sapiens" |
| function | String | ○ | 功能描述 | "Cyclooxygenase activity" |

**标准参考**:
- UniProt
- HGNC (HUGO Gene Nomenclature Committee)
- Ensembl

---

### 1.3 Pathway (通路)

**定义**: 生物分子参与的信号传导或代谢通路。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| pathway_id | IRI | ✓ | 唯一标识符 | KEGG:hsa04630 |
| name | String | ✓ | 通路名称 | "JAK-STAT signaling pathway" |
| pathway_type | Enum | ○ | 通路类型 | signaling/metabolic |

**标准参考**:
- KEGG
- Reactome
- WikiPathways

---

### 1.4 Assay (实验/生物检测)

**定义**: 用于检测化合物活性或特异性的实验方法。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| assay_id | IRI | ✓ | 唯一标识符 | BAO:0000194 |
| name | String | ✓ | 实验名称 | "cell viability assay" |
| assay_type | Enum | ✓ | 实验类型 | binding/functional/phenotypic |
| detection_method | String | ○ | 检测方法 | "fluorescence" |

**标准参考**:
- BAO (BioAssay Ontology)

---

## 二、临床实体 (clinical:ClinicalEntity)

### 2.1 ClinicalTrial (临床试验)

**定义**: 评估药物安全性和有效性的临床研究。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| trial_id | IRI | ✓ | 唯一标识符 | NCT00001234 |
| title | String | ✓ | 试验标题 | "Study of X in Disease Y" |
| phase | Enum | ✓ | 试验阶段 | I/II/III/IV |
| status | Enum | ✓ | 试验状态 | recruiting/active/completed |
| start_date | Date | ○ | 开始日期 | 2023-01-15 |
| end_date | Date | ○ | 结束日期 | 2025-12-31 |
| enrollment | Integer | ○ | 入组人数 | 200 |

**标准参考**:
- ClinicalTrials.gov
- EU Clinical Trials Register

---

### 2.2 Patient (患者/受试者)

**定义**: 参与临床试验或接受治疗的患者。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| patient_id | IRI | ✓ | 唯一标识符 | (匿名化ID) |
| age | Integer | ○ | 年龄 | 45 |
| sex | Enum | ○ | 性别 | male/female |
| condition | IRI | ✓ | 患病情况 | DOID:4346 |

---

### 2.3 Intervention (干预措施)

**定义**: 临床试验中使用的药物、设备或程序。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| intervention_id | IRI | ✓ | 唯一标识符 | - |
| type | Enum | ✓ | 干预类型 | drug/device/procedure |
| name | String | ✓ | 名称 | "Aspirin 100mg" |
| dosage | String | ○ | 剂量 | "100mg daily" |

---

### 2.4 Outcome (结局)

**定义**: 临床试验的主要或次要终点。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| outcome_id | IRI | ✓ | 唯一标识符 | - |
| type | Enum | ✓ | 结局类型 | primary/secondary |
| measure | String | ✓ | 测量指标 | "Overall Survival" |
| time_point | String | ○ | 时间点 | "12 months" |

---

## 三、生产实体 (manufacturing:ManufacturingEntity)

### 3.1 Manufacturer (制造商)

**定义**: 药品生产企业。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| manufacturer_id | IRI | ✓ | 唯一标识符 | - |
| name | String | ✓ | 企业名称 | "Pfizer Inc." |
| country | String | ○ | 所在国家 | "USA" |
| type | Enum | ○ | 企业类型 | innovator/generic |

---

### 3.2 Supplier (供应商)

**定义**: 原料药或包装材料供应商。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| supplier_id | IRI | ✓ | 唯一标识符 | - |
| name | String | ✓ | 供应商名称 | "Sigma-Aldrich" |
| material_type | String | ○ | 供应物料类型 | "API" |

---

### 3.3 API (Active Pharmaceutical Ingredient)

**定义**: 药物活性成分。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| api_id | IRI | ✓ | 唯一标识符 | - |
| name | String | ✓ | API名称 | "Acetylsalicylic acid" |
| cas_number | String | ○ | CAS号 | "50-78-2" |

---

### 3.4 Facility (生产设施)

**定义**: 药品生产场所。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| facility_id | IRI | ✓ | 唯一标识符 | - |
| name | String | ✓ | 设施名称 | "Pfizer New York Facility" |
| location | String | ○ | 地理位置 | "New York, USA" |
| certification | String | ○ | 认证状态 | "GMP certified" |

---

## 四、监管实体 (regulatory:RegulatoryEntity)

### 4.1 RegulatoryAgency (监管机构)

**定义**: 负责药品监管的政府机构。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| agency_id | IRI | ✓ | 唯一标识符 | - |
| name | String | ✓ | 机构名称 | "FDA" |
| country | String | ✓ | 所在国家 | "USA" |
| scope | String | ○ | 监管范围 | "drugs and biologics" |

---

### 4.2 Submission (申报)

**定义**: 向监管机构提交的药品注册申请。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| submission_id | IRI | ✓ | 唯一标识符 | - |
| type | Enum | ✓ | 申请类型 | NDA/BLA/ANDA/MAA |
| submission_date | Date | ✓ | 提交日期 | 2023-05-01 |
| status | Enum | ✓ | 审评状态 | under review/approved/rejected |

---

### 4.3 Approval (批准)

**定义**: 监管机构对药品的上市批准。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| approval_id | IRI | ✓ | 唯一标识符 | - |
| approval_number | String | ✓ | 批准文号 | "NDA 123456" |
| approval_date | Date | ✓ | 批准日期 | 2023-08-15 |
| indications | List | ○ | 批准适应症 | ["migraine", "fever"] |

---

### 4.4 AdverseEvent (不良事件)

**定义**: 药物使用中发生的不良反应。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| event_id | IRI | ✓ | 唯一标识符 | - |
| type | String | ✓ | 事件类型 | "Stevens-Johnson syndrome" |
| severity | Enum | ○ | 严重程度 | mild/moderate/severe |
| report_date | Date | ✓ | 报告日期 | 2023-06-01 |

---

## 五、商业实体 (commercial:CommercialEntity)

### 5.1 Market (市场)

**定义**: 药品销售区域或市场。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| market_id | IRI | ✓ | 唯一标识符 | - |
| name | String | ✓ | 市场名称 | "US Market" |
| region | String | ○ | 区域 | "North America" |

---

### 5.2 Pricing (定价)

**定义**: 药品价格信息。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| price_id | IRI | ✓ | 唯一标识符 | - |
| price | Float | ✓ | 价格 | 99.99 |
| currency | String | ✓ | 货币 | "USD" |
| effective_date | Date | ○ | 生效日期 | 2023-01-01 |

---

### 5.3 Reimbursement (报销)

**定义**: 医保报销政策。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| reimbursement_id | IRI | ✓ | 唯一标识符 | - |
| policy_type | Enum | ✓ | 政策类型 | full/partial/none |
| coverage_rate | Float | ○ | 报销比例 | 0.8 |

---

### 5.4 Sales (销售)

**定义**: 药品销售数据。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| sales_id | IRI | ✓ | 唯一标识符 | - |
| revenue | Float | ✓ | 销售额 | 1000000 |
| period | String | ✓ | 时间段 | "Q1 2023" |
| units | Integer | ○ | 销售单位 | 50000 |

---

## 六、供应链实体 (supplychain:SupplyChainEntity)

### 6.1 Distribution (分销)

**定义**: 药品分销网络。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| distribution_id | IRI | ✓ | 唯一标识符 | - |
| channel_type | Enum | ✓ | 渠道类型 | retail/hospital/online |

---

### 6.2 Inventory (库存)

**定义**: 药品库存信息。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| inventory_id | IRI | ✓ | 唯一标识符 | - |
| quantity | Integer | ✓ | 库存数量 | 10000 |
| unit | String | ○ | 单位 | "bottles" |

---

### 6.3 Shortage (短缺)

**定义**: 药品短缺事件。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| shortage_id | IRI | ✓ | 唯一标识符 | - |
| start_date | Date | ✓ | 开始日期 | 2023-01-01 |
| reason | String | ○ | 短缺原因 | "manufacturing delay" |
| status | Enum | ✓ | 状态 | active/resolved |

---

### 6.4 Logistics (物流)

**定义**: 药品运输物流信息。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| logistics_id | IRI | ✓ | 唯一标识符 | - |
| shipment_type | Enum | ✓ | 运输方式 | air/ground/sea |
| temperature_requirement | String | ○ | 温控要求 | "2-8°C" |

---

## 七、跨领域实体

### 7.1 Disease (疾病)

**定义**: 疾病或病症。

**核心属性**:
| 属性名 | 数据类型 | 必填 | 描述 | 示例 |
|-------|---------|------|------|------|
| disease_id | IRI | ✓ | 唯一标识符 | MONDO:0002020 |
| name | String | ✓ | 疾病名称 | "migraine" |
| icd10 | String | ○ | ICD-10编码 | "G43" |

**标准参考**:
- MONDO Disease Ontology
- Disease Ontology (DO)
- ICD-10/11
- SNOMED-CT

---

## 实体标识符映射表

| 实体类型 | 主标识符 | 备用标识符 |
|---------|---------|-----------|
| Chemical | InChIKey | PubChem CID, ChEMBL ID, ChEBI ID |
| Gene/Protein | HGNC Symbol | Ensembl ID, Entrez ID, UniProt ID |
| Disease | MONDO ID | DOID, ICD-10, SNOMED-CT, UMLS |
| Drug | RxNorm CUI | DrugBank ID, ATC Code |
| ClinicalTrial | NCT Number | EudraCT, JCTC |
| Publication | DOI | PMID, PMCID |

---

*文档版本: v1.0*
*创建日期: 2026-02-04*
