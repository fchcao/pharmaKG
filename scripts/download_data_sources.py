#!/usr/bin/env python3
"""
外部数据源下载脚本
按领域下载 ChEMBL、ClinicalTrials.gov、FDA 等数据源

使用方法:
    python3 scripts/download_data_sources.py --domain rd --limit 100
    python3 scripts/download_data_sources.py --all --limit 100
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import requests
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataSourceDownloader:
    """数据源下载器"""

    def __init__(self, base_dir: Path, network_turbo: bool = True):
        """
        初始化下载器

        Args:
            base_dir: 基础目录
            network_turbo: 是否使用网络加速
        """
        self.base_dir = base_dir
        self.network_turbo = network_turbo

        # 创建目录结构
        self.sources_dir = base_dir / "data" / "sources"
        self.sources_dir.mkdir(parents=True, exist_ok=True)

        # 领域目录
        self.domains = {
            'rd': self.sources_dir / 'rd',           # R&D domain
            'clinical': self.sources_dir / 'clinical',  # Clinical domain
            'sc': self.sources_dir / 'sc',           # Supply Chain domain
            'regulatory': self.sources_dir / 'regulatory'  # Regulatory domain
        }

        for domain_dir in self.domains.values():
            domain_dir.mkdir(parents=True, exist_ok=True)

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
            logger.info(f"下载 {description or url} -> {destination}")

            # 使用网络加速（如果可用）
            if self.network_turbo:
                os.system('source /etc/network_turbo 2>/dev/null')

            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()

            # 写入文件
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = destination.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"✓ 下载完成: {destination.name} ({file_size:.2f} MB)")
            return True

        except Exception as e:
            logger.error(f"✗ 下载失败 {url}: {e}")
            return False

    def download_chembl_data(self, limit: Optional[int] = None) -> Dict[str, bool]:
        """
        下载 ChEMBL 数据 (R&D 领域)

        Args:
            limit: 限制下载数量

        Returns:
            下载结果
        """
        logger.info("=" * 60)
        logger.info("下载 ChEMBL 数据 (R&D 领域)")
        logger.info("=" * 60)

        results = {}
        dest_dir = self.domains['rd']

        # ChEMBL 数据下载链接
        # 使用 EBI FTP 的 HTTP 镜像
        chembl_files = {
            'chembl_34_sqlite.tar.gz': 'https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_34/chembl_34_sqlite.tar.gz',
            'chembl_34_molecules.tar.gz': 'https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_34/chembl_34_molecules.tar.gz',
        }

        for filename, url in chembl_files.items():
            if limit and len(results) >= limit:
                break
            destination = dest_dir / filename
            results[filename] = self.download_file(url, destination, f"ChEMBL {filename}")

        return results

    def download_clinical_trials_data(self, limit: Optional[int] = None) -> Dict[str, bool]:
        """
        下载 ClinicalTrials.gov 数据 (临床领域)

        Args:
            limit: 限制下载数量

        Returns:
            下载结果
        """
        logger.info("=" * 60)
        logger.info("下载 ClinicalTrials.gov 数据 (临床领域)")
        logger.info("=" * 60)

        results = {}
        dest_dir = self.domains['clinical']

        # ClinicalTrials.gov 数据下载链接
        ct_files = {
            'AllPublicXML.zip': 'https://clinicaltrials.gov/AllPublicXML.zip',
            'AAParticipant.zip': 'https://clinicaltrials.gov/AllAPIs/AAParticipant.zip',
        }

        for filename, url in ct_files.items():
            if limit and len(results) >= limit:
                break
            destination = dest_dir / filename
            results[filename] = self.download_file(url, destination, f"ClinicalTrials.gov {filename}")

        return results

    def download_fda_shortage_data(self, limit: Optional[int] = None) -> Dict[str, bool]:
        """
        下载 FDA 药品短缺数据 (供应链领域)

        Args:
            limit: 限制下载数量

        Returns:
            下载结果
        """
        logger.info("=" * 60)
        logger.info("下载 FDA 药品短缺数据 (供应链领域)")
        logger.info("=" * 60)

        results = {}
        dest_dir = self.domains['sc']

        # FDA 药品短缺数据
        fda_sc_files = {
            'drug-shortages.xlsx': 'https://www.accessdata.fda.gov/drugsatfda_docs/CSV/drug-shortages.xlsx',
        }

        for filename, url in fda_sc_files.items():
            if limit and len(results) >= limit:
                break
            destination = dest_dir / filename
            results[filename] = self.download_file(url, destination, f"FDA 短缺数据 {filename}")

        return results

    def download_fda_products_data(self, limit: Optional[int] = None) -> Dict[str, bool]:
        """
        下载 FDA 产品数据 (监管领域)

        Args:
            limit: 限制下载数量

        Returns:
            下载结果
        """
        logger.info("=" * 60)
        logger.info("下载 FDA 产品数据 (监管领域)")
        logger.info("=" * 60)

        results = {}
        dest_dir = self.domains['regulatory']

        # FDA 产品和应用数据
        fda_reg_files = {
            'products_and_submissions.zip': 'https://www.accessdata.fda.gov/cder/ndctext.zip',
            'fda_drug_events.tsv.zip': 'https://www.accessdata.fda.gov/DER/ENFORCEMENT/CDER/Drug_Events/CDER_Drug_Events.tsv.zip',
        }

        for filename, url in fda_reg_files.items():
            if limit and len(results) >= limit:
                break
            destination = dest_dir / filename
            results[filename] = self.download_file(url, destination, f"FDA 产品数据 {filename}")

        return results

    def download_all_domains(self, limit: Optional[int] = None) -> Dict[str, Dict[str, bool]]:
        """
        下载所有领域的数据

        Args:
            limit: 每个领域限制下载数量

        Returns:
            所有下载结果
        """
        all_results = {}

        all_results['rd'] = self.download_chembl_data(limit)
        all_results['clinical'] = self.download_clinical_trials_data(limit)
        all_results['sc'] = self.download_fda_shortage_data(limit)
        all_results['regulatory'] = self.download_fda_products_data(limit)

        return all_results


def print_summary(all_results: Dict[str, Dict[str, bool]]):
    """打印下载摘要"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("下载摘要")
    logger.info("=" * 60)

    total = 0
    success = 0

    for domain, results in all_results.items():
        domain_total = len(results)
        domain_success = sum(1 for v in results.values() if v)
        total += domain_total
        success += domain_success

        logger.info(f"{domain.upper()}: {domain_success}/{domain_total} 成功")

    logger.info("")
    logger.info(f"总计: {success}/{total} 文件下载成功")


def main():
    parser = argparse.ArgumentParser(description='下载 PharmaKG 外部数据源')
    parser.add_argument(
        '--domain', '-d',
        choices=['rd', 'clinical', 'sc', 'regulatory'],
        help='指定下载的领域'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='下载所有领域的数据'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=None,
        help='每个领域限制下载文件数量'
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

    # 检查参数
    if not args.all and not args.domain:
        parser.error("请指定 --domain 或 --all")

    base_dir = Path(args.base_dir)
    downloader = DataSourceDownloader(base_dir, network_turbo=not args.no_network_turbo)

    # 下载数据
    if args.all:
        all_results = downloader.download_all_domains(args.limit)
    else:
        if args.domain == 'rd':
            all_results = {'rd': downloader.download_chembl_data(args.limit)}
        elif args.domain == 'clinical':
            all_results = {'clinical': downloader.download_clinical_trials_data(args.limit)}
        elif args.domain == 'sc':
            all_results = {'sc': downloader.download_fda_shortage_data(args.limit)}
        elif args.domain == 'regulatory':
            all_results = {'regulatory': downloader.download_fda_products_data(args.limit)}

    print_summary(all_results)

    return 0


if __name__ == '__main__':
    sys.exit(main())
