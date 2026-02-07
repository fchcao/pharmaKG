# PharmaKG 数据源映射策略

## 一、数据源清单

### 1.1 R&D 领域数据源

| 数据源 | 覆盖范围 | 访问方式 | 更新频率 | 许可证 |
|--------|---------|---------|---------|--------|
| **ChEMBL** | 化合物、靶点、生物活性 | REST API | 季度 | CC0 1.0 |
| **DrugBank** | 药物、靶点、通路 | XML (需认证) | 季度 | 学术许可 |
| **PubChem** | 化学结构、生物测定 | REST API | 每月 | PD |
| **UniProt** | 蛋白质/靶点 | REST API | 每周 | CC BY 4.0 |
| **KEGG** | 通路、疾病 | REST API | 每月 | 学术许可 |
| **Open Targets** | 靶点-疾病关联 | REST API | 每月 | CC BY 4.0 |
| **BindingDB** | 结合亲和力数据 | 下载 | 季度 | CC0 1.0 |

### 1.2 临床领域数据源

| 数据源 | 覆盖范围 | 访问方式 | 更新频率 | 许可证 |
|--------|---------|---------|---------|--------|
| **ClinicalTrials.gov** | 临床试验 | API v2 | 每日 | PD |
| **EudraCT** | 欧洲试验 | API | 每周 | EMA |
| **JCTC** | 日本试验 | API | 每月 | PMDA |
| **ICMJE** | 试验注册 | 抓取 | 每月 | - |
| **WHO ICTRP** | 国际试验注册 | API | 每月 | WHO |

### 1.3 供应链领域数据源

| 数据源 | 覆盖范围 | 访问方式 | 更新频率 | 许可证 |
|--------|---------|---------|---------|--------|
| **FDA Drug Shortages** | 美国药品短缺 | API/RSS | 每周 | HHS |
| **EMA Shortages** | 欧洲药品短缺 | 下载 | 每月 | EMA |
| **Drug.com** | 制造商信息 | 抓取 | 每月 | - |
| **Pharmacompass** | 制药公司 | 抓取 | 每月 | - |
| **Orange Book** | 仿制药 | 下载 | 每月 | FDA |

### 1.4 监管领域数据源

| 数据源 | 覆盖范围 | 访问方式 | 更新频率 | 许可证 |
|--------|---------|---------|---------|--------|
| **Drugs@FDA** | 批准产品 | 下载 | 每月 | FDA |
| **EMA EPAR** | 欧洲批准 | 下载 | 每月 | EMA |
| **PMDA** | 日本批准 | 下载 | 每月 | PMDA |
| **FDA Adverse Events** | 不良事件 | API | 每月 | FDA |
| **FAERS** | 不良事件报告 | 下载 | 每季度 | FDA |

---

## 二、标识符映射策略

### 2.1 化合物标识符

| 标识符类型 | 命名空间 | 用途 | 优先级 |
|-----------|---------|------|-------|
| **InChIKey** | `inchikey:` | 主键（标准化） | P0 |
| **ChEMBL ID** | `chembl:` | R&D 数据 | P1 |
| **DrugBank ID** | `drugbank:` | 药物数据 | P1 |
| **PubChem CID** | `pubchem.cid:` | 化学数据 | P2 |
| **UNII** | `unii:` | FDA 标识符 | P2 |
| **CAS RN** | `cas:` | 化学文摘社 | P3 |
| **RxNorm CUI** | `rxnorm:` | 临床药物 | P1 |

**映射规则**：
- 主键使用 InChIKey（唯一且标准化）
- ChEMBL 和 DrugBank 作为主要交叉引用
- PubChem CID 用于扩展化学信息
- RxNorm CUI 用于临床数据连接

### 2.2 靶点/蛋白质标识符

| 标识符类型 | 命名空间 | 用途 | 优先级 |
|-----------|---------|------|-------|
| **UniProt Accession** | `uniprot:` | 主键 | P0 |
| **Ensembl Gene ID** | `ensembl:` | 基因数据 | P1 |
| **Entrez Gene ID** | `entrez.gene:` | NCBI 数据 | P1 |
| **HGNC Symbol** | `hgnc:` | 基因符号 | P2 |
| **RefSeq** | `refseq:` | 参考序列 | P2 |
| **ChEMBL Target ID** | `chembl.target:` | R&D 数据 | P2 |

