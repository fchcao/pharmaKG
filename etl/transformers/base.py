#===========================================================
# PharmaKG ETL - 基础转换器类
# Pharmaceutical Knowledge Graph - Base Transformer
#===========================================================
# 版本: v1.0
# 描述: 通用数据转换基类，提供验证、标准化、映射功能
#===========================================================

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class TransformationStatus(Enum):
    """转换状态"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    VALIDATION_ERROR = "validation_error"


@dataclass
class TransformationResult:
    """转换结果"""
    status: TransformationStatus
    input_record: Dict
    output_record: Optional[Dict]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

    @property
    def is_valid(self) -> bool:
        return self.status == TransformationStatus.SUCCESS


class BaseTransformer(ABC):
    """
    数据转换器基类

    提供：
    - 数据验证
    - 字段映射
    - 数据类型转换
    - 标准化处理
    - 错误处理
    """

    def __init__(self, name: str, strict_mode: bool = False):
        """
        初始化转换器

        Args:
            name: 转换器名称
            strict_mode: 严格模式（验证失败时抛出异常）
        """
        self.name = name
        self.strict_mode = strict_mode
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }

    @abstractmethod
    def transform(self, record: Dict) -> TransformationResult:
        """
        转换单条记录

        Args:
            record: 输入记录

        Returns:
            转换结果
        """
        pass

    def transform_batch(
        self,
        records: List[Dict]
    ) -> List[TransformationResult]:
        """
        批量转换记录

        Args:
            records: 输入记录列表

        Returns:
            转换结果列表
        """
        results = []

        for record in records:
            self.stats["total"] += 1
            result = self.transform(record)
            results.append(result)

            # 更新统计
            if result.status == TransformationStatus.SUCCESS:
                self.stats["success"] += 1
            elif result.status == TransformationStatus.FAILED:
                self.stats["failed"] += 1
            elif result.status == TransformationStatus.SKIPPED:
                self.stats["skipped"] += 1

        return results

    def validate(self, record: Dict) -> List[str]:
        """
        验证记录数据

        Args:
            record: 输入记录

        Returns:
            错误列表（空列表表示验证通过）
        """
        errors = []

        # 检查必需字段
        for field in self.get_required_fields():
            if field not in record or record[field] is None:
                errors.append(f"Missing required field: {field}")

        return errors

    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """
        获取必需字段列表

        Returns:
            必需字段名称列表
        """
        pass

    def normalize_string(self, value: Any) -> Optional[str]:
        """
        标准化字符串

        - 去除首尾空格
        - 统一大小写（根据配置）
        - 移除特殊字符

        Args:
            value: 输入值

        Returns:
            标准化后的字符串
        """
        if value is None:
            return None

        if not isinstance(value, str):
            value = str(value)

        # 去除首尾空格
        value = value.strip()

        # 移除多余的空格
        value = " ".join(value.split())

        return value if value else None

    def normalize_date(self, value: Any, input_format: str = None) -> Optional[str]:
        """
        标准化日期为 ISO 格式

        Args:
            value: 输入值
            input_format: 输入格式字符串

        Returns:
            ISO 格式日期字符串 (YYYY-MM-DD)
        """
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None

        try:
            # 尝试解析日期
            if isinstance(value, str) and input_format:
                dt = datetime.strptime(value, input_format)
            elif isinstance(value, str):
                # 尝试常见格式
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d"]:
                    try:
                        dt = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return None
            else:
                return None

            return dt.strftime("%Y-%m-%d")

        except (ValueError, TypeError):
            logger.warning(f"Failed to parse date: {value}")
            return None

    def map_enum_value(
        self,
        value: Any,
        mapping: Dict[str, str],
        default: Any = None
    ) -> Any:
        """
        映射枚举值

        Args:
            value: 输入值
            mapping: 映射字典
            default: 默认值

        Returns:
            映射后的值
        """
        if value is None:
            return default

        key = str(value).strip().lower()
        return mapping.get(key, default)

    def extract_numeric(
        self,
        value: Any,
        default: float = None
    ) -> Optional[float]:
        """
        提取数值

        Args:
            value: 输入值（可能包含单位等）
            default: 默认值

        Returns:
            提取的数值
        """
        if value is None:
            return default

        try:
            # 尝试直接转换
            if isinstance(value, (int, float)):
                return float(value)

            # 字符串处理
            if isinstance(value, str):
                # 移除常见的单位符号
                value = value.strip()
                for suffix in [" nM", " μM", " mM", " M", " mg", " kg"]:
                    value = value.replace(suffix, "")
                    value = value.replace(suffix.lower(), "")

                # 处理科学计数法
                value = value.replace("×10^", "e")

                return float(value)

        except (ValueError, TypeError):
            logger.warning(f"Failed to extract numeric from: {value}")
            return default

    def get_stats(self) -> Dict[str, int]:
        """获取转换统计"""
        return self.stats.copy()

    def reset_stats(self):
        """重置统计"""
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }


class FieldMapping:
    """
    字段映射配置

    定义源字段到目标字段的映射关系
    """

    def __init__(
        self,
        mappings: Dict[str, str],
        default_values: Optional[Dict[str, Any]] = None,
        transformers: Optional[Dict[str, callable]] = None
    ):
        """
        初始化字段映射

        Args:
            mappings: 源字段到目标字段的映射
            default_values: 默认值
            transformers: 字段转换函数
        """
        self.mappings = mappings
        self.default_values = default_values or {}
        self.transformers = transformers or {}

    def apply(self, record: Dict) -> Dict:
        """
        应用字段映射

        Args:
            record: 源记录

        Returns:
            映射后的记录
        """
        result = {}

        for source_field, target_field in self.mappings.items():
            value = record.get(source_field)

            # 应用转换函数
            if target_field in self.transformers:
                value = self.transformers[target_field](value)

            # 使用默认值
            if value is None and target_field in self.default_values:
                value = self.default_values[target_field]

            result[target_field] = value

        return result

    def apply_reverse(self, record: Dict) -> Dict:
        """
        应用反向字段映射

        Args:
            record: 目标记录

        Returns:
            源记录
        """
        result = {}

        # 创建反向映射
        reverse_mappings = {v: k for k, v in self.mappings.items()}

        for source_field, value in record.items():
            target_field = reverse_mappings.get(source_field)
            if target_field:
                result[target_field] = value
            else:
                result[source_field] = value

        return result
