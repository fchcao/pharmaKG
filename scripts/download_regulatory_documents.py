#!/usr/bin/env python3
"""
监管文档下载脚本
从 CDE 和 FDA 网站下载监管法规文档

数据源:
- CDE 指导原则: https://www.cde.org.cn/zdyz/index
- CDE 政策列表: https://www.cde.org.cn/main/policy/listpage/9f9c74c73e0f8f56a8bfbc646055026d
- FDA 指导文档: https://www.fda.gov/regulatory-information/search-fda-guidance-documents
- FDA 药物开发: https://www.fda.gov/drugs/development-approval-process-drugs
"""

import os
import sys
import logging
import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("请安装依赖: pip install requests beautifulsoup4")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RegulatoryDocumentDownloader:
    """监管文档下载器"""

    def __init__(self, base_dir: Path, network_turbo: bool = True):
        """
        初始化下载器

        Args:
            base_dir: 基础目录
            network_turbo: 是否使用网络加速
        """
        self.base_dir = base_dir
        self.network_turbo = network_turbo
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # 创建目录结构
        self.sources_dir = base_dir / "data" / "sources" / "regulatory"
        self.sources_dir.mkdir(parents=True, exist_ok=True)

        # 按来源组织目录
        self.cde_dir = self.sources_dir / "CDE"
        self.fda_dir = self.sources_dir / "FDA"
        self.cde_dir.mkdir(parents=True, exist_ok=True)
        self.fda_dir.mkdir(parents=True, exist_ok=True)

        # 已下载文件记录
        self.downloaded_files: Set[str] = set()

    def enable_network_turbo(self):
        """启用网络加速"""
        if self.network_turbo:
            os.system('source /etc/network_turbo 2>/dev/null')

    def download_file(self, url: str, destination: Path, description: str = "") -> bool:
        """
        下载文件

        Args:
            url: 文件URL
            destination: 目标路径
            description: 文件描述

        Returns:
            是否成功
        """
        try:
            if destination.exists():
                logger.debug(f"文件已存在，跳过: {destination.name}")
                return True

            logger.info(f"下载 {description or url}")

            response = self.session.get(url, stream=True, timeout=120)
            response.raise_for_status()

            # 写入文件
            destination.parent.mkdir(parents=True, exist_ok=True)
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = destination.stat().st_size / 1024  # KB
            logger.info(f"✓ 下载完成: {destination.name} ({file_size:.1f} KB)")
            self.downloaded_files.add(str(destination))
            return True

        except Exception as e:
            logger.error(f"✗ 下载失败 {url}: {e}")
            return False

    def scrape_cde_guidance(self, limit: Optional[int] = None) -> List[str]:
        """
        抓取 CDE 指导原则页面

        Args:
            limit: 限制下载数量

        Returns:
            下载的文档URL列表
        """
        logger.info("=" * 60)
        logger.info("抓取 CDE 指导原则")
        logger.info("=" * 60)

        base_url = "https://www.cde.org.cn/zdyz/index"
        downloaded = []

        try:
            self.enable_network_turbo()
            response = self.session.get(base_url, timeout=60)
            response.raise_for_status()

            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找文档链接 - CDE 网站通常有特定的链接结构
            # 这里需要根据实际页面结构调整选择器
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$|\.doc$|\.docx$', re.I))

            logger.info(f"找到 {len(pdf_links)} 个文档链接")

            for i, link in enumerate(pdf_links):
                if limit and i >= limit:
                    break

                href = link.get('href')
                if not href:
                    continue

                # 构建完整URL
                if href.startswith('/'):
                    doc_url = f"https://www.cde.org.cn{href}"
                elif not href.startswith('http'):
                    doc_url = urljoin(base_url, href)
                else:
                    doc_url = href

                # 获取文件名
                filename = os.path.basename(urlparse(doc_url).path)
                if not filename or filename == '':
                    filename = f"cde_document_{i}.pdf"

                destination = self.cde_dir / "guidance" / filename
                if self.download_file(doc_url, destination, f"CDE 指导原则 {filename}"):
                    downloaded.append(doc_url)

                # 延迟避免请求过快
                time.sleep(0.5)

        except Exception as e:
            logger.error(f"抓取 CDE 指导原则失败: {e}")

        return downloaded

    def scrape_cde_policy(self, limit: Optional[int] = None) -> List[str]:
        """
        抓取 CDE 政策列表页面

        Args:
            limit: 限制下载数量

        Returns:
            下载的文档URL列表
        """
        logger.info("=" * 60)
        logger.info("抓取 CDE 政策列表")
        logger.info("=" * 60)

        base_url = "https://www.cde.org.cn/main/policy/listpage/9f9c74c73e0f8f56a8bfbc646055026d"
        downloaded = []

        try:
            self.enable_network_turbo()
            response = self.session.get(base_url, timeout=60)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找文档链接
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$|\.doc$|\.docx$', re.I))

            logger.info(f"找到 {len(pdf_links)} 个文档链接")

            for i, link in enumerate(pdf_links):
                if limit and i >= limit:
                    break

                href = link.get('href')
                if not href:
                    continue

                if href.startswith('/'):
                    doc_url = f"https://www.cde.org.cn{href}"
                elif not href.startswith('http'):
                    doc_url = urljoin(base_url, href)
                else:
                    doc_url = href

                filename = os.path.basename(urlparse(doc_url).path)
                if not filename:
                    filename = f"cde_policy_{i}.pdf"

                destination = self.cde_dir / "policy" / filename
                if self.download_file(doc_url, destination, f"CDE 政策 {filename}"):
                    downloaded.append(doc_url)

                time.sleep(0.5)

        except Exception as e:
            logger.error(f"抓取 CDE 政策列表失败: {e}")

        return downloaded

    def scrape_fda_guidance(self, limit: Optional[int] = None) -> List[str]:
        """
        抓取 FDA 指导文档

        Args:
            limit: 限制下载数量

        Returns:
            下载的文档URL列表
        """
        logger.info("=" * 60)
        logger.info("抓取 FDA 指导文档")
        logger.info("=" * 60)

        # FDA 指导文档搜索页面
        base_url = "https://www.fda.gov/regulatory-information/search-fda-guidance-documents"
        downloaded = []

        try:
            self.enable_network_turbo()
            response = self.session.get(base_url, timeout=60)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # FDA 网站通常使用特定的链接结构
            # 查找包含 "download" 或 "pdf" 的链接
            pdf_links = soup.find_all('a', href=re.compile(r'/media/\d+/download', re.I))

            logger.info(f"找到 {len(pdf_links)} 个指导文档链接")

            for i, link in enumerate(pdf_links):
                if limit and i >= limit:
                    break

                href = link.get('href')
                if not href:
                    continue

                if href.startswith('/'):
                    doc_url = f"https://www.fda.gov{href}"
                else:
                    doc_url = href

                filename = os.path.basename(urlparse(doc_url).path)
                if not filename:
                    filename = f"fda_guidance_{i}.pdf"

                destination = self.fda_dir / "guidance" / filename
                if self.download_file(doc_url, destination, f"FDA 指导文档 {filename}"):
                    downloaded.append(doc_url)

                time.sleep(0.5)

        except Exception as e:
            logger.error(f"抓取 FDA 指导文档失败: {e}")

        return downloaded

    def scrape_fda_drug_development(self, limit: Optional[int] = None) -> List[str]:
        """
        抓取 FDA 药物开发审批流程文档

        Args:
            limit: 限制下载数量

        Returns:
            下载的文档URL列表
        """
        logger.info("=" * 60)
        logger.info("抓取 FDA 药物开发文档")
        logger.info("=" * 60)

        base_url = "https://www.fda.gov/drugs/development-approval-process-drugs"
        downloaded = []

        try:
            self.enable_network_turbo()
            response = self.session.get(base_url, timeout=60)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找 PDF 文档链接
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$|/media/\d+/download', re.I))

            logger.info(f"找到 {len(pdf_links)} 个文档链接")

            for i, link in enumerate(pdf_links):
                if limit and i >= limit:
                    break

                href = link.get('href')
                if not href:
                    continue

                if href.startswith('/'):
                    doc_url = f"https://www.fda.gov{href}"
                else:
                    doc_url = href

                filename = os.path.basename(urlparse(doc_url).path)
                if not filename:
                    filename = f"fda_drug_dev_{i}.pdf"

                destination = self.fda_dir / "drug_development" / filename
                if self.download_file(doc_url, destination, f"FDA 药物开发 {filename}"):
                    downloaded.append(doc_url)

                time.sleep(0.5)

        except Exception as e:
            logger.error(f"抓取 FDA 药物开发文档失败: {e}")

        return downloaded

    def download_all(self, limit_per_source: Optional[int] = None) -> Dict[str, List[str]]:
        """
        下载所有监管文档

        Args:
            limit_per_source: 每个来源限制下载文档数量

        Returns:
            所有下载结果
        """
        all_results = {}

        all_results['cde_guidance'] = self.scrape_cde_guidance(limit_per_source)
        all_results['cde_policy'] = self.scrape_cde_policy(limit_per_source)
        all_results['fda_guidance'] = self.scrape_fda_guidance(limit_per_source)
        all_results['fda_drug_dev'] = self.scrape_fda_drug_development(limit_per_source)

        return all_results


