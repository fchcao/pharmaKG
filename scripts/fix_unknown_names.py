#!/usr/bin/env python3
"""
修复 Neo4j 中名称为 "Unknown" 的化合物和靶点
将 "Unknown" 替换为对应的 chembl_id/target_id
"""

from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "pharmaKG2024!"

def fix_compound_names(driver):
    """修复化合物名称"""
    with driver.session() as session:
        # 查找所有名称为 "Unknown" 的化合物
        result = session.run("""
            MATCH (c:Compound)
            WHERE c.name = 'Unknown' OR c.name IS NULL
            RETURN c.chembl_id as chembl_id, c.name as current_name
            LIMIT 1000
        """)

        compounds_to_fix = list(result)
        logger.info(f"找到 {len(compounds_to_fix)} 个需要修复的化合物")

        batch_size = 100
        for i in range(0, len(compounds_to_fix), batch_size):
            batch = compounds_to_fix[i:i + batch_size]

            # 使用 UNWIND 批量更新
            session.run("""
                UNWIND $batch AS row
                MATCH (c:Compound {chembl_id: row.chembl_id})
                SET c.name = row.chembl_id
            """, batch=[{"chembl_id": record["chembl_id"]} for record in batch])

            logger.info(f"已修复 {min(i + batch_size, len(compounds_to_fix))}/{len(compounds_to_fix)} 个化合物")

def fix_target_names(driver):
    """修复靶点名称"""
    with driver.session() as session:
        # 查找所有名称为 "Unknown" 或包含 "Unknown" 的靶点
        result = session.run("""
            MATCH (t:Target)
            WHERE t.name = 'Unknown Target' OR t.name = 'Unknown' OR t.name IS NULL
            RETURN t.target_id as target_id, t.name as current_name
            LIMIT 1000
        """)

        targets_to_fix = list(result)
        logger.info(f"找到 {len(targets_to_fix)} 个需要修复的靶点")

        batch_size = 100
        for i in range(0, len(targets_to_fix), batch_size):
            batch = targets_to_fix[i:i + batch_size]

            session.run("""
                UNWIND $batch AS row
                MATCH (t:Target {target_id: row.target_id})
                SET t.name = row.target_id
            """, batch=[{"target_id": record["target_id"]} for record in batch])

            logger.info(f"已修复 {min(i + batch_size, len(targets_to_fix))}/{len(targets_to_fix)} 个靶点")

def verify_fix(driver):
    """验证修复结果"""
    with driver.session() as session:
        # 检查化合物
        compound_result = session.run("""
            MATCH (c:Compound)
            WHERE c.name = 'Unknown' OR c.name IS NULL
            RETURN count(c) as count
        """)
        compound_count = compound_result.single()["count"]
        logger.info(f"修复后仍有 {compound_count} 个化合物名称为 'Unknown'")

        # 检查靶点
        target_result = session.run("""
            MATCH (t:Target)
            WHERE t.name = 'Unknown Target' OR t.name = 'Unknown' OR t.name IS NULL
            RETURN count(t) as count
        """)
        target_count = target_result.single()["count"]
        logger.info(f"修复后仍有 {target_count} 个靶点名称为 'Unknown'")

        # 显示一些示例
        sample_result = session.run("""
            MATCH (c:Compound)
            RETURN c.chembl_id, c.name
            LIMIT 5
        """)
        logger.info("化合物样本:")
        for record in sample_result:
            logger.info(f"  {record['c.chembl_id']}: {record['c.name']}")

def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        logger.info("开始修复数据...")
        fix_compound_names(driver)
        fix_target_names(driver)
        verify_fix(driver)
        logger.info("修复完成!")
    finally:
        driver.close()

if __name__ == "__main__":
    main()
