#!/usr/bin/env python3
#===========================================================
# 测试搜索服务功能
# Test Search Service Functionality
#===========================================================
# 版本: v1.0
# 创建日期: 2025-02-08
#===========================================================

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.search_service import SearchService
from api.database import get_db
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_search_service():
    """测试搜索服务功能"""

    print("=" * 60)
    print("测试搜索服务功能 / Testing Search Service")
    print("=" * 60)

    # 初始化服务
    service = SearchService()
    db = get_db()

    # 测试1: 验证数据库连接
    print("\n[测试1] 验证数据库连接 / Verify Database Connection")
    try:
        if db.verify_connection():
            print("✓ 数据库连接成功 / Database connection successful")
        else:
            print("✗ 数据库连接失败 / Database connection failed")
            return
    except Exception as e:
        print(f"✗ 数据库连接错误 / Connection error: {str(e)}")
        return

    # 测试2: 列出现有索引
    print("\n[测试2] 列出现有全文索引 / List Existing Full-text Indexes")
    try:
        indexes = service.list_fulltext_indexes()
        print(f"找到 {len(indexes)} 个索引 / Found {len(indexes)} indexes")
        for idx in indexes:
            print(f"  - {idx.get('name')}: {idx.get('labelsOrTypes')} ({idx.get('properties')})")
    except Exception as e:
        print(f"✗ 列出索引失败 / Failed to list indexes: {str(e)}")

    # 测试3: 创建全文索引
    print("\n[测试3] 创建全文搜索索引 / Create Full-text Indexes")
    try:
        result = service.create_fulltext_indexes()
        if result.get("success"):
            print(f"✓ 成功创建 {len(result.get('indexes_created', []))} 个索引")
            for idx_name in result.get("indexes_created", []):
                print(f"  - {idx_name}")
        else:
            print("✗ 索引创建失败")
        if result.get("errors"):
            print("错误信息 / Errors:")
            for error in result.get("errors", []):
                print(f"  - {error}")
    except Exception as e:
        print(f"✗ 创建索引失败 / Failed to create indexes: {str(e)}")

    # 测试4: 全文搜索
    print("\n[测试4] 全文搜索测试 / Full-text Search Test")
    try:
        result = service.fulltext_search(
            query_text="aspirin",
            entity_types=None,
            limit=5
        )
        print(f"✓ 搜索完成，找到 {result.get('total', 0)} 个结果")
        print(f"  返回 {result.get('returned', 0)} 个结果")
        for item in result.get("results", [])[:3]:
            print(f"  - {item.get('entity_type')}: {item.get('name')} (score: {item.get('score', 0):.2f})")
    except Exception as e:
        print(f"✗ 全文搜索失败 / Full-text search failed: {str(e)}")

    # 测试5: 模糊搜索
    print("\n[测试5] 模糊搜索测试 / Fuzzy Search Test")
    try:
        result = service.fuzzy_search(
            query_text="asprin",  # 拼写错误
            entity_type="Compound",
            search_field="name",
            max_distance=2,
            limit=5
        )
        print(f"✓ 模糊搜索完成，找到 {result.get('total', 0)} 个结果")
        print(f"  方法: {result.get('method', 'UNKNOWN')}")
        for item in result.get("results", [])[:3]:
            print(f"  - {item.get('name')} (相似度: {item.get('similarity', 0):.2f})")
    except Exception as e:
        print(f"✗ 模糊搜索失败 / Fuzzy search failed: {str(e)}")

    # 测试6: 搜索建议
    print("\n[测试6] 搜索建议测试 / Search Suggestions Test")
    try:
        result = service.get_suggestions(
            prefix="asp",
            entity_type="Compound",
            search_field="name",
            limit=5
        )
        print(f"✓ 获取 {result.get('total', 0)} 个建议")
        for suggestion in result.get("suggestions", []):
            print(f"  - {suggestion.get('text')} (频率: {suggestion.get('frequency', 0)})")
    except Exception as e:
        print(f"✗ 搜索建议失败 / Search suggestions failed: {str(e)}")

    # 测试7: 聚合搜索
    print("\n[测试7] 聚合搜索测试 / Aggregate Search Test")
    try:
        result = service.aggregate_search(
            query_text="cancer",
            group_by="entity_type",
            limit=10
        )
        print(f"✓ 聚合搜索完成，{result.get('total_groups', 0)} 个分组")
        for group in result.get("groups", [])[:3]:
            group_label = group.get('entity_type') or group.get('domain', 'Unknown')
            print(f"  - {group_label}: {group.get('count', 0)} 个结果")
    except Exception as e:
        print(f"✗ 聚合搜索失败 / Aggregate search failed: {str(e)}")

    # 测试8: 多实体搜索
    print("\n[测试8] 多实体搜索测试 / Multi-entity Search Test")
    try:
        entity_config = [
            {"entity_type": "Compound", "search_field": "name"},
            {"entity_type": "Target", "search_field": "name"}
        ]
        result = service.multi_entity_search(
            query_text="kinase",
            entity_config=entity_config,
            limit_per_entity=3
        )
        print(f"✓ 多实体搜索完成，{result.get('total_entities', 0)} 个实体类型，{result.get('total_results', 0)} 个结果")
        for entity_type, data in result.get("results", {}).items():
            print(f"  - {entity_type}: {data.get('count', 0)} 个结果")
    except Exception as e:
        print(f"✗ 多实体搜索失败 / Multi-entity search failed: {str(e)}")

    print("\n" + "=" * 60)
    print("测试完成 / Testing Complete")
    print("=" * 60)


if __name__ == "__main__":
    test_search_service()
