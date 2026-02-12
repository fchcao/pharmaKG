"""
NMPA Spider Base Module
提供NMPA爬虫的基类和通用功能
"""

import scrapy
import logging
from typing import Generator, Optional, Dict, Any, List
from abc import ABC, abstractmethod
from urllib.parse import urljoin

# Configure logging
logger = logging.getLogger(__name__)


class NMPADocument:
    """NMPA法规文档数据模型"""

    def __init__(self, **kwargs):
        self.url = kwargs.get('url', '')
        self.title = kwargs.get('title', '')
        self.publish_date = kwargs.get('publish_date', '')
        self.category = kwargs.get('category', '法规')
        self.content = kwargs.get('content', '')
        self.source_url = kwargs.get('source_url', '')
        self.attachments = kwargs.get('attachments', [])
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


class NMPABaseSpider(scrapy.Spider, ABC):
    """NMPA爬虫基类 - 定义通用接口和功能"""

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 16,
        'USER_AGENT': 'Mozilla/5.0 (compatible; NMPA-Spider/1.0; +scrapy@nmpa.gov.cn)',
        'TELNETCONV_TIMEOUT': 30,
        'RETRY_TIMES': 3,
        'COOKIES_ENABLED': False,
        'ROBOTSTXT_OBEY': True,
        'LOG_LEVEL': 'INFO'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visited_urls = set()

    def parse(self, response, **kwargs):
        """解析HTML响应 - 子类需要实现"""
        yield {
            'url': response.url,
            'title': '解析方法待实现',
            'category': 'base',
            'content': '子类需要实现parse方法'
        }

    def start_requests(self):
        """开始发送请求前的初始化"""
        logger.info(f"{self.name}开始发送请求...")

    def get_request_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            'User-Agent': self.custom_settings.get('USER_AGENT'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh-CN;q=0.9',
            'Accept-Encoding': 'gzip, deflate'
        }

    def extract_links(self, response, **kwargs):
        """提取链接 - 子类需要实现"""
        logger.info(f"{self.name}提取链接功能待实现")
        return []

    def is_valid_url(self, url: str) -> bool:
        """验证URL是否有效"""
        return url.startswith('http') and 'nmpa.gov.cn' in url


def create_spider_settings(settings_file: str, output_dir: str = './data/sources/regulations/nmpa') -> None:
    """创建Scrapy配置文件"""
    import os

    os.makedirs(os.path.dirname(output_dir), exist_ok=True)

    config_content = f"""
# NMPA Spider Settings
# Bot名称
BOT_NAME = {spider_name}

# 用户代理
USER_AGENT = Mozilla/5.0 (compatible; NMPA-Spider/1.0; +scrapy@nmpa.gov.cn)

# 请求设置
DOWNLOAD_DELAY = 2
TELNETCONV_TIMEOUT = 30
CONCURRENT_REQUESTS = 16
RETRY_TIMES = 3

# 机器人设置
COOKIES_ENABLED = False
ROBOTSTXT_OBEY = True
LOG_LEVEL = INFO

# 数据存储
DATA_DIR = {output_dir}
"""

    with open(settings_file, 'w', encoding='utf-8') as f:
        f.write(config_content)

    return settings_file


if __name__ == '__main__':
    print("=== NMPA Spider基类框架创建完成 ===")
    print(f"配置文件: {create_spider_settings()}")
    print("\n下一步：继承基类开发具体的爬虫实现类")
    print("提示：运行 'scrapy genspider nmpa' 测试基类")
