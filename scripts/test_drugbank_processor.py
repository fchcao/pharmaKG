#!/usr/bin/env python3
#===========================================================
# PharmaKG DrugBank 处理器测试脚本
# Pharmaceutical Knowledge Graph - DrugBank Processor Test
#===========================================================
# 版本: v1.0
# 描述: 测试 DrugBank 处理器的功能
#===========================================================

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from processors.drugbank_processor import DrugBankProcessor, DrugBankExtractionConfig


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_drugbank_xml():
    """创建测试用的 DrugBank XML 文件"""
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<drugbank xmlns="http://drugbank.ca">
    <drug type="small molecule" created="2005-06-13" updated="2020-10-16">
        <drugbank-id primary="true">DB01001</drugbank-id>
        <name>Acetaminophen</name>
        <description>Acetaminophen is a pain reliever and a fever reducer.</description>
        <cas-number>103-90-2</cas-number>
        <unii>362O9ITL9D</unii>
        <state>solid</state>
        <groups>
            <group>approved</group>
        </groups>
        <general-references>
            <articles>
                <article>
                    <pubmed-id>1111</pubmed-id>
                </article>
            </articles>
        </general-references>
        <synthesis-reference/>
        <indication>For the treatment of mild to moderate pain and fever.</indication>
        <pharmacodynamics>Acetaminophen is a p-aminophenol derivative.</pharmacodynamics>
        <mechanism-of-action>
            <action>Increased pain threshold.</action>
            <description-of-action>The exact mechanism of action is not fully understood.</description-of-action>
        </mechanism-of-action>
        <toxicity>
            <ld50>338 mg/kg (oral, mouse)</ld50>
        </toxicity>
        <metabolism>Primarily metabolized in the liver.</metabolism>
        <absorption>Rapidly absorbed from the gastrointestinal tract.</absorption>
        <half-life>2 hours</half-life>
        <protein-binding>25%</protein-binding>
        <route-of-elimination>Renal</route-of-elimination>
        <volume-of-distribution>1 L/kg</volume-of-distribution>
        <clearance>13 mL/min</clearance>
        <classification>
            <description>This compound belongs to the class of organic compounds known as p-aminophenols.</description>
            <direct-parent>p-Aminophenols</direct-parent>
            <alternative-parent>Phenols</alternative-parent>
        </classification>
        <salinity/>
        <salt>
            <drugbank-id>DBSALT123</drugbank-id>
            <name>Acetaminophen hydrochloride</name>
            <unii>XXX</unii>
        </salt>
        <synonyms>
            <synonym language="english">Paracetamol</synonym>
        </synonyms>
        <products>
            <product>
                <name>Tylenol</name>
                <ndc-code>50580-400</ndc-code>
                <labeller>J&J</labeller>
                <dose>
                    <value>500</value>
                    <unit>mg</unit>
                </dose>
                <route>Oral</route>
                <form>tablet</form>
            </product>
        </products>
        <international-brands>
            <international-brand>
                <name>Panadol</name>
                <company>GSK</company>
            </international-brand>
        </international-brands>
        <dosages>
            <dosage>
                <form>tablet</form>
                <route>Oral</route>
                <strength>500 mg</strength>
            </dosage>
        </dosages>
        <atc-codes>
            <atc-code code="N02BE01" level="5">
                <code level="1">N</code>
                <code level="2">N02</code>
                <code level="3">N02B</code>
                <code level="4">N02BE</code>
                <code level="5">N02BE01</code>
                <atc-levels>
                    <level code="N">
                        <name>Nervous system</name>
                    </level>
                    <level code="N02">
                        <name>Analgesics</name>
                    </level>
                    <level code="N02B">
                        <name>Other analgesics and antipyretics</name>
                    </level>
                    <level code="N02BE">
                        <name>Anilides</name>
                    </level>
                    <level code="N02BE01">
                        <name>paracetamol</name>
                    </level>
                </atc-levels>
            </atc-code>
        </atc-codes>
        <categories>
            <category>
                <category>Analgesics</category>
            </category>
        </categories>
        <affected-organisms>
            <affected-organism>Humans and other mammals</affected-organism>
        </affected-organisms>
        <dosage-forms>
            <dosage-form>tablet</dosage-form>
            <dosage-form>capsule</dosage-form>
            <dosage-form>liquid</dosage-form>
        </dosage-forms>
        <targets>
            <target>
                <id>BE0004299</id>
                <name>Cyclooxygenase-2</name>
                <organism>Humans</organism>
                <action>Inhibitor</action>
                <known-action>true</known-action>
                <polypeptide id="P35354">
                    <name>Prostaglandin G/H synthase 2</name>
                    <general-function>Prostaglandin-endoperoxide synthase activity</general-function>
                    <specific-function>Conversion of arachidonate to prostaglandin G2</specific-function>
                    <gene-family>Cyclooxygenase</gene-family>
                    <external-identifiers>
                        <external-identifier>
                            <resource>UniProtKB</resource>
                            <identifier>P35354</identifier>
                        </external-identifier>
                        <external-identifier>
                            <resource>NCBI Gene</resource>
                            <identifier>5743</identifier>
                        </external-identifier>
                    </external-identifiers>
                    <synonyms>
                        <synonym>COX-2</synonym>
                        <synonym>PTGS2</synonym>
                    </synonyms>
                    <locus>HSA1</locus>
                    <cellular-location>Membrane</cellular-location>
                    <transmembrane-regions>0</transmembrane-regions>
                    <signal-regions>0</signal-regions>
                    <molecular-weight>72806.0 Da</molecular-weight>
                    <amino-acid-count>604</amino-acid-count>
                    <gene-name>PTGS2</gene-name>
                    <general-references>
                        <articles>
                            <article>
                                <pubmed-id>2222</pubmed-id>
                            </article>
                        </articles>
                    </general-references>
                </polypeptide>
            </target>
        </targets>
        <enzymes>
            <enzyme>
                <id>BE0003908</id>
                <name>Cytochrome P450 2E1</name>
                <organism>Humans</organism>
                <polypeptide id="P05181">
                    <name>Cytochrome P450 2E1</name>
                    <gene-name>CYP2E1</gene-name>
                    <external-identifiers>
                        <external-identifier>
                            <resource>UniProtKB</resource>
                            <identifier>P05181</identifier>
                        </external-identifier>
                    </external-identifiers>
                </polypeptide>
            </enzyme>
        </enzymes>
        <transporters/>
        <carriers/>
        <drug-interactions>
            <drug-interaction>
                <drugbank-id>DB00831</drugbank-id>
                <name>Warfarin</name>
                <description>Acetaminophen may increase the anticoagulant activities of Warfarin.</description>
            </drug-interaction>
            <drug-interaction>
                <drugbank-id>DB00252</drugbank-id>
                <name>Phenytoin</name>
                <description>The therapeutic efficacy of Acetaminophen can be decreased when used in combination with Phenytoin.</description>
            </drug-interaction>
        </drug-interactions>
        <food-interactions/>
        <sequences>
            <sequence format="txt">CC(C)Cc1ccc(cc1)C(C)C(=O)O</sequence>
        </sequences>
        <experimental-properties/>
        <external-identifiers>
            <external-identifier>
                <resource>ChEMBL</resource>
                <identifier>CHEMBL112</identifier>
            </external-identifier>
            <external-identifier>
                <resource>PubChem Compound</resource>
                <identifier>1983</identifier>
            </external-identifier>
            <external-identifier>
                <resource>Wikipedia</resource>
                <identifier>Acetaminophen</identifier>
            </external-identifier>
        </external-identifiers>
        <external-links/>
        <calculated-properties>
            <property>
                <kind>logP</kind>
                <value>0.46</value>
                <source>ALOGPS</source>
            </property>
            <property>
                <kind>Molecular Weight</kind>
                <value>151.16 g/mol</value>
                <source>Calculated</source>
            </property>
        </calculated-properties>
    </drug>
