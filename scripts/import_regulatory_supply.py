#!/usr/bin/env python3
"""
导入监管和供应链数据
- FDA Complete Response Letters (CRLs)
- FDA Drug Shortages (通过 API 获取)
"""

import json
import logging
import requests
from datetime import datetime
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "pharmaKG2024!"

def import_crl_data(driver, crl_file):
    """导入 FDA Complete Response Letters"""
    logger.info(f"导入 CRL 数据: {crl_file}")

    with open(crl_file, 'r') as f:
        data = json.load(f)

    results = data.get('results', [])
    logger.info(f"找到 {len(results)} 封 CRL")

    with driver.session() as session:
        # 创建 CRL 节点
        count = 0
        batch = []

        for crl in results:
            batch.append({
                'file_name': crl.get('file_name', ''),
                'letter_date': crl.get('letter_date', ''),
                'letter_year': crl.get('letter_year'),
                'letter_type': crl.get('letter_type', ''),
                'approval_status': crl.get('approval_status', ''),
                'application_number': ', '.join(crl.get('application_number', [])) if isinstance(crl.get('application_number'), list) else crl.get('application_number', ''),
                'company_name': crl.get('company_name', ''),
                'company_address': crl.get('company_address', ''),
                'company_rep': crl.get('company_rep', ''),
                'approver_name': crl.get('approver_name', ''),
                'approver_title': crl.get('approver_title', ''),
                'approver_center': ', '.join(crl.get('approver_center', [])) if isinstance(crl.get('approver_center'), list) else crl.get('approver_center', ''),
                'text_preview': crl.get('text', '')[:500] if crl.get('text') else ''
            })

            if len(batch) >= 100:
                _batch_create_crls(session, batch)
                count += len(batch)
                logger.info(f"已导入 {count}/{len(results)} 封 CRL")
                batch = []

        if batch:
            _batch_create_crls(session, batch)
            count += len(batch)

        logger.info(f"✅ CRL 导入完成: {count} 封")

        # 创建公司节点和关系
        create_company_relationships(session, results)

    return count

def _batch_create_crls(session, batch):
    """批量创建 CRL 节点"""
    session.run("""
        UNWIND $batch AS row
        MERGE (c:CompleteResponseLetter {file_name: row.file_name})
        SET c.letter_date = row.letter_date,
            c.letter_year = row.letter_year,
            c.letter_type = row.letter_type,
            c.approval_status = row.approval_status,
            c.application_number = row.application_number,
            c.company_name = row.company_name,
            c.company_address = row.company_address,
            c.company_rep = row.company_rep,
            c.approver_name = row.approver_name,
            c.approver_title = row.approver_title,
            c.approver_center = row.approver_center,
            c.text_preview = row.text_preview,
            c.source = 'FDA'
    """, batch=batch)

def create_company_relationships(session, results):
    """创建公司节点和 CRL-公司关系"""
    logger.info("创建公司节点和关系...")

    companies = {}
    for crl in results:
        company_name = crl.get('company_name', '')
        if company_name and company_name not in companies:
            companies[company_name] = {
                'name': company_name,
                'address': crl.get('company_address', '')
            }

    # 创建公司节点
    batch = list(companies.values())
    session.run("""
        UNWIND $batch AS row
        MERGE (c:Company {name: row.name})
        SET c.address = row.address,
            c.type = 'Pharmaceutical'
    """, batch=batch)

    logger.info(f"创建了 {len(companies)} 个公司节点")

    # 创建 CRL-公司关系
    session.run("""
        MATCH (crl:CompleteResponseLetter)
        MATCH (c:Company {name: crl.company_name})
        MERGE (crl)-[:SENT_TO]->(c)
    """)

def fetch_drug_shortages():
    """从 FDA API 获取药品短缺数据"""
    logger.info("从 FDA API 获取药品短缺数据...")

    url = "https://api.fda.gov/drug/shortages.json"
    params = {"limit": 100}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        results = data.get('results', [])
        logger.info(f"获取到 {len(results)} 条短缺记录")
        return results
    except Exception as e:
        logger.error(f"获取短缺数据失败: {e}")
        return []

def import_drug_shortages(driver, shortages):
    """导入药品短缺数据"""
    if not shortages:
        logger.warning("没有短缺数据可导入")
        return 0

    logger.info(f"导入 {len(shortages)} 条药品短缺记录")

    with driver.session() as session:
        count = 0
        batch = []

        for shortage in shortages:
            open_fda = shortage.get('openfda', {})

            batch.append({
                'id': shortage.get('id', ''),
                'generic_name': ', '.join(open_fda.get('generic_name', [])) if open_fda.get('generic_name') else shortage.get('generic_name', ''),
                'brand_name': ', '.join(open_fda.get('brand_name', [])) if open_fda.get('brand_name') else '',
                'manufacturer': ', '.join(open_fda.get('manufacturer_name', [])) if open_fda.get('manufacturer_name') else shortage.get('company_name', ''),
                'shortage_status': shortage.get('shortage_status', ''),
                'initial_posting_date': shortage.get('initial_posting_date', ''),
                'update_date': shortage.get('update_date', ''),
                'reason_for_shortage': shortage.get('shortage_reason', ''),
                'therapeutic_categories': ', '.join(open_fda.get('pharm_class', [])) if open_fda.get('pharm_class') else '',
                'route': ', '.join(open_fda.get('route', [])) if open_fda.get('route') else '',
                'dosage_form': ', '.join(open_fda.get('dosage_form', [])) if open_fda.get('dosage_form') else ''
            })

            if len(batch) >= 50:
                _batch_create_shortages(session, batch)
                count += len(batch)
                logger.info(f"已导入 {count}/{len(shortages)} 条短缺记录")
                batch = []

        if batch:
            _batch_create_shortages(session, batch)
            count += len(batch)

        logger.info(f"✅ 药品短缺导入完成: {count} 条")

    return count

