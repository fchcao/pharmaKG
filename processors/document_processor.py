#===========================================================
# PharmaKG 通用文档处理器
# Pharmaceutical Knowledge Graph - Generic Document Processor
#===========================================================

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus
from extractors.named_entity import NamedEntityExtractor
from extractors.attribute import AttributeExtractor
from extractors.base import EntityType

logger = logging.getLogger(__name__)


class GenericDocumentProcessor(BaseProcessor):
    """通用文档处理器"""

    PROCESSOR_NAME = "GenericDocumentProcessor"
    SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.txt']
    OUTPUT_SUBDIR = "documents"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.entity_extractor = NamedEntityExtractor(config)
        self.attribute_extractor = AttributeExtractor(config)

    def scan(self, source_path: Union[str, Path]) -> List[Path]:
        """扫描源目录"""
        source_path = Path(source_path)
        files = []

        if source_path.is_file():
            return [source_path] if source_path.suffix in self.SUPPORTED_FORMATS else []

        for ext in self.SUPPORTED_FORMATS:
            files.extend(source_path.rglob(f"*{ext}"))

        return [f for f in files if not self.is_processed(f)]

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """提取文档数据"""
        content = self._read_file(file_path)
        if not content:
            return {}

        # 提取文本内容（限制长度）
        text_content = content[:10000] if len(content) > 10000 else content

        # 提取实体
        entities = self.entity_extractor.extract_entities(text_content)

        # 提取属性
        attributes = self.attribute_extractor.extract_attributes(text_content)

        return {
            'content': text_content,
            'entities': entities,
            'attributes': attributes,
            'metadata': {
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'file_format': file_path.suffix,
            }
        }

    def _read_file(self, file_path: Path) -> Optional[str]:
        """读取文件"""
        suffix = file_path.suffix.lower()

        if suffix == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return None

        elif suffix == '.pdf':
            try:
                import PyPDF2
                text = ''
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text()
                return text
            except ImportError:
                logger.warning("PyPDF2未安装，无法提取PDF内容")
                return None
            except Exception as e:
                logger.warning(f"PDF提取失败: {e}")
                return None

        else:
            # 其他格式尝试按文本读取
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except:
                return None

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换数据"""
        # 简单实现：创建文档实体
        metadata = raw_data.get('metadata', {})

        doc_entity = {
            'label': 'Document',
            'properties': {
                'primary_id': f"DOC-{hash(metadata.get('file_name', '')) % 100000:05d}",
                'title': metadata.get('file_name', ''),
                'file_format': metadata.get('file_format', ''),
                'source': 'GenericDocument',
            }
        }

        return {'entities': [doc_entity], 'relationships': []}

    def validate(self, data: Dict[str, Any]) -> bool:
        """验证数据"""
        return bool(data.get('entities'))
