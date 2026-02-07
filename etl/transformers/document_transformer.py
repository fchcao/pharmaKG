"""
文档转换器 - 将提取的文档数据转换为图数据格式
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from pathlib import Path
import hashlib
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DocumentTransformationResult:
    """文档转换结果"""
    success: bool
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentTransformer:
    """
    文档转换器

    将文档提取器输出的数据转换为 Neo4j 节点和关系
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化文档转换器

        Args:
            config: 配置字典，可能包含：
                - document_id_prefix: 文档ID前缀
                - generate_snippets: 是否生成内容片段
                - snippet_length: 片段长度
        """
        self.document_id_prefix = config.get('document_id_prefix', 'DOC') if config else 'DOC'
        self.generate_snippets = config.get('generate_snippets', True) if config else True
        self.snippet_length = config.get('snippet_length', 500) if config else 500

    def transform(self, raw_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> DocumentTransformationResult:
        """
        转换单个文档记录

        Args:
            raw_data: 原始数据（来自提取器）
            context: 转换上下文

        Returns:
            DocumentTransformationResult: 转换结果
        """
        try:
            # 生成文档属性
            properties = self._build_properties(raw_data)

            # 创建节点
            node = {
                'label': 'RegulatoryDocument',
                'properties': properties
            }

            # 创建关系（空列表，文档间关系需要后续处理）
            relationships = []

            return DocumentTransformationResult(
                success=True,
                nodes=[node],
                relationships=relationships,
                raw_data=raw_data
            )

        except Exception as e:
            logger.error(f"转换文档失败: {e}")
            return DocumentTransformationResult(
                success=False,
                raw_data=raw_data,
                error=str(e)
            )

    def transform_batch(self, raw_data_list: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> DocumentTransformationResult:
        """
        批量转换文档记录

        Args:
            raw_data_list: 原始数据列表
            context: 转换上下文

        Returns:
            DocumentTransformationResult: 转换结果
        """
        all_nodes = []
        all_relationships = []
        failed_records = []

        for raw_data in raw_data_list:
            result = self.transform(raw_data, context)
            if result.success:
                all_nodes.extend(result.nodes)
                all_relationships.extend(result.relationships)
            else:
                failed_records.append({
                    'raw_data': raw_data,
                    'error': result.error
                })

        return DocumentTransformationResult(
            success=len(failed_records) == 0,
            nodes=all_nodes,
            relationships=all_relationships,
            raw_data=raw_data_list,
            metadata={
                'total_records': len(raw_data_list),
                'successful': len(all_nodes),
                'failed': len(failed_records),
                'failed_records': failed_records
            }
        )

    def _build_properties(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建节点属性"""
        properties = {}

        # 必填字段
        properties['document_id'] = self._generate_document_id(raw_data.get('file_path', ''))
        properties['document_title'] = self._clean_filename(raw_data.get('file_name', ''))
        properties['file_path'] = raw_data.get('file_path', '')
        properties['file_format'] = raw_data.get('file_format', '')
        properties['file_size'] = raw_data.get('file_size', 0)
        properties['checksum'] = raw_data.get('checksum', '')

        # 可选字段
        if raw_data.get('content'):
            if self.generate_snippets:
                properties['content_snippet'] = self._generate_snippet(raw_data['content'])
            properties['full_text'] = self._truncate_content(raw_data['content'])

        if raw_data.get('created_time'):
            properties['publication_date'] = self._parse_date(raw_data['created_time'])

        if raw_data.get('modified_time'):
            properties['revision_date'] = self._parse_date(raw_data['modified_time'])

        # 默认值
        properties.setdefault('language', 'zh-CN')
        properties.setdefault('version', '1.0')
        properties.setdefault('document_status', 'Final')
        properties.setdefault('document_type', raw_data.get('file_format', 'Document'))

        return properties

    def _generate_document_id(self, file_path: str) -> str:
        """生成文档 ID"""
        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f"{self.document_id_prefix}-{path_hash}"

    def _clean_filename(self, file_name: str) -> str:
        """清理文件名作为标题"""
        name = Path(file_name).stem
        name = name.replace('_', ' ').replace('-', ' ')
        return name

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            return date_str

    def _generate_snippet(self, content: Optional[str]) -> Optional[str]:
        """生成内容片段"""
        if not content:
            return None
        if not self.generate_snippets:
            return None
        snippet = content[:self.snippet_length]
        if len(content) > self.snippet_length:
            snippet += '...'
        return snippet

    def _truncate_content(self, content: Optional[str]) -> Optional[str]:
        """截断内容"""
        if not content:
            return None
        max_length = 50000  # 50KB
        if len(content) > max_length:
            return content[:max_length]
        return content
