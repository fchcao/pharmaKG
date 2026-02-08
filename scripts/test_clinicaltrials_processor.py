#!/usr/bin/env python3
#===========================================================
# ClinicalTrials.gov 处理器测试脚本
# Pharmaceutical Knowledge Graph - ClinicalTrials.gov Processor Test
#===========================================================
# 版本: v1.0
# 描述: 测试 ClinicalTrials.gov API v2 处理器功能
#===========================================================

import sys
import logging
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from processors.clinicaltrials_processor import (
    ClinicalTrialsProcessor,
    ClinicalTrialsExtractionConfig,
    StudyPhase,
    StudyStatus,
    ProcessingMode
)


def test_processor_initialization():
    """测试处理器初始化"""
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*60)
    logger.info("测试 1: 处理器初始化 / Test 1: Processor Initialization")
    logger.info("="*60)

    try:
        # 创建默认配置
        config = {}
        processor = ClinicalTrialsProcessor(config)

        logger.info(f"处理器名称: {processor.PROCESSOR_NAME}")
        logger.info(f"输出子目录: {processor.OUTPUT_SUBDIR}")
        logger.info(f"API 基础 URL: {processor.extraction_config.api_base_url}")
        logger.info(f"速率限制: {processor.extraction_config.rate_limit_per_second} 请求/秒")
        logger.info(f"页面大小: {processor.extraction_config.page_size}")

        assert processor.PROCESSOR_NAME == "ClinicalTrialsProcessor"
        assert processor.OUTPUT_SUBDIR == "clinicaltrials"
        assert processor.extraction_config.rate_limit_per_second == 2.0

        logger.info("✓ 处理器初始化成功")
        return True

    except Exception as e:
        logger.error(f"✗ 处理器初始化失败: {e}")
        return False


def test_custom_config():
    """测试自定义配置"""
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*60)
    logger.info("测试 2: 自定义配置 / Test 2: Custom Configuration")
    logger.info("="*60)

    try:
        # 创建自定义配置
        config = {
            'extraction': {
                'page_size': 50,
                'rate_limit_per_second': 1.0,
                'max_studies': 100,
                'max_retries': 5,
                'save_raw_response': False,
                'map_to_chembl': False,
                'map_to_mondo': False
            }
        }

        processor = ClinicalTrialsProcessor(config)

        logger.info(f"页面大小: {processor.extraction_config.page_size}")
        logger.info(f"速率限制: {processor.extraction_config.rate_limit_per_second} 请求/秒")
        logger.info(f"最大研究数: {processor.extraction_config.max_studies}")
        logger.info(f"最大重试次数: {processor.extraction_config.max_retries}")
        logger.info(f"映射到 ChEMBL: {processor.extraction_config.map_to_chembl}")
        logger.info(f"映射到 MONDO: {processor.extraction_config.map_to_mondo}")

        assert processor.extraction_config.page_size == 50
        assert processor.extraction_config.rate_limit_per_second == 1.0
        assert processor.extraction_config.max_studies == 100
        assert processor.extraction_config.max_retries == 5
        assert processor.extraction_config.map_to_chembl == False
        assert processor.extraction_config.map_to_mondo == False

        logger.info("✓ 自定义配置成功")
        return True

    except Exception as e:
        logger.error(f"✗ 自定义配置失败: {e}")
        return False


def test_fetch_single_study():
    """测试获取单个研究"""
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*60)
    logger.info("测试 3: 获取单个研究 / Test 3: Fetch Single Study")
    logger.info("="*60)

    try:
        # 创建处理器
        config = {
            'extraction': {
                'rate_limit_per_second': 2.0,
                'save_raw_response': False
            }
        }

        processor = ClinicalTrialsProcessor(config)

        # 获取一个已知的研究（使用一个著名的 NCT ID）
        nct_id = "NCT00001234"  # 一个示例 NCT ID

        logger.info(f"正在获取研究: {nct_id}")
        study_data = processor.fetch_by_nct_id(nct_id)

        if study_data:
            logger.info(f"✓ 成功获取研究数据")
            logger.info(f"  研究标识 / Study ID: {study_data.get('protocolSection', {}).get('identificationModule', {}).get('nctId')}")
            logger.info(f"  简短标题 / Brief Title: {study_data.get('protocolSection', {}).get('identificationModule', {}).get('briefTitle', 'N/A')}")
            logger.info(f"  研究状态 / Status: {study_data.get('protocolSection', {}).get('statusModule', {}).get('overallStatus', 'N/A')}")
            logger.info(f"  研究阶段 / Phase: {study_data.get('protocolSection', {}).get('designModule', {}).get('phase', 'N/A')}")

            return True
        else:
            logger.warning(f"✗ 无法获取研究 {nct_id}（可能不存在或 API 不可用）")
            return False

    except Exception as e:
        logger.error(f"✗ 获取单个研究失败: {e}")
        return False