def print_summary(all_results: Dict[str, List[str]]):
    """打印下载摘要"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("下载摘要")
    logger.info("=" * 60)

    total = 0
    for source, urls in all_results.items():
        count = len(urls)
        total += count
        logger.info(f"{source}: {count} 文档")

    logger.info(f"总计: {total} 文档下载成功")


def main():
    parser = argparse.ArgumentParser(description='下载监管法规文档')
    parser.add_argument(
        '--source', '-s',
        choices=['cde_guidance', 'cde_policy', 'fda_guidance', 'fda_drug_dev'],
        help='指定下载来源'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='下载所有来源'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=10,
        help='每个来源限制下载文档数量 (默认: 10)'
    )
    parser.add_argument(
        '--base-dir', '-b',
        type=str,
        default=str(Path(__file__).parent.parent),
        help='项目基础目录'
    )
    parser.add_argument(
        '--no-network-turbo',
        action='store_true',
        help='不使用网络加速'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.all and not args.source:
        parser.error("请指定 --source 或 --all")

    base_dir = Path(args.base_dir)
    downloader = RegulatoryDocumentDownloader(base_dir, network_turbo=not args.no_network_turbo)

    if args.all:
        all_results = downloader.download_all(args.limit)
    elif args.source == 'cde_guidance':
        all_results = {'cde_guidance': downloader.scrape_cde_guidance(args.limit)}
    elif args.source == 'cde_policy':
        all_results = {'cde_policy': downloader.scrape_cde_policy(args.limit)}
    elif args.source == 'fda_guidance':
        all_results = {'fda_guidance': downloader.scrape_fda_guidance(args.limit)}
    elif args.source == 'fda_drug_dev':
        all_results = {'fda_drug_dev': downloader.scrape_fda_drug_development(args.limit)}

    print_summary(all_results)

    return 0


if __name__ == '__main__':
    sys.exit(main())
