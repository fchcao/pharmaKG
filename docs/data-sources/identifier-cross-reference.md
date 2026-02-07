# PharmaKG 标识符交叉引用规范

## 一、标识符命名空间定义

### 1.1 命名空间前缀规范

所有标识符使用 `namespace:value` 格式，确保全局唯一性和可解析性。

```
格式: <prefix>:<identifier>

示例:
  chembl:CHEMBL25
  uniprot:P35354
  mondo:0002020
  nct:NCT000001
```

### 1.2 官方命名空间注册表

| 前缀 | 注册机构 | URI 模板 | 示例 |
|------|---------|---------|------|
| chembl | ChEMBL | https://www.ebi.ac.uk/chembl/compound_report_card/{id} | chembl:CHEMBL25 |
| drugbank | DrugBank | https://go.drugbank.com/drugs/{id} | drugbank:DB00945 |
| pubchem | PubChem | https://pubchem.ncbi.nlm.nih.gov/compound/{id} | pubchem.cid:2158 |
| uniprot | UniProt | https://www.uniprot.org/uniprot/{id} | uniprot:P35354 |
| ensembl | Ensembl | https://www.ensembl.org/Gene/Summary?g={id} | ensembl:ENSG00000141510 |
| entrez | NCBI | https://www.ncbi.nlm.nih.gov/gene/{id} | entrez.gene:6654 |
| hgnc | HGNC | https://www.genenames.org/data/hgnc_data.php?hgnc_id={id} | hgnc:8825 |
| mondo | MONDO | https://mondo.monarchinitiative.org/disease/MONDO:{id} | mondo:0002020 |
| doid | DOID | https://disease-ontology.org/DOID:{id} | doid:9351 |
| icd10 | WHO | https://icd.who.int/browse10/2019/en#/I10 | icd10:I10 |
| icd11 | WHO | https://icd.who.int/browse11/l-m/en/{id} | icd11:BD10.0 |
| snomedct | SNOMED | https://confluence.ihtsdotools.org/ | snomedct:263811008 |
| mesh | MeSH | https://www.ncbi.nlm.nih.gov/mesh/{id} | mesh:D015994 |
| nct | ClinicalTrials.gov | https://clinicaltrials.gov/ct2/show/{id} | nct:NCT000001 |
| eudract | EMA | https://www.clinicaltrialsregister.eu/ctr-search/trial/{id} | eudract:2005-004016-26 |
| rxnorm | RxNorm | https://mor.nlm.nih.gov/RxNorm/search?query={id} | rxnorm:2555 |
| unii | FDA | https://fda.gov/UNII/{id} | unii:R16CO5Y76E |

---

## 二、化合物标识符映射

### 2.1 主键选择

**主键**: InChIKey (Standardized InChI Key)

```cypher
// 化合物节点结构
(:Compound {
  primary_id: "inchikey:BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
  inchikey: "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
  name: "Aspirin",
  smiles: "CC(=O)OC1=CC=CC=C1C(=O)O",
  standard_inchi: "InChI=1S/C9H8O4/c1-6-13-8-5-9(11)12-7(6)4-2-3-10(12)13-13/h2-5H,1H3,(H,11,12)"
})
```

### 2.2 交叉引用属性

```cypher
// 标识符交叉引用
(:Compound)-[:HAS_IDENTIFIER]->(:CompoundIdentifier {
  namespace: "chembl",
  id: "CHEMBL25",
  url: "https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL25"
})

(:Compound)-[:HAS_IDENTIFIER]->(:CompoundIdentifier {
  namespace: "drugbank",
  id: "DB00945",
  url: "https://go.drugbank.com/drugs/DB00945"
})

(:Compound)-[:HAS_IDENTIFIER]->(:CompoundIdentifier {
  namespace: "pubchem.cid",
  id: "2158",
  url: "https://pubchem.ncbi.nlm.nih.gov/compound/2158"
})
```

### 2.3 标识符优先级