def test_fetch_by_query():
    """测试按查询获取研究"""
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*60)
    logger.info("测试 4: 按查询获取研究 / Test 4: Fetch by Query")
    logger.info("="*60)

    try:
        # 创建处理器（限制获取数量以加快测试）
        config = {
            'extraction': {
                'page_size': 10,
                'rate_limit_per_second': 2.0,
                'max_studies': 10,  # 限制获取数量
                'max_pages': 1,     # 只获取一页
                'save_raw_response': False
            }
        }

        processor = ClinicalTrialsProcessor(config)

        # 查询糖尿病相关研究
        query_term = "diabetes"

        logger.info(f"正在查询: {query_term}")
        raw_data = processor.fetch_by_query(query_term)

        if raw_data and 'studies' in raw_data:
            studies = raw_data['studies']
            logger.info(f"✓ 成功获取 {len(studies)} 个研究")

            # 显示前几个研究的基本信息
            for i, study in enumerate(studies[:3]):
                protocol = study.get('protocolSection', {})
                identification = protocol.get('identificationModule', {})
                status = protocol.get('statusModule', {})

                logger.info(f"\n  研究 {i+1}:")
                logger.info(f"    NCT ID: {identification.get('nctId', 'N/A')}")
                logger.info(f"    标题: {identification.get('briefTitle', 'N/A')[:80]}")
                logger.info(f"    状态: {status.get('overallStatus', 'N/A')}")

            return True
        else:
            logger.warning(f"✗ 无法获取研究数据")
            return False

    except Exception as e:
        logger.error(f"✗ 按查询获取研究失败: {e}")
        return False


def test_transform_study():
    """测试研究数据转换"""
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*60)
    logger.info("测试 5: 研究数据转换 / Test 5: Transform Study Data")
    logger.info("="*60)

    try:
        # 创建处理器
        config = {
            'extraction': {
                'rate_limit_per_second': 2.0,
                'save_raw_response': False,
                'map_to_chembl': False,  # 禁用交叉域映射以加快测试
                'map_to_mondo': False
            }
        }

        processor = ClinicalTrialsProcessor(config)

        # 创建一个模拟的研究数据
        mock_study = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCTTEST001",
                    "briefTitle": "Test Study for Diabetes Treatment",
                    "officialTitle": "A Randomized Trial of Test Drug for Diabetes",
                    "orgStudyId": "TEST-001"
                },
                "statusModule": {
                    "overallStatus": "Recruiting",
                    "startDateStruct": {"date": "2024-01-01"},
                    "primaryCompletionDateStruct": {"date": "2025-12-31"}
                },
                "designModule": {
                    "phase": "Phase 2",
                    "studyType": "Interventional",
                    "enrollmentInfo": {"count": 100}
                },
                "armsInterventionsModule": {
                    "interventions": [
                        {
                            "type": "Drug",
                            "name": "Test Drug",
                            "description": "A test medication"
                        }
                    ]
                },
                "conditionsModule": {
                    "conditions": [
                        {
                            "name": "Diabetes",
                            "meshTerms": ["Diabetes Mellitus"]
                        }
                    ]
                },
                "eligibilityModule": {
                    "eligibilityCriteria": "Inclusion: Age 18-80\nExclusion: Pregnancy"
                },
                "contactsLocationsModule": {
                    "locations": [
                        {
                            "facility": {"name": "Test Hospital"},
                            "city": "Boston",
                            "state": "Massachusetts",
                            "country": "United States"
                        }
                    ]
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {
                        "name": "Test Pharma Inc",
                        "agencyClass": "Industry"
                    },
                    "responsibleParty": {
                        "name": "Dr. John Smith"
                    }
                },
                "outcomesModule": {
                    "primaryOutcomes": [
                        {
                            "measure": "Change in HbA1c",
                            "timeFrame": "6 months"
                        }
                    ]
                }
            }
        }

        # 转换研究数据
        entities, relationships = processor._transform_study(mock_study)

        logger.info(f"✓ 转换成功")
        logger.info(f"  实体数量 / Entities: {len(entities)}")
        logger.info(f"  关系数量 / Relationships: {len(relationships)}")

        # 统计实体类型
        entity_types = {}
        for entity in entities:
            entity_type = entity.get('entity_type', 'Unknown')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

        logger.info(f"\n  实体类型统计 / Entity Types:")
        for entity_type, count in entity_types.items():
            logger.info(f"    {entity_type}: {count}")

        # 统计关系类型
        rel_types = {}
        for rel in relationships:
            rel_type = rel.get('relationship_type', 'Unknown')
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1

        logger.info(f"\n  关系类型统计 / Relationship Types:")
        for rel_type, count in rel_types.items():
            logger.info(f"    {rel_type}: {count}")

        return True

    except Exception as e:
        logger.error(f"✗ 研究数据转换失败: {e}", exc_info=True)
        return False


