"""
文档 ETL 管道 - 用于处理监管文档的导入
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from ..extractors import DocumentExtractor
from ..transformers import DocumentTransformer
from ..loaders import Neo4jBatchLoader
from ..config import get_etl_config

logger = logging.getLogger(__name__)


class DocumentPipeline:
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
        self.name = "DocumentPipeline"
        self.config = config or {}

        # 获取 ETL 配置
        etl_config = get_etl_config()

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
        self.loader = Neo4jBatchLoader(
            uri=etl_config.neo4j_uri,
            user=etl_config.neo4j_user,
            password=etl_config.neo4j_password,
            database=etl_config.neo4j_database,
            batch_size=etl_config.batch_size,
            timeout=etl_config.timeout,
            max_retries=etl_config.max_retries,
            dry_run=etl_config.dry_run
        )

        # 统计数据
        self.stats = {
            "files_processed": 0,
            "files_failed": 0,
            "nodes_created": 0,
            "relationships_created": 0
        }

    def run(
        self,
        source: str,
        recursive: bool = False,
        pattern: str = '*',
        load_to_neo4j: bool = True,
        dry_run: bool = False,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        运行文档管道

        Args:
            source: 文件或目录路径
            recursive: 是否递归处理目录
            pattern: 文件名模式过滤
            load_to_neo4j: 是否加载数据到 Neo4j
            dry_run: 试运行模式
            batch_size: 批次大小

        Returns:
            执行结果统计
        """
        logger.info("=" * 60)
        logger.info("开始运行文档 ETL 管道")
        logger.info("=" * 60)
        logger.info(f"数据源: {source}")
        logger.info(f"递归处理: {recursive}")
        logger.info(f"文件模式: {pattern}")

        start_time = datetime.now()

        try:
            # 1. 抽取阶段
            logger.info("\n[1/3] 抽取阶段")
            extracted_data = self._extract_phase(source, recursive, pattern)

            if not extracted_data.get('success'):
                raise RuntimeError(f"文档抽取失败: {extracted_data.get('error')}")

            self.stats['files_processed'] = extracted_data.get('records_processed', 0)

            # 2. 转换阶段
            logger.info("\n[2/3] 转换阶段")
            transformed_data = self._transform_phase(extracted_data.get('records', []))

            if not transformed_data.get('success'):
                raise RuntimeError(f"数据转换失败: {transformed_data.get('error')}")

            # 3. 加载阶段
            load_results = {"dry_run": dry_run}
            if load_to_neo4j and not dry_run:
                logger.info("\n[3/3] 加载阶段")
                load_results = self._load_phase(
                    transformed_data.get('nodes', []),
                    transformed_data.get('relationships', []),
                    batch_size
                )
            else:
                logger.info("\n[3/3] 加载阶段 (跳过)")

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "pipeline": "DocumentPipeline",
                "status": "success",
                "duration_seconds": duration,
                "source": source,
                "extraction": {
                    "files_processed": self.stats["files_processed"],
                    "files_failed": self.stats.get("files_failed", 0)
                },
                "transformation": {
                    "nodes_generated": len(transformed_data.get('nodes', [])),
                    "relationships_generated": len(transformed_data.get('relationships', []))
                },
                "loading": load_results
            }

            logger.info("\n" + "=" * 60)
            logger.info(f"文档 ETL 管道完成，耗时 {duration:.2f} 秒")
            logger.info(f"处理文件: {self.stats['files_processed']}")
            logger.info(f"创建节点: {load_results.get('nodes_created', 0)}")
            logger.info(f"创建关系: {load_results.get('relationships_created', 0)}")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"文档 ETL 管道运行失败: {e}", exc_info=True)
            return {
                "pipeline": "DocumentPipeline",
                "status": "failed",
                "error": str(e),
                "extraction": {
                    "files_processed": self.stats.get("files_processed", 0)
                }
            }

    def _extract_phase(self, source: str, recursive: bool, pattern: str) -> Dict[str, Any]:
        """抽取阶段"""
        try:
            extraction_result = self.extractor.extract(source, recursive=recursive, pattern=pattern)

            if not extraction_result.success:
                return {
                    'success': False,
                    'error': extraction_result.error,
                    'records_processed': 0
                }

            return {
                'success': True,
                'records': extraction_result.records,
                'records_processed': extraction_result.metrics.total_records if extraction_result.metrics else 0
            }
        except Exception as e:
            logger.error(f"抽取阶段失败: {e}")
            return {'success': False, 'error': str(e), 'records_processed': 0}

    def _transform_phase(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """转换阶段"""
        try:
            transformation_result = self.transformer.transform_batch(records)

            if not transformation_result.success:
                return {
                    'success': False,
                    'error': transformation_result.error,
                    'nodes': [],
                    'relationships': []
                }

            return {
                'success': True,
                'nodes': transformation_result.nodes,
                'relationships': transformation_result.relationships
            }
        except Exception as e:
            logger.error(f"转换阶段失败: {e}")
            return {'success': False, 'error': str(e), 'nodes': [], 'relationships': []}

    def _load_phase(self, nodes: List[Dict], relationships: List[Dict], batch_size: int) -> Dict[str, Any]:
        """加载阶段"""
        try:
            load_result = self.loader.load_batch(nodes, relationships, batch_size)

            if load_result.success:
                self.stats['nodes_created'] = load_result.nodes_created
                self.stats['relationships_created'] = load_result.relationships_created

            return {
                'success': load_result.success,
                'nodes_created': load_result.nodes_created if load_result.success else 0,
                'relationships_created': load_result.relationships_created if load_result.success else 0,
                'error': load_result.error if not load_result.success else None
            }
        except Exception as e:
            logger.error(f"加载阶段失败: {e}")
            return {'success': False, 'error': str(e), 'nodes_created': 0, 'relationships_created': 0}

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
    dry_run: bool = False,
    batch_size: int = 100,
    **config
) -> Dict[str, Any]:
    """
    运行文档管道的便捷函数

    Args:
        source: 文件或目录路径
        recursive: 是否递归处理目录
        pattern: 文件名模式过滤
        load_data: 是否加载数据到 Neo4j
        dry_run: 是否试运行
        batch_size: 批次大小
        **config: 额外配置

    Returns:
        执行结果统计
    """
    pipeline = DocumentPipeline(config)
    return pipeline.run(
        source,
        recursive=recursive,
        pattern=pattern,
        load_to_neo4j=load_data,
        dry_run=dry_run,
        batch_size=batch_size
    )
