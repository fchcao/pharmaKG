#!/usr/bin/env python3
#===========================================================
# PharmaKG FDA Drugs@FDA API 处理器测试脚本
# Pharmaceutical Knowledge Graph - FDA Drugs@FDA API Processor Test Script
#===========================================================
# 版本: v1.0
# 描述: 测试 Drugs@FDA 处理器的各种功能
#===========================================================

import logging
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径 / Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from processors.drugsatfda_processor import (
    DrugsAtFDAProcessor,
    DrugsAtFDAExtractionConfig,
    ApprovalType,
    SubmissionType,
    SubmissionStatus,
    ReviewPriority,
    MarketingStatus
)


# 配置日志 / Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_basic_fetch():
    """测试基本数据获取 / Test basic data fetching"""
    print("\n" + "="*60)
    print("测试 1: 基本数据获取 / Test 1: Basic Data Fetching")
    print("="*60)

    config = {
        'extraction': {
            'max_applications': 5,
            'page_size': 5,
            'rate_limit_per_second': 1.0,
            'save_raw_response': False
        }
    }

    processor = DrugsAtFDAProcessor(config)

    # 获取少量数据 / Fetch small amount of data
    raw_data = processor.fetch_all_applications(max_applications=5)

    print(f"✓ 成功获取 {len(raw_data.get('results', []))} 个申请 / Successfully fetched {len(raw_data.get('results', []))} applications")

    # 显示第一个申请的信息 / Display first application info
    if raw_data.get('results'):
        first_app = raw_data['results'][0]
        print(f"\n第一个申请 / First application:")
        print(f"  申请号 / Application number: {first_app.get('application_number')}")
        print(f"  产品数量 / Product count: {len(first_app.get('products', []))}")
        print(f"  提交数量 / Submission count: {len(first_app.get('submissions', []))}")

    return raw_data


def test_transform_and_validate(raw_data):
    """测试数据转换和验证 / Test data transformation and validation"""
    print("\n" + "="*60)
    print("测试 2: 数据转换和验证 / Test 2: Data Transformation and Validation")
    print("="*60)

    config = {
        'extraction': {
            'map_unii_to_chembl': False,
            'map_to_clinical_trials': False
        }
    }

    processor = DrugsAtFDAProcessor(config)

    # 转换数据 / Transform data
    transformed_data = processor.transform(raw_data)

    # 验证数据 / Validate data
    is_valid = processor.validate(transformed_data)

    print(f"✓ 数据验证: {'通过' if is_valid else '失败'} / Data validation: {'Passed' if is_valid else 'Failed'}")

    entities = transformed_data.get('entities', {})
    relationships = transformed_data.get('relationships', [])

    print(f"\n实体统计 / Entity statistics:")
    for entity_type, entity_list in entities.items():
        print(f"  {entity_type}: {len(entity_list)}")

    print(f"\n关系数量 / Relationship count: {len(relationships)}")

    return transformed_data, is_valid


def test_query_by_brand_name():
    """测试按品牌名查询 / Test query by brand name"""
    print("\n" + "="*60)
    print("测试 3: 按品牌名查询 / Test 3: Query by Brand Name")
    print("="*60)

    config = {
        'extraction': {
            'max_applications': 3,
            'page_size': 3,
            'rate_limit_per_second': 1.0
        }
    }

    processor = DrugsAtFDAProcessor(config)

    # 查询 Lipitor / Query Lipitor
    raw_data = processor.fetch_by_brand_name("Lipitor", max_applications=3)

    print(f"✓ 查询 'Lipitor' 返回 {len(raw_data.get('results', []))} 个结果 / Query 'Lipitor' returned {len(raw_data.get('results', []))} results")

    if raw_data.get('results'):
        first_result = raw_data['results'][0]
        print(f"\n第一个结果 / First result:")
        print(f"  申请号 / Application number: {first_result.get('application_number')}")
        products = first_result.get('products', [])
        if products:
            print(f"  品牌名 / Brand name: {products[0].get('brand_name')}")
            print(f"  通用名 / Generic name: {products[0].get('generic_name')}")

    return raw_data


