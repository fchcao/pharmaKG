#!/usr/bin/env python3
#===========================================================
# PharmaKG PDA PDF处理器测试脚本
# Pharmaceutical Knowledge Graph - PDA PDF Processor Test Script
#===========================================================
# 版本: v1.0
# 描述: 测试PDA技术报告PDF处理器的各项功能
#===========================================================

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from processors.pda_pdf_processor import PDAPDFProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


#===========================================================
# 测试配置
#===========================================================

PDA_SOURCE_DIR = project_root / "data/sources/documents/PDA TR 全集"
TEST_OUTPUT_DIR = project_root / "data/processed/documents/pda_technical_reports/test"

# 测试用的PDA技术报告编号（覆盖不同类别）
TEST_TR_NUMBERS = ['TR1', 'TR13', 'TR22', 'TR26', 'TR29', 'TR34']


#===========================================================
# 测试用例
#===========================================================

def test_processor_initialization():
    """测试处理器初始化"""
    logger.info("=" * 60)
    logger.info("测试1: 处理器初始化")
    logger.info("=" * 60)

    try:
        processor = PDAPDFProcessor({
            'cache_enabled': True,
            'batch_size': 5
        })

        assert processor.PROCESSOR_NAME == "PDAPDFProcessor"
        assert processor.SUPPORTED_FORMATS == ['.pdf']
        assert len(processor.PDA_CATEGORIES) > 0

        logger.info("✓ 处理器初始化成功")
        logger.info(f"  支持的格式: {processor.SUPPORTED_FORMATS}")
        logger.info(f"  PDA类别数: {len(processor.PDA_CATEGORIES)}")

        return processor

    except Exception as e:
        logger.error(f"✗ 处理器初始化失败: {e}")
        return None


def test_scan_directory(processor: PDAPDFProcessor):
    """测试目录扫描"""
    logger.info("\n" + "=" * 60)
    logger.info("测试2: 目录扫描")
    logger.info("=" * 60)

    if not PDA_SOURCE_DIR.exists():
        logger.warning(f"源目录不存在: {PDA_SOURCE_DIR}")
        logger.info("跳过目录扫描测试")
        return []

    try:
        files = processor.scan(PDA_SOURCE_DIR)

        logger.info(f"✓ 扫描完成，找到 {len(files)} 个PDF文件")

        # 显示前10个文件
        for i, file_path in enumerate(files[:10], 1):
            size_mb = file_path.stat().st_size / (1024 * 1024)
            logger.info(f"  {i}. {file_path.name} ({size_mb:.2f} MB)")

        if len(files) > 10:
            logger.info(f"  ... 还有 {len(files) - 10} 个文件")

        return files

    except Exception as e:
        logger.error(f"✗ 目录扫描失败: {e}")
        return []


