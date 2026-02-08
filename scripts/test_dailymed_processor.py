#!/usr/bin/env python3
#===========================================================
# PharmaKG DailyMed 处理器测试脚本
# Pharmaceutical Knowledge Graph - DailyMed Processor Test
#===========================================================
# 版本: v1.0
# 描述: 测试 DailyMed 处理器的功能
#===========================================================

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from processors.dailymed_processor import DailyMedProcessor, DailyMedExtractionConfig


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_dailymed_xml():
    """创建测试用的 DailyMed SPL XML 文件"""
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<document xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <id root="2.16.840.1.113883.4.9" extension="1234"/>
    <code code="123456" codeSystem="2.16.840.1.113883.6.69" codeSystemName="NDC"/>
    <title>Tylenol (acetaminophen) Tablets</title>

    <effectiveTime value="20200101"/>
    <setId root="2.16.840.1.113883.4.9" extension="test_set_id"/>
    <versionNumber value="1"/>

    <author>
        <assignedEntity>
            <representedOrganization>
                <name>Johnson &amp; Johnson</name>
            </representedOrganization>
        </assignedEntity>
    </author>

    <component>
        <structuredBody>
            <component>
                <section>
                    <id root="1234"/>
                    <code code="34066-1" codeSystem="2.16.840.1.113883.6.1" displayName="PRODUCT SECTION"/>
                    <title>PRODUCT INFORMATION</title>
                    <text>
                        <paragraph>Tylenol (acetaminophen) is a pain reliever and fever reducer.</paragraph>
                    </text>

                    <effectiveTime value="20200101"/>

                    <subject>
                        <manufacturedProduct>
                            <manufacturedMaterial>
                                <code code="XXXX" displayName="acetaminophen"/>
                                <name>acetaminophen</name>
                                <formCode displayName="TABLET"/>
                                <asEntityRef>
                                    <playingSubstance>
                                        <code code="XXXX" displayName="acetaminophen"/>
                                        <name>acetaminophen</name>
                                    </playingSubstance>
                                </asEntityRef>
                            </manufacturedMaterial>
                            <manufacturerOrganization>
                                <name>Johnson &amp; Johnson Consumer Healthcare</name>
                            </manufacturerOrganization>
                        </manufacturedProduct>
                    </subject>

                    <author>
                        <assignedEntity>
                            <representedOrganization>
                                <name>Johnson &amp; Johnson</name>
                            </representedOrganization>
                        </assignedEntity>
                    </author>

                    <component>
                        <section>
                            <id root="5678"/>
                            <code code="34070-3" codeSystem="2.16.840.1.113883.6.1" displayName="ACTIVE INGREDIENT SECTION"/>
                            <title>ACTIVE INGREDIENT</title>
                            <text>
                                <paragraph>Active ingredient: Acetaminophen 500 mg</paragraph>
                            </text>
                        </section>
                    </component>

                    <component>
                        <section>
                            <id root="5679"/>
                            <code code="34071-1" codeSystem="2.16.840.1.113883.6.1" displayName="INACTIVE INGREDIENT SECTION"/>
                            <title>INACTIVE INGREDIENTS</title>
                            <text>
                                <paragraph>Inactive ingredients: Carnauba wax, corn starch, hypromellose, magnesium stearate, powdered cellulose</paragraph>
                            </text>
                        </section>
                    </component>

                    <component>
                        <section>
                            <id root="5680"/>
                            <code code="34072-9" codeSystem="2.16.840.1.113883.6.1" displayName="DOSAGE AND ADMINISTRATION SECTION"/>
                            <title>DOSAGE AND ADMINISTRATION</title>
                            <text>
                                <paragraph>Do not take more than directed (see liver warning).</paragraph>
                                <paragraph>Adults and children 12 years and over: Take 2 tablets every 4 to 6 hours while symptoms last.</paragraph>
                                <paragraph>Children under 12 years: Ask a doctor.</paragraph>
                            </text>
                        </section>
                    </component>

                    <component>
                        <section>
                            <id root="5681"/>
                            <code code="34073-7" codeSystem="2.16.840.1.113883.6.1" displayName="INDICATIONS AND USAGE SECTION"/>
                            <title>INDICATIONS AND USAGE</title>
                            <text>
                                <paragraph>Tylenol is a pain reliever and a fever reducer.</paragraph>
                                <paragraph>temporarily relieves minor aches and pains due to:</paragraph>
                                <list>
                                    <item>headache</item>
                                    <item>muscular aches</item>
                                    <item>backache</item>
                                    <item>minor pain of arthritis</item>
                                    <item>the common cold</item>
                                    <item>menstrual cramps</item>
                                    <item>toothache</item>
                                </list>
                                <paragraph>temporarily reduces fever</paragraph>
                            </text>
                        </section>
                    </component>

                    <component>
                        <section>
                            <id root="5682"/>
                            <code code="34084-4" codeSystem="2.16.840.1.113883.6.1" displayName="CONTRAINDICATIONS SECTION"/>
                            <title>CONTRAINDICATIONS</title>
                            <text>
                                <paragraph>Do not use if you are allergic to acetaminophen.</paragraph>
                                <paragraph>Do not use with any other drug containing acetaminophen (prescription or nonprescription).</paragraph>
                                <paragraph>Do not use if you have liver disease.</paragraph>
                            </text>
                        </section>
                    </component>

                    <component>
                        <section>
                            <id root="5683"/>
                            <code code="34085-1" codeSystem="2.16.840.1.113883.6.1" displayName="WARNINGS AND PRECAUTIONS SECTION"/>
                            <title>WARNINGS</title>
                            <text>
                                <paragraph><content styleCode="bold">Liver warning:</content> This product contains acetaminophen. Severe liver damage may occur if you take more than 4000 mg in 24 hours.</paragraph>
                                <paragraph><content styleCode="bold">Allergy alert:</content> Acetaminophen may cause severe skin reactions.</paragraph>
                            </text>
                        </section>
                    </component>

                    <component>
                        <section>
                            <id root="5684"/>
                            <code code="34085-2" codeSystem="2.16.840.1.113883.6.1" displayName="BOXED WARNING SECTION"/>
                            <title>BOXED WARNING</title>
                            <text>
                                <paragraph><content styleCode="bold">WARNING: HEPATOTOXICITY</content></paragraph>
                                <paragraph>Acetaminophen has been associated with cases of acute liver failure, at times resulting in liver transplant and death.</paragraph>
                            </text>
                        </section>
                    </component>

                    <component>
                        <section>
                            <id root="5685"/>
                            <code code="34088-5" codeSystem="2.16.840.1.113883.6.1" displayName="ADVERSE REACTIONS SECTION"/>
                            <title>ADVERSE REACTIONS</title>
                            <text>
                                <paragraph>The most common adverse reactions are:</paragraph>
                                <list>
                                    <item>nausea</item>
                                    <item>vomiting</item>
                                    <item>headache</item>
                                    <item>dizziness</item>
                                    <item>rash</item>
                                </list>
                                <paragraph>Severe adverse reactions include:</paragraph>
                                <list>
                                    <item>anaphylaxis</item>
                                    <item>hepatotoxicity</item>
                                    <item>hypersensitivity reactions</item>
                                </list>
                            </text>
                        </section>
                    </component>

                    <component>
                        <section>
                            <id root="5686"/>
                            <code code="34095-0" codeSystem="2.16.840.1.113883.6.1" displayName="USE IN SPECIFIC POPULATIONS SECTION"/>
                            <title>USE IN SPECIFIC POPULATIONS</title>
                            <text>
                                <paragraph><content styleCode="bold">Pregnancy:</content> Acetaminophen can be used during pregnancy.</paragraph>
                                <paragraph><content styleCode="bold">Lactation:</content> Acetaminophen is excreted in human milk.</paragraph>
                            </text>
                        </section>
                    </component>

                    <component>
                        <section>
                            <id root="5687"/>
                            <code code="34096-8" codeSystem="2.16.840.1.113883.6.1" displayName="DRUG INTERACTIONS SECTION"/>
                            <title>DRUG INTERACTIONS</title>
                            <text>
                                <paragraph><content styleCode="bold">Warfarin:</content> Acetaminophen may increase the anticoagulant effect of warfarin.</paragraph>
                                <paragraph><content styleCode="bold">Alcohol:</content> Chronic alcohol use may increase the risk of liver damage.</paragraph>
                            </text>
                        </section>
                    </component>

                    <component>
                        <section>
                            <id root="5688"/>
                            <code code="34100-7" codeSystem="2.16.840.1.113883.6.1" displayName="PHARMACOGENOMICS SECTION"/>
                            <title>PHARMACOGENOMICS</title>
                            <text>
                                <paragraph><content styleCode="bold">CYP2E1:</content> Genetic variations in CYP2E1 may affect acetaminophen metabolism.</paragraph>
                                <paragraph><content styleCode="bold">GST:</content> Glutathione S-transferase polymorphisms may increase susceptibility to acetaminophen-induced hepatotoxicity.</paragraph>
                            </text>
                        </section>
                    </component>

                    <component>
                        <section>
                            <id root="5689"/>
                            <code code="34107-2" codeSystem="2.16.840.1.113883.6.1" displayName="CLINICAL PHARMACOLOGY SECTION"/>
                            <title>CLINICAL PHARMACOLOGY</title>
                            <text>
                                <paragraph><content styleCode="bold">Mechanism of Action:</content> Acetaminophen is a centrally acting analgesic and antipyretic.</paragraph>
                                <paragraph><content styleCode="bold">Pharmacokinetics:</content> Absorption is rapid from the gastrointestinal tract.</paragraph>
                            </text>
                        </section>
                    </component>
                </section>
            </component>
        </structuredBody>
    </component>
