#!/usr/bin/env python3
"""
导入所有 FDA Complete Response Letters (CRLs)
使用 file_name + letter_date + company_name + application_number 作为唯一标识
"""

import json
import logging
import hashlib
from datetime import datetime
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "pharmaKG2024!"

def generate_crl_id(file_name, letter_date, company_name, application_number):
    """生成唯一 CRL ID，包含 application_number"""
    app_num = application_number if isinstance(application_number, str) else ', '.join(application_number or [])
    unique_str = f"{file_name}_{letter_date}_{company_name}_{app_num}"
    return hashlib.md5(unique_str.encode()).hexdigest()[:16]

def import_all_crls(driver, crl_file):
    """导入所有 FDA Complete Response Letters"""
    logger.info(f"导入 CRL 数据: {crl_file}")

    with open(crl_file, 'r') as f:
        data = json.load(f)

    results = data.get('results', [])
    logger.info(f"JSON 文件中共有 {len(results)} 条 CRL 记录")

    with driver.session() as session:
        # 清除现有 CRL 数据
        logger.info("清除现有 CRL 数据...")
        session.run("MATCH (c:CompleteResponseLetter) DETACH DELETE c")

        # 创建 CRL 节点
        count = 0
        batch = []
        seen_ids = set()

        for crl in results:
            file_name = crl.get('file_name', '')
            letter_date = crl.get('letter_date', '')
            company_name = crl.get('company_name', '')
            application_number = crl.get('application_number', '')

            # 生成唯一 ID (包含 application_number)
            crl_id = generate_crl_id(file_name, letter_date, company_name, application_number)

            # 跳过完全重复的记录
            if crl_id in seen_ids:
                logger.warning(f"跳过重复记录: {file_name}, {letter_date}, {company_name}, {application_number}")
                continue
            seen_ids.add(crl_id)

            batch.append({
                'crl_id': crl_id,
                'file_name': file_name,
                'letter_date': letter_date,
                'letter_year': crl.get('letter_year'),
                'letter_type': crl.get('letter_type', ''),
                'approval_status': crl.get('approval_status', ''),
                'application_number': ', '.join(application_number) if isinstance(application_number, list) else (application_number or ''),
                'company_name': company_name,
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
                logger.info(f"已导入 {count}/{len(results)} 条 CRL 记录")
                batch = []

        if batch:
            _batch_create_crls(session, batch)
            count += len(batch)

        logger.info(f"✅ CRL 导入完成: {count} 条唯一记录")

        # 创建公司节点和关系
        create_company_relationships(session, results)

    return count

def _batch_create_crls(session, batch):
    """批量创建 CRL 节点"""
    session.run("""
        UNWIND $batch AS row
        CREATE (c:CompleteResponseLetter {crl_id: row.crl_id})
        SET c.file_name = row.file_name,
            c.letter_date = row.letter_date,
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

    # 先清除现有公司关系
    session.run("MATCH ()-[r:SENT_TO]->() DELETE r")

    # 收集所有唯一公司
    companies = {}
    for crl in results:
        company_name = crl.get('company_name', '')
        if company_name and company_name not in companies:
            companies[company_name] = {
                'name': company_name,
                'address': crl.get('company_address', '')
            }

    # 创建或更新公司节点
    batch = list(companies.values())
    session.run("""
        UNWIND $batch AS row
        MERGE (c:Company {name: row.name})
        SET c.address = row.address,
            c.type = 'Pharmaceutical'
    """, batch=batch)

    logger.info(f"创建了 {len(companies)} 个公司节点")

    # 创建 CRL-公司关系
    result = session.run("""
        MATCH (crl:CompleteResponseLetter)
        MATCH (c:Company {name: crl.company_name})
        MERGE (crl)-[:SENT_TO]->(c)
        RETURN count(crl) as count
    """)
    rel_count = result.single()["count"]
    logger.info(f"创建了 {rel_count} 个 SENT_TO 关系")

def verify_import(driver):
    """验证导入结果"""
    with driver.session() as session:
        result = session.run("MATCH (c:CompleteResponseLetter) RETURN count(c) as count")
        crl_count = result.single()["count"]

        result = session.run("MATCH (c:Company) RETURN count(c) as count")
        company_count = result.single()["count"]

        result = session.run("MATCH ()-[r:SENT_TO]->() RETURN count(r) as count")
        rel_count = result.single()["count"]

        logger.info(f"\n📊 导入结果统计:")
        logger.info(f"   Complete Response Letters: {crl_count}")
        logger.info(f"   Companies: {company_count}")
        logger.info(f"   SENT_TO 关系: {rel_count}")

        # 显示一些示例
        logger.info(f"\n📋 示例 CRL (前5条):")
        result = session.run("""
            MATCH (c:CompleteResponseLetter)
            RETURN c.application_number, c.letter_type, c.company_name, c.approval_status, c.letter_date
            LIMIT 5
        """)
        for record in result:
            logger.info(f"   {record['c.application_number']} - {record['c.letter_type']} - {record['c.company_name']} ({record['c.approval_status']}) - {record['c.letter_date']}")

        # 按 approval_status 分组统计
        logger.info(f"\n📊 按 approval_status 分组:")
        result = session.run("""
            MATCH (c:CompleteResponseLetter)
            RETURN c.approval_status as status, count(c) as count
            ORDER BY count DESC
        """)
        for record in result:
            logger.info(f"   {record['status'] or 'Unknown'}: {record['count']}")

def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        start_time = datetime.now()

        # 导入所有 CRL 数据
        crl_file = '/root/autodl-tmp/pj-pharmaKG/data/sources/reviews_crl/transparency-crl-0001-of-0001.json'
        import_all_crls(driver, crl_file)

        # 验证导入
        verify_import(driver)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"\n⏱️ 总耗时: {elapsed:.1f} 秒")
        logger.info("✅ 所有 CRL 数据导入完成!")

    finally:
        driver.close()

if __name__ == "__main__":
    main()
