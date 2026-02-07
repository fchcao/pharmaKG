"""
文档转换器 - 将提取的文档数据转换为图数据格式
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from pathlib import Path

from .base import BaseTransformer, TransformationResult, TransformationStatus, FieldMapping

logger = logging.getLogger(__name__)


class DocumentTransformer(BaseTransformer):
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
        super().__init__(config)
        self.document_id_prefix = config.get('document_id_prefix', 'DOC') if config else 'DOC'
        self.generate_snippets = config.get('generate_snippets', True) if config else True
        self.snippet_length = config.get('snippet_length', 500) if config else 500

        # 定义字段映射
        self.field_mappings = self._init_field_mappings()

    def _init_field_mappings(self) -> Dict[str, FieldMapping]:
        """初始化字段映射"""
        return {
            'document_id': FieldMapping(
                source_field='file_path',
                target_field='document_id',
                required=True,
                transform_func=self._generate_document_id
            ),
            'title': FieldMapping(
                source_field='file_name',
                target_field='document_title',
                required=True,
                transform_func=self._clean_filename
            ),
            'document_type': FieldMapping(
                source_field='file_format',
                target_field='document_type',
                default_value='Document'
            ),
            'file_path': FieldMapping(
                source_field='file_path',
                target_field='file_path',
                required=True
            ),
            'file_format': FieldMapping(
                source_field='file_format',
                target_field='file_format',
                required=True
            ),
            'file_size': FieldMapping(
                source_field='file_size',
                target_field='file_size',
                required=True
            ),
            'checksum': FieldMapping(
                source_field='checksum',
                target_field='checksum',
                required=True
            ),
            'created_time': FieldMapping(
                source_field='created_time',
                target_field='publication_date',
                transform_func=self._parse_date
            ),
            'modified_time': FieldMapping(
                source_field='modified_time',
                target_field='revision_date',
                transform_func=self._parse_date
            ),
            'content': FieldMapping(
                source_field='content',
                target_field='content_snippet',
                transform_func=self._generate_snippet
            ),
            'full_text': FieldMapping(
                source_field='content',
                target_field='full_text',
                transform_func=self._truncate_content
            ),
            'language': FieldMapping(
                source_field=None,
                target_field='language',
                default_value='zh-CN'
            ),
            'version': FieldMapping(
                source_field=None,
                target_field='version',
                default_value='1.0'
            ),
            'status': FieldMapping(
                source_field=None,
                target_field='document_status',
                default_value='Final'
            )
        }

    def transform(self, raw_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> TransformationResult:
        """
        转换单个文档记录

        Args:
            raw_data: 原始数据（来自提取器）
            context: 转换上下文

        Returns:
            TransformationResult: 转换结果
        """
        try:
            # 应用字段映射
            properties = self._apply_field_mappings(raw_data)

            # 创建节点
            node = {
                'label': 'RegulatoryDocument',
                'properties': properties
            }

            # 创建关系
            relationships = []

            # 如果是 PDF，可能引用其他文档
            if properties.get('file_format') == 'pdf' and raw_data.get('content'):
                refs = self._extract_references(raw_data.get('content', ''))
                for ref in refs:
                    relationships.append({
                        'from_node': 'RegulatoryDocument',
                        'from_id': properties['document_id'],
                        'to_node': 'RegulatoryDocument',
                        'relationship_type': 'REFERENCES',
                        'to_id': ref
                    })

            return TransformationResult(
                success=True,
                nodes=[node],
                relationships=relationships,
                raw_data=raw_data,
                status=TransformationStatus.COMPLETED
            )

        except Exception as e:
            logger.error(f"转换文档失败: {e}")
            return TransformationResult(
                success=False,
                raw_data=raw_data,
                error=str(e),
                status=TransformationStatus.FAILED
            )

    def transform_batch(self, raw_data_list: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> TransformationResult:
        """
        批量转换文档记录

        Args:
            raw_data_list: 原始数据列表
            context: 转换上下文

        Returns:
            TransformationResult: 转换结果
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

        return TransformationResult(
            success=len(failed_records) == 0,
            nodes=all_nodes,
            relationships=all_relationships,
            raw_data=raw_data_list,
            status=TransformationStatus.COMPLETED if len(failed_records) == 0 else TransformationStatus.PARTIAL,
            metadata={
                'total_records': len(raw_data_list),
                'successful': len(all_nodes),
                'failed': len(failed_records),
                'failed_records': failed_records
            }
        )

    def _apply_field_mappings(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """应用字段映射"""
        properties = {}

        for target_field, mapping in self.field_mappings.items():
            value = None

            if mapping.transform_func:
                # 使用转换函数
                source_value = raw_data.get(mapping.source_field) if mapping.source_field else None
                value = mapping.transform_func(source_value, raw_data)
            elif mapping.source_field:
                # 直接映射
                value = raw_data.get(mapping.source_field)

            # 使用默认值
            if value is None and mapping.default_value is not None:
                value = mapping.default_value

            # 检查必填字段
            if mapping.required and value is None:
                raise ValueError(f"必填字段 {target_field} 缺失")

            if value is not None:
                properties[target_field] = value

        return properties

    def _generate_document_id(self, file_path: str, raw_data: Dict[str, Any]) -> str:
        """生成文档 ID"""
        # 使用文件路径的哈希值作为 ID
        import hashlib
        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f"{self.document_id_prefix}-{path_hash}"

    def _clean_filename(self, file_name: str, raw_data: Dict[str, Any]) -> str:
        """清理文件名作为标题"""
        # 去掉扩展名
        name = Path(file_name).stem
        # 替换下划线和连字符为空格
        name = name.replace('_', ' ').replace('-', ' ')
        return name

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            # 尝试解析 ISO 格式日期
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
        # 取前 N 个字符作为片段
        snippet = content[:self.snippet_length]
        if len(content) > self.snippet_length:
            snippet += '...'
        return snippet

    def _truncate_content(self, content: Optional[str]) -> Optional[str]:
        """截断内容"""
        if not content:
            return None
        # 如果内容太长，可以选择截断
        max_length = 50000  # 50KB
        if len(content) > max_length:
            return content[:max_length]
        return content

    def _extract_references(self, content: str) -> List[str]:
        """从内容中提取文档引用"""
        # 这里可以实现更复杂的引用提取逻辑
        # 简单实现：查找可能的文档 ID 模式
        import re
        # 匹配类似 "DOC-xxxxxxxx" 的模式
        pattern = r'DOC-[a-f0-9]{8}'
        return re.findall(pattern, content)

    def get_field_mappings(self) -> Dict[str, FieldMapping]:
        """获取字段映射"""
        return self.field_mappings.copy()