</document>
"""

    # 创建测试文件
    test_dir = Path(__file__).parent.parent / "data" / "sources" / "dailymed"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "test_spl.xml"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_xml)

    logger.info(f"Created test DailyMed SPL XML file: {test_file}")
    return test_file


def test_dailymed_processor():
    """测试 DailyMed 处理器"""
    logger.info("=" * 60)
    logger.info("Testing DailyMed Processor")
    logger.info("=" * 60)

    # 创建测试文件
    test_file = create_test_dailymed_xml()

    # 创建处理器配置
    config = {
        'extraction': {
            'batch_size': 100,
            'max_files': 10,
            'query': None,
            'ndc': None,
            'set_id': None,
            'include_unapproved': False,
            'include_labeler_only': False,
            'extract_indications': True,
            'extract_contraindications': True,
            'extract_warnings': True,
            'extract_adverse_reactions': True,
            'extract_pharmacogenomics': True,
            'extract_boxed_warnings': True,
            'map_to_chembl': True,
            'map_to_drugbank': True,
            'api_base_url': 'https://dailymed.nlm.nih.gov/dailymed/api/v2',
            'download_dir': None,
            'use_api': False
        }
    }

    # 创建处理器
    processor = DailyMedProcessor(config)

    # 处理测试文件
    result = processor.process(
        source_path=test_file.parent,
        output_to=str(test_file.parent.parent / "processed"),
        save_intermediate=True
    )

    # 输出结果
    print(f"\n{'='*60}")
    print(f"DailyMed Processor Test Results")
    print(f"{'='*60}")
    print(f"Status: {result.status.value}")
    print(f"Files processed: {result.metrics.files_processed}")
    print(f"Entities extracted: {result.metrics.entities_extracted}")
    print(f"Relationships extracted: {result.metrics.relationships_extracted}")
    print(f"Processing time: {result.metrics.processing_time_seconds:.2f} seconds")

    if result.metadata:
        stats = result.metadata.get('stats', {})
        print(f"\nDetailed Statistics:")
        print(f"  Compounds: {stats.get('compounds', 0)}")
        print(f"  Conditions: {stats.get('conditions', 0)}")
        print(f"  Biomarkers: {stats.get('biomarkers', 0)}")
        print(f"  Adverse Events: {stats.get('adverse_events', 0)}")
        print(f"  Indications: {stats.get('indications', 0)}")
        print(f"  Contraindications: {stats.get('contraindications', 0)}")
        print(f"  Boxed Warnings: {stats.get('boxed_warnings', 0)}")

    # 检查实体内容
    if result.entities:
        print(f"\nSample Entities:")
        for entity in result.entities[:5]:
            print(f"  - {entity.get('entity_type')}: {entity.get('primary_id')}")
            if 'properties' in entity and 'name' in entity['properties']:
                print(f"    Name: {entity['properties']['name']}")

    # 检查关系内容
    if result.relationships:
        print(f"\nSample Relationships:")
        for rel in result.relationships[:5]:
            print(f"  - {rel.get('relationship_type')}: {rel.get('source_entity_id')} -> {rel.get('target_entity_id')}")

    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for warning in result.warnings[:5]:
            print(f"  - {warning}")

    if result.output_path:
        print(f"\nOutput files: {result.output_path}")

    return result.status.value == "completed"


if __name__ == '__main__':
    success = test_dailymed_processor()
    sys.exit(0 if success else 1)
