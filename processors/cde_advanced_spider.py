#!/usr/bin/env python3
"""
CDE Spider - 高级版
完全模拟真实浏览器行为，复制手动访问的请求特征
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("请先安装 playwright: pip install playwright && playwright install chromium")
    raise

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CDEAdvancedSpider:
    """CDE 高级爬虫 - 完全模拟真实浏览器"""

    BASE_URL = "https://www.cde.org.cn"

    # 从手动访问获取的真实请求头
    MANUAL_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Cookie': 'Path=/; FSSBBIl1UgzbN7N80S=QUzBQRplbh_ImOla9eRxb_SQWkvmHPKp.vVzmpW5TDRcuYAilEM3bvaOAw64Bg_c',
        'Host': 'www.cde.org.cn',
        'Pragma': 'no-cache',
        'Referer': 'https://www.cde.org.cn/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Sec-Ch-Ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        'Sec-Ch-Ua-Mobile': '?1',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0 Safari/537.36'
    }

    # 从手动访问获取的真实 Cookie
    MANUAL_COOKIES = [
        {
            'name': 'FSSBBIl1UgzbN7N80S',
            'value': '3zI4GTXPdyAUN.hL9ZYqZgUCm.khdpnnZFMGL1gVk1adjZu8CkJSmaLHfkLTpA4YcZLREZyOWxRqU8Tqmlyv60ZhUwJCtMXraeNsbOfVx_2W4z.FQ2LotBmm7cNZQYlHJRwc1WUOfCHeKUymhH7G_XjkyVPdihmfiVpwskkiXPRPlVkf.vbhnLUszrfLb5Uod4CuVzKh4SCAwquEOJ8_Tod6152bblA_w7qqqqr1k6748UgxnzQXO4hl1gnwrykHvPnqxwL8v1tYxLq7OPPdER759C.Y34LLPfX8HDm25661|Q1Xey.UPqlWVP7pCYHWVNGqCViMLI2SOUHW9ynr5EI_ZQXO4hl1gnwrykHvPnqxwL8v1tYxLq7OPPdER759C.Y34LLPfX8HDm25661|Q1Xey.UPqlWVP7pCYHWVNGqCViMLI2SOUHW9ynr5EI_ZQXO4hl1gnwrykHvPnqxwL8v1tYxLq7OPPdER759C.Y34LLPfX8HDm25661|Q1Xey.UPqlWVP7pCYHWVNGqCViMLI2SOUHW9ynr5EI_ZQXO4hl1gnwrykHvPnqxwL8v1tYxLq7OPPdER759C.Y34LLPfX8HDm25661|Q1Xey.UPqlWVP7pCYHWVNGqCViMLI2SOUHW9ynr5EI_ZQXO4hl1gnwrykHvPnqxwL8v1tYxLq7OPPdER759C.Y34LLPfX8HDm25661|Q1Xey.UPqlWVP7pCYHWVNGqCViMLI2SOUHW9ynr5EI_ZQXO4hl1gnwrykHvPnqxwL8v1tYxLq7OPPdER759C.Y34LLPfX8HDm25661|Q1Xey.UPqlWVP7pCYHWVNGqCViMLI2SOUHW9ynr5EI_ZQXO4hl1gnwrykHvPnqxwL8v1tYxLq7OPPdER759C.Y34LLPfX8HDm25661|Q1Xey.UPqlWVP7pCYHWVNGqCViMLI2SOUHW9ynr5EI_ZQBot_6抓取',
            'domain': '.cde.org.cn',
            'path': '/',
            'sameSite': 'Lax'
        }
    ]

    def __init__(self, output_dir: str = './data/sources/regulations/cde'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
        self.start_time = datetime.now()

    async def get_context_with_cookies(self, context):
        """获取并设置 Cookies"""
        # 先设置手动获取的真实 Cookies
        for cookie in self.MANUAL_COOKIES:
            await context.add_cookies(cookie)

        logger.info(f"已设置 {len(self.MANUAL_COOKIES)} 个手动获取的 Cookies")
        return

    async def fetch_zdyz_page(self, page):
        """爬取指导原则页面"""
        url = f"{self.BASE_URL}/zdyz/index"
        logger.info(f"正在访问: {url}")

        response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)

        if response.status != 200:
            logger.warning(f"HTTP {response.status}: {url}")
            return []

        # 额外等待，确保JS完全执行
        await asyncio.sleep(3)
        await page.wait_for_timeout(5000)

        # 查找所有PDF链接
        pdf_links = await page.query_selector_all('a[href$=".pdf"]')
        logger.info(f"找到 {len(pdf_links)} 个 PDF 链接")

        documents = []
        for idx, link in enumerate(pdf_links[:100]):
            try:
                href = await link.get_attribute('href')
                text = await link.inner_text()

                if not href or not text:
                    continue

                # 构造完整URL
                doc_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"

                documents.append({
                    'title': text.strip(),
                    'url': doc_url,
                    'category': '指导原则',
                    'source_url': page.url,
                    'crawl_date': datetime.now().isoformat(),
                })

                if idx % 10 == 0:
                    logger.info(f"已处理 {idx + 1} 条记录...")

            except Exception as e:
                logger.error(f"解析链接失败: {e}")

        return documents

    async def fetch_policy_page(self, page):
        """爬取政策文件列表页面"""
        try:
            # CDE 政策页面需要不同的 URL 格式
            listpage_urls = [
                'https://www.cde.org.cn/main/policy/listpage/9f9c74c73e0f8f56a8bfbc646055026d',
                'https://www.cde.org.cn/main/policy/listpage/9cd8db3b7530c6fa0c86485e563f93c7'
            ]

            all_documents = []

            for url in listpage_urls:
                logger.info(f"正在访问政策页面: {url}")
                response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)

                if response.status != 200:
                    logger.warning(f"HTTP {response.status}: {url}")
                    continue

                # 等待页面加载
                await asyncio.sleep(3)
                await page.wait_for_timeout(5000)

                # 查找列表项
                list_items = await page.query_selector_all('li')
                logger.info(f"找到 {len(list_items)} 个列表项")

                for item in list_items[:50]:
                    try:
                        title_elem = await item.query_selector('a')
                        link_elem = await item.query_selector('a')

                        if not title_elem or not link_elem:
                            continue

                        title = await title_elem.inner_text()
                        doc_url = await link_elem.get_attribute('href')

                        if not doc_url:
                            # 尝试从文本内容中提取URL
                            link_text = await link_elem.inner_text()
                            if link_text.startswith('http') or link_text.startswith('www.'):
                                doc_url = link_text
                            else:
                                doc_url = f"{self.BASE_URL}/{link_text}"

                        if title and doc_url:
                            all_documents.append({
                                'title': title.strip(),
                                'url': doc_url,
                                'category': '政策文件',
                                'source_url': page.url,
                                'crawl_date': datetime.now().isoformat(),
                            })

                    except Exception as e:
                        logger.warning(f"解析列表项失败: {e}")
                        continue

            return all_documents

        except Exception as e:
            logger.error(f"解析政策页面失败: {e}")
            return []

    async def run(self):
        """运行爬虫"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage'
                ]
            )

            try:
                # 创建浏览器上下文，设置真实浏览器指纹
                context = await browser.new_context(
                    user_agent=self.MANUAL_HEADERS['User-Agent'],
                    viewport={'width': 1920, 'height': 1080},
                    locale='zh-CN',
                )

                # 设置手动获取的 Cookies
                await self.get_context_with_cookies(context)

                # 创建页面
                page = await context.new_page()

                # 爬取各页面
                all_documents = []

                # 爬取指导原则
                logger.info("开始爬取指导原则页面...")
                zdyz_docs = await self.fetch_zdyz_page(page)
                all_documents.extend(zdyz_docs)
                logger.info(f"指导原则: 提取 {len(zdyz_docs)} 条")

                # 爬取政策文件
                logger.info("开始爬取政策文件页面...")
                policy_docs = await self.fetch_policy_page(page)
                all_documents.extend(policy_docs)
                logger.info(f"政策文件: 提取 {len(policy_docs)} 条")

                # 保存结果
                self.results = all_documents
                self._save_results('cde_all')

                logger.info(f"总计提取 {len(all_documents)} 条记录")

            finally:
                await browser.close()

    def _save_results(self, page_name: str):
        """保存结果"""
        if not self.results:
            logger.warning("没有数据需要保存")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f'cde_{page_name}_{timestamp}.json'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        logger.info(f"结果已保存到: {output_file}")


async def main():
    spider = CDEAdvancedSpider()
    await spider.run()


if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("CDE Advanced Spider - 模拟真实浏览器")
    logger.info("=" * 50)
    asyncio.run(main())
