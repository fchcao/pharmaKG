#!/usr/bin/env python3
"""
Quick Test Data Import for PharmaKG
快速导入测试数据到 Neo4j
"""

import sqlite3
import logging
from pathlib import Path
from neo4j import GraphDatabase

# 配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "pharmaKG2024!"
CHEMBL_DB = "/root/autodl-tmp/pj-pharmaKG/data/sources/rd/chembl_36/chembl_36_sqlite/chembl_36.db"
LIMIT_COMPOUNDS = 100
LIMIT_TARGETS = 50

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_test_data():
    """导入测试数据到 Neo4j"""

    logger.info("开始导入测试数据...")

    # 连接 Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        # 清空现有数据
        with driver.session() as session:
            logger.info("清空现有数据...")
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("数据已清空")

        # 连接 ChEMBL 数据库
        logger.info(f"连接 ChEMBL 数据库: {CHEMBL_DB}")
        conn = sqlite3.connect(CHEMBL_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        with driver.session() as session:
            # 1. 导入化合物
            logger.info(f"导入 {LIMIT_COMPOUNDS} 个化合物...")
            cursor.execute("""
                SELECT chembl_id, molregno, pref_name, molecule_type, max_phase
                FROM molecule_dictionary
                LIMIT ?
            """, (LIMIT_COMPOUNDS,))

            compounds = cursor.fetchall()
            compound_count = 0

            for row in compounds:
                try:
                    chembl_id = row['chembl_id']
                    molregno = row['molregno']
                    pref_name = row['pref_name'] or 'Unknown'

                    # 创建化合物节点
                    session.run("""
                        MERGE (c:Compound {chembl_id: $chembl_id})
                        SET c.molregno = $molregno,
                            c.name = $name,
                            c.molecule_type = $mol_type,
                            c.max_phase = $max_phase
                    """, chembl_id=chembl_id, molregno=molregno, name=pref_name,
                       mol_type=row['molecule_type'], max_phase=row['max_phase'])
                    compound_count += 1

                    if compound_count % 10 == 0:
                        logger.info(f"  已导入 {compound_count} 个化合物...")

                except Exception as e:
                    logger.error(f"导入化合物失败: {e}")

            logger.info(f"✅ 化合物导入完成: {compound_count} 个")

            # 2. 导入靶点 - 简化版本
            logger.info(f"导入靶点数据...")
            cursor.execute("""
                SELECT td.tid, td.chembl_id as target_chembl_id, td.pref_name,
                       td.organism, td.target_type
                FROM target_dictionary td
                WHERE td.target_type = 'SINGLE PROTEIN'
                LIMIT ?
            """, (LIMIT_TARGETS,))

            targets = cursor.fetchall()
            target_count = 0

            for row in targets:
                try:
                    tid = row['tid']
                    target_chembl_id = row['target_chembl_id']
                    pref_name = row['pref_name'] or 'Unknown Target'
                    organism = row['organism'] or 'Unknown'

                    # 使用 chembl_id 作为主要 ID
                    session.run("""
                        MERGE (t:Target {target_id: $target_id})
                        SET t.tid = $tid,
                            t.chembl_id = $chembl_id,
                            t.name = $name,
                            t.organism = $organism,
                            t.target_type = $target_type
                    """, target_id=target_chembl_id, tid=tid, chembl_id=target_chembl_id,
                       name=pref_name, organism=organism, target_type=row['target_type'])
                    target_count += 1

                except Exception as e:
                    logger.error(f"导入靶点失败: {e}")

            logger.info(f"✅ 靶点导入完成: {target_count} 个")

            # 3. 导入一些生物活性数据（化合物-靶点关系）
            logger.info("导入生物活性数据...")
            cursor.execute("""
                SELECT a.molregno, a.pchembl_value,
                       md.chembl_id as compound_chembl_id,
                       td.chembl_id as target_chembl_id
                FROM activities a
                JOIN molecule_dictionary md ON a.molregno = md.molregno
                JOIN assays ass ON a.assay_id = ass.assay_id
                JOIN target_dictionary td ON ass.tid = td.tid
                WHERE a.pchembl_value IS NOT NULL
                LIMIT 50
            """)

            activities = cursor.fetchall()
            activity_count = 0

            for row in activities:
                try:
                    compound_chembl_id = row['compound_chembl_id']
                    target_chembl_id = row['target_chembl_id']
                    pchembl_value = row['pchembl_value']

                    # 创建关系
                    result = session.run("""
                        MATCH (c:Compound {chembl_id: $chembl_id})
                        MATCH (t:Target {target_id: $target_id})
                        MERGE (c)-[r:ACTS_ON]->(t)
                        SET r.pchembl_value = $pchembl_value
                        RETURN c.name as compound, t.name as target
                    """, chembl_id=compound_chembl_id, target_id=target_chembl_id,
                       pchembl_value=pchembl_value)

                    if result.peek():
                        activity_count += 1

                except Exception as e:
                    pass  # 忽略无法匹配的关系

            logger.info(f"✅ 生物活性导入完成: {activity_count} 个关系")

        # 验证导入结果
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as total")
            total = result.single()['total']
            logger.info(f"📊 总节点数: {total}")

            result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
            rels = result.single()['total']
            logger.info(f"📊 总关系数: {rels}")

            # 显示一些示例数据
            logger.info("\n📋 示例化合物:")
            result = session.run("MATCH (c:Compound) RETURN c.name, c.chembl_id LIMIT 5")
            for row in result:
                logger.info(f"  - {row['c.name']} ({row['c.chembl_id']})")

            logger.info("\n📋 示例靶点:")
            result = session.run("MATCH (t:Target) RETURN t.name LIMIT 5")
            for row in result:
                logger.info(f"  - {row['t.name']}")

        logger.info("✅ 测试数据导入完成!")

    except Exception as e:
        logger.error(f"导入失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()
        conn.close()

if __name__ == "__main__":
    import_test_data()