| 优先级 | 标识符 | 特点 | 来源 |
|-------|--------|------|------|
| P0 | InChIKey | 唯一、标准化 | IUPAC |
| P1 | ChEMBL ID | R&D 数据丰富 | EMBL-EBI |
| P1 | DrugBank ID | 药物信息全面 | DrugBank |
| P2 | PubChem CID | 化学数据 | NCBI |
| P2 | UNII | FDA 标准 | FDA |
| P3 | CAS RN | 化学文摘 | CAS |

---

## 三、靶点/蛋白质标识符映射

### 3.1 主键选择

**主键**: UniProt Accession (推荐) 或 Ensembl Gene ID

```cypher
// 靶点节点结构
(:Target {
  primary_id: "uniprot:P35354",
  name: "Prostaglandin G/H synthase 2",
  target_class: "Enzyme",
  protein_type: "Cyclooxygenase"
})
```

### 3.2 交叉引用属性

```cypher
(:Target)-[:HAS_IDENTIFIER]->(:TargetIdentifier {
  namespace: "uniprot",
  id: "P35354",
  url: "https://www.uniprot.org/uniprot/P35354"
})

(:Target)-[:HAS_IDENTIFIER]->(:TargetIdentifier {
  namespace: "ensembl.gene",
  id: "ENSG00000141510",
  url: "https://www.ensembl.org/Gene/Summary?g=ENSG00000141510"
})

(:Target)-[:HAS_IDENTIFIER]->(:TargetIdentifier {
  namespace: "entrez.gene",
  id: "6654",
  url: "https://www.ncbi.nlm.nih.gov/gene/6654"
})

(:Target)-[:HAS_IDENTIFIER]->(:TargetIdentifier {
  namespace: "hgnc",
  id: "8825",
  gene_symbol: "PTGS2"
})
```

### 3.3 靶点类型标识符

| 靶点类型 | 推荐标识符 | 备选标识符 |
|---------|-----------|-----------|
| 酶 | UniProt | EC Number |
| 受体 | UniProt | IUPHAR |
| 离子通道 | UniProt | ChEMBL Target |
| 转运体 | UniProt | TCDB |
| 转录因子 | UniProt | TFClass |

---

## 四、疾病标识符映射

### 4.1 主键选择

**主键**: MONDO ID (Monarch Disease Ontology)

```cypher
// 疾病节点结构
(:Disease {
  primary_id: "mondo:0002020",
  name: "Essential hypertension",
  disease_class: "Cardiovascular disease",
  therapeutic_area: "Cardiovascular"
})
```

### 4.2 交叉引用属性

```cypher
(:Disease)-[:HAS_IDENTIFIER]->(:DiseaseIdentifier {
  namespace: "mondo",
  id: "0002020",
  url: "https://mondo.monarchinitiative.org/disease/MONDO:0002020"
})

(:Disease)-[:HAS_IDENTIFIER]->(:DiseaseIdentifier {
  namespace: "doid",
  id: "DOID:9351",
  url: "https://disease-ontology.org/DOID:9351"
})

(:Disease)-[:HAS_IDENTIFIER]->(:DiseaseIdentifier {
  namespace: "icd10",
  id: "I10",
  description: "Essential (primary) hypertension"
})

(:Disease)-[:HAS_IDENTIFIER]->(:DiseaseIdentifier {
  namespace: "snomedct",
  id: "263811008",
  description: "Essential hypertension"
})

(:Disease)-[:HAS_IDENTIFIER]->(:DiseaseIdentifier {
  namespace: "mesh",
  id: "D015994",
  description: "Hypertension"
})
```

### 4.3 疾病本体层次

```
MONDO (主)
├── DOID (疾病本体)
│   ├── 罕见病
│   └── 常见疾病
├── ICD-10/11 (临床编码)
│   ├── 诊断编码
│   └── 死因编码
├── SNOMED-CT (临床术语)
├── MeSH (医学主题词)
└── Orphanet (罕见病)
```

---

## 五、临床试验标识符映射

### 5.1 主键选择

**主键**: NCT Number (ClinicalTrials.gov)

