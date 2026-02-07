"""
文档 ETL 管道 - 用于处理监管文档的导入
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..extractors import DocumentExtractor
from ..transformers import DocumentTransformer
from ..loaders import Neo4jBatchLoader
from ..config import get_etl_config
from ..base import BasePipeline, PipelineResult, PipelineStatus

logger = logging.getLogger(__name__)


class DocumentPipeline(BasePipeline):
    """
    文档 ETL 管道

    负责将监管文档从文件系统导入到 Neo4j 图数据库
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化文档管道

        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.name = "DocumentPipeline"

        # 获取 ETL 配置
        etl_config = get_etl_config()
        neo4j_config = etl_config.get('neo4j', {})

        # 初始化组件
        extractor_config = {
            'base_path': config.get('documents_path', '') if config else '',
            'supported_formats': config.get('supported_formats', ['.pdf', '.docx', '.doc', '.txt']) if config else ['.pdf', '.docx', '.doc', '.txt'],
            'max_file_size': config.get('max_file_size', 100 * 1024 * 1024) if config else 100 * 1024 * 1024,
            'extract_content': config.get('extract_content', True) if config else True,
            'content_max_length': config.get('content_max_length', 10000) if config else 10000
        }

        transformer_config = {
            'document_id_prefix': config.get('document_id_prefix', 'DOC') if config else 'DOC',
            'generate_snippets': config.get('generate_snippets', True) if config else True,
            'snippet_length': config.get('snippet_length', 500) if config else 500
        }

        self.extractor = DocumentExtractor(extractor_config)
        self.transformer = DocumentTransformer(transformer_config)
        self.loader = Neo4jBatchLoader(neo4j_config)

    def run(
        self,
        source: str,
        **kwargs
    ) -> PipelineResult:
        """
        运行文档管道

        Args:
            source: 文件或目录路径
            **kwargs: 额外参数
                - recursive: 是否递归处理目录
                - pattern: 文件名模式过滤
                - batch_size: 批次大小
                - load_data: 是否加载数据到 Neo4j

        Returns:
            PipelineResult: 管道运行结果
        """
        try:
            logger.info(f"开始运行文档管道: {source}")
            self.status = PipelineStatus.RUNNING

            # 验证数据源
            if not self.extractor.validate_source(source):
                raise ValueError(f"无效的数据源: {source}")

            # 1. 提取
            logger.info("开始提取文档...")
            recursive = kwargs.get('recursive', False)
            pattern = kwargs.get('pattern', '*')
            extraction_result = self.extractor.extract(source, recursive=recursive, pattern=pattern)

            if not extraction_result.success:
                raise RuntimeError(f"文档提取失败: {extraction_result.error}")

            logger.info(f"提取完成，共 {extraction_result.metrics.records_processed} 个文档")

            # 2. 转换
            logger.info("开始转换数据...")
            transformation_result = self.transformer.transform_batch(extraction_result.records)

            if not transformation_result.success:
                raise RuntimeError(f"数据转换失败: {transformation_result.error}")

            logger.info(f"转换完成，生成 {len(transformation_result.nodes)} 个节点")

            # 3. 加载
            load_data = kwargs.get('load_data', True)
            load_result = None
            if load_data:
                logger.info("开始加载数据到 Neo4j...")
                batch_size = kwargs.get('batch_size', 100)
                load_result = self.loader.load_batch(
                    transformation_result.nodes,
                    transformation_result.relationships,
                    batch_size=batch_size
                )

                if not load_result.success:
                    raise RuntimeError(f"数据加载失败: {load_result.error}")

                logger.info(f"加载完成，创建 {load_result.nodes_created} 个节点，{load_result.relationships_created} 个关系")

            # 构建结果
            result = PipelineResult(
                success=True,
                status=PipelineStatus.COMPLETED,
                pipeline_name=self.name,
                source=source,
                metadata={
                    'extraction': {
                        'records_processed': extraction_result.metrics.records_processed,
                        'duration_seconds': extraction_result.metrics.duration_seconds
                    },
                    'transformation': {
                        'nodes_created': len(transformation_result.nodes),
                        'relationships_created': len(transformation_result.relationships),
                        'failed_records': transformation_result.metadata.get('failed_records', []) if transformation_result.metadata else []
                    },
                    'loading': {
                        'nodes_created': load_result.nodes_created if load_result else 0,
                        'relationships_created': load_result.relationships_created if load_result else 0,
                        'duration_seconds': load_result.duration_seconds if load_result else 0
                    } if load_result else None
                }
            )

            self.status = PipelineStatus.COMPLETED
            logger.info("文档管道运行完成")
            return result

        except Exception as e:
            logger.error(f"文档管道运行失败: {e}")
            self.status = PipelineStatus.FAILED
            return PipelineResult(
                success=False,
                status=PipelineStatus.FAILED,
                pipeline_name=self.name,
                source=source,
                error=str(e)
            )

    def validate_source(self, source: str) -> bool:
        """
        验证数据源

        Args:
            source: 数据源路径

        Returns:
            是否有效
        """
        return self.extractor.validate_source(source)

    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        return self.extractor.get_supported_formats()


def run_document_pipeline(
    source: str,
    recursive: bool = False,
    pattern: str = '*',
    load_data: bool = True,
    batch_size: int = 100,
    **config
) -> PipelineResult:
    """
    运行文档管道的便捷函数

    Args:
        source: 文件或目录路径
        recursive: 是否递归处理目录
        pattern: 文件名模式过滤
        load_data: 是否加载数据到 Neo4j
        batch_size: 批次大小
        **config: 额外配置

    Returns:
        PipelineResult: 管道运行结果
    """
    pipeline = DocumentPipeline(config)
    return pipeline.run(
        source,
        recursive=recursive,
        pattern=pattern,
        load_data=load_data,
        batch_size=batch_size
    )
