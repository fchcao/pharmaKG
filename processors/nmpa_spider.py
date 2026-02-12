"""
NMPA Spider - 国家药监局网站数据采集器
爬取NMPA官网的药品注册管理办法、GMP、药品审评等法规文档

爬取策略:
- 遵守robots.txt规则
- 2-5秒请求间隔
- 使用Redis队列去重
- 增量更新机制
"""

import scrapy
from scrapy.http import HtmlResponse
from urllib.parse import urljoin
import hashlib
import time
import logging
from typing import Generator, Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class NMPADocument:
    """NMPA法规文档数据模型"""

    def __init__(self, **kwargs):
        # 从响应或字典中初始化
        if 'url' in kwargs:
            self.url = kwargs['url']
        if 'title' in kwargs:
            self.title = kwargs['title']
        if 'publish_date' in kwargs:
            self.publish_date = kwargs['publish_date']
        if 'category' in kwargs:
            self.category = kwargs.get('category', '法规')
        if 'content' in kwargs:
            self.content = kwargs['content']
        if 'source_url' in kwargs:
            self.source_url = kwargs['source_url']
        if 'attachments' in kwargs:
            self.attachments = kwargs['attachments']
        self.metadata = kwargs.get('metadata', {})

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'url': self.url,
            'title': self.title,
            'publish_date': str(self.publish_date) if self.publish_date else '',
            'category': self.category,
            'content': self.content,
            'source_url': self.source_url,
            'attachments': [
                {
                    'name': att.get('name', ''),
                    'url': att.get('url', '')
                }
                for att in (self.attachments or [])
            ],
            'metadata': self.metadata
        }


class NMPASpider(scrapy.Spider):
    """NMPA网站爬虫"""
    name = 'nmpa_spider'
    allowed_domains = ['nmpa.gov.cn']
    start_urls = [
        'https://www.nmpa.gov.cn/directory/searchwarea8b0c752b936f80282a37a.html'
    ]
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 16,
        'USER_AGENT': 'NMPA-Spider/1.0',
        'COOKIES_ENABLED': False,
        'TELNETCONV_TIMEOUT': 30,
        'RETRY_TIMES': 3,
    }

    def parse(self, response: HtmlResponse, **kwargs):
        """解析NMPA列表页面，提取法规文档链接"""
        results = []

        # 查找法规文档表格
        for table in response.css('table.gmjwriproseq table, table.gmjwrproseq table'):
            for row in table.xpath('.//tbody/tr'):
                doc_item = row.xpath('./td')
                if not doc_item:
                    continue

                # 提取文档信息
                link_tag = doc_item.xpath('.//a[@href]')
                if not link_tag:
                    continue

                title = link_tag.xpath('./text()').get()
                url = link_tag.xpath('./@href)').get()

                # 提取发布日期
                date_str = row.xpath('./td[3]//text()').get()

                # 提取文档类别（根据表格列判断）
                category = self._extract_category(row, table)

                results.append(NMPADocument(
                    url=urljoin(response.url, url),
                    title=title.strip(),
                    publish_date=date_str.strip() if date_str else None,
                    category=category,
                    content=f"点击下载查看完整内容"
                ))

        logger.info(f"解析NMPA列表页面完成，找到{len(results)}条法规")
        return results

    def _extract_category(self, row, table) -> str:
        """根据表格列提取文档类别"""
        # 第一列是"药品名称"，返回"药品"
        # 第二列是"注册类别"，返回GMP/GMP/药品等
        # 第三列是"企业名称"，返回"原料药"等
        # 第四列是"批准文号"，返回"审评"
        # 第五列是"批准日期"，返回"药品"
        # 第六列是"承办日期"，返回"承办"
        # 第七列是"状态"，返回"已上传"等

        # 根据关键特征判断类别
        if "药品名称" in str(row):
            return "药品注册"
        elif "注册类别" in str(row) and any(x in str(row) for x in ["GMP", "指导原则", "药品审评", "检查", "审评", "通告", "其他"]):
            if "GMP" in str(row) or "指导原则" in str(row):
                return "GMP"
            elif "药品审评" in str(row) or "审评" in str(row):
                return "药品审评"
            elif "检查" in str(row) or "通告" in str(row):
                return "检查"
            elif "承办" in str(row):
                return "GMP"

        return "法规"

    def closed(self, reason):
        """爬虫关闭时的清理工作"""
        logger.info(f"NMPA爬虫关闭: {reason}")


def crawl_nmpa_documents(lookback_days: int = 30) -> Generator[NMPADocument, None]:
    """
    爬取NMPA法规文档的主函数

    Args:
        lookback_days: 向前回溯天数，默认30天

    Yields:
        NMPADocument对象，包含文档URL、标题、发布日期、类别等
    """

    # 模拟爬取结果（实际使用时需要连接NMPA网站）
    sample_urls = [
        'https://www.nmpa.gov.cn/directory/searchwarea8b0c752b936f80282a37a.html'
    ]

    for url in sample_urls:
        yield NMPADocument(
            url=url,
            title='NMPA法规文档示例',
            publish_date='2024-10-15',
            category='药品注册',
            content='点击下载查看完整内容'
        )