```cypher
// 临床试验节点结构
(:ClinicalTrial {
  primary_id: "nct:NCT000001",
  trial_id: "NCT000001",
  title: "Methylprednisolone vs. Placebo in Traumatic Brain Injury",
  phase: "Phase 3",
  status: "Completed"
})
```

### 5.2 交叉引用属性

```cypher
(:ClinicalTrial)-[:HAS_IDENTIFIER]->(:TrialIdentifier {
  namespace: "nct",
  id: "NCT000001",
  url: "https://clinicaltrials.gov/ct2/show/NCT000001"
})

(:ClinicalTrial)-[:HAS_IDENTIFIER]->(:TrialIdentifier {
  namespace: "eudract",
  id: "2005-004016-26",
  url: "https://www.clinicaltrialsregister.eu/ctr-search/trial/2005-004016-26"
})

(:ClinicalTrial)-[:HAS_IDENTIFIER]->(:TrialIdentifier {
  namespace: "jctc",
  id: "JCTC-I000001",
  url: "https://jrct.niph.go.jp/en-latest/detail/JCTC-I000001"
})
```

### 5.3 试验注册库映射

| 注册库 | 前缀 | 地理覆盖 | 标识符格式 |
|--------|------|---------|-----------|
| ClinicalTrials.gov | nct | 全球 | NCT######## |
| EudraCT | eudract | 欧洲 | YYYY-NNNNNN-NN |
| JCTC | jctc | 日本 | JCTC-I###### |
| CTRI | ctri | 印度 | CTRI/YYYY/MM/NNNN |
| ChiCTR | chictr | 中国 | ChiCTRNNNNNNN |

---

## 六、监管申报标识符映射

### 6.1 FDA 申报标识符

```cypher
// FDA 申报节点
(:Submission {
  primary_id: "fda.nda:022568",
  submission_id: "NDA 022568",
  submission_type: "NDA",
  submission_date: "2011-07-18",
  sponsor: "Pfizer Inc."
})
```

### 6.2 FDA 申报类型

| 类型 | 前缀 | 全称 | 用途 |
|------|------|------|------|
| NDA | fda.nda | New Drug Application | 新药申请 |
| ANDA | fda.anda | Abbreviated NDA | 仿制药申请 |
| BLA | fda.bla | Biologics License Application | 生物制品申请 |
| sNDA | fda.snda | Supplemental NDA | 补充申请 |
| 505(b)(2) | fda.505b2 | 505(b)(2) Application | 改剂型申请 |

### 6.3 EMA 申报标识符

```cypher
(:Submission {
  primary_id: "ema.ma:EU/1/00/000/EMEA/H/C",
  submission_id: "EU/1/00/000/EMEA/H/C",
  submission_type: "MA",
  procedure: "Centralized",
  submission_date: "2000-01-01"
})
```

---

## 七、标识符解析服务

### 7.1 解析 API 设计

```python
class IdentifierResolver:
    """标识符解析服务"""

    def resolve(self, identifier: str) -> Dict:
        """
        解析标识符，返回标准化信息

        Args:
            identifier: 标识符字符串 (如 "chembl:CHEMBL25")

        Returns:
            {
                "namespace": "chembl",
                "id": "CHEMBL25",
                "url": "https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL25",
                "canonical_id": "inchikey:BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                "entity_type": "Compound"
            }
        """
        pass

    def map_to_canonical(self, identifier: str, entity_type: str) -> str:
        """
        将任意标识符映射到规范标识符

        Args:
            identifier: 输入标识符
            entity_type: 实体类型

        Returns:
            规范标识符
        """
        pass
```

### 7.2 批量解析

```python
def batch_resolve(identifiers: List[str]) -> Dict[str, Dict]:
    """
    批量解析标识符

    Args:
        identifiers: 标识符列表

    Returns:
        {identifier: resolved_info, ...}
    """
    pass
```

---

## 八、标识符映射表存储

### 8.1 映射表结构

