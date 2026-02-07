#===========================================================
# PharmaKG ETL - 靶点数据转换器
# Pharmaceutical Knowledge Graph - Target Transformer
#===========================================================
# 版本: v1.0
# 描述: 标准化靶点数据，UniProt ID 标准化，蛋白质分类
#===========================================================

import logging
import re
from typing import Dict, Optional, List
from .base import BaseTransformer, TransformationResult, FieldMapping


logger = logging.getLogger(__name__)


class TargetTransformer(BaseTransformer):
    """
    靶点/蛋白质数据转换器

    功能：
    - UniProt ID 标准化
    - 蛋白质分类映射
    - 靶点类型推断
    - 标识符交叉引用
    """

    # 靶点类型映射
    TARGET_TYPE_MAPPING = {
        "enzyme": "Enzyme",
        "receptor": "Receptor",
        "ion channel": "IonChannel",
        "transporter": "Transporter",
        "transcription factor": "TranscriptionFactor",
        "binding protein": "BindingProtein",
        "structural protein": "StructuralProtein"
    }

    def __init__(self, strict_mode: bool = False):
        """初始化靶点转换器"""
        super().__init__(name="TargetTransformer", strict_mode=strict_mode)

        # 字段映射
        self.mapping = FieldMapping(
            mappings={
                # ChEMBL 字段
                "target_chembl_id": "chembl_id",
                "target_pref_name": "name",
                "target_type": "target_class",
                "organism": "organism",
                "species": "species",
                # UniProt 字段
                "accession": "uniprot_id",
                "gene_name": "gene_symbol",
                "protein_name": "name",
                "organism": "organism"
            }
        )

    def transform(self, record: Dict) -> TransformationResult:
        """转换靶点记录"""
        errors = self.validate(record)
        if errors and self.strict_mode:
            return TransformationResult(
                status=TransformationStatus.VALIDATION_ERROR,
                input_record=record,
                output_record=None,
                errors=errors,
                warnings=[],
                metadata={"transformer": self.name}
            )

        try:
            mapped = self.mapping.apply(record)
            normalized = self._normalize_target(mapped)

            validation_errors = self._validate_normalized(normalized)
            if validation_errors:
                return TransformationResult(
                    status=TransformationStatus.VALIDATION_ERROR,
                    input_record=record,
                    output_record=None,
                    errors=validation_errors,
                    warnings=[],
                    metadata={"transformer": self.name}
                )

            return TransformationResult(
                status=TransformationStatus.SUCCESS,
                input_record=record,
                output_record=normalized,
                errors=[],
                warnings=[],
                metadata={"transformer": self.name}
            )

        except Exception as e:
            logger.error(f"Failed to transform target: {e}")
            return TransformationResult(
                status=TransformationStatus.FAILED,
                input_record=record,
                output_record=None,
                errors=[str(e)],
                warnings=[],
                metadata={"transformer": self.name}
            )

    def get_required_fields(self) -> List[str]:
        return ["name"]

    def _normalize_target(self, record: Dict) -> Dict:
        """标准化靶点数据"""
        return {
            "primary_id": self._get_primary_id(record),
            "name": self.normalize_string(record.get("name")),
            "synonyms": self._extract_synonyms(record),
            "gene_symbol": self._normalize_gene_symbol(record.get("gene_symbol")),
            "uniprot_id": self._normalize_uniprot_id(record.get("uniprot_id")),
            "chembl_id": record.get("chembl_id"),
            "target_class": self._normalize_target_class(record.get("target_class")),
            "protein_type": self._infer_protein_type(record),
            "organism": self._normalize_organism(record.get("organism")),
            "species": self._normalize_species(record.get("species")),
            "identifiers": self._normalize_identifiers(record),
            "data_source": record.get("data_source", "unknown")
        }

    def _get_primary_id(self, record: Dict) -> str:
        """获取主键（优先 UniProt）"""
        # UniProt ID 作为主键
        uniprot_id = self._normalize_uniprot_id(record.get("uniprot_id"))
        if uniprot_id:
            return f"uniprot:{uniprot_id}"

        # 备用：ChEMBL
        chembl_id = record.get("chembl_id")
        if chembl_id:
            return f"chembl.target:{chembl_id}"

        # 最终备用：名称
        name = record.get("name")
        if name:
            return f"target:{name.lower().replace(' ', '-')}"

        raise ValueError("Cannot determine target primary identifier")

    def _normalize_uniprot_id(self, uniprot_id: Optional[str]) -> Optional[str]:
        """标准化 UniProt ID"""
        if not uniprot_id:
            return None

        uniprot_id = self.normalize_string(uniprot_id)

        # UniProt ID 格式验证
        if not re.match(r'^[OPQ][0-9A-Z]{3}[0-9A-Z]{1}[0-9A-Z]{3}$', uniprot_id):
            logger.warning(f"Invalid UniProt ID format: {uniprot_id}")
            return None

        return uniprot_id

    def _normalize_gene_symbol(self, symbol: Optional[str]) -> Optional[str]:
        """标准化基因符号"""
        if not symbol:
            return None

        # 基因符号通常大写
        return self.normalize_string(symbol).upper()

    def _normalize_target_class(self, target_class: Optional[str]) -> Optional[str]:
        """标准化靶点分类"""
        if not target_class:
            return None

        # 标准化
        target_class = self.normalize_string(target_class).lower()
        return self.TARGET_TYPE_MAPPING.get(target_class, target_class.title())

    def _infer_protein_type(self, record: Dict) -> Optional[str]:
        """推断蛋白质类型"""
        target_class = record.get("target_class", "").lower()

        if "enzyme" in target_class:
            return "Enzyme"
        elif "receptor" in target_class:
            return "Receptor"
        elif "channel" in target_class:
            return "IonChannel"
        elif "transporter" in target_class:
            return "Transporter"
        elif "factor" in target_class:
            return "TranscriptionFactor"

        return "Protein"

    def _normalize_organism(self, organism: Optional[str]) -> Optional[str]:
        """标准化生物体名称"""
        return self.normalize_string(organism)

    def _normalize_species(self, species: Optional[str]) -> Optional[str]:
        """标准化物种"""
        if not species:
            return None

        species = self.normalize_string(species).lower()

        # 物种映射
        species_mapping = {
            "homo sapiens": "Human",
            "mus musculus": "Mouse",
            "rattus norvegicus": "Rat",
            "danio rerio": "Zebrafish",
            "drosophila melanogaster": "Fruit fly"
        }

        return species_mapping.get(species, species.title())

    def _extract_synonyms(self, record: Dict) -> List[str]:
        """提取同义词"""
        synonyms = []

        # 从各个字段提取
        for field in ["synonyms", "alternative_names", "aliases"]:
            value = record.get(field)
            if isinstance(value, list):
                synonyms.extend(value)
            elif isinstance(value, str):
                synonyms.append(value)

        return list(set(synonyms))

    def _normalize_identifiers(self, record: Dict) -> Dict[str, str]:
        """标准化标识符"""
        identifiers = {}

        primary_id = self._get_primary_id(record)
        identifiers["primary"] = primary_id

        # 各种数据库 ID
        if record.get("uniprot_id"):
            uniprot_id = self._normalize_uniprot_id(record["uniprot_id"])
            if uniprot_id:
                identifiers["uniprot"] = f"uniprot:{uniprot_id}"

        if record.get("chembl_id"):
            identifiers["chembl"] = f"chembl.target:{record['chembl_id']}"

        if record.get("entrez_gene_id"):
            identifiers["entrez.gene"] = f"entrez.gene:{record['entrez_gene_id']}"

        if record.get("ensembl_gene_id"):
            identifiers["ensembl"] = f"ensembl:{record['ensembl_gene_id']}"

        if record.get("hgnc_id"):
            identifiers["hgnc"] = f"hgnc:{record['hgnc_id']}"

        return identifiers

    def _validate_normalized(self, record: Dict) -> List[str]:
        """验证标准化记录"""
        errors = []

        if not record.get("name"):
            errors.append("Missing required field: name")

        # 验证 UniProt ID 格式
        uniprot_id = record.get("uniprot_id")
        if uniprot_id and not re.match(r'^[OPQ][0-9A-Z]{3}[0-9A-Z]{1}[0-9A-Z]{3}$', uniprot_id):
            errors.append(f"Invalid UniProt ID format: {uniprot_id}")

        return errors