def test_extract_single_pdf(processor: PDAPDFProcessor, file_path: Path):
    """测试单个PDF提取"""
    logger.info("\n" + "=" * 60)
    logger.info(f"测试3: 单个PDF提取 - {file_path.name}")
    logger.info("=" * 60)

    try:
        result = processor.extract(file_path)

        if not result:
            logger.warning("PDF提取返回空结果")
            return None

        logger.info("✓ PDF提取成功")
        logger.info(f"  页数: {result.get('page_count', 0)}")
        logger.info(f"  包含表格: {'是' if result.get('has_tables') else '否'}")
        logger.info(f"  报告编号: {result.get('metadata', {}).get('report_number', 'N/A')}")
        logger.info(f"  标题: {result.get('metadata', {}).get('title', 'N/A')[:60]}...")

        # 统计实体
        entities = result.get('entities', [])
        entity_counts = {}

        for entity in entities:
            entity_type = entity.get('entity_type', 'unknown')
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

        logger.info(f"  提取实体数: {len(entities)}")
        for entity_type, count in sorted(entity_counts.items()):
            logger.info(f"    - {entity_type}: {count}")

        logger.info(f"  提取关系数: {len(result.get('relationships', []))}")

        # 显示部分实体示例
        if entities:
            logger.info("\n  实体示例（前3个）:")
            for entity in entities[:3]:
                logger.info(f"    - {entity.get('entity_type')}: {entity.get('name', entity.get('standard_name', entity.get('manufacturer_name', 'N/A')))}")

        return result

    except Exception as e:
        logger.error(f"✗ PDF提取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_batch_processing(processor: PDAPDFProcessor, files: list):
    """测试批量处理"""
    logger.info("\n" + "=" * 60)
    logger.info("测试4: 批量处理")
    logger.info("=" * 60)

    # 限制处理数量（测试用）
    test_files = files[:min(5, len(files))]

    logger.info(f"批量处理 {len(test_files)} 个文件")

    try:
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        result = processor.process_batch(test_files, TEST_OUTPUT_DIR)

        logger.info("✓ 批量处理完成")
        logger.info(f"  处理成功: {result.metrics.files_processed}")
        logger.info(f"  处理失败: {result.metrics.files_failed}")
        logger.info(f"  总实体数: {result.metrics.entities_extracted}")
        logger.info(f"  总关系数: {result.metrics.relationships_extracted}")
        logger.info(f"  处理时间: {result.metrics.processing_time_seconds:.2f}秒")

        if result.metrics.files_processed > 0:
            avg_time = result.metrics.processing_time_seconds / result.metrics.files_processed
            logger.info(f"  平均每文件: {avg_time:.2f}秒")

        return result

    except Exception as e:
        logger.error(f"✗ 批量处理失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_pattern_matching(processor: PDAPDFProcessor):
    """测试正则表达式模式匹配"""
    logger.info("\n" + "=" * 60)
    logger.info("测试5: 正则表达式模式匹配")
    logger.info("=" * 60)

    test_cases = {
        '洁净室分级': [
            'ISO Class 5 cleanroom',
            'ISO 7 area',
            'EU GMP Grade A',
            'Class 100,000 area',
        ],
        '质量标准': [
            'ISO 14644-1 standard',
            'EU GMP Annex 1 requirements',
            'USP <71> sterility test',
            'ASTM E2500 guidance',
        ],
        '环境参数': [
            'Temperature: 20-25°C',
            'Relative humidity: 30-60% RH',
            'Air changes: 20 per hour',
            'Not more than 100 CFU/m³',
            'Pressure differential: 15 Pa',
        ],
        '工艺类型': [
            'Moist heat sterilization',
            'Gamma irradiation',
            'Aseptic filling process',
            'Media fill simulation',
            'Visual inspection',
        ],
        '检测方法': [
            'Microbiological examination',
            'Endotoxin test',
            'Particle count test',
            'Bioburden determination',
        ],
        '频率': [
            'Test per batch',
            'Daily monitoring',
            'Weekly sampling',
            'Quarterly review',
        ]
    }

    all_passed = True

    for category, test_strings in test_cases.items():
        logger.info(f"\n测试类别: {category}")

        for test_str in test_strings:
            try:
                if category == '洁净室分级':
                    result = processor._extract_cleanroom_classification(test_str)
                    passed = bool(result)
                elif category == '质量标准':
                    # 测试标准模式匹配
                    passed = any(
                        pattern.search(test_str)
                        for pattern in processor.standard_patterns.values()
                    )
                elif category == '环境参数':
                    result = processor._extract_environmental_requirements(test_str)
                    passed = bool(result)
                elif category == '工艺类型':
                    passed = any(
                        pattern.search(test_str)
                        for pattern in processor.process_type_patterns
                    )
                elif category == '检测方法':
                    passed = any(
                        pattern.search(test_str)
                        for pattern in processor.assay_type_patterns
                    )
                elif category == '频率':
                    result = processor._extract_frequency(test_str)
                    passed = result != 'as_required'
                else:
                    passed = False

                status = "✓" if passed else "✗"
                logger.info(f"  {status} '{test_str}' -> {result if 'result' in locals() else 'matched' if passed else 'not matched'}")

                if not passed:
                    all_passed = False

            except Exception as e:
                logger.error(f"  ✗ '{test_str}' -> Error: {e}")
                all_passed = False

    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("✓ 所有模式匹配测试通过")
    else:
        logger.warning("⚠ 部分模式匹配测试失败")

    return all_passed


def test_metadata_parsing(processor: PDAPDFProcessor):
    """测试元数据解析"""
    logger.info("\n" + "=" * 60)
    logger.info("测试6: 元数据解析")
    logger.info("=" * 60)

    test_filenames = [
        'PDA TR1-Validation of Moist Heat Sterilization Processes (Revised 2007).pdf',
        'PDA TR13-Fundamentals of an Environmental Monitoring Program (Revised 2014).pdf',
        'PDA TR22-Process Simulation Testing (Revised 2011).pdf',
        'PDA TR34-Design and Validation of Aseptic Processes (2008).pdf',
        'PDA TR1-湿热灭菌工艺验证（2007修订）.pdf',
    ]

    for filename in test_filenames:
        file_path = Path(filename)
        metadata = processor._parse_pda_metadata(file_path, {})

        logger.info(f"\n文件名: {filename}")
        logger.info(f"  报告编号: {metadata.report_number}")
        logger.info(f"  标题: {metadata.title[:50]}...")
        logger.info(f"  年份: {metadata.year or 'N/A'}")
        logger.info(f"  修订版: {metadata.revision or 'N/A'}")
        logger.info(f"  类别: {metadata.category or 'N/A'}")
        logger.info(f"  语言: {metadata.language}")

    logger.info("\n✓ 元数据解析测试完成")


def test_output_files():
    """测试输出文件"""
    logger.info("\n" + "=" * 60)
    logger.info("测试7: 输出文件验证")
    logger.info("=" * 60)

    if not TEST_OUTPUT_DIR.exists():
        logger.warning(f"输出目录不存在: {TEST_OUTPUT_DIR}")
        return

    # 查找生成的JSON文件
    json_files = list(TEST_OUTPUT_DIR.glob("*.json"))

    if not json_files:
        logger.warning("未找到输出JSON文件")
        return

    logger.info(f"找到 {len(json_files)} 个JSON文件")

    for json_file in json_files:
        logger.info(f"\n文件: {json_file.name}")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                logger.info(f"  记录数: {len(data)}")
                if data:
                    logger.info(f"  首条示例: {str(data[0])[:100]}...")
            elif isinstance(data, dict):
                if 'statistics' in data:
                    logger.info("  类型: 汇总统计")
                    for key, value in data['statistics'].items():
                        logger.info(f"    {key}: {value}")
                else:
                    logger.info(f"  键数: {len(data)}")
            else:
                logger.info(f"  类型: {type(data).__name__}")

        except Exception as e:
            logger.error(f"  读取失败: {e}")


#===========================================================
# 主测试流程
#===========================================================

def run_all_tests():
    """运行所有测试"""
    logger.info("\n" + "=" * 60)
    logger.info("PDA PDF处理器测试套件")
    logger.info("=" * 60)
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 测试1: 初始化
    processor = test_processor_initialization()
    if not processor:
        logger.error("处理器初始化失败，终止测试")
        return

    # 测试2: 目录扫描
    files = test_scan_directory(processor)

    # 测试3: 单个PDF提取（如果有文件）
    if files:
        # 选择第一个文件进行详细测试
        test_file = files[0]
        test_extract_single_pdf(processor, test_file)
    else:
        logger.warning("\n没有可用的PDF文件，跳过PDF提取测试")

    # 测试4: 批量处理（如果有文件）
    if files and len(files) > 1:
        test_batch_processing(processor, files)

    # 测试5: 模式匹配
    test_pattern_matching(processor)

    # 测试6: 元数据解析
    test_metadata_parsing(processor)

    # 测试7: 输出文件验证
    test_output_files()

    logger.info("\n" + "=" * 60)
    logger.info("测试套件完成")
    logger.info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)


#===========================================================
# 快速测试（单个文件）
#===========================================================

def quick_test(file_path: str = None):
    """快速测试单个文件"""
    logger.info("快速测试模式")

    processor = PDAPDFProcessor()

    if not file_path:
        # 查找第一个PDA PDF文件
        if PDA_SOURCE_DIR.exists():
            files = list(PDA_SOURCE_DIR.glob("PDA*.pdf"))
            if files:
                file_path = str(files[0])
            else:
                logger.error("未找到PDA PDF文件")
                return
        else:
            logger.error(f"源目录不存在: {PDA_SOURCE_DIR}")
            return

    logger.info(f"测试文件: {file_path}")

    result = processor.extract(Path(file_path))

    if result:
        logger.info("\n提取结果:")
        logger.info(f"  报告编号: {result.get('metadata', {}).get('report_number')}")
        logger.info(f"  标题: {result.get('metadata', {}).get('title')}")
        logger.info(f"  页数: {result.get('page_count')}")

        entities = result.get('entities', [])
        logger.info(f"\n实体类型统计:")
        entity_counts = {}
        for entity in entities:
            entity_type = entity.get('entity_type', 'unknown')
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

        for entity_type, count in sorted(entity_counts.items()):
            logger.info(f"  {entity_type}: {count}")

        logger.info(f"\n关系数: {len(result.get('relationships', []))}")

        # 保存结果
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_file = TEST_OUTPUT_DIR / f"quick_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"\n结果已保存到: {output_file}")


#===========================================================
# 命令行接口
#===========================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='PDA PDF处理器测试')
    parser.add_argument(
        '--quick',
        action='store_true',
        help='快速测试模式（只测试单个文件）'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='指定测试文件路径'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.quick:
        quick_test(args.file)
    else:
        run_all_tests()