**映射规则**：
- 主键使用 UniProt Accession
- Ensembl Gene ID 连接基因组数据
- HGNC Symbol 用于用户友好显示

### 2.3 疾病标识符

| 标识符类型 | 命名空间 | 用途 | 优先级 |
|-----------|---------|------|-------|
| **MONDO ID** | `mondo:` | 主键（标准化） | P0 |
| **DOID** | `doid:` | 疾病本体 | P1 |
| **ICD-10** | `icd10:` | 临床编码 | P1 |
| **ICD-11** | `icd11:` | WHO 标准 | P1 |
| **SNOMED-CT** | `snomedct:` | 临床术语 | P2 |
| **MeSH** | `mesh:` | 医学主题词 | P2 |
| **Orphanet** | `orphanet:` | 罕见病 | P2 |
| **UMLS CUI** | `umls:` | 统一医学语言 | P2 |

**映射规则**：
- MONDO ID 作为主键（整合多个本体）
- DOID 作为疾病本体基础
- ICD-10/11 用于临床应用

### 2.4 临床试验标识符

| 标识符类型 | 命名空间 | 用途 | 优先级 |
|-----------|---------|------|-------|
| **NCT Number** | `nct:` | ClinicalTrials.gov | P0 |
| **EudraCT Number** | `eudract:` | 欧洲试验 | P1 |
| **JCTC Number** | `jctc:` | 日本试验 | P1 |
| **CTRI** | `ctri:` | 印度试验 | P2 |
| **ChiCTR** | `chictr:` | 中国试验 | P2 |

### 2.5 监管标识符

| 标识符类型 | 命名空间 | 用途 | 优先级 |
|-----------|---------|------|-------|
| **FDA NDA/ANDA** | `fda.nda:`, `fda.anda:` | FDA 申报 | P0 |
| **EMA MA** | `ema.ma:` | EMA 市场授权 | P0 |
| **PMDA Approval** | `pmda:` | 日本批准 | P1 |
| **UNII** | `unii:` | 唯一成分标识 | P1 |

---

## 三、跨数据源映射表

### 3.1 化合物交叉引用

```cypher
// 化合物标识符映射节点示例
(:CompoundIdentifier {
  primary_id: "inchikey:BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
  identifiers: {
    inchikey: "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
    chembl: "CHEMBL25",
    drugbank: "DB00945",
    pubchem_cid: "2158",
    unii: "R16CO5Y76E",
    rxnorm_cui: "2555"
  },
  name: "Aspirin"
})
```

### 3.2 靶点交叉引用

```cypher
// 靶点标识符映射节点示例
(:TargetIdentifier {
  primary_id: "uniprot:P35354",
  identifiers: {
    uniprot: "P35354",
    ensembl_gene: "ENSG00000141510",
    entrez_gene: "6654",
    hgnc_symbol: "PTGS2",
    chembl_target: "CHEMBL230",
    refseq: "NP_000953"
  },
  name: "Prostaglandin G/H synthase 2",
  target_class: "Enzyme"
})
```

### 3.3 疾病交叉引用

```cypher
// 疾病标识符映射节点示例
(:DiseaseIdentifier {
  primary_id: "mondo:0002020",
  identifiers: {
    mondo: "0002020",
    doid: "DOID:9351",
    icd10: "I10",
    icd11: "BD10.0",
    snomedct: "263811008",
    mesh: "D015994",
    umls_cui: "C0020538"
  },
  name: "Essential hypertension",
  therapeutic_area: "Cardiovascular"
})
```

---

## 四、数据优先级与导入顺序

### 4.1 数据源优先级

**Tier 1（核心数据源）** - 必须导入：
- ChEMBL（R&D 核心数据）
- ClinicalTrials.gov（临床核心数据）
- Drugs@FDA（监管核心数据）

**Tier 2（重要数据源）** - 强烈建议：
- DrugBank（补充药物信息）
- UniProt（蛋白质数据）
- Open Targets（靶点-疾病关联）
- FDA Drug Shortages（供应链数据）

**Tier 3（扩展数据源）** - 可选：
- PubChem（化学结构扩展）
- KEGG（通路数据）
- EMA 数据（欧洲监管数据）
- FAERS（不良事件详细数据）

### 4.2 导入顺序

