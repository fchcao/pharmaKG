#!/usr/bin/env python3
#===========================================================
# UniProt 处理器测试脚本
# Pharmaceutical Knowledge Graph - UniProt Processor Test
#===========================================================

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from processors.uniprot_processor import UniProtProcessor, UniProtExtractionConfig, OrganismFilter


def test_uniprot_processor_file():
    """测试 UniProt 处理器（文件模式）"""

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # 创建测试 UniProt ID 文件
    test_ids = [
        "P04637",  # TP53 - 人类肿瘤抑制因子
        "P08253",  # MMP2 - 基质金属蛋白酶
        "P35354",  # PTGS2 - COX-2 酶
        "P00734",  # F2 - 凝血酶原
        "P10275"   # AR - 雄激素受体
    ]

    test_file = Path("/tmp/test_uniprot_ids.txt")
    with open(test_file, 'w') as f:
        for uniprot_id in test_ids:
            f.write(f"{uniprot_id}\n")

    logger.info(f"创建测试文件: {test_file}")
    logger.info(f"测试 UniProt IDs: {test_ids}")

    # 创建处理器配置
    config = {
        'extraction': {
            'batch_size': 5,
            'rate_limit': 5.0,
            'max_retries': 3,
            'timeout': 30,
            'cache_enabled': True,
            'include_go_annotations': True,
            'include_diseases': True,
            'include_subcellular_location': True,
            'min_quality': 'reviewed'
        }
    }

    logger.info("创建 UniProt 处理器...")
    processor = UniProtProcessor(config)

    logger.info(f"扫描文件: {test_file}")
    files = processor.scan(test_file)
    logger.info(f"找到 {len(files)} 个文件")

    if not files:
        logger.error("未找到测试文件")
        return False

    # 处理文件
    try:
        result = processor.process(
            source_path=test_file,
            output_to=None,
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
            logger.info(f"  靶点处理: {stats.get('targets_processed', 0)}")
            logger.info(f"  靶点增强: {stats.get('targets_enhanced', 0)}")
            logger.info(f"  疾病提取: {stats.get('diseases_extracted', 0)}")
            logger.info(f"  GO注释提取: {stats.get('go_annotations_extracted', 0)}")
            logger.info(f"  关系创建: {stats.get('relationships_created', 0)}")
            logger.info(f"  API请求: {stats.get('api_requests_made', 0)}")
            logger.info(f"  缓存命中: {stats.get('cache_hits', 0)}")

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
            output_files = list(output_dir.glob("uniprot_*.json"))
            logger.info(f"\n生成的输出文件:")
            for f in output_files:
                logger.info(f"  - {f.name} ({f.stat().st_size} bytes)")

        return result.status.value in ['completed', 'partial']

    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        return False

    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()


def test_uniprot_processor_organism():
    """测试 UniProt 处理器（生物体搜索模式）"""

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # 创建处理器配置
    config = {
        'extraction': {
            'batch_size': 10,
            'rate_limit': 5.0,
            'cache_enabled': True,
            'include_go_annotations': True,
            'include_diseases': True,
            'min_quality': 'reviewed'
        }
    }

    logger.info("创建 UniProt 处理器（生物体搜索模式）...")
    processor = UniProtProcessor(config)

    try:
        # 测试人类蛋白质搜索（限制数量）
        logger.info("\n测试人类蛋白质搜索（限制20个结果）...")
        uniprot_data = processor.fetch_by_organism(
            organism=OrganismFilter.HUMAN,
            limit=20,
            query="kinase"  # 搜索激酶
        )

        logger.info(f"获取到 {len(uniprot_data)} 个 UniProt 条目")

        # 转换数据
        logger.info("\n转换数据...")

        # 创建临时数据结构
        raw_data = {
            'targets': uniprot_data,
            'source_file': 'organism_search_human',
            'extraction_timestamp': '2024-01-01T00:00:00',
            'uniprot_ids': [entry.get('primaryAccession') for entry in uniprot_data]
        }

        transformed_data = processor.transform(raw_data)

        # 验证
        if not processor.validate(transformed_data):
            logger.error("数据验证失败")
            return False

        # 收集实体和关系
        all_entities = []
        all_relationships = []

        entities_dict = transformed_data.get('entities', {})
        relationships = transformed_data.get('relationships', [])

        for entity_type, entity_list in entities_dict.items():
            for entity in entity_list:
                all_entities.append({
                    **entity,
                    'entity_type': entity_type
                })

        all_relationships.extend(relationships)

        logger.info(f"\n{'='*60}")
        logger.info(f"转换结果:")
        logger.info(f"{'='*60}")
        logger.info(f"靶点实体: {len([e for e in all_entities if e.get('entity_type') == 'rd:Target'])}")
        logger.info(f"疾病实体: {len([e for e in all_entities if e.get('entity_type') == 'rd:Disease'])}")
        logger.info(f"关系数量: {len(all_relationships)}")

        # 显示一些示例实体
        logger.info(f"\n示例靶点:")
        for entity in all_entities[:3]:
            if entity.get('entity_type') == 'rd:Target':
                props = entity.get('properties', {})
                logger.info(f"  - {entity.get('primary_id')}: {props.get('name')}")
                logger.info(f"    基因符号: {props.get('gene_symbol')}")
                logger.info(f"    生物体: {props.get('organism')}")
                logger.info(f"    GO注释: {len(props.get('go_annotations', {}).get('molecular_function', []))} 个分子功能")

        return True

    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        return False


def test_extraction_config():
    """测试提取配置"""
    logger = logging.getLogger(__name__)

    logger.info("\n测试提取配置...")

    # 默认配置
    config1 = UniProtExtractionConfig()
    logger.info(f"默认配置: batch_size={config1.batch_size}, rate_limit={config1.rate_limit}")

    # 自定义配置
    config2 = UniProtExtractionConfig(
        batch_size=50,
        rate_limit=15.0,
        min_quality="all"
    )
    logger.info(f"自定义配置: batch_size={config2.batch_size}, rate_limit={config2.rate_limit}, min_quality={config2.min_quality}")

    return True


def test_api_endpoints():
    """测试 UniProt API 端点"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    logger.info("\n测试 UniProt API 端点...")

    # 创建处理器
    config = {
        'extraction': {
            'rate_limit': 5.0,
            'cache_enabled': False
        }
    }

    processor = UniProtProcessor(config)

    # 测试单个条目获取
    test_id = "P04637"  # TP53
    logger.info(f"\n测试单个条目获取: {test_id}")

    entry_data = processor._fetch_single_entry(test_id)

    if entry_data:
        logger.info(f"成功获取条目: {entry_data.get('primaryAccession')}")
        logger.info(f"蛋白名称: {entry_data.get('proteinDescription', {}).get('recommendedName', {}).get('fullName', {}).get('value', 'N/A')}")
        logger.info(f"生物体: {entry_data.get('organism', {}).get('scientificName', 'N/A')}")

        # 检查注释
        comments = entry_data.get('comments', [])
        disease_comments = [c for c in comments if c.get('commentType') == 'DISEASE']
        go_refs = entry_data.get('uniProtKBCrossReferences', [])
        go_refs = [r for r in go_refs if r.get('database') == 'GO']

        logger.info(f"疾病注释: {len(disease_comments)} 个")
        logger.info(f"GO 注释: {len(go_refs)} 个")

        return True
    else:
        logger.error("获取条目失败")
        return False


def main():
    """主测试函数"""
    success = True

    print("="*60)
    print("UniProt 处理器测试")
    print("="*60)

    # 运行测试
    print("\n[1/4] 测试提取配置...")
    success &= test_extraction_config()

    print("\n[2/4] 测试 API 端点...")
    success &= test_api_endpoints()

    print("\n[3/4] 测试文件模式处理...")
    success &= test_uniprot_processor_file()

    print("\n[4/4] 测试生物体搜索模式...")
    success &= test_uniprot_processor_organism()

    print("\n" + "="*60)
    if success:
        print("所有测试通过！")
        return 0
    else:
        print("测试失败！")
        return 1


if __name__ == '__main__':
    sys.exit(main())