class DiseaseTransformer(BaseTransformer):
    """
    疾病数据转换器

    功能：
    - MONDO ID 标准化
    - 疾病本体对齐
    - 治疗领域分类
    - 疾病层次结构
    """

    def __init__(self, strict_mode: bool = False):
        """初始化疾病转换器"""
        super().__init__(name="DiseaseTransformer", strict_mode=strict_mode)

    def transform(self, record: Dict) -> TransformationResult:
        """转换疾病记录"""
        errors = self.validate(record)

        try:
            normalized = self._normalize_disease(record)

            return TransformationResult(
                status=TransformationStatus.SUCCESS,
                input_record=record,
                output_record=normalized,
                errors=errors,
                warnings=[],
                metadata={"transformer": self.name}
            )

        except Exception as e:
            logger.error(f"Failed to transform disease: {e}")
            return TransformationResult(
                status=TransformationStatus.FAILED,
                input_record=record,
                output_record=None,
                errors=[str(e)] + errors,
                warnings=[],
                metadata={"transformer": self.name}
            )

    def get_required_fields(self) -> List[str]:
        return ["name"]

    def _normalize_disease(self, record: Dict) -> Dict:
        """标准化疾病数据"""
        return {
            "primary_id": self._get_primary_id(record),
            "name": self.normalize_string(record.get("name")),
            "synonyms": self._extract_synonyms(record),
            "disease_class": record.get("disease_class"),
            "therapeutic_area": self._normalize_therapeutic_area(record.get("therapeutic_area")),
            "identifiers": self._normalize_identifiers(record),
            "data_source": record.get("data_source", "unknown")
        }

    def _get_primary_id(self, record: Dict) -> str:
        """获取主键（优先 MONDO）"""
        # MONDO ID
        mondo_id = record.get("mondo_id")
        if mondo_id:
            return f"mondo:{mondo_id.lstrip('0')}"

        # DOID
        doid = record.get("doid")
        if doid:
            doid_clean = doid.replace("DOID:", "")
            return f"doid:{doid_clean}"

        # ICD-10/11
        icd_code = record.get("icd_code")
        if icd_code:
            return f"icd10:{icd_code}"

        raise ValueError("Cannot determine disease primary identifier")

    def _normalize_therapeutic_area(self, area: Optional[str]) -> Optional[str]:
        """标准化治疗领域"""
        if not area:
            return None

        area = self.normalize_string(area).lower()

        # 治疗领域映射
        area_mapping = {
            "cardiovascular": "Cardiovascular",
            "oncology": "Oncology",
            "neurology": "Neurology",
            "respiratory": "Respiratory",
            "gastroenterology": "Gastroenterology",
            "endocrinology": "Endocrinology",
            "immunology": "Immunology",
            "infectious": "Infectious Disease"
        }

        return area_mapping.get(area, area.title())

    def _extract_synonyms(self, record: Dict) -> List[str]:
        """提取疾病同义词"""
        synonyms = []

        for field in ["synonyms", "alternative_names", "mesh_terms"]:
            value = record.get(field)
            if isinstance(value, list):
                synonyms.extend(value)
            elif isinstance(value, str):
                synonyms.append(value)

        return list(set(synonyms))

    def _normalize_identifiers(self, record: Dict) -> Dict[str, str]:
        """标准化疾病标识符"""
        identifiers = {}

        # 各种本体 ID
        if record.get("mondo_id"):
            mondo_clean = record["mondo_id"].lstrip('0')
            identifiers["mondo"] = f"mondo:{mondo_clean}"

        if record.get("doid"):
            doid_clean = record["doid"].replace("DOID:", "")
            identifiers["doid"] = f"doid:{doid_clean}"

        if record.get("icd_code"):
            identifiers["icd10"] = f"icd10:{record['icd_code']}"

        if record.get("mesh_id"):
            identifiers["mesh"] = f"mesh:{record['mesh_id']}"

        if record.get("snomedct_id"):
            identifiers["snomedct"] = f"snomedct:{record['snomedct_id']}"

        if record.get("umls_cui"):
            identifiers["umls"] = f"umls:{record['umls_cui']}"

        return identifiers
