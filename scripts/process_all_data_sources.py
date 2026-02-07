#!/usr/bin/env python3
#===========================================================
# PharmaKG Data Sources Processing Orchestrator
# 数据源处理编排器
#===========================================================
# 版本: v1.0
# 描述: 处理 data/sources 目录下所有数据源并导入 Neo4j
#===========================================================

import os
import sys
import json
import logging
import sqlite3
import tarfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from etl.config import get_etl_config
from etl.extractors.document_extractor import DocumentExtractor
from etl.transformers.document_transformer import DocumentTransformer
from etl.loaders.neo4j_batch import Neo4jBatchLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理编排器"""

    def __init__(self):
        self.project_root = project_root
        self.sources_dir = project_root / "data" / "sources"
        self.processed_dir = project_root / "data" / "processed"
        self.validated_dir = project_root / "data" / "validated"
        self.import_dir = project_root / "data" / "import"

        # Create directories
        for dir_path in [self.processed_dir, self.validated_dir, self.import_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Get ETL config
        self.config = get_etl_config()
        self.loader = Neo4jBatchLoader(
            uri=self.config.neo4j_uri,
            user=self.config.neo4j_user,
            password=self.config.neo4j_password,
            database=self.config.neo4j_database,
            batch_size=self.config.batch_size,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            dry_run=self.config.dry_run
        )

        self.stats = {
            'processed_files': 0,
            'imported_records': 0,
            'errors': []
        }

    def run_all(self) -> Dict[str, Any]:
        """运行所有数据处理流程"""
        logger.info("=" * 70)
        logger.info("开始处理所有数据源")
        logger.info("=" * 70)

        start_time = datetime.now()
        results = {}

        try:
            # 1. 处理监管文档 (CDE/FDA)
            results['regulatory_documents'] = self.process_regulatory_documents()

            # 2. 处理中药2025WPS数据
            results['tcm_wps'] = self.process_tcm_wps_data()

            # 3. 处理Transparency CRL数据
            results['transparency_crl'] = self.process_transparency_crl()

            # 4. 处理ChEMBL数据库
            results['chembl'] = self.process_chembl_database()

            # 5. 处理PDF文档
            results['pdf_documents'] = self.process_pdf_documents()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 汇总结果
            summary = {
                'status': 'success',
                'duration_seconds': duration,
                'results': results,
                'stats': self.stats
            }

            logger.info("=" * 70)
            logger.info(f"数据处理完成，耗时 {duration:.2f} 秒")
            logger.info(f"处理文件数: {self.stats['processed_files']}")
            logger.info(f"导入记录数: {self.stats['imported_records']}")
            if self.stats['errors']:
                logger.info(f"错误数: {len(self.stats['errors'])}")
            logger.info("=" * 70)

            return summary

        except Exception as e:
            logger.error(f"数据处理失败: {e}", exc_info=True)
            return {
                'status': 'failed',
                'error': str(e),
                'stats': self.stats
            }

    def process_regulatory_documents(self) -> Dict[str, Any]:
        """处理已抓取的监管文档"""
        logger.info("\n[1/5] 处理监管文档...")

        # 使用现有的文档管道
        from etl.pipelines.document_pipeline import DocumentPipeline

        pipeline = DocumentPipeline()

        # 处理已下载的文档
        cde_path = self.sources_dir / "regulatory" / "CDE"
        fda_path = self.sources_dir / "regulatory" / "FDA"

        total_processed = 0

        for source_path in [cde_path, fda_path]:
            if source_path.exists():
                result = pipeline.run(
                    str(source_path),
                    recursive=True,
                    load_to_neo4j=True,
                    dry_run=False
                )
                total_processed += result.get('extraction', {}).get('files_processed', 0)
                self.stats['imported_records'] += result.get('loading', {}).get('nodes_created', 0)

        return {'files_processed': total_processed}

    def process_tcm_wps_data(self) -> Dict[str, Any]:
        """处理中药2025WPS数据"""
        logger.info("\n[2/5] 处理中药2025WPS数据...")

        tcm_dir = self.sources_dir / "中药2025WPS"
        if not tcm_dir.exists():
            return {'status': 'skipped', 'reason': 'Directory not found'}

        # 收集所有JSON元数据文件（排除utf8和paragraphs文件）
        all_json_files = list(tcm_dir.glob("*/*.json"))
        metadata_files = [f for f in all_json_files if 'utf8' not in f.name and 'paragraphs' not in f.name]

        logger.info(f"找到 {len(metadata_files)} 个中药政策文档元数据文件")

        processed_records = []
        for json_file in metadata_files:  # 处理所有文件
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 数据应该是字典
                    if isinstance(data, dict):
                        processed_records.append(data)
                    elif isinstance(data, list):
                        processed_records.extend(data)
                    self.stats['processed_files'] += 1
            except Exception as e:
                logger.warning(f"处理文件 {json_file} 失败: {e}")
                self.stats['errors'].append(str(json_file))

        logger.info(f"成功处理 {len(processed_records)} 条记录")

        # 保存到processed目录
        output_file = self.processed_dir / "tcm_wps_processed.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_records, f, ensure_ascii=False, indent=2)

        # 导入到Neo4j
        nodes_created = self._import_tcm_wps_records(processed_records)
        self.stats['imported_records'] += nodes_created

        return {
            'files_processed': len(processed_records),
            'nodes_created': nodes_created
        }

    def _import_tcm_wps_records(self, records: List[Dict]) -> int:
        """导入中药WPS记录到Neo4j"""
        records_to_load = []
        skipped = 0

        for record in records:
            page_id = record.get('page_id')
            if not page_id:
                skipped += 1
                continue

            properties = {
                'primary_id': f"TCM-{page_id}",
                'title_cn': record.get('title_cn', ''),
                'title_en': record.get('title_en', ''),
                'url': record.get('url', ''),
                'organization': record.get('organization', ''),
                'official_release_date': record.get('offical_release_date', ''),
                'effective_date': record.get('effective_date', ''),
                'status': record.get('status', 'N/A'),
                'subject_words': ','.join(record.get('subject_words', [])) if isinstance(record.get('subject_words'), list) else '',
                'document_type': 'PolicyDocument',
                'source': '中药2025WPS'
            }

            records_to_load.append(properties)

        if skipped > 0:
            logger.warning(f"跳过 {skipped} 条没有page_id的记录")

        logger.info(f"准备加载 {len(records_to_load)} 条PolicyDocument记录")

        # 创建约束（如果不存在）
        self._create_policy_constraint()

        # 导入节点
        return self.loader.load_nodes(
            label='PolicyDocument',
            records=records_to_load,
            merge_key='primary_id'
        )

    def _create_policy_constraint(self):
        """创建PolicyDocument约束"""
        from neo4j import GraphDatabase

        with GraphDatabase.driver(
            self.config.neo4j_uri,
            auth=(self.config.neo4j_user, self.config.neo4j_password)
        ) as driver:
            with driver.session(database=self.config.neo4j_database) as session:
                try:
                    session.run("""
                        CREATE CONSTRAINT policy_id IF NOT EXISTS
                        FOR (p:PolicyDocument) REQUIRE p.primary_id IS UNIQUE
                    """)
                except Exception as e:
                    logger.warning(f"创建约束失败 (可能已存在): {e}")

    def process_transparency_crl(self) -> Dict[str, Any]:
        """处理Transparency CRL数据"""
        logger.info("\n[3/5] 处理Transparency CRL数据...")

        crl_file = self.sources_dir / "transparency-crl-0001-of-0001.json"
        if not crl_file.exists():
            return {'status': 'skipped', 'reason': 'File not found'}

        with open(crl_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = data.get('results', [])
        logger.info(f"找到 {len(results)} 条CRL记录")

        # 处理记录
        processed_records = []
        for record in results:
            # 安全获取application_number
            app_numbers = record.get('application_number', [])
            app_number = app_numbers[0] if app_numbers and len(app_numbers) > 0 else ''

            processed_record = {
                'application_number': app_number,
                'letter_type': record.get('letter_type', ''),
                'letter_date': record.get('letter_date', ''),
                'company_name': record.get('company_name', ''),
                'approval_status': record.get('approval_status', ''),
                'approver_name': record.get('approver_name', ''),
                'drug_name': self._extract_drug_name(record.get('text', '')),
                'text_snippet': record.get('text', '')[:500] + '...' if len(record.get('text', '')) > 500 else record.get('text', '')
            }
            processed_records.append(processed_record)

        # 保存到processed目录
        output_file = self.processed_dir / "transparency_crl_processed.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_records, f, ensure_ascii=False, indent=2)

        # 导入到Neo4j
        nodes_created = self._import_crl_records(processed_records)
        self.stats['imported_records'] += nodes_created

        return {
            'records_processed': len(processed_records),
            'nodes_created': nodes_created
        }

    def _extract_drug_name(self, text: str) -> str:
        """从文本中提取药物名称"""
        # 简单提取：查找 "for XXX)" 或 "for XXX," 后的内容
        import re
        patterns = [
            r'for\s+([A-Z][a-z]+)\s*\)',
            r'for\s+([A-Z][a-z]+)\s+,',
        ]
        for pattern in patterns:
            match = re.search(pattern, text[:1000])
            if match:
                return match.group(1)
        return 'Unknown'

    def _import_crl_records(self, records: List[Dict]) -> int:
        """导入CRL记录到Neo4j"""
        records_to_load = []
        skipped = 0

        for record in records:
            app_number = record.get('application_number', '')
            letter_date = record.get('letter_date', '')

            if not app_number or not letter_date:
                skipped += 1
                continue

            properties = {
                'primary_id': f"CRL-{app_number}-{letter_date.replace('/', '')}",
                'application_number': app_number,
                'letter_type': record.get('letter_type', ''),
                'letter_date': letter_date,
                'company_name': record.get('company_name', ''),
                'approval_status': record.get('approval_status', ''),
                'approver_name': record.get('approver_name', ''),
                'drug_name': record.get('drug_name', ''),
                'text_snippet': record.get('text_snippet', ''),
                'document_type': 'CompleteResponseLetter',
                'source': 'FDA_Transparency'
            }

            records_to_load.append(properties)

        if skipped > 0:
            logger.warning(f"跳过 {skipped} 条没有application_number或letter_date的记录")

        logger.info(f"准备加载 {len(records_to_load)} 条RegulatoryAction记录")

        # 创建约束
        self._create_regulatory_action_constraint()

        # 导入节点
        return self.loader.load_nodes(
            label='RegulatoryAction',
            records=records_to_load,
            merge_key='primary_id'
        )

    def _create_regulatory_action_constraint(self):
        """创建RegulatoryAction约束"""
        from neo4j import GraphDatabase

        with GraphDatabase.driver(
            self.config.neo4j_uri,
            auth=(self.config.neo4j_user, self.config.neo4j_password)
        ) as driver:
            with driver.session(database=self.config.neo4j_database) as session:
                try:
                    session.run("""
                        CREATE CONSTRAINT regulatory_action_id IF NOT EXISTS
                        FOR (r:RegulatoryAction) REQUIRE r.primary_id IS UNIQUE
                    """)
                except Exception as e:
                    logger.warning(f"创建约束失败: {e}")

    def process_chembl_database(self) -> Dict[str, Any]:
        """处理ChEMBL数据库"""
        logger.info("\n[4/5] 处理ChEMBL数据库...")

        chembl_archive = self.sources_dir / "rd" / "chembl_34_sqlite.tar.gz"
        if not chembl_archive.exists():
            return {'status': 'skipped', 'reason': 'Archive not found'}

        # 检查文件是否完整
        if chembl_archive.stat().st_size < 1000:
            logger.warning(f"ChEMBL归档文件过小或损坏，跳过处理")
            return {'status': 'skipped', 'reason': 'Archive file is corrupted or incomplete'}

        # 解压
        extract_dir = self.processed_dir / "chembl"
        extract_dir.mkdir(exist_ok=True)

        try:
            # 检查是否已经解压
            existing_db = list(extract_dir.rglob("*.db"))
            if existing_db:
                logger.info(f"使用已解压的数据库: {existing_db[0]}")
                db_file = existing_db[0]
            else:
                with tarfile.open(chembl_archive, 'r:gz') as tar:
                    tar.extractall(extract_dir)

                # 查找数据库文件
                db_file = None
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if file.endswith('.db'):
                            db_file = Path(root) / file
                            break
                    if db_file:
                        break

                if not db_file:
                    return {'status': 'failed', 'error': 'Database file not found'}

            logger.info(f"ChEMBL数据库: {db_file}")

            # 导入数据
            compounds_imported, targets_imported = self._import_chembl_data(db_file)

            return {
                'compounds_imported': compounds_imported,
                'targets_imported': targets_imported
            }

        except tarfile.ReadError as e:
            logger.warning(f"ChEMBL归档文件损坏，跳过: {e}")
            return {'status': 'skipped', 'reason': 'Archive file is corrupted'}
        except Exception as e:
            logger.error(f"处理ChEMBL失败: {e}")
            return {'status': 'failed', 'error': str(e)}

    def _import_chembl_data(self, db_file: Path) -> tuple:
        """从ChEMBL数据库导入化合物和靶点"""
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        # 导入化合物（限制数量）
        cursor.execute("""
            SELECT chembl_id, canonical_smiles, molecule_type, max_phase
            FROM compound_structures
            JOIN molecule_dictionary ON compound_structures.molregno = molecule_dictionary.molregno
            LIMIT 1000
        """)
        compounds = cursor.fetchall()

        compound_records = []
        for comp in compounds:
            properties = {
                'primary_id': comp[0] or f"CHEMBL-UNKNOWN",
                'canonical_smiles': comp[1] or '',
                'molecule_type': comp[2] or 'Small molecule',
                'max_phase': comp[3] or 0,
                'source': 'ChEMBL'
            }
            compound_records.append(properties)

        compounds_created = self.loader.load_nodes(
            label='Compound',
            records=compound_records,
            merge_key='primary_id'
        )

        # 导入靶点
        cursor.execute("""
            SELECT chembl_id, target_type, organism
            FROM target_dictionary
            LIMIT 500
        """)
        targets = cursor.fetchall()

        target_records = []
        for tgt in targets:
            properties = {
                'primary_id': tgt[0] or f"TARGET-UNKNOWN",
                'target_type': tgt[1] or 'Unknown',
                'organism': tgt[2] or 'Unknown',
                'source': 'ChEMBL'
            }
            target_records.append(properties)

        targets_created = self.loader.load_nodes(
            label='Target',
            records=target_records,
            merge_key='primary_id'
        )

        conn.close()

        return compounds_created, targets_created

    def process_pdf_documents(self) -> Dict[str, Any]:
        """处理PDF文档"""
        logger.info("\n[5/5] 处理PDF文档...")

        # 检查PyPDF2是否安装
        try:
            import PyPDF2
        except ImportError:
            logger.warning("PyPDF2 未安装，跳过PDF内容提取。仅记录文件元数据。")

        # 查找所有PDF文件
        pdf_files = list(self.sources_dir.rglob("*.pdf"))
        logger.info(f"找到 {len(pdf_files)} 个PDF文件")

        # 使用文档管道处理
        from etl.pipelines.document_pipeline import DocumentPipeline

        pipeline = DocumentPipeline()

        total_processed = 0
        # 限制处理数量，避免超时
        max_pdfs = 10
        for pdf_file in pdf_files[:max_pdfs]:
            try:
                result = pipeline.run(
                    str(pdf_file),
                    load_to_neo4j=True,
                    dry_run=False
                )
                total_processed += result.get('extraction', {}).get('files_processed', 0)
                self.stats['imported_records'] += result.get('loading', {}).get('nodes_created', 0)
            except Exception as e:
                logger.warning(f"处理PDF {pdf_file.name} 失败: {e}")
                self.stats['errors'].append(str(pdf_file))

        logger.info(f"已处理 {min(len(pdf_files), max_pdfs)}/{len(pdf_files)} 个PDF文件")

        return {
            'pdf_files_processed': total_processed,
            'total_pdf_files_found': len(pdf_files)
        }


def main():
    """主函数"""
    processor = DataProcessor()
    result = processor.run_all()

    # 保存结果
    results_file = project_root / "data" / "processing_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"\n处理结果已保存到: {results_file}")

    return 0 if result['status'] == 'success' else 1


if __name__ == '__main__':
    sys.exit(main())
