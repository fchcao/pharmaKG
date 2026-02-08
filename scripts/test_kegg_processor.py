#!/usr/bin/env python3
#===========================================================
# KEGG Processor 测试脚本
# Pharmaceutical Knowledge Graph - KEGG Processor Test
#===========================================================
# 版本: v1.0
# 描述: 测试 KEGG 处理器的基本功能
#===========================================================

import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from processors.kegg_processor import KEGGProcessor, OrganismCode


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_basic_setup():
    """测试基本初始化"""
    print("\n" + "="*60)
    print("测试 1: 基本初始化")
    print("="*60)

    try:
        config = {
            'extraction': {
                'batch_size': 10,
                'rate_limit': 5.0,
                'cache_enabled': True
            }
        }

        processor = KEGGProcessor(config)

        print(f"✓ 处理器初始化成功")
        print(f"  - 处理器名称: {processor.PROCESSOR_NAME}")
        print(f"  - 批处理大小: {processor.extraction_config.batch_size}")
        print(f"  - 速率限制: {processor.extraction_config.rate_limit} 请求/秒")
        print(f"  - 缓存启用: {processor.extraction_config.cache_enabled}")

        return processor

    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        return None


def test_list_pathways(processor: KEGGProcessor):
    """测试列出通路"""
    print("\n" + "="*60)
    print("测试 2: 列出人类通路（前10个）")
    print("="*60)

    try:
        pathway_ids = processor.list_pathways(organism=OrganismCode.HUMAN)

        # 只显示前10个
        display_count = min(10, len(pathway_ids))

        print(f"✓ 找到 {len(pathway_ids)} 个人类通路")
        print(f"  前 {display_count} 个通路:")

        for i, pathway_id in enumerate(pathway_ids[:display_count], 1):
            print(f"    {i}. {pathway_id}")

        return pathway_ids[:5]  # 返回前5个用于后续测试

    except Exception as e:
        print(f"✗ 列出通路失败: {e}")
        return []


def test_fetch_single_pathway(processor: KEGGProcessor, pathway_ids: list):
    """测试获取单个通路"""
    print("\n" + "="*60)
    print("测试 3: 获取通路详情")
    print("="*60)

    if not pathway_ids:
        print("⊗ 跳过（没有可用的通路 ID）")
        return None

    try:
        pathway_id = pathway_ids[0]
        print(f"获取通路: {pathway_id}")

        pathway_data = processor._fetch_single_pathway(pathway_id)

        if pathway_data:
            print(f"✓ 成功获取通路数据")
            print(f"  - 通路 ID: {pathway_data.get('pathway_id')}")
            print(f"  - 名称: {pathway_data.get('name') or pathway_data.get('title')}")
            print(f"  - 描述: {pathway_data.get('description', 'N/A')[:100]}...")
            print(f"  - 基因数量: {len(pathway_data.get('genes', []))}")
            print(f"  - 化合物数量: {len(pathway_data.get('compounds', []))}")

            return pathway_data
        else:
            print(f"✗ 获取通路数据失败")

    except Exception as e:
        print(f"✗ 获取通路失败: {e}")
        return None


def test_transform_pathway(processor: KEGGProcessor, pathway_data: dict):
    """测试转换通路"""
    print("\n" + "="*60)
    print("测试 4: 转换通路数据为知识图谱实体")
    print("="*60)

    if not pathway_data:
        print("⊗ 跳过（没有可用的通路数据）")
        return None

    try:
        pathway_entity = processor._transform_pathway(pathway_data)

        if pathway_entity:
            print(f"✓ 成功转换通路实体")
            print(f"  - 实体类型: {pathway_entity.get('entity_type')}")
            print(f"  - 主 ID: {pathway_entity.get('primary_id')}")
            print(f"  - 名称: {pathway_entity.get('properties', {}).get('name')}")
            print(f"  - 生物体: {pathway_entity.get('properties', {}).get('organism')}")
            print(f"  - 通路类型: {pathway_entity.get('properties', {}).get('pathway_type')}")
            print(f"  - 通路分类: {pathway_entity.get('properties', {}).get('pathway_category')}")

            return pathway_entity
        else:
            print(f"✗ 转换通路实体失败")

    except Exception as e:
        print(f"✗ 转换通路失败: {e}")
        return None