def test_query_by_application_number():
    """测试按申请号查询 / Test query by application number"""
    print("\n" + "="*60)
    print("测试 4: 按申请号查询 / Test 4: Query by Application Number")
    print("="*60)

    config = {
        'extraction': {
            'rate_limit_per_second': 1.0
        }
    }

    processor = DrugsAtFDAProcessor(config)

    # 查询 NDA020709 (Lipitor) / Query NDA020709 (Lipitor)
    application_number = "NDA020709"
    application_data = processor.fetch_by_application_number(application_number)

    if application_data:
        print(f"✓ 成功获取申请 {application_number} / Successfully fetched application {application_number}")
        print(f"\n申请详情 / Application details:")
        print(f"  申请号 / Application number: {application_data.get('application_number')}")
        print(f"  产品数量 / Product count: {len(application_data.get('products', []))}")
        print(f"  提交数量 / Submission count: {len(application_data.get('submissions', []))}")

        products = application_data.get('products', [])
        if products:
            print(f"\n第一个产品 / First product:")
            print(f"  品牌名 / Brand name: {products[0].get('brand_name')}")
            print(f"  通用名 / Generic name: {products[0].get('generic_name')}")
            print(f"  剂型 / Dosage form: {products[0].get('dosage_form')}")
            print(f"  途径 / Route: {products[0].get('route')}")
            print(f"  营销状态 / Marketing status: {products[0].get('marketing_status')}")
    else:
        print(f"✗ 未找到申请 {application_number} / Application {application_number} not found")

    return application_data


def test_cross_domain_mapping():
    """测试交叉域映射 / Test cross-domain mapping"""
    print("\n" + "="*60)
    print("测试 5: 交叉域映射 / Test 5: Cross-Domain Mapping")
    print("="*60)

    config = {
        'extraction': {
            'max_applications': 3,
            'page_size': 3,
            'rate_limit_per_second': 1.0,
            'map_unii_to_chembl': True,
            'map_to_clinical_trials': False,  # 先禁用临床试验映射 / Disable clinical trials mapping first
            'use_mychem_api': True
        }
    }

    processor = DrugsAtFDAProcessor(config)

    # 获取数据 / Fetch data
    raw_data = processor.fetch_all_applications(max_applications=3)

    # 转换数据 / Transform data
    transformed_data = processor.transform(raw_data)

    # 检查交叉域映射 / Check cross-domain mapping
    relationships = transformed_data.get('relationships', [])
    cross_domain_rels = [r for r in relationships if r.get('source') == 'Drugs@FDA-CrossDomain']

    print(f"✓ 交叉域关系数量 / Cross-domain relationship count: {len(cross_domain_rels)}")

    if cross_domain_rels:
        print(f"\n交叉域关系示例 / Cross-domain relationship example:")
        for rel in cross_domain_rels[:3]:
            print(f"  {rel.get('relationship_type')}: {rel.get('source_entity_id')} → {rel.get('target_entity_id')}")

    return transformed_data


def test_save_results():
    """测试结果保存 / Test result saving"""
    print("\n" + "="*60)
    print("测试 6: 结果保存 / Test 6: Result Saving")
    print("="*60)

    config = {
        'extraction': {
            'max_applications': 3,
            'page_size': 3,
            'rate_limit_per_second': 1.0,
            'map_unii_to_chembl': False,
            'map_to_clinical_trials': False
        }
    }

    processor = DrugsAtFDAProcessor(config)

    # 获取数据 / Fetch data
    raw_data = processor.fetch_all_applications(max_applications=3)

    # 转换数据 / Transform data
    transformed_data = processor.transform(raw_data)

    # 保存结果 / Save results
    entities = transformed_data.get('entities', {})
    relationships = transformed_data.get('relationships', [])

    # 使用临时目录 / Use temporary directory
    output_dir = Path("/tmp/drugsatfda_test_output")

    output_path = processor.save_results(entities, relationships, str(output_dir))

    print(f"✓ 结果已保存到 / Results saved to: {output_path}")

    # 验证文件创建 / Verify file creation
    output_dir_path = Path(output_dir)
    if output_dir_path.exists():
        files = list(output_dir_path.glob("*.json"))
        print(f"✓ 创建了 {len(files)} 个文件 / Created {len(files)} files")
        for file in files:
            print(f"  - {file.name}")

    return output_path


