#!/usr/bin/env python3
#===========================================================
# ChEMBL 处理器测试脚本
# Pharmaceutical Knowledge Graph - ChEMBL Processor Test
#===========================================================

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from processors.chembl_processor import ChEMBLProcessor, ChEMBLExtractionConfig


def test_chembl_processor():
    """测试 ChEMBL 处理器"""

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # 测试数据库路径
    db_path = Path('/root/autodl-tmp/pj-pharmaKG/data/sources/rd/chembl_34/chembl_34_sqlite/chembl_34.db')

    if not db_path.exists():
        logger.error(f"数据库文件不存在: {db_path}")
        return False

    # 创建处理器配置（小批量用于测试）
    config = {
        'extraction': {
            'batch_size': 100,
            'limit_compounds': 50,
            'limit_targets': 30,
            'limit_assays': 20,
            'limit_activities': 100,
            'min_confidence_score': 8,
            'include_parent_only': True,
            'deduplicate_by_inchikey': True,
            'deduplicate_by_uniprot': True
        }
    }

    logger.info("创建 ChEMBL 处理器...")
    processor = ChEMBLProcessor(config)

    logger.info(f"扫描数据库: {db_path}")
    files = processor.scan(db_path)
    logger.info(f"找到 {len(files)} 个数据库文件")

    if not files:
        logger.error("未找到 ChEMBL 数据库文件")
        return False

    # 处理第一个文件
    test_file = files[0]
    logger.info(f"测试处理: {test_file}")

    try:
        result = processor.process(
            source_path=test_file,
            output_to=None,  # 使用默认输出目录
            save_intermediate=True
        )

        # 输出结果
        logger.info(f"\n{'='*60}")
        logger.info(f"处理状态: {result.status.value}")
        logger.info(f"{'='*60}")
        logger.info(f"处理的文件: {result.metrics.files_processed}")
        logger.info(f"失败的文件: {result.metrics.files_failed}")
        logger.info(f"提取的实体: {result.metrics.entities_extracted}")
        logger.info(f"提取的关系: {result.metrics.relationships_extracted}")
        logger.info(f"处理时间: {result.metrics.processing_time_seconds:.2f} 秒")

        if result.metadata:
            stats = result.metadata.get('stats', {})
            logger.info(f"\n详细统计:")
            logger.info(f"  化合物: {stats.get('compounds', 0)}")
            logger.info(f"  靶点: {stats.get('targets', 0)}")
            logger.info(f"  分析: {stats.get('assays', 0)}")
            logger.info(f"  生物活性: {stats.get('bioactivities', 0)}")
            logger.info(f"  去重化合物: {stats.get('dedup_compounds', 0)}")
            logger.info(f"  去重靶点: {stats.get('dedup_targets', 0)}")

        if result.errors:
            logger.warning(f"\n错误 ({len(result.errors)}):")
            for error in result.errors[:5]:
                logger.warning(f"  - {error}")

        if result.warnings:
            logger.warning(f"\n警告 ({len(result.warnings)}):")
            for warning in result.warnings[:5]:
                logger.warning(f"  - {warning}")

        if result.output_path:
            logger.info(f"\n输出文件: {result.output_path}")

        # 检查输出文件
        output_dir = Path(result.output_path).parent
        output_files = list(output_dir.glob("chembl_*.json"))
        logger.info(f"\n生成的输出文件:")
        for f in output_files:
            logger.info(f"  - {f.name} ({f.stat().st_size} bytes)")

        return result.status.value in ['completed', 'partial']

    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        return False


def test_extraction_config():
    """测试提取配置"""
    logger = logging.getLogger(__name__)

    logger.info("\n测试提取配置...")

    # 默认配置
    config1 = ChEMBLExtractionConfig()
    logger.info(f"默认配置: batch_size={config1.batch_size}, min_confidence={config1.min_confidence_score}")

    # 自定义配置
    config2 = ChEMBLExtractionConfig(
        batch_size=5000,
        limit_compounds=1000,
        min_confidence_score=7
    )
    logger.info(f"自定义配置: batch_size={config2.batch_size}, limit_compounds={config2.limit_compounds}")

    return True


if __name__ == '__main__':
    success = True

    # 运行测试
    success &= test_extraction_config()
    success &= test_chembl_processor()

    if success:
        print("\n所有测试通过！")
        sys.exit(0)
    else:
        print("\n测试失败！")
        sys.exit(1)