def _batch_create_shortages(session, batch):
    """批量创建短缺节点"""
    session.run("""
        UNWIND $batch AS row
        MERGE (s:DrugShortage {id: row.id})
        SET s.generic_name = row.generic_name,
            s.brand_name = row.brand_name,
            s.manufacturer = row.manufacturer,
            s.shortage_status = row.shortage_status,
            s.initial_posting_date = row.initial_posting_date,
            s.update_date = row.update_date,
            s.reason_for_shortage = row.reason_for_shortage,
            s.therapeutic_categories = row.therapeutic_categories,
            s.route = row.route,
            s.dosage_form = row.dosage_form,
            s.source = 'FDA'
    """, batch=batch)

def import_regulatory_documents(driver):
    """导入已处理的监管文档"""
    import os

    # 查找最新的 entities 文件
    entities_dir = '/root/autodl-tmp/pj-pharmaKG/data/processed/documents/regulatory'
    entities_files = [f for f in os.listdir(entities_dir) if f.startswith('entities_')]

    if not entities_files:
        logger.warning("没有找到已处理的监管文档")
        return 0

    latest_file = sorted(entities_files)[-1]
    entities_file = os.path.join(entities_dir, latest_file)

    logger.info(f"导入监管文档实体: {entities_file}")

    with open(entities_file, 'r') as f:
        entities = json.load(f)

    logger.info(f"找到 {len(entities)} 个实体")

    with driver.session() as session:
        # 按 entity_type 分组导入
        type_counts = {}

        for entity in entities:
            entity_type = entity.get('entity_type', 'Unknown')

            if entity_type not in type_counts:
                type_counts[entity_type] = 0

            # 根据类型创建节点
            if entity_type == 'RegulatoryDocument':
                session.run("""
                    MERGE (d:RegulatoryDocument {id: $id})
                    SET d.title = $title,
                        d.content = $content,
                        d.source = $source,
                        d.doc_type = $doc_type
                """, id=entity.get('id', ''), title=entity.get('title', ''),
                     content=entity.get('content', '')[:1000], source=entity.get('source', ''),
                     doc_type=entity.get('doc_type', ''))
                type_counts[entity_type] += 1

        logger.info(f"导入实体统计: {type_counts}")

    return sum(type_counts.values())

def verify_import(driver):
    """验证导入结果"""
    with driver.session() as session:
        # 统计节点
        result = session.run("MATCH (c:CompleteResponseLetter) RETURN count(c) as count")
        crl_count = result.single()["count"]

        result = session.run("MATCH (c:Company) RETURN count(c) as count")
        company_count = result.single()["count"]

        result = session.run("MATCH (s:DrugShortage) RETURN count(s) as count")
        shortage_count = result.single()["count"]

        result = session.run("MATCH (d:RegulatoryDocument) RETURN count(d) as count")
        doc_count = result.single()["count"]

        # 统计关系
        result = session.run("MATCH ()-[r:SENT_TO]->() RETURN count(r) as count")
        sent_to_count = result.single()["count"]

        logger.info(f"\n📊 导入结果统计:")
        logger.info(f"   Complete Response Letters: {crl_count}")
        logger.info(f"   Companies: {company_count}")
        logger.info(f"   Drug Shortages: {shortage_count}")
        logger.info(f"   Regulatory Documents: {doc_count}")
        logger.info(f"   SENT_TO 关系: {sent_to_count}")

        # 显示一些示例
        if crl_count > 0:
            logger.info(f"\n📋 示例 CRL:")
            result = session.run("""
                MATCH (c:CompleteResponseLetter)
                RETURN c.letter_type, c.company_name, c.approval_status, c.letter_date
                LIMIT 5
            """)
            for record in result:
                logger.info(f"   {record['c.letter_type']} - {record['c.company_name']} ({record['c.approval_status']}) - {record['c.letter_date']}")

        if shortage_count > 0:
            logger.info(f"\n📋 示例药品短缺:")
            result = session.run("""
                MATCH (s:DrugShortage)
                RETURN s.generic_name, s.shortage_status, s.manufacturer
                LIMIT 5
            """)
            for record in result:
                logger.info(f"   {record['s.generic_name']} - {record['s.shortage_status']} ({record['s.manufacturer']})")

def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        start_time = datetime.now()

        # 1. 导入 CRL 数据
        crl_file = '/root/autodl-tmp/pj-pharmaKG/data/sources/reviews_crl/transparency-crl-0001-of-0001.json'
        import_crl_data(driver, crl_file)

        # 2. 获取并导入药品短缺数据
        shortages = fetch_drug_shortages()
        if shortages:
            import_drug_shortages(driver, shortages)

        # 3. 验证导入
        verify_import(driver)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"\n⏱️ 总耗时: {elapsed:.1f} 秒")
        logger.info("✅ 监管和供应链数据导入完成!")

    finally:
        driver.close()

if __name__ == "__main__":
    main()