def test_create_relationships(processor: KEGGProcessor, pathway_data: dict, pathway_entity: dict):
    """测试创建关系"""
    print("\n" + "="*60)
    print("测试 5: 创建通路关系")
    print("="*60)

    if not pathway_data or not pathway_entity:
        print("⊗ 跳过（没有可用的数据）")
        return

    try:
        relationships = processor._create_pathway_relationships(pathway_data, pathway_entity)

        print(f"✓ 成功创建 {len(relationships)} 个关系")

        # 按类型分组
        rel_types = {}
        for rel in relationships:
            rel_type = rel.get('relationship_type')
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1

        print(f"  关系类型分布:")
        for rel_type, count in rel_types.items():
            print(f"    - {rel_type}: {count}")

        # 显示前3个关系
        print(f"  前 3 个关系:")
        for i, rel in enumerate(relationships[:3], 1):
            print(f"    {i}. {rel.get('relationship_type')}: "
                  f"{rel.get('source_entity_id')} → {rel.get('target_entity_id')}")

    except Exception as e:
        print(f"✗ 创建关系失败: {e}")


def test_uniprot_mapping(processor: KEGGProcessor):
    """测试 KEGG 基因到 UniProt 映射"""
    print("\n" + "="*60)
    print("测试 6: KEGG 基因到 UniProt 映射")
    print("="*60)

    try:
        # 测试人类基因映射
        test_gene_ids = ['10458', '673', '7157']  # 一些人类基因 ID

        print(f"测试映射 {len(test_gene_ids)} 个基因:")

        for gene_id in test_gene_ids:
            uniprot_id = processor._map_kegg_gene_to_uniprot(gene_id, OrganismCode.HUMAN)
            status = "✓" if uniprot_id else "✗"
            print(f"  {status} {gene_id} → {uniprot_id or '未找到'}")

        print(f"✓ 映射测试完成")

    except Exception as e:
        print(f"✗ 映射测试失败: {e}")


def test_batch_fetch(processor: KEGGProcessor, pathway_ids: list):
    """测试批量获取"""
    print("\n" + "="*60)
    print("测试 7: 批量获取通路数据")
    print("="*60)

    if not pathway_ids:
        print("⊗ 跳过（没有可用的通路 ID）")
        return

    try:
        batch_size = 3
        test_ids = pathway_ids[:batch_size]

        print(f"批量获取 {len(test_ids)} 个通路:")

        batch_data = processor._fetch_batch_pathway_data(test_ids)

        print(f"✓ 成功获取 {len(batch_data)} 个通路")

        for i, pathway_data in enumerate(batch_data, 1):
            pathway_id = pathway_data.get('pathway_id')
            name = pathway_data.get('name') or pathway_data.get('title', 'N/A')
            print(f"  {i}. {pathway_id}: {name[:50]}...")

    except Exception as e:
        print(f"✗ 批量获取失败: {e}")


def test_caching(processor: KEGGProcessor, pathway_ids: list):
    """测试缓存功能"""
    print("\n" + "="*60)
    print("测试 8: 缓存功能")
    print("="*60)

    if not pathway_ids:
        print("⊗ 跳过（没有可用的通路 ID）")
        return

    try:
        pathway_id = pathway_ids[0]

        # 第一次获取（应该从 API）
        print("第一次获取（应该从 API）:")
        processor.stats.cache_hits = 0
        data1 = processor._fetch_single_pathway(pathway_id)
        api_requests_1 = processor.stats.api_requests_made
        cache_hits_1 = processor.stats.cache_hits

        # 第二次获取（应该从缓存）
        print("第二次获取（应该从缓存）:")
        data2 = processor._fetch_single_pathway(pathway_id)
        api_requests_2 = processor.stats.api_requests_made
        cache_hits_2 = processor.stats.cache_hits

        if data1 and data2:
            print(f"✓ 缓存功能正常")
            print(f"  - 第一次请求后: {api_requests_1} API 请求, {cache_hits_1} 缓存命中")
            print(f"  - 第二次请求后: {api_requests_2} API 请求, {cache_hits_2} 缓存命中")
            print(f"  - 新增 API 请求: {api_requests_2 - api_requests_1}")
            print(f"  - 新增缓存命中: {cache_hits_2 - cache_hits_1}")
        else:
            print(f"✗ 缓存测试失败")

    except Exception as e:
        print(f"✗ 缓存测试失败: {e}")