def test_transform_and_validate():
    """测试完整的转换和验证流程"""
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*60)
    logger.info("测试 6: 转换和验证流程 / Test 6: Transform and Validate")
    logger.info("="*60)

    try:
        # 创建处理器
        config = {
            'extraction': {
                'save_raw_response': False,
                'map_to_chembl': False,
                'map_to_mondo': False
            }
        }

        processor = ClinicalTrialsProcessor(config)

        # 创建模拟数据
        raw_data = {
            'studies': [
                {
                    "protocolSection": {
                        "identificationModule": {
                            "nctId": "NCTTEST002",
                            "briefTitle": "Another Test Study"
                        },
                        "statusModule": {"overallStatus": "Completed"},
                        "designModule": {
                            "phase": "Phase 3",
                            "studyType": "Interventional",
                            "enrollmentInfo": {"count": 200}
                        },
                        "armsInterventionsModule": {"interventions": []},
                        "conditionsModule": {"conditions": []},
                        "eligibilityModule": {},
                        "contactsLocationsModule": {"locations": []},
                        "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Test Sponsor"}},
                        "outcomesModule": {"primaryOutcomes": [], "secondaryOutcomes": []}
                    }
                }
            ]
        }

        # 转换数据
        transformed_data = processor.transform(raw_data)

        # 验证数据
        is_valid = processor.validate(transformed_data)

        if is_valid:
            logger.info("✓ 数据验证通过")
            logger.info(f"  实体总数: {sum(len(v) for v in transformed_data['entities'].values())}")
            logger.info(f"  关系总数: {len(transformed_data['relationships'])}")
            return True
        else:
            logger.warning("✗ 数据验证失败")
            return False

    except Exception as e:
        logger.error(f"✗ 转换和验证流程失败: {e}")
        return False


def test_save_results():
    """测试保存结果"""
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*60)
    logger.info("测试 7: 保存结果 / Test 7: Save Results")
    logger.info("="*60)

    try:
        # 创建处理器
        config = {
            'extraction': {
                'save_raw_response': False,
                'map_to_chembl': False,
                'map_to_mondo': False
            }
        }

        processor = ClinicalTrialsProcessor(config)

        # 创建模拟数据
        entities = {
            'clinical:ClinicalTrial': [
                {
                    'primary_id': 'ClinicalTrial-NCTTEST003',
                    'identifiers': {'NCT': 'NCTTEST003'},
                    'properties': {'nct_id': 'NCTTEST003', 'brief_title': 'Test Study'},
                    'entity_type': 'clinical:ClinicalTrial'
                }
            ],
            'clinical:Intervention': []
        }

        relationships = [
            {
                'relationship_type': 'TESTS_INTERVENTION',
                'source_entity_id': 'ClinicalTrial-NCTTEST003',
                'target_entity_id': 'Intervention-test',
                'properties': {},
                'source': 'Test'
            }
        ]

        # 保存结果
        output_dir = processor.data_root / "processed" / "documents" / "clinicaltrials" / "test"
        output_path = processor.save_results(entities, relationships, str(output_dir))

        logger.info(f"✓ 结果已保存到: {output_path}")

        # 验证文件是否存在
        if output_path.exists():
            logger.info(f"✓ 摘要文件存在")

            # 读取并显示摘要
            with open(output_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)

            logger.info(f"  处理器: {summary.get('processor')}")
            logger.info(f"  实体总数: {summary.get('total_entities')}")
            logger.info(f"  关系总数: {summary.get('total_relationships')}")

            return True
        else:
            logger.warning(f"✗ 摘要文件不存在")
            return False

    except Exception as e:
        logger.error(f"✗ 保存结果失败: {e}")
        return False


def test_enums():
    """测试枚举类型"""
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*60)
    logger.info("测试 8: 枚举类型 / Test 8: Enum Types")
    logger.info("="*60)

    try:
        # 测试研究阶段枚举
        logger.info("研究阶段 / Study Phases:")
        for phase in StudyPhase:
            logger.info(f"  - {phase.name}: {phase.value}")

        # 测试研究状态枚举
        logger.info("\n研究状态 / Study Statuses:")
        for status in StudyStatus:
            logger.info(f"  - {status.name}: {status.value}")

        # 测试处理模式枚举
        logger.info("\n处理模式 / Processing Modes:")
        for mode in ProcessingMode:
            logger.info(f"  - {mode.name}: {mode.value}")

        logger.info("✓ 枚举类型测试成功")
        return True

    except Exception as e:
        logger.error(f"✗ 枚举类型测试失败: {e}")
        return False


