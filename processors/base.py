#===========================================================
# PharmaKG 基础处理器
# Pharmaceutical Knowledge Graph - Base Processor
#===========================================================
# 版本: v1.0
# 描述: 所有数据处理器的基础类
#===========================================================

import logging
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


@dataclass
class ProcessingMetrics:
    """处理指标"""
    files_scanned: int = 0
    files_processed: int = 0
    files_failed: int = 0
    files_skipped: int = 0
    entities_extracted: int = 0
    relationships_extracted: int = 0
    entities_mapped: int = 0
    relationships_mapped: int = 0
    processing_time_seconds: float = 0.0
    memory_used_mb: float = 0.0


@dataclass
class ProcessingResult:
    """处理结果"""
    status: ProcessingStatus
    processor_name: str
    source_path: str
    metrics: ProcessingMetrics = field(default_factory=ProcessingMetrics)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    output_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "processor_name": self.processor_name,
            "source_path": self.source_path,
            "metrics": {
                "files_scanned": self.metrics.files_scanned,
                "files_processed": self.metrics.files_processed,
                "files_failed": self.metrics.files_failed,
                "files_skipped": self.metrics.files_skipped,
                "entities_extracted": self.metrics.entities_extracted,
                "relationships_extracted": self.metrics.relationships_extracted,
                "entities_mapped": self.metrics.entities_mapped,
                "relationships_mapped": self.metrics.relationships_mapped,
                "processing_time_seconds": self.metrics.processing_time_seconds,
            },
            "entities_count": len(self.entities),
            "relationships_count": len(self.relationships),
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "output_path": self.output_path,
        }

    def save(self, filepath: Union[str, Path]):
        """保存结果到文件"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


class BaseProcessor(ABC):
    """
    数据处理器基类

    所有处理器必须继承此类并实现核心方法
    """

    # 处理器名称
    PROCESSOR_NAME: str = "BaseProcessor"

    # 支持的文件格式
    SUPPORTED_FORMATS: List[str] = []

    # 输出目录结构
    OUTPUT_SUBDIR: str = ""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化处理器

        Args:
            config: 处理器配置
        """
        self.config = config or {}
        self.project_root = Path(__file__).parent.parent
        self.data_root = self.project_root / "data"
        self.logger = logging.getLogger(self.__class__.__name__)

        # 目录路径
        self.sources_dir = self.data_root / "sources"
        self.processed_dir = self.data_root / "processed"
        self.validated_dir = self.data_root / "validated"
        self.import_dir = self.data_root / "import"
        self.archive_dir = self.data_root / "archive"

        # 处理器专用目录
        self.entities_output_dir = self.processed_dir / "entities" / self.OUTPUT_SUBDIR
        self.relationships_output_dir = self.processed_dir / "relationships" / self.OUTPUT_SUBDIR
        self.documents_output_dir = self.processed_dir / "documents" / self.OUTPUT_SUBDIR

        # 创建输出目录
        for dir_path in [self.entities_output_dir, self.relationships_output_dir, self.documents_output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self._metrics = ProcessingMetrics()
        self._errors = []
        self._warnings = []

    @abstractmethod
    def scan(self, source_path: Union[str, Path]) -> List[Path]:
        """
        扫描源目录，找出需要处理的文件

        Args:
            source_path: 源目录路径

        Returns:
            需要处理的文件列表
        """
        pass

    @abstractmethod
    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        从文件中提取数据

        Args:
            file_path: 文件路径

        Returns:
            提取的数据字典
        """
        pass

    @abstractmethod
    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换提取的数据

        Args:
            raw_data: 原始提取数据

        Returns:
            转换后的数据
        """
        pass

    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证数据

        Args:
            data: 待验证数据

        Returns:
            是否验证通过
        """
        pass

    def process(
        self,
        source_path: Union[str, Path],
        output_to: Optional[str] = None,
        save_intermediate: bool = True
    ) -> ProcessingResult:
        """
        处理数据源的主流程

        Args:
            source_path: 源数据路径
            output_to: 输出目录（可选）
            save_intermediate: 是否保存中间结果

        Returns:
            处理结果
        """
        start_time = datetime.now()
        source_path = Path(source_path)

        logger.info(f"[{self.PROCESSOR_NAME}] 开始处理: {source_path}")

        # 重置状态
        self._metrics = ProcessingMetrics()
        self._errors = []
        self._warnings = []

        try:
            # 1. 扫描文件
            files = self.scan(source_path)
            self._metrics.files_scanned = len(files)

            if not files:
                self._warnings.append(f"未找到可处理的文件: {source_path}")
                return ProcessingResult(
                    status=ProcessingStatus.SKIPPED,
                    processor_name=self.PROCESSOR_NAME,
                    source_path=str(source_path),
                    metrics=self._metrics,
                    warnings=self._warnings
                )

            logger.info(f"找到 {len(files)} 个文件待处理")

            # 2. 处理每个文件
            all_entities = []
            all_relationships = []

            for file_path in files:
                try:
                    # 提取
                    raw_data = self.extract(file_path)
                    if not raw_data:
                        self._metrics.files_skipped += 1
                        continue

                    # 转换
                    transformed_data = self.transform(raw_data)
                    if not transformed_data:
                        self._metrics.files_skipped += 1
                        continue

                    # 验证
                    if not self.validate(transformed_data):
                        self._warnings.append(f"数据验证失败: {file_path.name}")
                        self._metrics.files_skipped += 1
                        continue

                    # 收集实体和关系
                    entities = transformed_data.get('entities', [])
                    relationships = transformed_data.get('relationships', [])

                    all_entities.extend(entities)
                    all_relationships.extend(relationships)

                    self._metrics.files_processed += 1
                    self._metrics.entities_extracted += len(entities)
                    self._metrics.relationships_extracted += len(relationships)

                except Exception as e:
                    logger.error(f"处理文件失败 {file_path}: {e}")
                    self._errors.append(f"{file_path.name}: {str(e)}")
                    self._metrics.files_failed += 1

            # 3. 保存结果
            output_path = None
            if save_intermediate and (all_entities or all_relationships):
                output_path = self._save_results(all_entities, all_relationships, output_to)

            # 4. 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            self._metrics.processing_time_seconds = processing_time

            # 5. 确定最终状态
            if self._metrics.files_failed > 0:
                status = ProcessingStatus.PARTIAL
            elif self._metrics.files_processed == 0:
                status = ProcessingStatus.SKIPPED
            else:
                status = ProcessingStatus.COMPLETED

            logger.info(f"[{self.PROCESSOR_NAME}] 处理完成: "
                       f"处理={self._metrics.files_processed}, "
                       f"失败={self._metrics.files_failed}, "
                       f"跳过={self._metrics.files_skipped}, "
                       f"实体={len(all_entities)}, "
                       f"关系={len(all_relationships)}, "
                       f"耗时={processing_time:.2f}秒")

            return ProcessingResult(
                status=status,
                processor_name=self.PROCESSOR_NAME,
                source_path=str(source_path),
                metrics=self._metrics,
                entities=all_entities,
                relationships=all_relationships,
                errors=self._errors,
                warnings=self._warnings,
                output_path=str(output_path) if output_path else None
            )

        except Exception as e:
            logger.error(f"[{self.PROCESSOR_NAME}] 处理失败: {e}", exc_info=True)
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                processor_name=self.PROCESSOR_NAME,
                source_path=str(source_path),
                metrics=self._metrics,
                errors=[str(e)]
            )

    def _save_results(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        output_to: Optional[str] = None
    ) -> Path:
        """
        保存处理结果

        Args:
            entities: 实体列表
            relationships: 关系列表
            output_to: 自定义输出目录

        Returns:
            输出文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 确定输出目录
        if output_to:
            output_dir = Path(output_to)
        else:
            output_dir = self.documents_output_dir

        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存实体
        if entities:
            entities_file = output_dir / f"entities_{timestamp}.json"
            with open(entities_file, 'w', encoding='utf-8') as f:
                json.dump(entities, f, ensure_ascii=False, indent=2)
            logger.debug(f"保存实体到: {entities_file}")

        # 保存关系
        if relationships:
            relationships_file = output_dir / f"relationships_{timestamp}.json"
            with open(relationships_file, 'w', encoding='utf-8') as f:
                json.dump(relationships, f, ensure_ascii=False, indent=2)
            logger.debug(f"保存关系到: {relationships_file}")

        # 保存处理摘要
        summary = {
            "processor": self.PROCESSOR_NAME,
            "timestamp": timestamp,
            "entities_count": len(entities),
            "relationships_count": len(relationships),
            "processing_time": self._metrics.processing_time_seconds,
        }
        summary_file = output_dir / f"summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        return summary_file

    def generate_file_hash(self, file_path: Path) -> str:
        """
        生成文件哈希值

        Args:
            file_path: 文件路径

        Returns:
            文件的MD5哈希值
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def is_processed(self, file_path: Path) -> bool:
        """
        检查文件是否已处理

        Args:
            file_path: 文件路径

        Returns:
            是否已处理
        """
        # 检查归档目录
        archive_path = self.archive_dir / "processed" / self.OUTPUT_SUBDIR
        if archive_path.exists():
            file_hash = self.generate_file_hash(file_path)
            hash_file = archive_path / f"{file_hash}.processed"
            return hash_file.exists()

        return False

    def mark_as_processed(self, file_path: Path):
        """
        标记文件为已处理

        Args:
            file_path: 文件路径
        """
        archive_path = self.archive_dir / "processed" / self.OUTPUT_SUBDIR
        archive_path.mkdir(parents=True, exist_ok=True)

        file_hash = self.generate_file_hash(file_path)
        hash_file = archive_path / f"{file_hash}.processed"

        with open(hash_file, 'w') as f:
            json.dump({
                "file_path": str(file_path),
                "file_hash": file_hash,
                "processed_at": datetime.now().isoformat(),
                "processor": self.PROCESSOR_NAME
            }, f, indent=2)
