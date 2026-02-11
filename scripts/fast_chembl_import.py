#!/usr/bin/env python3
"""
快速 ChEMBL 数据导入脚本
直接从 ChEMBL SQLite 导入数据到 Neo4j，避免复杂查询
"""

import sqlite3
import logging
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Neo4j 连接配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "pharmaKG2024!"

def import_compounds(cursor, session, limit=10000):
    """导入化合物"""
    logger.info(f"导入化合物 (limit={limit})...")

    # 简单查询，避免复杂 JOIN
    query = f"""
        SELECT md.molregno, md.chembl_id, md.pref_name, md.molecule_type, md.max_phase,
               cs.canonical_smiles, cs.standard_inchi_key
        FROM molecule_dictionary md
        LEFT JOIN compound_structures cs ON md.molregno = cs.molregno
        WHERE md.chembl_id IS NOT NULL
        LIMIT {limit}
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    logger.info(f"查询到 {len(rows)} 个化合物")

    count = 0
    batch = []

    for row in rows:
        molregno, chembl_id, pref_name, mol_type, max_phase, smiles, inchikey = row

        batch.append({
            'chembl_id': chembl_id,
            'molregno': molregno,
            'name': pref_name or chembl_id,  # 使用 chembl_id 作为 fallback
            'molecule_type': mol_type,
            'max_phase': max_phase,
            'smiles': smiles,
            'inchikey': inchikey
        })

        if len(batch) >= 1000:
            _batch_create_compounds(session, batch)
            count += len(batch)
            logger.info(f"已导入 {count}/{len(rows)} 个化合物")
            batch = []

    if batch:
        _batch_create_compounds(session, batch)
        count += len(batch)

    logger.info(f"✅ 化合物导入完成: {count} 个")
    return count

def _batch_create_compounds(session, batch):
    """批量创建化合物"""
    session.run("""
        UNWIND $batch AS row
        MERGE (c:Compound {chembl_id: row.chembl_id})
        SET c.molregno = row.molregno,
            c.name = row.name,
            c.molecule_type = row.molecule_type,
            c.max_phase = row.max_phase,
            c.canonical_smiles = row.smiles,
            c.inchikey = row.inchikey
    """, batch=batch)

def import_targets(cursor, session, limit=5000):
    """导入靶点"""
    logger.info(f"导入靶点 (limit={limit})...")

    query = f"""
        SELECT tid, chembl_id, pref_name, target_type, organism
        FROM target_dictionary
        WHERE chembl_id IS NOT NULL
        LIMIT {limit}
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    logger.info(f"查询到 {len(rows)} 个靶点")

    batch = []
    count = 0

    for row in rows:
        tid, chembl_id, pref_name, target_type, organism = row

        batch.append({
            'target_id': chembl_id,
            'chembl_id': chembl_id,
            'tid': tid,
            'name': pref_name or chembl_id,
            'target_type': target_type,
            'organism': organism
        })

        if len(batch) >= 1000:
            _batch_create_targets(session, batch)
            count += len(batch)
            logger.info(f"已导入 {count}/{len(rows)} 个靶点")
            batch = []

    if batch:
        _batch_create_targets(session, batch)
        count += len(batch)

    logger.info(f"✅ 靶点导入完成: {count} 个")
    return count

def _batch_create_targets(session, batch):
    """批量创建靶点"""
    session.run("""
        UNWIND $batch AS row
        MERGE (t:Target {target_id: row.target_id})
        SET t.chembl_id = row.chembl_id,
            t.tid = row.tid,
            t.name = row.name,
            t.target_type = row.target_type,
            t.organism = row.organism
    """, batch=batch)