```cypher
// 标识符映射节点
(:IdentifierMapping {
  canonical_id: "inchikey:BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
  entity_type: "Compound",
  identifiers: [
    "chembl:CHEMBL25",
    "drugbank:DB00945",
    "pubchem.cid:2158",
    "unii:R16CO5Y76E",
    "rxnorm:2555"
  ],
  last_updated: "2025-02-06T00:00:00Z"
})
```

### 8.2 映射关系

```cypher
// 化合物与其标识符的关系
(:Compound)-[:HAS_CANONICAL_ID]->(:IdentifierMapping)
(:CompoundIdentifier)-[:MAPS_TO]->(:IdentifierMapping)
```

---

## 九、标识符验证规则

### 9.1 格式验证

| 标识符类型 | 正则表达式 | 示例 |
|-----------|-----------|------|
| ChEMBL ID | `^CHEMBL\d+$` | CHEMBL25 |
| DrugBank ID | `^DB\d{5}$` | DB00945 |
| PubChem CID | `^\d+$` | 2158 |
| UniProt | `^[OPQ][0-9A-Z]{3}[0-9A-Z]{1}[0-9A-Z]{3}$` | P35354 |
| Ensembl Gene | `^ENSG\d{11}$` | ENSG00000141510 |
| MONDO | `^\d{7}$` | 0002020 |
| NCT Number | `^NCT\d{8}$` | NCT000001 |
| FDA NDA | `^\d{6}$` | 022568 |
| InChIKey | `^[A-Z]{14}-[A-Z]{10}-[A-Z]$` | BSYNRYMUTXBXSQ-UHFFFAOYSA-N |

### 9.2 校验位验证

```python
def validate_uniprot_id(accession: str) -> bool:
    """验证 UniProt Accession 格式"""
    import re
    pattern = r'^[OPQ][0-9A-Z]{3}[0-9A-Z]{1}[0-9A-Z]{3}$'
    return bool(re.match(pattern, accession))

def validate_inchikey(inchikey: str) -> bool:
    """验证 InChIKey 格式和校验位"""
    import re
    pattern = r'^[A-Z]{14}-[A-Z]{10}-[A-Z]$'
    if not re.match(pattern, inchikey):
        return False
    # 校验位验证（第一段）
    # ... 实际校验逻辑
    return True
```

---

## 十、标识符服务 API

### 10.1 查询端点

```
GET /api/identifiers/resolve?identifier=chembl:CHEMBL25
GET /api/identifiers/map?identifier=CHEMBL25&target_namespace=inchikey
GET /api/identifiers/crossref?namespace=chembl&id=CHEMBL25
```

### 10.2 响应格式

```json
{
  "input": "chembl:CHEMBL25",
  "resolved": {
    "namespace": "chembl",
    "id": "CHEMBL25",
    "url": "https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL25"
  },
  "canonical_id": "inchikey:BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
  "cross_references": [
    {"namespace": "drugbank", "id": "DB00945"},
    {"namespace": "pubchem.cid", "id": "2158"},
    {"namespace": "unii", "id": "R16CO5Y76E"}
  ],
  "entity": {
    "type": "Compound",
    "name": "Aspirin",
    "primary_id": "inchikey:BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
  }
}
```

---

## 十一、数据更新与维护

### 11.1 映射表更新

- **MONDO**: 每月更新
- **UniProt**: 每周更新
- **ChEMBL**: 季度更新
- **RxNorm**: 每周更新

### 11.2 映射质量监控

- 孤立标识符检测
- 一对多映射检查
- 映射循环检测
- 过期标识符清理

---

## 十二、最佳实践

### 12.1 标识符使用建议

1. **始终使用规范标识符作为主键**
2. **保留原始标识符作为交叉引用**
3. **记录标识符来源和更新时间**
4. **使用命名空间前缀避免歧义**
5. **定期更新标识符映射表**

### 12.2 错误处理

- 无法解析的标识符记录到错误日志
- 保留原始标识符字符串
- 提供手动审核机制
- 建立标识符黑名单
