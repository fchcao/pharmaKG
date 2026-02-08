#===========================================================
# PharmaKG 监管文档处理器
# Pharmaceutical Knowledge Graph - Regulatory Document Processor
#===========================================================
# 版本: v1.0
# 描述: 处理监管文档，提取实体和关系
#===========================================================

import logging
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus, ProcessingMetrics
from extractors.named_entity import NamedEntityExtractor
from extractors.relationship import RelationshipExtractor
from extractors.attribute import AttributeExtractor
from extractors.base import EntityType, ExtractedEntity, ExtractedRelationship
from mappers.entity_mapper import EntityMapper

logger = logging.getLogger(__name__)


class RegulatoryDocumentProcessor(BaseProcessor):
    """
    监管文档处理器

    处理CDE、FDA等监管机构的文档，提取实体和关系
    """

    PROCESSOR_NAME = "RegulatoryDocumentProcessor"
    SUPPORTED_FORMATS = ['.txt', '.pdf', '.docx', '.doc', '.html']
    OUTPUT_SUBDIR = "regulatory"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        super().__init__(config)

        # 初始化提取器
        self.entity_extractor = NamedEntityExtractor(config)
        self.relationship_extractor = RelationshipExtractor(config)
        self.attribute_extractor = AttributeExtractor(config)
        self.entity_mapper = EntityMapper(config)

        # 配置
        self.extract_relationships = config.get('extract_relationships', True)
        self.cross_document_links = config.get('cross_document_links', True)

    def scan(self, source_path: Union[str, Path]) -> List[Path]:
        """扫描源目录"""
        source_path = Path(source_path)

        if source_path.is_file():
            return [source_path] if source_path.suffix in self.SUPPORTED_FORMATS else []

        files = []
        for ext in self.SUPPORTED_FORMATS:
            files.extend(source_path.rglob(f"*{ext}"))

        # 排除已处理的文件
        unprocessed_files = [f for f in files if not self.is_processed(f)]

        return unprocessed_files

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """从文件中提取数据"""
        self.logger.debug(f"提取文件: {file_path}")

        # 读取文件内容
        content = self._read_file(file_path)
        if not content:
            return {}

        # 生成文档ID
        doc_id = self._generate_document_id(file_path)

        # 提取元数据
        metadata = self._extract_metadata(file_path, content)

        # 提取属性
        attributes = self.attribute_extractor.extract_regulatory_attributes(content)

        # 提取实体
        entities = self.entity_extractor.extract_entities(
            content,
            extract_types=[
                EntityType.REGULATORY_AGENCY,
                EntityType.COMPANY,
                EntityType.DOCUMENT,
                EntityType.GUIDELINE,
                EntityType.ORGANIZATION,
            ]
        )

        # 添加文档本身作为实体
        doc_entity = ExtractedEntity(
            entity_type=EntityType.REGULATORY_DOCUMENT,
            text=metadata.get('title', file_path.stem),
            confidence=1.0,
            properties={
                'document_id': doc_id,
                'file_path': str(file_path),
                'file_format': file_path.suffix,
                **metadata,
                **attributes,
            }
        )
        entities.insert(0, doc_entity)  # 文档实体作为第一个

        # 提取关系
        relationships = []
        if self.extract_relationships:
            relationships = self.relationship_extractor.extract_relationships(
                content,
                entities
            )

        return {
            'document_id': doc_id,
            'content': content,
            'metadata': metadata,
            'attributes': attributes,
            'entities': entities,
            'relationships': relationships,
            'file_path': str(file_path),
        }

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换提取的数据"""
        if not raw_data:
            return {}

        # 映射实体到本体
        mapped_entities = self.entity_mapper.map_entities(raw_data.get('entities', []))

        # 映射关系到本体
        mapped_relationships = self._map_relationships(
            raw_data.get('relationships', []),
            raw_data.get('entities', [])
        )

        # 添加文档关系
        document_relations = self._create_document_relations(raw_data)

        mapped_relationships.extend(document_relations)

        return {
            'entities': mapped_entities,
            'relationships': mapped_relationships,
            'metadata': raw_data.get('metadata', {}),
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        """验证数据"""
        # 检查是否有实体
        if not data.get('entities'):
            return False

        # 检查是否有主标识符
        for entity in data['entities']:
            if 'properties' in entity and 'primary_id' in entity['properties']:
                return True

        return False

    def _read_file(self, file_path: Path) -> Optional[str]:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"读取文件失败 {file_path}: {e}")
            return None

    def _generate_document_id(self, file_path: Path) -> str:
        """生成文档ID"""
        # 使用文件路径的哈希值
        file_path = Path(file_path).resolve()
        try:
            path_str = str(file_path.relative_to(self.sources_dir.resolve()))
        except ValueError:
            # 如果文件不在sources_dir下，使用文件名
            path_str = file_path.name
        hash_value = hashlib.md5(path_str.encode()).hexdigest()[:8]
        return f"REG-{hash_value}"

    def _extract_metadata(
        self,
        file_path: Path,
        content: str
    ) -> Dict[str, Any]:
        """提取文档元数据"""
        metadata = {
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'file_format': file_path.suffix,
        }

        # 从文件名推断标题
        if file_path.suffix in ['.txt', '.pdf', '.docx']:
            # 尝试从文件名提取标题
            title = file_path.stem
            # 移除常见后缀
            for suffix in ['_txt', '_processed', '_final']:
                title = title.replace(suffix, '')
            metadata['title'] = title

        # 从内容提取标题（第一行通常包含标题）
        lines = content.split('\n')
        if lines:
            first_line = lines[0].strip()
            if len(first_line) > 5 and len(first_line) < 200:
                # 可能是标题
                if not metadata.get('title'):
                    metadata['title'] = first_line

        # 从路径推断分类
        path_parts = file_path.parts
        if 'CDE' in path_parts or 'cde' in path_parts:
            metadata['source_agency'] = 'CDE'
            metadata['agency'] = 'CDE'
        elif 'FDA' in path_parts or 'fda' in path_parts:
            metadata['source_agency'] = 'FDA'
            metadata['agency'] = 'FDA'
        elif 'GMP' in path_parts:
            metadata['document_category'] = 'GMP'

        return metadata

    def _map_relationships(
        self,
        relationships: List[ExtractedRelationship],
        entities: List[ExtractedEntity]
    ) -> List[Dict[str, Any]]:
        """映射关系到本体"""
        mapped = []

        for rel in relationships:
            mapped.append({
                'from': rel.source_entity.get_primary_id(),
                'to': rel.target_entity.get_primary_id(),
                'relationship_type': rel.relationship_type.value,
                'properties': {
                    'confidence': rel.confidence,
                    'source': rel.source,
                }
            })

        return mapped

    def _create_document_relations(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建文档关系"""
        relations = []
        doc_id = raw_data.get('document_id')

        # 文档-实体关系（MENTIONS）
        for entity in raw_data.get('entities', [])[1:]:  # 跳过文档实体本身
            relations.append({
                'from': doc_id,
                'to': entity.get_primary_id() if hasattr(entity, 'get_primary_id') else f"ENTITY-{hash(entity.text) % 10000:04d}",
                'relationship_type': 'MENTIONS',
                'properties': {
                    'confidence': 0.8,
                    'source': 'document_content',
                }
            })

        return relations

    def process_batch(
        self,
        source_dir: Union[str, Path],
        batch_size: int = 50
    ) -> ProcessingResult:
        """
        批量处理文档

        Args:
            source_dir: 源目录
            batch_size: 批次大小

        Returns:
            处理结果
        """
        source_dir = Path(source_dir)

        self.logger.info(f"开始批量处理: {source_dir}")

        # 扫描文件
        files = self.scan(source_dir)
        total_files = len(files)

        if total_files == 0:
            return ProcessingResult(
                status=ProcessingStatus.SKIPPED,
                processor_name=self.PROCESSOR_NAME,
                source_path=str(source_dir),
                metrics=ProcessingMetrics(),
            )

        self.logger.info(f"找到 {total_files} 个文件待处理")

        # 分批处理
        all_entities = []
        all_relationships = []

        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            self.logger.info(f"处理批次 {i // batch_size + 1}/{(len(files) + batch_size - 1) // batch_size}")

            for file_path in batch:
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

                    # 收集
                    all_entities.extend(transformed_data.get('entities', []))
                    all_relationships.extend(transformed_data.get('relationships', []))

                    self._metrics.files_processed += 1
                    self._metrics.entities_extracted += len(transformed_data.get('entities', []))
                    self._metrics.relationships_extracted += len(transformed_data.get('relationships', []))

                    # 标记为已处理
                    self.mark_as_processed(file_path)

                except Exception as e:
                    self.logger.error(f"处理文件失败 {file_path}: {e}")
                    self._errors.append(f"{file_path.name}: {str(e)}")
                    self._metrics.files_failed += 1

        # 保存结果
        output_path = None
        if all_entities or all_relationships:
            output_path = self._save_results(all_entities, all_relationships)

        # 更新指标
        self._metrics.files_scanned = total_files
        self._metrics.entities_mapped = len(all_entities)
        self._metrics.relationships_mapped = len(all_relationships)

        # 确定状态
        if self._metrics.files_failed > 0:
            status = ProcessingStatus.PARTIAL
        elif self._metrics.files_processed == 0:
            status = ProcessingStatus.SKIPPED
        else:
            status = ProcessingStatus.COMPLETED

        return ProcessingResult(
            status=status,
            processor_name=self.PROCESSOR_NAME,
            source_path=str(source_dir),
            metrics=self._metrics,
            entities=all_entities,
            relationships=all_relationships,
            errors=self._errors,
            warnings=self._warnings,
            output_path=str(output_path) if output_path else None,
        )


# 便捷函数
def process_regulatory_documents(
    source_dir: Union[str, Path],
    config: Optional[Dict[str, Any]] = None
) -> ProcessingResult:
    """
    处理监管文档的便捷函数

    Args:
        source_dir: 源目录
        config: 配置

    Returns:
        处理结果
    """
    processor = RegulatoryDocumentProcessor(config)
    return processor.process_batch(source_dir)
