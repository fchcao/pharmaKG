#===========================================================
# PharmaKG ETL - 数据质量检查器
# Pharmaceutical Knowledge Graph - Data Quality Checker
#===========================================================
# 版本: v1.0
# 描述: 全面的数据质量检查
#===========================================================

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter

from .validators import (
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    validate_batch,
    ValidatorFactory
)


logger = logging.getLogger(__name__)


class QualityDimension(str, Enum):
    """数据质量维度"""
    COMPLETENESS = "completeness"      # 完整性
    ACCURACY = "accuracy"              # 准确性
    CONSISTENCY = "consistency"        # 一致性
    VALIDITY = "validity"              # 有效性
    UNIQUENESS = "uniqueness"          # 唯一性
    TIMELINESS = "timeliness"          # 及时性


@dataclass
class QualityMetric:
    """质量指标"""
    dimension: QualityDimension
    name: str
    value: float
    threshold: float
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def score_percent(self) -> float:
        return self.value * 100


@dataclass
class QualityReport:
    """数据质量报告"""
    record_type: str
    total_records: int
    valid_records: int
    invalid_records: int
    metrics: List[QualityMetric] = field(default_factory=list)
    issues_summary: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    @property
    def validity_rate(self) -> float:
        if self.total_records == 0:
            return 0.0
        return self.valid_records / self.total_records

    @property
    def overall_quality_score(self) -> float:
        """综合质量评分 (0-1)"""
        if not self.metrics:
            return self.validity_rate

        # 加权平均
        weights = {
            QualityDimension.COMPLETENESS: 0.25,
            QualityDimension.VALIDITY: 0.30,
            QualityDimension.CONSISTENCY: 0.20,
            QualityDimension.UNIQUENESS: 0.15,
            QualityDimension.TIMELINESS: 0.10
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for metric in self.metrics:
            weight = weights.get(metric.dimension, 0.1)
            weighted_sum += metric.value * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0


class DataQualityChecker:
    """
    数据质量检查器

    执行全面的数据质量评估
    """

    def __init__(self, threshold: float = 0.9):
        """
        初始化质量检查器

        Args:
            threshold: 质量阈值（低于此值视为不合格）
        """
        self.threshold = threshold
        self.metrics_history: List[QualityMetric] = []

    def check_completeness(
        self,
        records: List[Dict],
        required_fields: List[str]
    ) -> QualityMetric:
        """
        检查完整性

        计算必需字段的填充率

        Args:
            records: 记录列表
            required_fields: 必需字段列表

        Returns:
            完整性指标
        """
        if not records:
            return QualityMetric(
                dimension=QualityDimension.COMPLETENESS,
                name="Field Completeness",
                value=0.0,
                threshold=self.threshold,
                passed=False
            )

        field_completion = {}
        for field in required_fields:
            filled_count = sum(1 for r in records if r.get(field) not in [None, ""])
            field_completion[field] = filled_count / len(records)

        overall_completeness = sum(field_completion.values()) / len(field_completion)

        return QualityMetric(
            dimension=QualityDimension.COMPLETENESS,
            name="Field Completeness",
            value=overall_completeness,
            threshold=self.threshold,
            passed=overall_completeness >= self.threshold,
            details={
                "field_completion": field_completion,
                "total_fields": len(required_fields),
                "complete_records": sum(
                    1 for r in records
                    if all(r.get(f) not in [None, ""] for f in required_fields)
                )
            }
        )

    def check_validity(
        self,
        records: List[Dict],
        record_type: str
    ) -> QualityMetric:
        """
        检查有效性

        基于验证规则检查记录的有效性

        Args:
            records: 记录列表
            record_type: 记录类型

        Returns:
            有效性指标
        """
        results = validate_batch(records, record_type)

        valid_count = sum(1 for r in results if r.is_valid)
        validity_rate = valid_count / len(results) if results else 0.0

        return QualityMetric(
            dimension=QualityDimension.VALIDITY,
            name="Record Validity",
            value=validity_rate,
            threshold=self.threshold,
            passed=validity_rate >= self.threshold,
            details={
                "valid_count": valid_count,
                "invalid_count": len(results) - valid_count,
                "error_distribution": self._count_error_types(results)
            }
        )

    def check_uniqueness(
        self,
        records: List[Dict],
        key_field: str = "primary_id"
    ) -> QualityMetric:
        """
        检查唯一性

        Args:
            records: 记录列表
            key_field: 主键字段

        Returns:
            唯一性指标
        """
        if not records:
            return QualityMetric(
                dimension=QualityDimension.UNIQUENESS,
                name="Key Uniqueness",
                value=0.0,
                threshold=1.0,
                passed=False
            )

        keys = [r.get(key_field) for r in records if r.get(key_field)]
        key_counts = Counter(keys)
        duplicate_count = sum(count - 1 for count in key_counts.values() if count > 1)

        uniqueness_rate = (len(keys) - duplicate_count) / len(keys) if keys else 0.0

        return QualityMetric(
            dimension=QualityDimension.UNIQUENESS,
            name="Key Uniqueness",
            value=uniqueness_rate,
            threshold=1.0,  # 主键应该完全唯一
            passed=uniqueness_rate == 1.0,
            details={
                "total_records": len(records),
                "unique_keys": len(key_counts),
                "duplicate_keys": duplicate_count,
                "duplicate_samples": [
                    (key, count) for key, count in key_counts.items() if count > 1
                ][:5]  # 最多显示5个重复样本
            }
        )

    def check_consistency(
        self,
        records: List[Dict],
        consistency_rules: List[callable]
    ) -> QualityMetric:
        """
        检查一致性

        Args:
            records: 记录列表
            consistency_rules: 一致性规则函数列表

        Returns:
            一致性指标
        """
        if not records:
            return QualityMetric(
                dimension=QualityDimension.CONSISTENCY,
                name="Data Consistency",
                value=0.0,
                threshold=self.threshold,
                passed=False
            )

        total_checks = 0
        passed_checks = 0
        violations = []

        for rule in consistency_rules:
            for record in records:
                total_checks += 1
                try:
                    result = rule(record)
                    if result["valid"]:
                        passed_checks += 1
                    else:
                        violations.append({
                            "record_id": record.get("primary_id"),
                            "rule": rule.__name__,
                            "message": result.get("message", "Consistency violation")
                        })
                except Exception as e:
                    violations.append({
                        "record_id": record.get("primary_id"),
                        "rule": rule.__name__,
                        "message": f"Rule execution error: {e}"
                    })

        consistency_rate = passed_checks / total_checks if total_checks > 0 else 0.0

        return QualityMetric(
            dimension=QualityDimension.CONSISTENCY,
            name="Data Consistency",
            value=consistency_rate,
            threshold=self.threshold,
            passed=consistency_rate >= self.threshold,
            details={
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "violations": violations[:10]  # 最多显示10个违规
            }
        )

    def check_timeliness(
        self,
        records: List[Dict],
        date_field: str = "created_at",
        max_age_days: int = 365
    ) -> QualityMetric:
        """
        检查及时性

        检查数据是否在合理的时间范围内

        Args:
            records: 记录列表
            date_field: 日期字段
            max_age_days: 最大数据年龄（天）

        Returns:
            及时性指标
        """
        from datetime import datetime, timedelta

        if not records:
            return QualityMetric(
                dimension=QualityDimension.TIMELINESS,
                name="Data Timeliness",
                value=0.0,
                threshold=self.threshold,
                passed=False
            )

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        timely_count = 0

        for record in records:
            date_str = record.get(date_field)
            if date_str:
                try:
                    record_date = datetime.fromisoformat(date_str)
                    if record_date >= cutoff_date:
                        timely_count += 1
                except ValueError:
                    pass  # 无效日期不计入

        timeliness_rate = timely_count / len(records)

        return QualityMetric(
            dimension=QualityDimension.TIMELINESS,
            name="Data Timeliness",
            value=timeliness_rate,
            threshold=self.threshold,
            passed=timeliness_rate >= self.threshold,
            details={
                "timely_records": timely_count,
                "outdated_records": len(records) - timely_count,
                "max_age_days": max_age_days
            }
        )

    def generate_report(
        self,
        records: List[Dict],
        record_type: str,
        required_fields: Optional[List[str]] = None,
        consistency_rules: Optional[List[callable]] = None
    ) -> QualityReport:
        """
        生成完整的数据质量报告

        Args:
            records: 记录列表
            record_type: 记录类型
            required_fields: 必需字段列表
            consistency_rules: 一致性规则列表

        Returns:
            数据质量报告
        """
        logger.info(f"Generating quality report for {len(records)} {record_type} records")

        report = QualityReport(
            record_type=record_type,
            total_records=len(records)
        )

        # 运行各项检查
        metrics = []

        # 有效性检查
        validity_metric = self.check_validity(records, record_type)
        metrics.append(validity_metric)
        report.valid_records = int(validity_rate := validity_metric.details.get("valid_count", 0))
        report.invalid_records = len(records) - report.valid_records

        # 完整性检查
        if required_fields:
            completeness_metric = self.check_completeness(records, required_fields)
            metrics.append(completeness_metric)

        # 唯一性检查
        uniqueness_metric = self.check_uniqueness(records)
        metrics.append(uniqueness_metric)

        # 一致性检查
        if consistency_rules:
            consistency_metric = self.check_consistency(records, consistency_rules)
            metrics.append(consistency_metric)

        # 及时性检查
        timeliness_metric = self.check_timeliness(records)
        metrics.append(timeliness_metric)

        report.metrics = metrics

        # 生成问题摘要
        self._generate_issues_summary(report)

        # 生成建议
        self._generate_recommendations(report)

        return report

    def _count_error_types(
        self,
        results: List[ValidationResult]
    ) -> Dict[str, int]:
        """统计错误类型分布"""
        error_counts = defaultdict(int)

        for result in results:
            for issue in result.issues:
                error_counts[issue.code] += 1

        return dict(error_counts)

    def _generate_issues_summary(self, report: QualityReport) -> None:
        """生成问题摘要"""
        summary = defaultdict(int)

        for metric in report.metrics:
            for code, count in metric.details.get("error_distribution", {}).items():
                summary[code] += count

        report.issues_summary = dict(summary)

    def _generate_recommendations(self, report: QualityReport) -> None:
        """生成改进建议"""
        recommendations = []

        for metric in report.metrics:
            if not metric.passed:
                if metric.dimension == QualityDimension.COMPLETENESS:
                    recommendations.append(
                        f"Improve data completeness: {metric.details.get('total_fields', 0)} "
                        f"required fields have low fill rates"
                    )
                elif metric.dimension == QualityDimension.VALIDITY:
                    recommendations.append(
                        f"Address {metric.details.get('invalid_count', 0)} validation errors"
                    )
                elif metric.dimension == QualityDimension.UNIQUENESS:
                    recommendations.append(
                        f"Resolve {metric.details.get('duplicate_keys', 0)} duplicate key issues"
                    )
                elif metric.dimension == QualityDimension.CONSISTENCY:
                    recommendations.append(
                        f"Fix {len(metric.details.get('violations', []))} consistency violations"
                    )
                elif metric.dimension == QualityDimension.TIMELINESS:
                    recommendations.append(
                        f"Update {metric.details.get('outdated_records', 0)} outdated records"
                    )

        report.recommendations = recommendations

    def print_report(self, report: QualityReport) -> None:
        """打印质量报告"""
        print("\n" + "=" * 60)
        print(f"DATA QUALITY REPORT: {report.record_type.upper()}")
        print("=" * 60)

        print(f"\nTotal Records: {report.total_records}")
        print(f"Valid Records: {report.valid_records} ({report.validity_rate:.1%})")
        print(f"Invalid Records: {report.invalid_records}")

        print("\nQuality Metrics:")
        print("-" * 60)

        for metric in report.metrics:
            status = "✓ PASS" if metric.passed else "✗ FAIL"
            print(f"\n{metric.dimension.value.upper()}: {status}")
            print(f"  Name: {metric.name}")
            print(f"  Score: {metric.score_percent:.1f}% (threshold: {metric.threshold:.1%})")

        print(f"\nOverall Quality Score: {report.overall_quality_score:.1%}")

        if report.issues_summary:
            print("\nIssues Summary:")
            for code, count in report.issues_summary.items():
                print(f"  {code}: {count}")

        if report.recommendations:
            print("\nRecommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"  {i}. {rec}")

        print("\n" + "=" * 60)


# 预定义的一致性规则
def check_date_consistency(record: Dict) -> Dict[str, Any]:
    """日期一致性规则"""
    start_date = record.get("start_date")
    end_date = record.get("end_date") or record.get("completion_date")

    if start_date and end_date:
        try:
            from datetime import datetime
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)

            if end < start:
                return {
                    "valid": False,
                    "message": "End date before start date"
                }
        except ValueError:
            return {
                "valid": False,
                "message": "Invalid date format"
            }

    return {"valid": True}


def check_phase_consistency(record: Dict) -> Dict[str, Any]:
    """临床试验阶段一致性规则"""
    phase = record.get("phase", "")
    status = record.get("status", "")

    # 已完成的试验应该有阶段信息
    if status and "completed" in status.lower() and not phase:
        return {
            "valid": False,
            "message": "Completed trial missing phase information"
        }

    return {"valid": True}


def check_molecular_weight_consistency(record: Dict) -> Dict[str, Any]:
    """分子量一致性规则"""
    mw = record.get("molecular_weight")
    formula = record.get("molecular_formula")

    if mw and formula:
        # 简单检查：分子量应该大于0
        if mw <= 0:
            return {
                "valid": False,
                "message": "Molecular weight must be positive"
            }

    return {"valid": True}


# 默认一致性规则集
DEFAULT_CONSISTENCY_RULES = {
    "clinical_trial": [check_date_consistency, check_phase_consistency],
    "compound": [check_molecular_weight_consistency],
    "target": [],
    "disease": []
}
