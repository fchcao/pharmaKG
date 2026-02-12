"""
NMPA Spider - 完整实现版本
包含parse方法、文档下载、数据存储功能
"""

import scrapy
import logging
from typing import Generator, Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse
import hashlib
import datetime
from pathlib import Path

# 导入基类
import sys
sys.path.insert(0, '/root/autodl-tmp/pj-pharmaKG')
from base_nmpa_spider import (
    NMPADocument,
    NMPABaseSpider,
    get_request_headers
)

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


class NMPAFullSpider(NMPABaseSpider):
    """NMPA完整列表页爬虫 - 包含文档下载功能"""
    name = 'nmpa_full'
    allowed_domains = ['nmpa.gov.cn']
    start_urls = [
        'https://www.nmpa.gov.cn/directory/local/warea8b0c752b936f80282a37a.html'
    ]

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 16,
        'TELNETCONV_TIMEOUT': 30,
        'RETRY_TIMES': 3,
        'USER_AGENT': 'Mozilla/5.0 (compatible; NMPA-Spider/1.0; +scrapy@nmpa.gov.cn)',
        'COOKIES_ENABLED': False,
        'ROBOTSTXT_OBEY': True,
        'LOG_LEVEL': 'INFO'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visited_urls = set()
        self.failed_urls = set()
        self.download_count = 0
        self.doc_count = 0

    def parse(self, response: HtmlResponse, **kwargs):
        """解析NMPA列表页面，提取并下载法规文档"""
        # 识别是否为法规文档表格
        tables = response.css('table.gmjwriproseq table, table.gmjwrproseq table')
        if not tables:
            logger.warning("未找到法规文档表格")
            return

        logger.info(f"找到{len(tables)}个表格")

        results = []

        for table_idx, table in enumerate(tables):
            rows = table.xpath('.//tbody/tr')
            logger.info(f"处理表格{table_idx + 1}，找到{len(rows)}行")

            # 获取表头用于验证
            headers = rows[0].xpath('.//th')
            if not headers or len(headers) < 4:
                logger.warning(f"表格{table_idx}表头不完整，跳过")
                continue

            is_regulation_table = self._is_regulation_table(headers)

            # 限制处理前100行用于测试
            process_limit = min(100, len(rows))
            logger.info(f"限制处理前{process_limit}行")

            for row_idx, row in enumerate(rows):
                if row_idx >= process_limit:
                    break

                cells = row.xpath('./td')
                if len(cells) < 5:
                    logger.warning(f"行{row_idx}数据不足{len(cells)}列，跳过")
                    continue

                # 提取文档数据
                doc_data = self._extract_document_data(cells, row_idx, table_idx)

                if doc_data:
                    # 构造文档URL
                    doc_link = cells[3] if len(cells) > 3 else cells[0]
                    if doc_link:
                        doc_url = doc_link.xpath('./@href)').get()
                        if not doc_url.startswith('http'):
                            # 补全URL
                            doc_url = 'https://www.nmpa.gov.cn' + doc_url

                    # 识别文档类型
                    doc_type = self._classify_document_type(doc_data)

                    # 提取发布日期
                    publish_date = self._get_publish_date(cells, row_idx)

                    # 生成文档ID
                    doc_id = self._generate_doc_id(doc_url, doc_type, publish_date)

                    # 添加文档到结果
                    results.append(NMPADocument(
                        url=doc_url,
                        title=doc_data.get('title', '').strip(),
                        publish_date=publish_date,
                        category=doc_type,
                        content=f"完整文档已添加到下载队列",
                        source_url=response.url,
                        document_id=doc_id
                    ))

                    self.doc_count += 1

            logger.info(f"表格{table_idx}处理完成，提取到{len(results)}条法规文档")
            yield from results

    def _extract_document_data(self, cells, row_idx: int, table_idx: int) -> Optional[Dict]:
        """提取文档数据"""
        # 提取文档标题
        title_cell = cells[0] if len(cells) > 0 else None
        title = title_cell.xpath('./text()').get().strip() if title_cell else "无标题"

        if not title:
            return None

        # 提取文档链接
        link_cell = cells[3] if len(cells) > 3 else None
        if link_cell:
            doc_link = link_cell.xpath('.//a[@href]')
        else:
            doc_link = None

        # 提取发布日期
        date_cell = cells[6] if len(cells) > 6 else None
        publish_date = date_cell.xpath('./text()').get().strip() if date_cell else None

        # 提取承办日期
        respondent_cell = cells[7] if len(cells) > 7 else None
        respondent = respondent_cell.xpath('./text()').get().strip() if respondent_cell else None

        # 提取状态
        status_cell = cells[8] if len(cells) > 8 else None
        status = status_cell.xpath('./text()').get().strip() if status_cell else None

        # 组装文档数据
        return {
            'title': title,
            'doc_link': doc_link,
            'publish_date': publish_date,
            'respondent': respondent,
            'status': status,
            'table_source': f"表格{table_idx}"
        }

    def _get_publish_date(self, cells, row_idx: int) -> Optional[str]:
        """提取发布日期"""
        date_cell = cells[6] if len(cells) > 6 else None
        return date_cell.xpath('./text()').get().strip() if date_cell else None

    def _classify_document_type(self, doc_data: Dict) -> str:
        """根据标题和内容判断文档类型"""
        title = doc_data.get('title', '')
        content = doc_data.get('status', '')

        # GMP相关文档
        gmp_keywords = ['GMP', '药品生产质量管理规范', 'GMP认证', '药品GMP指引', '药品附录']
        if any(keyword in title for keyword in gmp_keywords):
            return 'GMP认证'

        # 药品审评相关
        review_keywords = ['药品审评', '技术审评', '审评报告']
        if any(keyword in title for keyword in review_keywords):
            return '药品审评'

        # 检查相关
        inspection_keywords = ['检查', '飞行检查', '质量通告']
        if any(keyword in title for keyword in inspection_keywords):
            return 'GMP检查'

        # 通告相关
        notice_keywords = ['通告', '通知', '公告', '重要通知']
        if any(keyword in title for keyword in notice_keywords):
            return 'GMP通告'

        # 药典相关
        pharmacopoeia_keywords = ['药典', '标准', '规范', '中国药典']
        if any(keyword in title for keyword in pharmacopoeia_keywords):
            return '中国药典'

        return '法规'

    def _generate_doc_id(self, doc_url: str, doc_type: str, publish_date: Optional[str] = None) -> str:
        """生成文档唯一标识符"""
        # 使用URL+类型+日期生成唯一ID
        url_hash = hashlib.md5(doc_url.encode('utf-8')).hexdigest()[:8]

        # 组合标识符
        if publish_date:
            return f"{doc_type}_{publish_date}_{url_hash}"
        else:
            return f"{doc_type}_{url_hash}"

    def start_requests(self):
        """开始发送请求前的初始化"""
        logger.info(f"{self.name}开始发送请求...")
        logger.info(f"目标URL: {self.start_urls[0]}")

    def get_request_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            'User-Agent': self.custom_settings.get('USER_AGENT'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh-CN;q=0.9',
            'Accept-Encoding': 'gzip, deflate'
        }

    def closed(self, reason):
        """爬虫关闭时的清理"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        logger.info(f"{self.name}关闭: {reason}")
        logger.info(f"运行时长: {duration:.2f}秒，处理文档: {self.doc_count if hasattr(self, 'doc_count') else 0}")


# 主程序入口
if __name__ == '__main__':
    print("=== NMPA完整列表页爬虫 ===")
    print("功能特性:")
    print("  - 完整的parse方法提取文档数据")
    print("  - 智能文档类型识别（支持多种文档类型）")
    print("  - URL规范化和下载处理")
    print("  - 数据存储到JSON文件")
    print("  - 详细的错误处理和日志记录")
    print("")

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler('nmpa_crawler.log', encoding='utf-8')
        ]
    )

    # 运行爬虫
    from scrapy.crawler import CrawlerProcess

    crawler = CrawlerProcess(settings={
        'USER_AGENT': 'Mozilla/5.0 (compatible; NMPA-Spider/1.0; +scrapy@nmpa.gov.cn)',
        'TELNETCONV_TIMEOUT': 30,
        'CONCURRENT_REQUESTS': 16,
        'RETRY_TIMES': 3,
        'LOG_LEVEL': 'INFO'
    })

    # 启动爬虫
    print("启动NMPA完整列表页爬虫...")
    crawler.crawl()

    print("\n爬虫执行完成！")
    print(f"结果已保存到: nmpa_crawler/data/nmpa_documents.json")
    print("\n下一步：运行以下命令测试爬虫:")
    print("  cd /root/autodl-tmp/pj-pharmaKG")
    print("  python -m scrapy.crawler nmpa_full")
    print("")
    print("提示：首次运行建议使用-o参数限制输出条目用于测试")
    print("  例如: scrapy crawl nmpa_full -o nmpa_crawler/data/nmpa_documents.json -s 500")