</drugbank>
"""

    # 创建测试文件
    test_dir = Path(__file__).parent.parent / "data" / "sources" / "drugbank"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "test_drugbank.xml"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_xml)

    logger.info(f"Created test DrugBank XML file: {test_file}")
    return test_file


def test_drugbank_processor():
    """测试 DrugBank 处理器"""
    logger.info("=" * 60)
    logger.info("Testing DrugBank Processor")
    logger.info("=" * 60)

    # 创建测试文件
    test_file = create_test_drugbank_xml()

    # 创建处理器配置
    config = {
        'extraction': {
            'batch_size': 1000,
            'limit_compounds': 10,
            'include_withdrawn': False,
            'include_experimental': True,
            'include_illicit': False,
            'min_approval_level': 'all',
            'extract_interactions': True,
            'extract_pharmacokinetics': True,
            'extract_enzymes': True,
            'extract_transporters': True,
            'extract_targets': True,
            'map_to_chembl': True
        }
    }

    # 创建处理器
    processor = DrugBankProcessor(config)

    # 处理测试文件
    result = processor.process(
        source_path=test_file.parent,
        output_to=str(test_file.parent.parent / "processed"),
        save_intermediate=True
    )

    # 输出结果
    print(f"\n{'='*60}")
    print(f"DrugBank Processor Test Results")
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
        print(f"  Targets: {stats.get('targets', 0)}")
        print(f"  Interactions: {stats.get('interactions', 0)}")
        print(f"  Enzymes: {stats.get('enzymes', 0)}")
        print(f"  Transporters: {stats.get('transporters', 0)}")

    # 检查实体内容
    if result.entities:
        print(f"\nSample Entities:")
        for entity in result.entities[:3]:
            print(f"  - {entity.get('entity_type')}: {entity.get('primary_id')}")
            if 'properties' in entity and 'name' in entity['properties']:
                print(f"    Name: {entity['properties']['name']}")

    # 检查关系内容
    if result.relationships:
        print(f"\nSample Relationships:")
        for rel in result.relationships[:3]:
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
    success = test_drugbank_processor()
    sys.exit(0 if success else 1)