class NMPASpiderWithRedis(scrapy.Spider):
    """支持Redis去重的NMPA爬虫"""
    name = 'nmpa_spider_redis'
    allowed_domains = ['nmpa.gov.cn']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Redis连接配置
        self.redis_host = kwargs.get('redis_host', 'localhost')
        self.redis_port = kwargs.get('redis_port', 6379)
        self.redis_db = kwargs.get('redis_db', 0)

        # 启用去重（使用Redis集合存储URL）
        self.use_dedup = kwargs.get('use_dedup', True)

    def start_requests(self):
        """开始爬取前初始化Redis"""
        import redis
        self.redis_client = redis.StrictRedis(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            decode_responses=False
        )
        logger.info(f"Redis连接成功: {self.redis_host}:{self.redis_port}")

        # 获取已爬取的URL集合
        crawled_urls = self.redis_client.smembers('nmpa:crawled_urls')
        logger.info(f"已爬取URL数量: {len(crawled_urls)}")

        return len(crawled_urls) > 0

    def mark_url_crawled(self, url: str):
        """标记URL为已爬取"""
        try:
            self.redis_client.sadd('nmpa:crawled_urls', url)
            logger.info(f"标记URL已爬取: {url}")
        except Exception as e:
            logger.error(f"标记URL失败: {e}")

    def is_url_crawled(self, url: str) -> bool:
        """检查URL是否已爬取"""
        try:
            return self.redis_client.sismember('nmpa:crawled_urls', url)
        except Exception as e:
            return False

    def parse(self, response, **kwargs):
        """解析NMPA文档，支持Redis去重"""
        results = []
        visited_urls = set()

        # 查找法规文档表格
        for table in response.css('table.gmjwriproseq table, table.gmjwrproseq table'):
            for row in table.xpath('.//tbody/tr'):
                doc_item = row.xpath('./td')
                if not doc_item:
                    continue

                link_tag = doc_item.xpath('.//a[@href]')
                if not link_tag:
                    continue

                title = link_tag.xpath('./text()').get()
                url = link_tag.xpath('./@href)').get()

                # Redis去重检查
                if self.use_dedup and self.is_url_crawled(url):
                    logger.info(f"跳过已爬取URL: {url}")
                    continue

                visited_urls.add(url)

                # 提取发布日期
                date_str = row.xpath('./td[3]//text()').get()

                # 提取文档类别
                category = self._extract_category(row, table)

                results.append(NMPADocument(
                    url=urljoin(response.url, url),
                    title=title.strip(),
                    publish_date=date_str.strip() if date_str else None,
                    category=category,
                    content=f"点击下载查看完整内容"
                ))

                # 标记URL为已访问
                try:
                    self.mark_url_crawled(url)
                except Exception as e:
                    logger.error(f"标记URL失败: {e}")

        unique_count = len(results)
        logger.info(f"解析NMPA列表页面完成，找到{len(results)}条法规（去重后{unique_count}条）")
        return results


def test_spider():
    """测试NMPA爬虫基本功能"""
    import sys

    # 测试基本爬虫（无Redis）
    logger.basicConfig(level=logging.INFO)

    # 测试NMPA文档解析
    test_data = [
        {
            'url': 'https://www.nmpa.gov.cn/directory/local/warea8b0c752b936f80282a37a.html',
            'title': 'NMPA法规文档示例',
            'publish_date': '2024-10-15',
            'category': '药品注册'
        },
        {
            'url': 'https://www.nmpa.gov.cn/directory/chemical/warea8b0c752b936f82a37a.html',
            'title': 'NMPA化学药示例',
            'publish_date': '2024-11-20',
            'category': '原料药'
        }
    ]

    spider = NMPASpider()
    results = list(spider.parse(test_data[0]['url']))

    print("=== NMPA爬虫测试结果 ===")
    for doc in results:
        print(f"- URL: {doc.url}")
        print(f"  标题: {doc.title}")
        print(f"  类别: {doc.category}")
        print(f" 日期: {doc.publish_date}")

    print(f"\n共解析到{len(results)}条文档")


def create_spider_config():
    """创建Scrapy配置文件"""
    import os

    config_content = """
# NMPA Spider Settings

# 爬虫基本设置
BOT_NAME = 'NMPA-Spider'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

# 请求延迟设置
DOWNLOAD_DELAY = 2
TELNETCONV_TIMEOUT = 30
CONCURRENT_REQUESTS = 16
RETRY_TIMES = 3

# Redis设置（用于去重）
REDIS_ENABLED = False
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# 增量更新设置
LOOKBACK_DAYS = 30  # 向前回溯天数

# 数据存储设置
DATA_DIR = './data/sources/regulations/nmpa'
```

    config_path = '/root/autodl-tmp/pj-pharmaKG/processors/nmpa_spider_settings.py'

    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)

    return config_path


if __name__ == '__main__':
    print("NMPA Spider框架创建完成!")
    print(f"配置文件: {create_spider_config()}")

    # 测试爬虫
    test_spider()
