#!/usr/bin/env python3
#===========================================================
# ETL 测试脚本 - 在测试数据上运行 ETL 管道
# Pharmaceutical Knowledge Graph - ETL Test Runner
#===========================================================
# 版本: v1.0
# 描述: 运行各领域 ETL 管道导入测试数据
#===========================================================

import os
import sys
import argparse
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 激活环境检查
def check_environment():
    """检查环境配置"""
    print("=== 环境检查 ===")

    # 检查 Python 环境
    print(f"✓ Python: {sys.version.split()[0]}")

    # 检查 Neo4j 连接
    try:
        from neo4j import GraphDatabase
        uri = "bolt://localhost:7687"
        username = "neo4j"
        password = "pharmaKG2024!"

        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        driver.close()
        print("✓ Neo4j: 连接成功 (bolt://localhost:7687)")
        return True
    except Exception as e:
        print(f"✗ Neo4j: 连接失败 - {e}")
        print("")
        print("请先启动 Neo4j:")
        print("  cd /root/autodl-tmp/pj-pharmaKG/neo4j/current")
        print("  bin/neo4j start")
        print("")
        print("或运行安装脚本:")
        print("  bash scripts/install_neo4j.sh <path-to-neo4j-tar.gz>")
        return False


def run_etl_test(pipeline_name, limit=10):
    """运行指定领域的 ETL 测试"""
    print(f"\n=== 运行 {pipeline_name.upper()} ETL 管道 ===")

    # 导入 ETL 模块
    if pipeline_name == "rd":
        from etl.pipelines.rd_pipeline import run_rd_pipeline
        print("导入 ChEMBL 化合物和靶点数据...")
        return run_rd_pipeline(limit_compounds=limit, limit_targets=limit)

    elif pipeline_name == "clinical":
        from etl.pipelines.clinical_pipeline import run_clinical_pipeline
        print("导入 ClinicalTrials.gov 临床试验数据...")
        return run_clinical_pipeline(limit=limit)

    elif pipeline_name == "supply":
        from etl.pipelines.sc_pipeline import run_supply_chain_pipeline
        print("导入 FDA 药品短缺数据...")
        return run_supply_chain_pipeline(limit=limit)

    elif pipeline_name == "regulatory":
        from etl.pipelines.regulatory_pipeline import run_regulatory_pipeline
        print("导入 FDA 产品和应用数据...")
        return run_regulatory_pipeline(limit=limit)

    else:
        print(f"未知的管道: {pipeline_name}")
        return False


def verify_import():
    """验证数据导入结果"""
    print("\n=== 验证数据导入 ===")

    from neo4j import GraphDatabase

    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "pharmaKG2024!"

    driver = GraphDatabase.driver(uri, auth=(username, password))

    try:
        with driver.session() as session:
            # 统计各领域实体数量
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS entity_type, count(n) AS count
                ORDER BY count DESC
            """)

            print("\n实体统计:")
            total = 0
            for record in result:
                entity_type = record["entity_type"]
                count = record["count"]
                total += count
                print(f"  {entity_type}: {count}")

            print(f"\n总计: {total} 个节点")

            # 统计关系数量
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            relation_count = result.single()["count"]
            print(f"关系: {relation_count} 个")

            # 显示示例查询
            print("\n示例查询:")

            # R&D 领域示例
            result = session.run("MATCH (c:Compound) RETURN c.name AS name LIMIT 5")
            compounds = [record["name"] for record in result]
            if compounds:
                print(f"\n化合物示例: {', '.join(compounds[:5])}")

            # 临床领域示例
            result = session.run("MATCH (t:ClinicalTrial) RETURN t.nct_id AS nct_id LIMIT 5")
            trials = [record["nct_id"] for record in result]
            if trials:
                print(f"临床试验示例: {', '.join(trials[:5])}")

    finally:
        driver.close()

    return True


def main():
    parser = argparse.ArgumentParser(description="运行 ETL 测试导入")
    parser.add_argument("--pipeline", "-p",
                       choices=["rd", "clinical", "supply", "regulatory", "all"],
                       default="all",
                       help="选择要运行的 ETL 管道")
    parser.add_argument("--limit", "-l", type=int, default=10,
                       help="限制导入的数据量（默认: 10）")
    parser.add_argument("--verify", "-v", action="store_true",
                       help="验证导入结果")

    args = parser.parse_args()

    print("=" * 50)
    print("PharmaKG ETL 测试运行器")
    print("=" * 50)

    # 检查环境
    if not check_environment():
        print("\n环境检查失败，请先安装并启动 Neo4j")
        return 1

    # 运行 ETL 管道
    pipelines = []
    if args.pipeline == "all":
        pipelines = ["rd", "clinical", "supply", "regulatory"]
    else:
        pipelines = [args.pipeline]

    results = {}
    for pipeline in pipelines:
        try:
            result = run_etl_test(pipeline, limit=args.limit)
            results[pipeline] = "成功" if result else "失败"
        except Exception as e:
            print(f"✗ {pipeline} 管道运行失败: {e}")
            results[pipeline] = f"错误: {e}"

    # 验证结果
    if args.verify:
        verify_import()

    # 显示结果摘要
    print("\n" + "=" * 50)
    print("运行结果摘要")
    print("=" * 50)
    for pipeline, result in results.items():
        status = "✓" if result == "成功" else "✗"
        print(f"{status} {pipeline}: {result}")


if __name__ == "__main__":
    main()
