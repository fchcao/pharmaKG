#!/usr/bin/env python3
"""
NMPA Spider Standalone Runner
直接运行爬虫，无需 Scrapy 项目结构
"""

import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add project path
sys.path.insert(0, '/root/autodl-tmp/pj-pharmaKG')

from processors.nmpa.spiders.nmpa_list_spider import NMPAListSpider

if __name__ == '__main__':
    process = CrawlerProcess(settings={
        'USER_AGENT': 'Mozilla/5.0 (compatible; NMPA-Spider/1.0; +scrapy@nmpa.gov.cn)',
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 16,
        'RETRY_TIMES': 3,
        'COOKIES_ENABLED': False,
        'ROBOTSTXT_OBEY': True,
        'LOG_LEVEL': 'INFO',
        'TELNETCONSOLE_TIMEOUT': 30,
    })
    
    process.crawl(NMPAListSpider)
    process.start()