```
1. 基础本体数据
   ├── 化合物（ChEMBL）
   ├── 靶点（UniProt + ChEMBL targets）
   └── 疾病（MONDO + DOID）

2. 标识符映射
   ├── 化合物交叉引用
   ├── 靶点交叉引用
   └── 疾病交叉引用

3. 关系数据
   ├── 化合物-靶点关系
   ├── 靶点-疾病关系
   └── 化合物-疾病关系

4. 临床数据
   ├── 临床试验
   ├── 受试者
   └── 不良事件

5. 供应链数据
   ├── 制造商
   └── 药品短缺

6. 监管数据
   ├── 申报
   └── 批准
```

---

## 五、数据更新策略

### 5.1 增量更新

| 数据源 | 增量更新标识 | 更新检测方法 |
|--------|-------------|-------------|
| ChEMBL | `last_Updated` | API 查询参数 |
| ClinicalTrials.gov | `lastUpdateDate` | API 查询参数 |
| Drugs@FDA | `submissionDate` | 文件时间戳 |
| UniProt | `entry_version` | API 版本检查 |

### 5.2 全量更新

对于不支持增量更新的数据源，采用：
- 基于时间戳的合并策略
- `last_seen` 属性跟踪
- 定期全量刷新（月度/季度）

### 5.3 更新频率建议

| 数据类型 | 更新频率 | 窗口期 |
|---------|---------|-------|
| 核心参考数据 | 月度 | 每月第一周 |
| 临床试验 | 每周 | 周日夜间 |
| 药品短缺 | 每周 | 周一凌晨 |
| 监管数据 | 月度 | 每月第二周 |
| 标识符映射 | 季度 | 每季度首月 |

---

## 六、数据质量保证

### 6.1 验证规则

1. **完整性检查**
   - 必填字段非空
   - 标识符格式验证
   - 关系完整性

2. **准确性检查**
   - 数值范围验证
   - 日期逻辑验证
   - 枚举值检查

3. **一致性检查**
   - 跨源一致性
   - 标识符映射一致性
   - 关系方向一致性

4. **时效性检查**
   - 数据新鲜度监控
   - 过期数据标识
   - 更新延迟告警

### 6.2 错误处理

- 记录所有导入错误
- 支持部分导入失败恢复
- 错误数据隔离存储
- 人工审核队列

---

## 七、API 访问配置

### 7.1 需要认证的数据源

| 数据源 | 认证方式 | 环境变量 |
|--------|---------|---------|
| DrugBank | API Key | `DRUGBANK_API_KEY` |
| ChEMBL (High volume) | API Key | `CHEMBL_API_KEY` |
| UMLS | API Key | `UMLS_API_KEY` |
| KEGG | License | `KEGG_LICENSE_ID` |

### 7.2 速率限制

| 数据源 | 速率限制 | 策略 |
|--------|---------|------|
| ChEMBL | 无限制 | - |
| PubChem | 5 req/sec | 延迟循环 |
| ClinicalTrials.gov | 建议延迟 | 1 req/0.5 sec |
| UniProt | 无限制 | - |

---

## 八、存储与备份

### 8.1 原始数据存储

```
data/
├── raw/
│   ├── chembl/
│   │   ├── chembl_30_dump.tar.gz
│   │   └── molecules/
│   ├── clinicaltrials/
│   │   └── study_fields/
│   └── fda/
│       └── drugsatfda/
├── processed/
│   ├── transformed/
│   └── validated/
└── backups/
    ├── weekly/
    └── monthly/
```

### 8.2 版本控制

- 原始数据快照
- 变更日志
- 可回滚机制

---

## 九、隐私与合规

### 9.1 数据使用许可

| 数据源 | 商业使用 | 再分发 | 修改 | 归属要求 |
|--------|---------|-------|------|---------|
| ChEMBL | ✅ | ✅ | ✅ | - |
| DrugBank (学术) | ❌ | ❌ | ✅ | ✅ |
| PubChem | ✅ | ✅ | ✅ | - |
| ClinicalTrials.gov | ✅ | ✅ | ✅ | - |
| UniProt | ✅ | ✅ | ✅ | ✅ |

### 9.2 GDPR 考虑

- 临床数据脱敏
- 患者隐私保护
- 数据处理记录
- 跨境传输合规

---

## 十、下一步行动

1. ✅ 创建数据源目录结构
2. ⏳ 开发基础抽取器框架
3. ⏳ 实现首个 ETL 管道（ChEMBL）
4. ⏳ 建立标识符映射服务
5. ⏳ 开发数据质量检查
