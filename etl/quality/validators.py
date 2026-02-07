#===========================================================
# PharmaKG ETL - 数据验证器
# Pharmaceutical Knowledge Graph - Data Validators
#===========================================================
# 版本: v1.0
# 描述: 数据质量验证器
#===========================================================

import logging
import re
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """验证严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """验证问题"""
    field: str
    severity: ValidationSeverity
    message: str
    code: str
    value: Any = None
    expected: Any = None


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    record_id: Optional[str] = None
    record_type: Optional[str] = None

    @property
    def critical_issues(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.CRITICAL]

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    def add_issue(self, issue: ValidationIssue) -> None:
        """添加问题"""
        self.issues.append(issue)
        if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
            self.is_valid = False


class BaseValidator:
    """
    基础验证器

    提供通用验证功能
    """

    def __init__(self, name: str, strict_mode: bool = False):
        """
        初始化验证器

        Args:
            name: 验证器名称
            strict_mode: 严格模式（任何警告都视为错误）
        """
        self.name = name
        self.strict_mode = strict_mode
        self.stats = {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "warnings": 0
        }

    def validate(self, record: Dict, record_id: str = None) -> ValidationResult:
        """
        验证记录

        Args:
            record: 输入记录
            record_id: 记录 ID

        Returns:
            验证结果
        """
        self.stats["total"] += 1

        result = ValidationResult(
            is_valid=True,
            record_id=record_id,
            record_type=self.name
        )

        # 执行所有验证
        self._validate_required_fields(record, result)
        self._validate_data_types(record, result)
        self._validate_formats(record, result)
        self._validate_value_ranges(record, result)
        self._validate_business_rules(record, result)

        # 严格模式处理
        if self.strict_mode and result.warnings:
            for warning in result.warnings:
                warning.severity = ValidationSeverity.ERROR
            result.is_valid = False

        # 更新统计
        if result.is_valid:
            self.stats["valid"] += 1
        else:
            self.stats["invalid"] += 1

        self.stats["warnings"] += len(result.warnings)

        return result

    def _validate_required_fields(
        self,
        record: Dict,
        result: ValidationResult
    ) -> None:
        """验证必需字段"""
        for field in self.get_required_fields():
            if field not in record or record[field] is None:
                result.add_issue(ValidationIssue(
                    field=field,
                    severity=ValidationSeverity.ERROR,
                    message=f"Missing required field: {field}",
                    code="MISSING_REQUIRED"
                ))

    def _validate_data_types(
        self,
        record: Dict,
        result: ValidationResult
    ) -> None:
        """验证数据类型"""
        type_rules = self.get_type_rules()

        for field, expected_type in type_rules.items():
            value = record.get(field)
            if value is not None:
                if not isinstance(value, expected_type):
                    result.add_issue(ValidationIssue(
                        field=field,
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid type for {field}: expected {expected_type.__name__}, got {type(value).__name__}",
                        code="INVALID_TYPE",
                        value=type(value).__name__,
                        expected=expected_type.__name__
                    ))

    def _validate_formats(
        self,
        record: Dict,
        result: ValidationResult
    ) -> None:
        """验证格式"""
        format_rules = self.get_format_rules()

        for field, pattern in format_rules.items():
            value = record.get(field)
            if value and isinstance(value, str):
                if not re.match(pattern, value):
                    result.add_issue(ValidationIssue(
                        field=field,
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid format for {field}: {value}",
                        code="INVALID_FORMAT",
                        value=value
                    ))

    def _validate_value_ranges(
        self,
        record: Dict,
        result: ValidationResult
    ) -> None:
        """验证值范围"""
        range_rules = self.get_range_rules()

        for field, (min_val, max_val) in range_rules.items():
            value = record.get(field)
            if value is not None:
                try:
                    numeric_value = float(value)
                    if numeric_value < min_val or numeric_value > max_val:
                        result.add_issue(ValidationIssue(
                            field=field,
                            severity=ValidationSeverity.WARNING,
                            message=f"Value out of range for {field}: {value} (expected: {min_val}-{max_val})",
                            code="VALUE_OUT_OF_RANGE",
                            value=value,
                            expected=f"{min_val}-{max_val}"
                        ))
                except (ValueError, TypeError):
                    result.add_issue(ValidationIssue(
                        field=field,
                        severity=ValidationSeverity.ERROR,
                        message=f"Non-numeric value for {field}: {value}",
                        code="INVALID_NUMERIC",
                        value=value
                    ))

    def _validate_business_rules(
        self,
        record: Dict,
        result: ValidationResult
    ) -> None:
        """验证业务规则"""
        # 子类可以覆盖此方法
        pass

    def get_required_fields(self) -> List[str]:
        """获取必需字段列表"""
        return []

    def get_type_rules(self) -> Dict[str, type]:
        """获取类型规则"""
        return {}

    def get_format_rules(self) -> Dict[str, str]:
        """获取格式规则"""
        return {}

    def get_range_rules(self) -> Dict[str, tuple]:
        """获取值范围规则"""
        return {}

    def get_stats(self) -> Dict[str, int]:
        """获取验证统计"""
        return self.stats.copy()


class CompoundValidator(BaseValidator):
    """
    化合物数据验证器

    验证规则：
    - 必需字段：primary_id, name
    - SMILES 格式验证
    - InChIKey 格式验证
    - 分子量范围检查
    """

    def __init__(self, strict_mode: bool = False):
        super().__init__(name="Compound", strict_mode=strict_mode)

    def get_required_fields(self) -> List[str]:
        return ["primary_id", "name"]

    def get_type_rules(self) -> Dict[str, type]:
        return {
            "molecular_weight": (int, float),
            "ro5_violations": int
        }

    def get_format_rules(self) -> Dict[str, str]:
        return {
            # InChIKey 格式: XX-XXX-X-XX
            "inchikey": r'^[A-Z]{14}-[A-Z]{10}-[A-Z]$',
            # SMILES 基本字符验证
            "smiles": r'^[CNOPSFBrClI[\]()=#+\-0-9nso@%\.]+$'
        }

    def get_range_rules(self) -> Dict[str, tuple]:
        return {
            "molecular_weight": (50, 2000),
            "ro5_violations": (0, 10)
        }

    def _validate_business_rules(
        self,
        record: Dict,
        result: ValidationResult
    ) -> None:
        # 验证至少有一种结构标识符
        has_structure = any([
            record.get("smiles"),
            record.get("inchikey"),
            record.get("standard_inchi")
        ])

        if not has_structure:
            result.add_issue(ValidationIssue(
                field="structure",
                severity=ValidationSeverity.WARNING,
                message="No structure identifier (SMILES/InChIKey) provided",
                code="MISSING_STRUCTURE"
            ))


class TargetValidator(BaseValidator):
    """
    靶点数据验证器

    验证规则：
    - 必需字段：primary_id, name
    - UniProt ID 格式验证
    """

    def __init__(self, strict_mode: bool = False):
        super().__init__(name="Target", strict_mode=strict_mode)

    def get_required_fields(self) -> List[str]:
        return ["primary_id", "name"]

    def get_format_rules(self) -> Dict[str, str]:
        return {
            # UniProt ID 格式
            "uniprot_id": r'^[OPQ][0-9A-Z]{3}[0-9A-Z]{1}[0-9A-Z]{3}$',
            # ChEMBL target ID 格式
            "chembl_id": r'^CHEMBL[0-9]+$'
        }


class DiseaseValidator(BaseValidator):
    """
    疾病数据验证器

    验证规则：
    - 必需字段：primary_id, name
    - MONDO ID 格式验证
    """

    def __init__(self, strict_mode: bool = False):
        super().__init__(name="Disease", strict_mode=strict_mode)

    def get_required_fields(self) -> List[str]:
        return ["primary_id", "name"]

    def get_format_rules(self) -> Dict[str, str]:
        return {
            # MONDO ID 格式
            "mondo_id": r'^MONDO:[0-9]+$',
            # DOID 格式
            "doid": r'^DOID:[0-9]+$'
        }


class ClinicalTrialValidator(BaseValidator):
    """
    临床试验验证器

    验证规则：
    - 必需字段：primary_id, trial_id, title
    - NCT ID 格式验证
    - 日期逻辑验证
    """

    def __init__(self, strict_mode: bool = False):
        super().__init__(name="ClinicalTrial", strict_mode=strict_mode)

    def get_required_fields(self) -> List[str]:
        return ["primary_id", "trial_id", "title"]

    def get_format_rules(self) -> Dict[str, str]:
        return {
            # NCT ID 格式
            "trial_id": r'^NCT[0-9]{8}$'
        }

    def _validate_business_rules(
        self,
        record: Dict,
        result: ValidationResult
    ) -> None:
        # 验证日期逻辑：完成日期不能早于开始日期
        start_date = record.get("start_date")
        completion_date = record.get("completion_date")

        if start_date and completion_date:
            try:
                start = datetime.fromisoformat(start_date)
                completion = datetime.fromisoformat(completion_date)

                if completion < start:
                    result.add_issue(ValidationIssue(
                        field="completion_date",
                        severity=ValidationSeverity.ERROR,
                        message=f"Completion date before start date",
                        code="INVALID_DATE_RANGE"
                    ))
            except ValueError:
                pass  # 日期格式已在其他验证中处理


class SupplyChainValidator(BaseValidator):
    """
    供应链数据验证器

    验证规则：
    - 制造商必需字段
    - 短缺状态验证
    """

    def __init__(self, strict_mode: bool = False):
        super().__init__(name="SupplyChain", strict_mode=strict_mode)

    def get_required_fields(self) -> List[str]:
        return ["primary_id"]

    def _validate_business_rules(
        self,
        record: Dict,
        result: ValidationResult
    ) -> None:
        # 验证短缺状态
        status = record.get("status")
        valid_statuses = ["active", "resolved", "current", "non-current"]

        if status and status.lower() not in valid_statuses:
            result.add_issue(ValidationIssue(
                field="status",
                severity=ValidationSeverity.WARNING,
                message=f"Unknown shortage status: {status}",
                code="UNKNOWN_STATUS",
                value=status
            ))


class RegulatoryValidator(BaseValidator):
    """
    监管数据验证器

    验证规则：
    - FDA 产品 ID 格式
    - NDA 编号格式
    """

    def __init__(self, strict_mode: bool = False):
        super().__init__(name="Regulatory", strict_mode=strict_mode)

    def get_required_fields(self) -> List[str]:
        return ["primary_id"]

    def get_format_rules(self) -> Dict[str, str]:
        return {
            # NDA 格式
            "appl_no": r'^(NDA|ANDA|BLA)[0-9]+$',
            # TE 码格式
            "te_code": r'^[A-Z]{1,2}$'
        }


# 验证器工厂
class ValidatorFactory:
    """验证器工厂"""

    _validators: Dict[str, type] = {
        "compound": CompoundValidator,
        "target": TargetValidator,
        "disease": DiseaseValidator,
        "clinical_trial": ClinicalTrialValidator,
        "supply_chain": SupplyChainValidator,
        "regulatory": RegulatoryValidator
    }

    @classmethod
    def create(
        cls,
        record_type: str,
        strict_mode: bool = False
    ) -> BaseValidator:
        """
        创建验证器

        Args:
            record_type: 记录类型
            strict_mode: 严格模式

        Returns:
            验证器实例
        """
        validator_class = cls._validators.get(record_type.lower())
        if not validator_class:
            logger.warning(f"Unknown record type: {record_type}, using base validator")
            return BaseValidator(name=record_type, strict_mode=strict_mode)

        return validator_class(strict_mode=strict_mode)

    @classmethod
    def register_validator(
        cls,
        record_type: str,
        validator_class: type
    ) -> None:
        """
        注册自定义验证器

        Args:
            record_type: 记录类型
            validator_class: 验证器类
        """
        cls._validators[record_type.lower()] = validator_class


# 批量验证函数
def validate_batch(
    records: List[Dict],
    record_type: str,
    strict_mode: bool = False
) -> List[ValidationResult]:
    """
    批量验证记录

    Args:
        records: 记录列表
        record_type: 记录类型
        strict_mode: 严格模式

    Returns:
        验证结果列表
    """
    validator = ValidatorFactory.create(record_type, strict_mode)
    results = []

    for record in records:
        record_id = record.get("primary_id") or record.get("id")
        result = validator.validate(record, record_id)
        results.append(result)

    logger.info(
        f"Validation complete: {validator.stats['valid']}/{validator.stats['total']} valid, "
        f"{validator.stats['warnings']} warnings"
    )

    return results