def test_enum_types():
    """测试枚举类型 / Test enum types"""
    print("\n" + "="*60)
    print("测试 7: 枚举类型 / Test 7: Enum Types")
    print("="*60)

    # 测试 ApprovalType / Test ApprovalType
    print("\nApprovalType:")
    for approval_type in ApprovalType:
        print(f"  - {approval_type.value}: {approval_type.name}")

    # 测试 SubmissionType / Test SubmissionType
    print("\nSubmissionType:")
    for submission_type in SubmissionType:
        print(f"  - {submission_type.value}: {submission_type.name}")

    # 测试 SubmissionStatus / Test SubmissionStatus
    print("\nSubmissionStatus:")
    for status in SubmissionStatus:
        print(f"  - {status.value}: {status.name}")

    # 测试 ReviewPriority / Test ReviewPriority
    print("\nReviewPriority:")
    for priority in ReviewPriority:
        print(f"  - {priority.value}: {priority.name}")

    # 测试 MarketingStatus / Test MarketingStatus
    print("\nMarketingStatus:")
    for status in MarketingStatus:
        print(f"  - {status.value}: {status.name}")

    print("✓ 所有枚举类型测试通过 / All enum type tests passed")


def test_deduplication():
    """测试去重功能 / Test deduplication"""
    print("\n" + "="*60)
    print("测试 8: 去重功能 / Test 8: Deduplication")
    print("="*60)

    config = {
        'extraction': {
            'max_applications': 5,
            'page_size': 5,
            'rate_limit_per_second': 1.0,
            'deduplicate_by_application_number': True
        }
    }

    processor = DrugsAtFDAProcessor(config)

    # 获取数据 / Fetch data
    raw_data = processor.fetch_all_applications(max_applications=5)

    # 转换数据 / Transform data
    transformed_data = processor.transform(raw_data)

    # 检查去重统计 / Check deduplication statistics
    print(f"✓ 去重申请数量 / Deduplicated applications: {processor.stats.applications_deduplicated}")

    return transformed_data


def test_error_handling():
    """测试错误处理 / Test error handling"""
    print("\n" + "="*60)
    print("测试 9: 错误处理 / Test 9: Error Handling")
    print("="*60)

    config = {
        'extraction': {
            'rate_limit_per_second': 1.0,
            'max_retries': 2
        }
    }

    processor = DrugsAtFDAProcessor(config)

    # 测试无效申请号 / Test invalid application number
    print("测试无效申请号 / Testing invalid application number:")
    result = processor.fetch_by_application_number("INVALID123")
    print(f"✓ 无效申请号返回: {result} (应为 None) / Invalid application number returned: {result} (should be None)")

    # 测试空查询 / Test empty query
    print("\n测试空品牌名查询 / Testing empty brand name query:")
    config2 = {
        'extraction': {
            'query_brand_name': '',
            'rate_limit_per_second': 1.0
        }
    }
    processor2 = DrugsAtFDAProcessor(config2)
    raw_data = processor2.fetch_all_applications(max_applications=1)
    print(f"✓ 空查询返回 {len(raw_data.get('results', []))} 个结果 / Empty query returned {len(raw_data.get('results', []))} results")

    print("✓ 错误处理测试完成 / Error handling tests completed")


def run_all_tests():
    """运行所有测试 / Run all tests"""
    print("\n" + "="*60)
    print("FDA Drugs@FDA 处理器测试套件 / FDA Drugs@FDA Processor Test Suite")
    print("="*60)
    print(f"开始时间 / Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    start_time = datetime.now()

    try:
        # 运行测试 / Run tests
        test_basic_fetch()

        raw_data = test_basic_fetch()
        test_transform_and_validate(raw_data)

        test_query_by_brand_name()
        test_query_by_application_number()
        test_cross_domain_mapping()
        test_save_results()
        test_enum_types()
        test_deduplication()
        test_error_handling()

        # 计算总时间 / Calculate total time
        elapsed_time = (datetime.now() - start_time).total_seconds()

        print("\n" + "="*60)
        print("测试总结 / Test Summary")
        print("="*60)
        print(f"✓ 所有测试完成 / All tests completed")
        print(f"总耗时 / Total time: {elapsed_time:.2f} 秒 / seconds")
        print(f"结束时间 / End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return 0

    except Exception as e:
        print(f"\n✗ 测试失败 / Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(run_all_tests())
