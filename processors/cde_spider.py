#!/usr/bin/env python3
"""
CDE Spider - 药品审评中心数据爬虫
使用 Playwright 爬取 CDE (药品审评中心) 网站数据

功能：
- 爬取药品审评相关政策文件
- 爬取指导原则文件
- 爬取受理目录信息
- 支持分页处理
- 自动 Cookie 管理
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Generator, Optional, Dict, Any, List
from urllib.parse import urljoin

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("请先安装 playwright: pip install playwright && playwright install chromium")
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CDEPlaywrightSpider:
    """CDE 药品审评中心爬虫 - Playwright版本

    目标网站：
    - https://www.cde.org.cn/zdyz/index - 指导原则
    - https://www.cde.org.cn/main/policy/listpage - 政策文件
    """

    # CDE 网站配置
    BASE_URL = "https://www.cde.org.cn"

    # 目标页面
    TARGET_PAGES = {
        "zdyz": "/zdyz/index",              # 指导原则
        "policy": "/main/policy/listpage",    # 政策文件
        "acceptance": "/zdyz/listpage",      # 受理目录
    }

    def __init__(self, output_dir: str = './data/sources/regulations/cde'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
        self.start_time = datetime.now()
        self.cookie_file = self.output_dir / 'cookies.json'

    async def get_cookies(self, context) -> None:
        """获取并保存 Cookies"""
        # 首次访问主页获取 Cookie
        logger.info("获取 Cookies...")
        page = await context.new_page()
        await page.goto(f"{self.BASE_URL}/", wait_until='domcontentloaded', timeout=30000)

        # 获取 Cookies 并保存正确格式
        cookies = await context.cookies()

        # 过滤出有效的 cookies（有 domain 或 path 的）
        valid_cookies = []
        for cookie in cookies:
            c = {k: v for k, v in cookie.items() if k not in ['sameSite', 'expires']}
            if 'domain' in c or 'path' in c:
                valid_cookies.append(c)

        # 保存到文件
        with open(self.cookie_file, 'w') as f:
            json.dump(valid_cookies, f)

        logger.info(f"已保存 {len(valid_cookies)} 个 Cookies")
        await page.close()

        return valid_cookies

    async def load_cookies(self, context) -> None:
        """从文件加载 Cookies"""
        if self.cookie_file.exists():
            try:
                logger.info("加载已保存的 Cookies...")
                with open(self.cookie_file, 'r') as f:
                    saved_cookies = json.load(f)

                # 转换为正确的格式
                cookies = []
                for c in saved_cookies:
                    # 处理字符串类型的cookie值
                    name = c.get('name', '')
                    value = c.get('value', '')

                    # 跳过无效的 cookie
                    if not name or not value:
                        continue

                    cookie = {
                        'name': name,
                        'value': str(value),
                        'domain': '.cde.org.cn',
                        'path': '/',
                    }

                    # 添加可选属性
                    if 'expires' in c:
                        cookie['expires'] = c['expires']
                    # sameSite 设置
                    if 'sameSite' in c:
                        cookie['sameSite'] = c['sameSite']

                    cookies.append(cookie)

                if cookies:
                    await context.add_cookies(cookies)
                    logger.info(f"已加载 {len(cookies)} 个 Cookies")
                else:
                    logger.warning("Cookie 文件为空，将使用无 Cookie 模式")
            except Exception as e:
                logger.warning(f"加载 Cookie 失败: {e}")
        return None

    async def fetch_page(self, page, url: str, max_retries: int = 3) -> Optional[str]:
        """获取页面内容，带重试机制"""
        for attempt in range(max_retries):
            try:
                logger.info(f"正在访问: {url} (尝试 {attempt + 1}/{max_retries})")

                # 随机延迟，模拟人类行为
                if attempt > 0:
                    delay = 2 + (attempt * 1.5)
                    await asyncio.sleep(delay)

                # 设置更多人性化的请求头
                response = await page.goto(
                    url,
                    wait_until='domcontentloaded',
                    timeout=60000
                )

                if response.status == 200:
                    # 等待页面完全加载
                    await page.wait_for_timeout(5000)

                    # 额外等待 JS 执行
                    await page.wait_for_timeout(3000)

                    content = await page.content()
                    logger.info(f"成功获取页面，大小: {len(content)} bytes")
                    return content
                elif response.status == 400:
                    logger.warning(f"HTTP 400 - 可能被识别为机器人，等待后重试...")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                else:
                    logger.warning(f"HTTP {response.status}: {url}")

            except Exception as e:
                logger.error(f"获取页面失败 (尝试 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)

        return None

    async def parse_zdyz_page(self, page) -> List[Dict]:
        """解析指导原则页面"""
        try:
            # 查找文档链接
            doc_links = await page.query_selector_all('a[href*=".pdf"]')
            logger.info(f"找到 {len(doc_links)} 个 PDF 链接")

            documents = []
            for link in doc_links[:50]:  # 限制50条测试
                href = await link.get_attribute('href')
                text = await link.inner_text()

                # 提取文档标题
                title = text.strip()

                # 构造完整 URL
                doc_url = urljoin(self.BASE_URL, href) if href else ""

                if title:
                    documents.append({
                        'title': title,
                        'url': doc_url,
                        'category': '指导原则',
                        'source_url': page.url,
                        'crawl_date': datetime.now().isoformat()
                    })

            return documents

        except Exception as e:
            logger.error(f"解析指导原则页面失败: {e}")
            return []

    async def parse_policy_page(self, page) -> List[Dict]:
        """解析政策文件列表页面"""
        try:
            # 查找列表项
            list_items = await page.query_selector_all('.list-item, li')
            logger.info(f"找到 {len(list_items)} 个列表项")

            documents = []
            for item in list_items[:50]:
                try:
                    # 查找标题
                    title_elem = await item.query_selector('a, .title')
                    if not title_elem:
                        continue
                    title = await title_elem.inner_text()

                    # 查找链接
                    link_elem = await item.query_selector('a')
                    doc_url = await link_elem.get_attribute('href') if link_elem else ""

                    # 查找日期
                    date_elem = await item.query_selector('.date, .time')
                    publish_date = await date_elem.inner_text() if date_elem else ""

                    doc_url = urljoin(self.BASE_URL, doc_url) if doc_url else ""

                    if title and doc_url:
                        documents.append({
                            'title': title.strip(),
                            'url': doc_url,
                            'publish_date': publish_date.strip(),
                            'category': '政策文件',
                            'source_url': page.url,
                            'crawl_date': datetime.now().isoformat()
                        })

                except Exception as e:
                    logger.warning(f"解析列表项失败: {e}")
                    continue

            return documents

        except Exception as e:
            logger.error(f"解析政策页面失败: {e}")
            return []

    def _classify_document(self, title: str, url: str) -> str:
        """分类文档"""
        title_lower = title.lower()

        # 根据URL和标题判断类型
        if 'zdyz' in url:
            return '指导原则'
        elif 'policy' in url:
            return '政策文件'
        elif 'acceptance' in url:
            return '受理目录'

        # 根据标题关键词判断
        if any(kw in title_lower for kw in ['指导', '原则', '指南']):
            return '指导原则'
        if any(kw in title for kw in ['技术', '要求', '标准']):
            return '技术要求'
        if any(kw in title for kw in ['通知', '公告', '通告']):
            return '通知公告'

        return '其他'

    async def crawl_page(self, page, page_name: str, path: str, retry_count: int = 0) -> List[Dict]:
        """爬取单个页面"""
        url = f"{self.BASE_URL}{path}"
        logger.info(f"开始爬取: {page_name} - {url} (重试: {retry_count}/3)")

        # 获取页面内容
        content = await self.fetch_page(page, url)
        if not content:
            logger.warning(f"无法获取页面内容: {url}")
            if retry_count < 3:
                # 重试前等待
                await asyncio.sleep(5)
                return await self.crawl_page(page, page_name, path, retry_count + 1)
            return []

        # 设置页面内容并解析
        await page.set_content(content)

        # 根据页面类型选择解析方法
        if 'zdyz' in path:
            documents = await self.parse_zdyz_page(page)
        elif 'policy' in path or 'listpage' in path:
            documents = await self.parse_policy_page(page)
        else:
            logger.warning(f"未知页面类型: {path}")
            return []

        logger.info(f"从 {page_name} 提取到 {len(documents)} 条记录")
        return documents

    async def run(self, pages: List[str] = None):
        """运行爬虫"""
        # 默认爬取所有页面
        if pages is None:
            pages = ['zdyz', 'policy']

        async with async_playwright() as p:
            # 启动浏览器 - 使用更多反检测措施
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )

            try:
                # 创建浏览器上下文 - 模拟真实浏览器
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    ignore_https_errors=True,
                    java_script_enabled=True,
                    # 额外的反检测设置
                    locale='zh-CN',
                    timezone_id='Asia/Shanghai',
                    geolocation={'latitude': 39.9, 'longitude': 116.4},
                    permissions=['geolocation']
                )

                # 加载或获取Cookies
                await self.load_cookies(context)
                if not self.cookie_file.exists():
                    await self.get_cookies(context)

                # 创建页面
                page = await context.new_page()

                # 爬取各页面
                all_documents = []
                for page_name in pages:
                    if page_name in self.TARGET_PAGES:
                        path = self.TARGET_PAGES[page_name]
                        documents = await self.crawl_page(page, page_name, path, retry_count=0)
                        all_documents.extend(documents)

                # 保存结果
                self.results = all_documents
                self._save_results(page_name)

                logger.info(f"爬取完成，共获取 {len(all_documents)} 条记录")

            finally:
                await browser.close()

    def _save_results(self, page_name: str = 'latest'):
        """保存爬取结果"""
        if not self.results:
            logger.warning("没有数据需要保存")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f'cde_{page_name}_{timestamp}.json'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        logger.info(f"结果已保存到: {output_file}")

        # 同时更新 latest 文件
        latest_file = self.output_dir / f'cde_{page_name}_latest.json'
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)


async def main():
    """主函数"""
    spider = CDEPlaywrightSpider()

    # 可指定要爬取的页面
    import sys
    pages = None
    if len(sys.argv) > 1:
        pages = sys.argv[1:]
        print(f"将爬取页面: {pages}")

    await spider.run(pages)


if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("CDE Playwright Spider")
    logger.info("=" * 50)
    logger.info(f"输出目录: {Path('./data/sources/regulations/cde')}")
    logger.info("")
    logger.info("可用页面:")
    logger.info("  zdyz    - 指导原则")
    logger.info("  policy  - 政策文件")
    logger.info("  all     - 所有页面")
    logger.info("")
    logger.info("使用方法:")
    logger.info("  python processors/cde_spider.py          # 爬取所有页面")
    logger.info("  python processors/cde_spider.py zdyz     # 只爬取指导原则")
    logger.info("  python processors/cde_spider.py policy    # 只爬取政策文件")
    logger.info("")

    asyncio.run(main())