def test_helper_methods():
    """测试辅助方法"""
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*60)
    logger.info("测试 9: 辅助方法 / Test 9: Helper Methods")
    logger.info("="*60)

    try:
        # 创建处理器
        processor = ClinicalTrialsProcessor({})

        # 测试日期解析
        date_struct = {"date": "2024-01-15"}
        parsed_date = processor._parse_date(date_struct)
        logger.info(f"日期解析 / Date parsing: {parsed_date}")
        assert parsed_date == "2024-01-15"

        # 测试研究阶段解析
        phase = processor._parse_study_phase("Phase 2")
        logger.info(f"阶段解析 / Phase parsing: {phase}")
        assert phase == "Phase 2"

        # 测试研究设计解析
        design_info = {
            "primaryPurpose": "Treatment",
            "masking": "Double",
            "allocation": "Randomized"
        }
        parsed_design = processor._parse_study_design(design_info)
        logger.info(f"设计解析 / Design parsing: {parsed_design}")
        assert parsed_design is not None
        assert parsed_design['primary_purpose'] == "Treatment"
        assert parsed_design['masking'] == "Double"

        logger.info("✓ 辅助方法测试成功")
        return True

    except Exception as e:
        logger.error(f"✗ 辅助方法测试失败: {e}")
        return False


def test_data_class_config():
    """测试配置数据类"""
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*60)
    logger.info("测试 10: 配置数据类 / Test 10: Configuration Data Class")
    logger.info("="*60)

    try:
        # 创建默认配置
        config1 = ClinicalTrialsExtractionConfig()
        logger.info(f"默认配置 / Default config:")
        logger.info(f"  API 基础 URL: {config1.api_base_url}")
        logger.info(f"  页面大小: {config1.page_size}")
        logger.info(f"  速率限制: {config1.rate_limit_per_second}")

        # 创建自定义配置
        config2 = ClinicalTrialsExtractionConfig(
            page_size=50,
            max_studies=1000,
            rate_limit_per_second=1.0
        )
        logger.info(f"\n自定义配置 / Custom config:")
        logger.info(f"  页面大小: {config2.page_size}")
        logger.info(f"  最大研究数: {config2.max_studies}")
        logger.info(f"  速率限制: {config2.rate_limit_per_second}")

        assert config2.page_size == 50
        assert config2.max_studies == 1000
        assert config2.rate_limit_per_second == 1.0

        logger.info("✓ 配置数据类测试成功")
        return True

    except Exception as e:
        logger.error(f"✗ 配置数据类测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    logger.info("\n" + "="*60)
    logger.info("ClinicalTrials.gov 处理器测试套件")
    logger.info("ClinicalTrials.gov Processor Test Suite")
    logger.info("="*60)

    test_results = []

    # 运行所有测试
    test_results.append(("处理器初始化", test_processor_initialization()))
    test_results.append(("自定义配置", test_custom_config()))
    test_results.append(("枚举类型", test_enums()))
    test_results.append(("配置数据类", test_data_class_config()))
    test_results.append(("辅助方法", test_helper_methods()))
    test_results.append(("研究数据转换", test_transform_study()))
    test_results.append(("转换和验证", test_transform_and_validate()))
    test_results.append(("保存结果", test_save_results()))

    # API 测试（这些可能需要网络连接）
    logger.info("\n" + "="*60)
    logger.info("API 测试（需要网络连接）/ API Tests (Network Required)")
    logger.info("="*60)

    test_results.append(("获取单个研究", test_fetch_single_study()))
    test_results.append(("按查询获取", test_fetch_by_query()))

    # 汇总结果
    logger.info("\n" + "="*60)
    logger.info("测试结果汇总 / Test Results Summary")
    logger.info("="*60)

    passed = 0
    failed = 0

    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{status} / {status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    logger.info(f"\n总计 / Total: {len(test_results)} 个测试")
    logger.info(f"通过 / Passed: {passed}")
    logger.info(f"失败 / Failed: {failed}")
    logger.info(f"通过率 / Pass Rate: {passed/len(test_results)*100:.1f}%")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()

    if success:
        print("\n所有测试通过！/ All tests passed!")
        sys.exit(0)
    else:
        print("\n部分测试失败！/ Some tests failed!")
        sys.exit(1)
