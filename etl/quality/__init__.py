#===========================================================
# PharmaKG ETL - 数据质量模块
# Pharmaceutical Knowledge Graph - Data Quality Module
#===========================================================
# 版本: v1.0
# 描述: 数据质量验证和检查
#===========================================================

from .validators import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    BaseValidator,
    CompoundValidator,
    TargetValidator,
    DiseaseValidator,
    ClinicalTrialValidator,
    SupplyChainValidator,
    RegulatoryValidator,
    ValidatorFactory,
    validate_batch
)

from .checker import (
    QualityDimension,
    QualityMetric,
    QualityReport,
    DataQualityChecker,
    check_date_consistency,
    check_phase_consistency,
    check_molecular_weight_consistency,
    DEFAULT_CONSISTENCY_RULES
)


__all__ = [
    # Validators
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationResult",
    "BaseValidator",
    "CompoundValidator",
    "TargetValidator",
    "DiseaseValidator",
    "ClinicalTrialValidator",
    "SupplyChainValidator",
    "RegulatoryValidator",
    "ValidatorFactory",
    "validate_batch",

    # Quality Checker
    "QualityDimension",
    "QualityMetric",
    "QualityReport",
    "DataQualityChecker",
    "check_date_consistency",
    "check_phase_consistency",
    "check_molecular_weight_consistency",
    "DEFAULT_CONSISTENCY_RULES"
]


# 便捷函数
def check_data_quality(
    records: list,
    record_type: str,
    required_fields: list = None,
    print_report: bool = True
) -> QualityReport:
    """
    检查数据质量

    Args:
        records: 记录列表
        record_type: 记录类型
        required_fields: 必需字段列表
        print_report: 是否打印报告

    Returns:
        数据质量报告
    """
    checker = DataQualityChecker()

    consistency_rules = DEFAULT_CONSISTENCY_RULES.get(record_type, [])

    report = checker.generate_report(
        records=records,
        record_type=record_type,
        required_fields=required_fields,
        consistency_rules=consistency_rules
    )

    if print_report:
        checker.print_report(report)

    return report