def test_save_results(processor: KEGGProcessor, pathway_data: dict):
    """测试保存结果"""
    print("\n" + "="*60)
    print("测试 9: 保存处理结果")
    print("="*60)

    if not pathway_data:
        print("⊗ 跳过（没有可用的通路数据）")
        return

    try:
        # 创建测试数据
        from processors.kegg_processor import ExtractionStats

        test_entities = [
            {
                'primary_id': 'test_pathway_1',
                'entity_type': 'rd:Pathway',
                'identifiers': {'KEGG': 'path:test123'},
                'properties': {'name': 'Test Pathway'}
            },
            {
                'primary_id': 'test_target_1',
                'entity_type': 'rd:Target',
                'identifiers': {'GeneSymbol': 'TEST1'},
                'properties': {'name': 'Test Target'}
            }
        ]

        test_relationships = [
            {
                'relationship_type': 'PARTICIPATES_IN',
                'source_entity_id': 'test_target_1',
                'target_entity_id': 'test_pathway_1',
                'properties': {'role': 'test'}
            }
        ]

        # 保存到测试目录
        test_output = processor.project_root / "data" / "processed" / "documents" / "kegg"
        test_output.mkdir(parents=True, exist_ok=True)

        output_path = processor._save_kegg_results(
            test_entities,
            test_relationships,
            str(test_output)
        )

        print(f"✓ 成功保存结果")
        print(f"  - 输出路径: {output_path}")

        # 检查文件是否存在
        if output_path and Path(output_path).exists():
            print(f"  - 摘要文件已创建")
            # 读取并显示摘要
            import json
            with open(output_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)
            print(f"  - 实体数量: {summary.get('total_entities', 0)}")
            print(f"  - 关系数量: {summary.get('total_relationships', 0)}")
        else:
            print(f"  ✗ 摘要文件未找到")

    except Exception as e:
        print(f"✗ 保存结果失败: {e}")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print(" "*15 + "KEGG Processor 测试套件")
    print("="*70)

    # 测试 1: 基本初始化
    processor = test_basic_setup()
    if not processor:
        print("\n✗ 测试失败：无法初始化处理器")
        return

    # 测试 2: 列出通路
    pathway_ids = test_list_pathways(processor)

    # 测试 3: 获取单个通路
    pathway_data = test_fetch_single_pathway(processor, pathway_ids)

    # 测试 4: 转换通路
    pathway_entity = test_transform_pathway(processor, pathway_data)

    # 测试 5: 创建关系
    test_create_relationships(processor, pathway_data, pathway_entity)

    # 测试 6: UniProt 映射
    test_uniprot_mapping(processor)

    # 测试 7: 批量获取
    test_batch_fetch(processor, pathway_ids)

    # 测试 8: 缓存
    test_caching(processor, pathway_ids)

    # 测试 9: 保存结果
    test_save_results(processor, pathway_data)

    # 最终清理
    if processor.cache_conn:
        processor.cache_conn.close()

    print("\n" + "="*70)
    print(" "*20 + "测试完成")
    print("="*70)
    print("\n注意: 这些测试需要访问 KEGG REST API (http://rest.kegg.jp)")
    print("如果 API 不可用或受速率限制，某些测试可能会失败。")
    print("KEGG API 仅供学术使用，请确保遵守使用条款。")


if __name__ == '__main__':
    run_all_tests()
