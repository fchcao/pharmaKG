#!/usr/bin/env python3
"""
NMPA Spider Test Script
用于测试NMPA列表页爬虫功能
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add processors path
sys.path.insert(0, '/root/autodl-tmp/pj-pharmaKG')

try:
    from processors.nmpa.spiders.nmpa_list_spider import NMPAListSpider
    from processors.nmpa.base_nmpa_spider import NMPADocument, NMPABaseSpider
except ImportError as e:
    logger.error(f"导入NMPA爬虫模块失败: {e}")
    sys.exit(1)


def test_spider_initialization():
    """测试爬虫初始化"""
    logger.info("=" * 50)
    logger.info("测试1: 爬虫初始化")
    logger.info("=" * 50)

    try:
        spider = NMPAListSpider()
        logger.info(f"✓ 爬虫名称: {spider.name}")
        logger.info(f"✓ 允许域名: {spider.allowed_domains}")
        logger.info(f"✓ 起始URL: {spider.start_urls}")
        logger.info("✓ 爬虫初始化成功\n")
        return spider
    except Exception as e:
        logger.error(f"✗ 爬虫初始化失败: {e}\n")
        return None


def test_document_classification(spider):
    """测试文档类型识别"""
    logger.info("=" * 50)
    logger.info("测试2: 文档类型识别")
    logger.info("=" * 50)

    test_titles = [
        "药品GMP认证指南",
        "飞行检查通告",
        "药品审评报告",
        "药典委员会通知",
        "普通药品文档"
    ]

    for title in test_titles:
        doc_type = spider._classify_document_type(title)
        logger.info(f"  '{title}' -> {doc_type}")

    logger.info("✓ 文档类型识别测试完成\n")


def test_doc_id_generation(spider):
    """测试文档ID生成"""
    logger.info("=" * 50)
    logger.info("测试3: 文档ID生成")
    logger.info("=" * 50)

    test_cases = [
        ("https://nmpa.gov.cn/doc1.pdf", "GMP认证", "2024-01-01"),
        ("https://nmpa.gov.cn/doc2.pdf", "GMP检查", None),
    ]

    for url, doc_type, date in test_cases:
        doc_id = spider._generate_doc_id(url, doc_type, date)
        logger.info(f"  URL: {url}")
        logger.info(f"  类型: {doc_type}, 日期: {date}")
        logger.info(f"  生成的ID: {doc_id}\n")

    logger.info("✓ 文档ID生成测试完成\n")


def test_table_detection(spider):
    """测试表格识别"""
    logger.info("=" * 50)
    logger.info("测试4: 表格识别逻辑")
    logger.info("=" * 50)

    # 模拟测试表头
    class MockHeader:
        def __init__(self, text):
            self.text = text

        def get(self):
            return self.text

    test_headers = [
        MockHeader("药品名称"),
        MockHeader("注册类别"),
        MockHeader("企业名称"),
        MockHeader("状态")
    ]

    is_valid = spider._is_regulation_table(test_headers)
    logger.info(f"  测试表头: {[h.get() for h in test_headers]}")
    logger.info(f"  识别结果: {'有效表格' if is_valid else '无效表格'}")
    logger.info("✓ 表格识别测试完成\n")


def test_run_scrapy_crawl():
    """测试实际爬取（需要Scrapy环境）"""
    logger.info("=" * 50)
    logger.info("测试5: Scrapy爬取命令")
    logger.info("=" * 50)

    commands = [
        "scrapy crawl nmpa_list -o test_output.json",
        "scrapy crawl nmpa_full -o test_full_output.json"
    ]

    logger.info("可用的爬取命令:")
    for cmd in commands:
        logger.info(f"  {cmd}")

    logger.info("\n提示: 在项目根目录运行上述命令执行实际爬取")


def main():
    """主测试函数"""
    logger.info("\n" + "=" * 50)
    logger.info("NMPA Spider 测试脚本")
    logger.info("=" * 50 + "\n")

    # 测试爬虫初始化
    spider = test_spider_initialization()
    if not spider:
        logger.error("爬虫初始化失败，终止测试")
        return

    # 测试文档类型识别
    test_document_classification(spider)

    # 测试文档ID生成
    test_doc_id_generation(spider)

    # 测试表格识别
    test_table_detection(spider)

    # 显示爬取命令
    test_run_scrapy_crawl()

    # 测试总结
    logger.info("=" * 50)
    logger.info("测试完成")
    logger.info("=" * 50)
    logger.info("\n下一步:")
    logger.info("  1. 运行爬虫: scrapy crawl nmpa_list -o test_output.json")
    logger.info("  2. 查看结果: cat test_output.json | python3 -m json.tool")
    logger.info("  3. 检查数据目录: ./data/sources/regulations/nmpa/")


if __name__ == '__main__':
    main()
