#!/usr/bin/env python3
#===========================================================
# PharmaKG 综合数据导入工具
# Pharmaceutical Knowledge Graph - Comprehensive Data Import
#===========================================================
# 版本: v1.0
# 描述: 导入所有数据源到Neo4j，包含完整日志记录
#===========================================================

import json
import logging
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime

# 配置日志
def setup_logging(log_dir: Path) -> logging.Logger:
    """配置日志系统"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    log_file = log_dir / f"comprehensive_import_{timestamp}.log"

    # 创建根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 清除现有handlers
    root_logger.handlers.clear()

    # 文件handler - 详细日志
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # 控制台handler - 简要日志
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


class ComprehensiveDataImporter:
    """
    综合数据导入器

    导入所有数据源到Neo4j，包含完整的日志记录和验证
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Neo4j配置
        self.neo4j_uri = self.config.get('neo4j_uri', 'bolt://localhost:7687')
        self.neo4j_user = self.config.get('neo4j_user', 'neo4j')
        self.neo4j_password = self.config.get('neo4j_password', 'pharmaKG2024!')
        self.neo4j_database = self.config.get('neo4j_database', 'neo4j')

        # 数据目录
        self.data_root = Path('/root/autodl-tmp/pj-pharmaKG/data')
        self.processed_dir = self.data_root / 'processed'
        self.log_dir = self.data_root / 'logs'
        self.log_dir.mkdir(exist_ok=True)

        # 设置日志
        self.logger = setup_logging(self.log_dir)

        # 导入统计
        self.import_stats = {
            'start_time': datetime.now().isoformat(),
            'entities_imported': 0,
            'relationships_imported': 0,
            'files_processed': [],
            'errors': [],
            'warnings': []
        }

    def run(self, clear_db: bool = False):
        """
        运行综合导入

        Args:
            clear_db: 是否清空现有数据库
        """
        self.logger.info("=" * 80)
        self.logger.info("PharmaKG 综合数据导入")
        self.logger.info("=" * 80)

        try:
            # 1. 清空数据库（如果需要）
            if clear_db:
                self._clear_database()

            # 2. 导入监管文档数据
            regulatory_stats = self._import_regulatory_data()

            # 3. 导入CRL数据
            crl_stats = self._import_crl_data()

            # 4. 验证和生成报告
            self._verify_and_report()

            # 5. 保存导入统计
            self._save_import_stats()

            self.logger.info("=" * 80)
            self.logger.info("✅ 综合数据导入完成")
            self.logger.info("=" * 80)

        except Exception as e:
            self.logger.error(f"导入失败: {e}", exc_info=True)
            raise

    def _clear_database(self):
        """清空数据库"""
        self.logger.info("清空Neo4j数据库...")

        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )

        try:
            with driver.session(database=self.neo4j_database) as session:
                # 删除所有关系
                result = session.run("MATCH ()-[r]->() DELETE r")
                deleted_rels = result.consume().counters.relationships_deleted
                self.logger.info(f"  删除 {deleted_rels} 个关系")
                self.import_stats['relationships_deleted'] = deleted_rels

                # 删除所有节点
                result = session.run("MATCH (n) DELETE n")
                deleted_nodes = result.consume().counters.nodes_deleted
                self.logger.info(f"  删除 {deleted_nodes} 个节点")
                self.import_stats['nodes_deleted'] = deleted_nodes

        finally:
            driver.close()

    def _import_regulatory_data(self) -> Dict[str, Any]:
        """导入监管文档数据"""
        self.logger.info("\n### 导入监管文档数据 ###")

        # 查找最新的修复后的数据文件
        reg_dir = self.processed_dir / 'documents' / 'regulatory'

        # 查找fixed文件
        entity_files = sorted(reg_dir.glob('entities_fixed_*.json'), reverse=True)
        rel_files = sorted(reg_dir.glob('relationships_fixed_*.json'), reverse=True)

        if not entity_files or not rel_files:
            self.logger.warning("未找到修复后的监管数据文件")
            return {'status': 'skipped', 'entities': 0, 'relationships': 0}

        entities_file = entity_files[0]
        relationships_file = rel_files[0]

        self.logger.info(f"使用数据文件:")
        self.logger.info(f"  实体: {entities_file.name}")
        self.logger.info(f"  关系: {relationships_file.name}")

        return self._import_data_files(entities_file, relationships_file, 'regulatory')

    def _import_crl_data(self) -> Dict[str, Any]:
        """导入CRL数据"""
        self.logger.info("\n### 导入CRL数据 ###")

        # 查找CRL JSON处理结果
        crl_dir = self.processed_dir / 'documents' / 'clinical_crl'

        if not crl_dir.exists():
            self.logger.warning("CRL数据目录不存在，跳过")
            return {'status': 'skipped', 'entities': 0, 'relationships': 0}

        # 优先查找修复后的关系文件
        entities_files = sorted(crl_dir.glob('entities_*.json'), reverse=True)
        relationships_files = sorted(crl_dir.glob('relationships_fixed_*.json'), reverse=True)

        # 如果没有修复后的文件，使用原始文件
        if not relationships_files:
            relationships_files = sorted(crl_dir.glob('relationships_*.json'), reverse=True)
            # 过滤掉fixed文件避免重复
            relationships_files = [f for f in relationships_files if 'fixed' not in f.name]

        if entities_files and relationships_files:
            # 使用最新的修复后的关系文件和对应的实体文件
            entities_file = entities_files[0]
            relationships_file = relationships_files[0]

            self.logger.info(f"使用CRL JSON数据:")
            self.logger.info(f"  实体: {entities_file.name}")
            self.logger.info(f"  关系: {relationships_file.name}")

            json_stats = self._import_data_files(entities_file, relationships_file, 'crl_json')
        else:
            json_stats = {'status': 'skipped', 'entities': 0, 'relationships': 0}

        # 查找CRL PDF处理结果
        crl_pdf_dir = self.processed_dir / 'documents' / 'clinical_crl_pdf'

        if crl_pdf_dir.exists():
            entities_files = sorted(crl_pdf_dir.glob('entities_*.json'), reverse=True)
            # 优先使用修复后的关系文件
            relationships_files = sorted(crl_pdf_dir.glob('relationships_fixed_*.json'), reverse=True)
            if not relationships_files:
                relationships_files = sorted(crl_pdf_dir.glob('relationships_*.json'), reverse=True)

            if entities_files and relationships_files:
                entities_file = entities_files[0]
                relationships_file = relationships_files[0]

                self.logger.info(f"使用CRL PDF数据:")
                self.logger.info(f"  实体: {entities_file.name}")
                self.logger.info(f"  关系: {relationships_file.name}")

                pdf_stats = self._import_data_files(entities_file, relationships_file, 'crl_pdf')
            else:
                pdf_stats = {'status': 'skipped', 'entities': 0, 'relationships': 0}
        else:
            pdf_stats = {'status': 'skipped', 'entities': 0, 'relationships': 0}

        # 合并统计
        return {
            'status': 'completed',
            'crl_json': json_stats,
            'crl_pdf': pdf_stats,
            'total_entities': json_stats.get('entities', 0) + pdf_stats.get('entities', 0),
            'total_relationships': json_stats.get('relationships', 0) + pdf_stats.get('relationships', 0)
        }

    def _import_data_files(
        self,
        entities_file: Path,
        relationships_file: Path,
        source_name: str
    ) -> Dict[str, Any]:
        """导入数据文件"""
        from neo4j import GraphDatabase

        self.logger.info(f"导入 {source_name} 数据:")

        # 加载数据
        with open(entities_file, 'r', encoding='utf-8') as f:
            entities = json.load(f)

        with open(relationships_file, 'r', encoding='utf-8') as f:
            relationships = json.load(f)

        self.logger.info(f"  加载 {len(entities)} 个实体, {len(relationships)} 个关系")

        driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )

        try:
            with driver.session(database=self.neo4j_database) as session:
                # 导入实体
                entities_by_label = defaultdict(list)
                entity_ids = set()

                for entity in entities:
                    label = entity.get('label', 'Unknown').replace(':', '_')
                    props = entity.get('properties', {})
                    primary_id = props.get('primary_id', '')

                    if not primary_id:
                        continue

                    entity_ids.add(primary_id)

                    # 扁平化
                    record = {'primary_id': primary_id}
                    for k, v in props.items():
                        if k != 'primary_id' and v is not None:
                            if isinstance(v, str):
                                v = v.replace('\n', ' ').replace('\r', '')
                            record[k] = v

                    entities_by_label[label].append(record)

                self.logger.info(f"  导入实体 ({len(entities_by_label)} 个标签):")
                for label, records in sorted(entities_by_label.items()):
                    batch_size = 500
                    imported = 0
                    for i in range(0, len(records), batch_size):
                        batch = records[i:i+batch_size]
                        query = f"""
                        UNWIND $batch AS row
                        MERGE (n:{label} {{primary_id: row.primary_id}})
                        SET n += row
                        RETURN count(n) as created
                        """
                        result = session.run(query, {"batch": batch})
                        imported += result.consume().counters.nodes_created
                    self.logger.info(f"    {label}: {imported} 个")
                    self.import_stats['entities_imported'] += imported

                # 导入关系
                relationships_by_type = defaultdict(list)
                valid_relationships = 0

                for rel in relationships:
                    from_id = rel.get('from', '')
                    to_id = rel.get('to', '')

                    if from_id in entity_ids and to_id in entity_ids:
                        rel_type = rel.get('relationship_type', 'RELATED_TO').replace(':', '_')
                        relationships_by_type[rel_type].append(rel)
                        valid_relationships += 1

                self.logger.info(f"  导入关系 ({len(relationships_by_type)} 个类型):")
                for rel_type, rels in sorted(relationships_by_type.items()):
                    batch_size = 500
                    imported = 0
                    for i in range(0, len(rels), batch_size):
                        batch = rels[i:i+batch_size]
                        query = f"""
                        UNWIND $batch AS row
                        MATCH (from {{primary_id: row.from}})
                        MATCH (to {{primary_id: row.to}})
                        MERGE (from)-[r:{rel_type}]->(to)
                        SET r += row.properties
                        RETURN count(r) as created
                        """
                        result = session.run(query, {"batch": batch})
                        imported += result.consume().counters.relationships_created
                    self.logger.info(f"    {rel_type}: {imported} 个")
                    self.import_stats['relationships_imported'] += imported

                self.logger.info(f"  有效关系: {valid_relationships}/{len(relationships)}")

                return {
                    'status': 'completed',
                    'source': source_name,
                    'entities': len(entities_by_label),
                    'relationships': len(relationships_by_type)
                }

        finally:
            driver.close()

    def _verify_and_report(self):
        """验证和生成报告"""
        self.logger.info("\n### 生成验证报告 ###")

        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )

        try:
            with driver.session(database=self.neo4j_database) as session:
                # 基本统计
                result = session.run("MATCH (n) RETURN count(n) as count")
                total_nodes = result.single()["count"]

                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                total_rels = result.single()["count"]

                self.logger.info(f"数据库统计:")
                self.logger.info(f"  总节点: {total_nodes}")
                self.logger.info(f"  总关系: {total_rels}")
                self.logger.info(f"  平均每节点关系数: {total_rels/total_nodes if total_nodes > 0 else 0:.2f}")

                # 连接性分析
                result = session.run("""
                    MATCH (n)
                    WITH count(n) as total
                    OPTIONAL MATCH (n)-[r]-()
                    WITH total, count(DISTINCT n) as connected
                    RETURN total, connected, toFloat(connected)/total*100 as percent
                """)
                record = result.single()
                connected_percent = record['percent']

                self.logger.info(f"连接性分析:")
                self.logger.info(f"  连接节点: {record['connected']}/{record['total']} ({connected_percent:.1f}%)")
                self.logger.info(f"  孤立节点: {record['total'] - record['connected']}")

                # 存储在统计中
                self.import_stats['final_nodes'] = total_nodes
                self.import_stats['final_relationships'] = total_rels
                self.import_stats['connected_percent'] = connected_percent
                self.import_stats['end_time'] = datetime.now().isoformat()

        finally:
            driver.close()

    def _save_import_stats(self):
        """保存导入统计"""
        stats_file = self.log_dir / f"import_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.import_stats, f, ensure_ascii=False, indent=2)

        self.logger.info(f"\n导入统计已保存: {stats_file}")


if __name__ == '__main__':
    import sys

    # 解析命令行参数
    clear_db = '--clear' in sys.argv

    importer = ComprehensiveDataImporter({
        'neo4j_uri': 'bolt://localhost:7687',
        'neo4j_user': 'neo4j',
        'neo4j_password': 'pharmaKG2024!',
        'neo4j_database': 'neo4j'
    })

    importer.run(clear_db=clear_db)
