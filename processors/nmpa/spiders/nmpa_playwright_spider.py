"""
NMPA Spider - Playwright版本
使用Playwright绕过反爬虫保护
"""

import asyncio
import json
import logging
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


class NMPAPlaywrightSpider:
    """NMPA爬虫 - Playwright版本
    
    使用Playwright浏览器绕过反爬虫保护
    """
    
    def __init__(self, output_file: str = 'test_output.json'):
        self.output_file = output_file
        self.results = []
        self.start_time = datetime.now()
        
    async def fetch_page(self, page, url: str) -> Optional[str]:
        """获取页面内容"""
        try:
            logger.info(f"正在访问: {url}")
            response = await page.goto(url, wait_until='networkidle', timeout=60000)
            
            if response.status != 200:
                logger.error(f"HTTP {response.status}: {url}")
                return None
            
            # 等待页面完全加载
            await page.wait_for_timeout(3000)
            
            # 获取页面内容
            content = await page.content()
            logger.info(f"页面大小: {len(content)} bytes")
            return content
            
        except Exception as e:
            logger.error(f"获取页面失败: {e}")
            return None
    
    async def parse_table(self, page) -> List[Dict]:
        """解析表格数据"""
        try:
            # 查找表格
            tables = await page.query_selector_all('table')
            logger.info(f"找到 {len(tables)} 个表格")
            
            documents = []
            
            for table_idx, table in enumerate(tables):
                # 获取表头
                headers = await table.query_selector_all('thead th')
                if not headers:
                    continue
                
                header_texts = [await h.inner_text() for h in headers]
                logger.info(f"表格{table_idx}表头: {header_texts[:3]}")
                
                # 检查是否为目标表格
                if not any('药品' in h for h in header_texts):
                    continue
                
                # 获取数据行
                rows = await table.query_selector_all('tbody tr')
                logger.info(f"表格{table_idx}有 {len(rows)} 行")
                
                for row in rows[:50]:  # 限制50行测试
                    cells = await row.query_selector_all('td')
                    if len(cells) < 3:
                        continue
                    
                    # 提取数据
                    title_elem = cells[0].query_selector('text')
                    title = await title_elem.inner_text() if title_elem else ""
                    
                    link_elem = cells[3].query_selector('a')
                    doc_url = await link_elem.get_attribute('href') if link_elem else ""
                    
                    date_elem = cells[6].query_selector('text')
                    publish_date = await date_elem.inner_text() if date_elem else ""
                    
                    if title:
                        doc_type = self._classify_document(title)
                        documents.append({
                            'title': title.strip(),
                            'url': urljoin('https://www.nmpa.gov.cn/', doc_url) if doc_url else '',
                            'publish_date': publish_date.strip(),
                            'category': doc_type,
                            'source_url': page.url,
                        })
                
            return documents
            
        except Exception as e:
            logger.error(f"解析表格失败: {e}")
            return []
    
    def _classify_document(self, title: str) -> str:
        """分类文档"""
        title_lower = title.lower()
        
        if any(kw in title_lower for kw in ['gmp', '药品生产质量管理规范']):
            return 'GMP认证'
        if any(kw in title for kw in ['药品审评', '审评报告']):
            return '药品审评'
        if any(kw in title for kw in ['检查', '飞行检查']):
            return 'GMP检查'
        if any(kw in title for kw in ['通告', '通知', '公告']):
            return 'GMP通告'
        if any(kw in title for kw in ['药典', '标准', '规范']):
            return '中国药典'
        return '其他'
    
    async def run(self):
        """运行爬虫"""
        url = 'https://www.nmpa.gov.cn/directory/local/warea8b0c752b936f80282a37a.html'
        
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            try:
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (compatible; NMPA-Spider/1.0)',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = await context.new_page()
                
                # 获取页面
                content = await self.fetch_page(page, url)
                if not content:
                    logger.error("无法获取页面内容")
                    return
                
                # 设置页面内容
                await page.set_content(content)
                
                # 解析数据
                documents = await self.parse_table(page)
                
                # 保存结果
                self.results = documents
                self._save_results()
                
                logger.info(f"成功提取 {len(documents)} 条记录")
                
            finally:
                await browser.close()
    
    def _save_results(self):
        """保存结果"""
        output_path = Path(self.output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        logger.info(f"结果已保存到: {output_path}")


async def main():
    """主函数"""
    spider = NMPAPlaywrightSpider()
    await spider.run()


if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("NMPA Playwright Spider")
    logger.info("=" * 50)
    asyncio.run(main())
