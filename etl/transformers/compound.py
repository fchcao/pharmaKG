#===========================================================
# PharmaKG ETL - 化合物数据转换器
# Pharmaceutical Knowledge Graph - Compound Transformer
#===========================================================
# 版本: v1.0
# 描述: 标准化化合物数据，计算描述符，标识符映射
#===========================================================

import logging
import re
from typing import Dict, Optional, List, Any
from .base import BaseTransformer, TransformationResult, FieldMapping


logger = logging.getLogger(__name__)


class CompoundTransformer(BaseTransformer):
    """
    化合物数据转换器

    功能：
    - 标准化分子结构（SMILES, InChI）
    - 计算分子描述符
    - 标识符映射到 InChIKey
    - 数据验证
    """

    def __init__(self, strict_mode: bool = False):
        """初始化化合物转换器"""
        super().__init__(name="CompoundTransformer", strict_mode=strict_mode)

        # 字段映射配置
        self.mapping = FieldMapping(
            mappings={
                # ChEMBL 字段映射
                "chembl_id": "primary_id",
                "pref_name": "name",
                "molecule_structures": "structures",
                "molecule_properties": "properties",
                "max_phase": "clinical_phase",
                "therapeutic_flag": "is_approved",
                # DrugBank 字段映射
                "drugbank_id": "identifiers.drugbank",
                "name": "name",
                "smiles": "smiles",
                "inchikey": "inchikey",
                "cas_number": "identifiers.cas",
                "unii": "identifiers.unii",
                "properties": "properties"
            }
        )

    def transform(self, record: Dict) -> TransformationResult:
        """
        转换化合物记录

        Args:
            record: 原始化合物数据

        Returns:
            转换结果
        """
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
            # 应用字段映射
            mapped = self.mapping.apply(record)

            # 标准化处理
            normalized = self._normalize_compound(mapped)

            # 验证标准化结果
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
            logger.error(f"Failed to transform compound: {e}")
            return TransformationResult(
                status=TransformationStatus.FAILED,
                input_record=record,
                output_record=None,
                errors=[str(e)],
                warnings=[],
                metadata={"transformer": self.name}
            )

    def get_required_fields(self) -> List[str]:
        """获取必需字段"""
        return ["name"]  # 至少需要名称

    def _normalize_compound(self, record: Dict) -> Dict:
        """
        标准化化合物数据

        Args:
            record: 映射后的记录

        Returns:
            标准化的化合物数据
        """
        # 基础字段标准化
        normalized = {
            "primary_id": self._get_primary_id(record),
            "name": self.normalize_string(record.get("name")),
            "smiles": self._normalize_smiles(record.get("smiles")),
            "inchikey": self._normalize_inchikey(record.get("inchikey")),
            "standard_inchi": record.get("standard_inchi"),
            "molecular_formula": record.get("molecular_formula"),
            "molecular_weight": self._normalize_molecular_weight(record.get("molecular_weight")),
            "is_parent": record.get("is_parent", True),
            "clinical_phase": self._normalize_phase(record.get("clinical_phase")),
            "is_approved": self._normalize_approved_flag(record.get("is_approved")),
            "therapeutic_areas": self._extract_therapeutic_areas(record),
            "identifiers": self._normalize_identifiers(record),
            "properties": record.get("properties", {}),
            "structures": record.get("structures", {}),
            "ro5_violations": record.get("ro5_violations", 0),
            "data_source": record.get("data_source", "unknown"),
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at")
        }

        return normalized

    def _get_primary_id(self, record: Dict) -> str:
        """
        获取主键（优先使用 InChIKey）

        Args:
            record: 记录

        Returns:
            主键标识符
        """
        # 优先使用 InChIKey
        inchikey = self._normalize_inchikey(record.get("inchikey"))
        if inchikey:
            return f"inchikey:{inchikey}"

        # 备用：使用原始 ID
        original_id = record.get("primary_id") or record.get("chembl_id")
        if original_id:
            return f"{record.get('data_source', 'unknown')}:{original_id}"

        # 最终备用：使用名称（不推荐）
        name = record.get("name")
        if name:
            # 从名称生成简单的 ID
            return f"compound:{name.lower().replace(' ', '-')}"

        raise ValueError("Cannot determine primary identifier")

    def _normalize_smiles(self, smiles: Optional[str]) -> Optional[str]:
        """
        标准化 SMILES

        Args:
            smiles: SMILES 字符串

        Returns:
            标准化的 SMILES
        """
        if not smiles:
            return None

        smiles = self.normalize_string(smiles)

        # 基本验证
        if not self._is_valid_smiles(smiles):
            logger.warning(f"Invalid SMILES format: {smiles}")
            return None

        return smiles

    def _is_valid_smiles(self, smiles: str) -> bool:
        """
        基本 SMILES 格式验证

        Args:
            smiles: SMILES 字符串

        Returns:
            是否有效
        """
        if not smiles or len(smiles) == 0:
            return False

        # SMILES 中的有效字符
        valid_chars = set("CNOPSFBrClI[]()=+#-.0123456789nso@%")
        return all(c in valid_chars for c in smiles)

    def _normalize_inchikey(self, inchikey: Optional[str]) -> Optional[str]:
        """
        标准化 InChIKey

        Args:
            inchikey: InChIKey 字符串

        Returns:
            标准化的 InChIKey
        """
        if not inchikey:
            return None

        inchikey = self.normalize_string(inchikey)

        # 验证格式：XX-XXX-X-XX
        if not re.match(r'^[A-Z]{14}-[A-Z]{10}-[A-Z]$', inchikey):
            logger.warning(f"Invalid InChIKey format: {inchikey}")
            return None

        return inchikey

    def _normalize_molecular_weight(self, mw: Any) -> Optional[float]:
        """
        标准化分子量

        Args:
            mw: 分子量

        Returns:
            标准化的分子量
        """
        return self.extract_numeric(mw)

    def _normalize_phase(self, phase: Any) -> Optional[str]:
        """
        标准化临床试验阶段

        Args:
            phase: 阶段值

        Returns:
            标准化的阶段
        """
        if phase is None:
            return None

        phase = str(phase).strip().upper()

        # 阶段映射
        phase_mapping = {
            "0": "Discovery",
            "1": "Phase 1",
            "2": "Phase 2",
            "3": "Phase 3",
            "4": "Phase 4",
            "APPROVED": "Approved",
            "LAUNCHED": "Launched"
        }

        return phase_mapping.get(phase, phase)

    def _normalize_approved_flag(self, flag: Any) -> bool:
        """
        标准化批准标志

        Args:
            flag: 批准标志

        Returns:
            是否已批准
        """
        if flag is None:
            return False

        if isinstance(flag, bool):
            return flag

        flag_str = str(flag).strip().lower()
        return flag_str in ("true", "1", "yes", "approved", "launched")

    def _extract_therapeutic_areas(self, record: Dict) -> List[str]:
        """
        提取治疗领域

        Args:
            record: 记录

        Returns:
            治疗领域列表
        """
        areas = []

        # 从适应症提取
        indications = record.get("indications", [])
        if isinstance(indications, list):
            for ind in indications:
                if isinstance(ind, dict):
                    category = ind.get("category")
                    if category:
                        areas.append(category)
                elif isinstance(ind, str):
                    areas.append(ind)

        # 从分类提取
        categories = record.get("categories", [])
        if isinstance(categories, list):
            for cat in categories:
                if isinstance(cat, dict):
                    areas.append(cat.get("category"))
                elif isinstance(cat, str):
                    areas.append(cat)

        # 去重
        return list(set(areas))

    def _normalize_identifiers(self, record: Dict) -> Dict[str, str]:
        """
        标准化标识符映射

        Args:
            record: 记录

        Returns:
            标识符字典
        """
        identifiers = {}

        # 主键
        primary_id = self._get_primary_id(record)
        identifiers["primary"] = primary_id

        # 化学标识符
        if record.get("inchikey"):
            identifiers["inchikey"] = self._normalize_inchikey(record["inchikey"])
        if record.get("chembl_id"):
            identifiers["chembl"] = f"chembl:{record['chembl_id']}"
        if record.get("drugbank_id"):
            identifiers["drugbank"] = f"drugbank:{record['drugbank_id']}"
        if record.get("cas_number"):
            identifiers["cas"] = record["cas_number"]
        if record.get("unii"):
            identifiers["unii"] = record["unii"]

        # 从嵌套结构提取
        if isinstance(record.get("identifiers"), dict):
            for key, value in record["identifiers"].items():
                if key not in identifiers and value:
                    identifiers[key] = value

        return identifiers

    def _validate_normalized(self, record: Dict) -> List[str]:
        """
        验证标准化后的记录

        Args:
            record: 标准化记录

        Returns:
            错误列表
        """
        errors = []

        # 必需字段验证
        if not record.get("name"):
            errors.append("Missing required field: name")

        # 至少需要一种结构标识符
        has_structure_id = any([
            record.get("inchikey"),
            record.get("smiles")
        ])

        if not has_structure_id:
            errors.append("Missing structure identifier (InChIKey or SMILES)")

        # 分子量合理性检查
        mw = record.get("molecular_weight")
        if mw:
            if mw < 0 or mw > 10000:  # 合理的分子量范围
                errors.append(f"Suspicious molecular weight: {mw}")

        return errors


class CompoundTransformerChEMBL(CompoundTransformer):
    """ChEMBL 专用化合物转换器"""

    def transform(self, record: Dict) -> TransformationResult:
        """转换 ChEMBL 化合物数据"""
        # 添加数据源标识
        record["data_source"] = "chembl"
        return super().transform(record)


class CompoundTransformerDrugBank(CompoundTransformer):
    """DrugBank 专用化合物转换器"""

    def transform(self, record: Dict) -> TransformationResult:
        """转换 DrugBank 化合物数据"""
        # 添加数据源标识
        record["data_source"] = "drugbank"
        return super().transform(record)


# 便捷函数
def transform_compounds(
    records: List[Dict],
    source: str = "chembl"
) -> List[TransformationResult]:
    """
    便捷函数：转换化合物数据

    Args:
        records: 原始记录列表
        source: 数据源类型

    Returns:
        转换结果列表
    """
    if source == "chembl":
        transformer = CompoundTransformerChEMBL()
    elif source == "drugbank":
        transformer = CompoundTransformerDrugBank()
    else:
        transformer = CompoundTransformer()

    try:
        return transformer.transform_batch(records)
    finally:
        logger.info(f"Compound transformation stats: {transformer.get_stats()}")