def import_bioactivities(cursor, session, limit=50000):
    """导入生物活性关系"""
    logger.info(f"导入生物活性关系 (limit={limit})...")

    # 只导入有 pchembl_value 的活动（表示高质量数据）
    query = f"""
        SELECT md.chembl_id as compound_chembl_id,
               td.chembl_id as target_chembl_id,
               a.pchembl_value,
               a.standard_type,
               a.standard_relation,
               a.standard_value,
               a.standard_units
        FROM activities a
        JOIN molecule_dictionary md ON a.molregno = md.molregno
        JOIN assays ass ON a.assay_id = ass.assay_id
        JOIN target_dictionary td ON ass.tid = td.tid
        WHERE a.pchembl_value IS NOT NULL
        AND a.pchembl_value >= 5
        AND md.chembl_id IS NOT NULL
        AND td.chembl_id IS NOT NULL
        LIMIT {limit}
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    logger.info(f"查询到 {len(rows)} 条生物活性记录")

    batch = []
    count = 0
    created = 0

    for row in rows:
        compound_id, target_id, pchembl, std_type, std_rel, std_val, std_units = row

        batch.append({
            'compound_id': compound_id,
            'target_id': target_id,
            'pchembl_value': float(pchembl) if pchembl else None,
            'standard_type': std_type,
            'standard_relation': std_rel,
            'standard_value': float(std_val) if std_val else None,
            'standard_units': std_units
        })

        if len(batch) >= 1000:
            created += _batch_create_bioactivities(session, batch)
            count += len(batch)
            logger.info(f"已处理 {count}/{len(rows)} 条，创建了 {created} 个关系")
            batch = []

    if batch:
        created += _batch_create_bioactivities(session, batch)
        count += len(batch)

    logger.info(f"✅ 生物活性导入完成: 处理了 {count} 条，创建了 {created} 个关系")
    return created

def _batch_create_bioactivities(session, batch):
    """批量创建生物活性关系"""
    result = session.run("""
        UNWIND $batch AS row
        MATCH (c:Compound {chembl_id: row.compound_id})
        MATCH (t:Target {target_id: row.target_id})
        MERGE (c)-[r:BINDS_TO]->(t)
        SET r.pchembl_value = row.pchembl_value,
            r.standard_type = row.standard_type,
            r.standard_relation = row.standard_relation,
            r.standard_value = row.standard_value,
            r.standard_units = row.standard_units,
            r.source = 'ChEMBL'
        RETURN count(r) as created
    """, batch=batch)

    record = result.single()
    return record["created"] if record else 0

def verify_import(driver):
    """验证导入结果"""
    from neo4j import GraphDatabase

    with driver.session() as session:
        # 统计节点
        result = session.run("MATCH (c:Compound) RETURN count(c) as count")
        compounds = result.single()["count"]

        result = session.run("MATCH (t:Target) RETURN count(t) as count")
        targets = result.single()["count"]

        result = session.run("MATCH ()-[r:BINDS_TO]->() RETURN count(r) as count")
        relationships = result.single()["count"]

        logger.info(f"\n📊 导入结果统计:")
        logger.info(f"   化合物: {compounds}")
        logger.info(f"   靶点: {targets}")
        logger.info(f"   BINDS_TO 关系: {relationships}")

        # 显示一些示例
        logger.info(f"\n📋 示例化合物:")
        result = session.run("""
            MATCH (c:Compound)
            RETURN c.chembl_id, c.name, c.max_phase
            LIMIT 5
        """)
        for record in result:
            logger.info(f"   {record['c.chembl_id']}: {record['c.name']} (phase {record['c.max_phase']})")

        logger.info(f"\n📋 示例靶点:")
        result = session.run("""
            MATCH (t:Target)
            RETURN t.chembl_id, t.name, t.organism
            LIMIT 5
        """)
        for record in result:
            logger.info(f"   {record['t.chembl_id']}: {record['t.name']} ({record['t.organism']})")

        if relationships > 0:
            logger.info(f"\n📋 示例化合物-靶点关系:")
            result = session.run("""
                MATCH (c:Compound)-[r:BINDS_TO]->(t:Target)
                RETURN c.chembl_id, t.chembl_id, r.pchembl_value
                LIMIT 5
            """)
            for record in result:
                logger.info(f"   {record['c.chembl_id']} -[pchembl={record['r.pchembl_value']}]-> {record['t.chembl_id']}")

def main():
    # 参数
    chembl_db = sys.argv[1] if len(sys.argv) > 1 else "data/sources/rd/chembl_36/chembl_36_sqlite/chembl_36.db"
    compound_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    target_limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
    activity_limit = int(sys.argv[4]) if len(sys.argv) > 4 else 50000

    logger.info(f"ChEMBL 数据库: {chembl_db}")
    logger.info(f"化合物限制: {compound_limit}")
    logger.info(f"靶点限制: {target_limit}")
    logger.info(f"活性限制: {activity_limit}")

    from neo4j import GraphDatabase

    # 连接数据库
    conn = sqlite3.connect(chembl_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        start_time = datetime.now()

        with driver.session() as session:
            # 导入数据
            import_compounds(cursor, session, compound_limit)
            import_targets(cursor, session, target_limit)
            import_bioactivities(cursor, session, activity_limit)

        # 验证
        verify_import(driver)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"\n⏱️ 总耗时: {elapsed:.1f} 秒")
        logger.info("✅ 导入完成!")

    finally:
        conn.close()
        driver.close()

if __name__ == "__main__":
    main()
