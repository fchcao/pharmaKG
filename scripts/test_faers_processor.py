#!/usr/bin/env python3
#===========================================================
# PharmaKG FAERS Processor Test Script
# Pharmaceutical Knowledge Graph - FAERS Processor Test
#===========================================================
# Version: v1.0
# Description: Test script for FDA FAERS Adverse Events Processor
#===========================================================

import logging
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from processors.faers_processor import FAERSProcessor, FAERSExtractionConfig


def setup_test_data():
    """
    Create mock FAERS data files for testing

    Returns:
        Temporary directory containing test data files
    """
    import csv
    import io

    temp_dir = tempfile.mkdtemp(prefix='faers_test_')

    # Create mock DEMO file
    demo_content = """safetyreportid$caseid$receivedate$serious$patientsex$patientage$patientageunit$patientweight$patientweightunit$safetyreportversion$reportertype
FAERS-2024-001$CASE001$20240101$Y$M$55$Year$75.5$kg$1.0$1
FAERS-2024-002$CASE002$20240102$Y$F$62$Year$68.2$kg$1.0$2
FAERS-2024-003$CASE003$20240103$N$M$45$Year$82.0$kg$1.0$5"""

    demo_file = Path(temp_dir) / "DEMO24Q1.txt"
    demo_file.write_text(demo_content)

    # Create mock DRUG file
    drug_content = """safetyreportid$drugseq$drugcharacterization$drugname$medicinalproduct$drugdosagetxt$drugadministration$drugroute
FAERS-2024-001$1$1$LISINOPRIL$Lisinopril 10mg$10 mg$Daily$Oral
FAERS-2024-001$2$2$ASPIRIN$Aspirin 81mg$81 mg$Daily$Oral
FAERS-2024-002$1$1$METFORMIN$Metformin 500mg$500 mg$Twice Daily$Oral
FAERS-2024-003$1$1$IBUPROFEN$Ibuprofen 200mg$200 mg$As Needed$Oral"""

    drug_file = Path(temp_dir) / "DRUG24Q1.txt"
    drug_file.write_text(drug_content)

    # Create mock REAC file
    reac_content = """safetyreportid$drugcharacterization$reactionmeddrapt$reactionmeddraversionpt
FAERS-2024-001$1$10009106$Angioedema
FAERS-2024-002$1$10017947$Hypoglycaemia
FAERS-2024-003$1$10028813$Abdominal pain"""

    reac_file = Path(temp_dir) / "REAC24Q1.txt"
    reac_file.write_text(reac_content)

    # Create mock OUTC file
    outc_content = """safetyreportid$patientoutcome
FAERS-2024-001$2
FAERS-2024-002$1
FAERS-2024-003$6"""

    outc_file = Path(temp_dir) / "OUTC24Q1.txt"
    outc_file.write_text(outc_content)

    return Path(temp_dir)


def test_faers_processor():
    """Test FAERS processor functionality"""
    print("="*60)
    print("Testing FAERS Processor")
    print("="*60)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # Create test data
    print("\n1. Setting up test data...")
    test_data_dir = setup_test_data()
    print(f"   Created test data directory: {test_data_dir}")

    # List test files
    test_files = list(test_data_dir.glob("*.txt"))
    print(f"   Test files created: {len(test_files)}")
    for f in test_files:
        print(f"     - {f.name}")

    # Create processor with test configuration
    print("\n2. Initializing FAERS Processor...")
    config = {
        'extraction': {
            'batch_size': 100,
            'max_reports': 10,
            'deduplicate_by_safetyreport_id': True,
            'map_to_chembl': False,  # Disable for testing
            'include_non_serious': True
        }
    }

    processor = FAERSProcessor(config)
    print(f"   Processor initialized: {processor.PROCESSOR_NAME}")

    # Test scan functionality
    print("\n3. Testing scan functionality...")
    files = processor.scan(test_data_dir)
    print(f"   Files found: {len(files)}")
    for f in files:
        print(f"     - {f.name}")

    # Test extract functionality for each file
    print("\n4. Testing extract functionality...")
    all_extracted_data = {}

    for file_path in files:
        print(f"   Extracting from: {file_path.name}")
        extracted_data = processor.extract(file_path)

        if extracted_data:
            file_type = extracted_data.get('file_type', 'UNKNOWN')
            records_count = len(extracted_data.get('records', []))
            print(f"     File type: {file_type}, Records: {records_count}")
            all_extracted_data[file_type] = extracted_data

    # Test transform functionality
    print("\n5. Testing transform functionality...")
    raw_data = {
        'results': list(processor.adverse_events_data.values())
    }

    # Need to properly structure the data for transform
    # Actually, let's use the process method which orchestrates everything

    # Test process method
    print("\n6. Testing full process workflow...")
    result = processor.process(test_data_dir, save_intermediate=True)

    print(f"   Processing status: {result.status.value}")
    print(f"   Files processed: {result.metrics.files_processed}")
    print(f"   Entities extracted: {result.metrics.entities_extracted}")
    print(f"   Relationships extracted: {result.metrics.relationships_extracted}")

    if result.errors:
        print(f"   Errors: {len(result.errors)}")
        for error in result.errors[:3]:
            print(f"     - {error}")

    # Test transform separately if we have data
    if processor.adverse_events_data:
        print("\n7. Testing transform separately...")
        # Transform needs the raw API format, but we have processed data
        # Let's check the internal data structures

        print(f"   Adverse events in memory: {len(processor.adverse_events_data)}")
        print(f"   Drugs in memory: {len(processor.drugs_data)}")
        print(f"   Reactions in memory: {len(processor.reactions_data)}")

        for safety_id, event_data in list(processor.adverse_events_data.items())[:2]:
            print(f"   Event {safety_id}:")
            print(f"     Serious: {event_data.get('serious')}")
            print(f"     Sex: {event_data.get('sex')}")
            print(f"     Age: {event_data.get('age')}")

    # Test statistics
    print("\n8. Testing statistics...")
    stats = processor.stats
    print(f"   Unique safetyreport IDs: {len(stats.unique_safetyreport_ids)}")
    print(f"   Files scanned: {stats.files_scanned}")
    print(f"   Files processed: {stats.files_processed}")

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Status: {'PASSED' if result.status.value == 'completed' else 'FAILED'}")
    print(f"Test data directory: {test_data_dir}")

    # Cleanup
    print("\nCleaning up test data...")
    import shutil
    shutil.rmtree(test_data_dir)
    print(f"Removed test directory: {test_data_dir}")

    return 0 if result.status.value == 'completed' else 1


def test_entity_creation():
    """Test individual entity creation methods"""
    print("\n" + "="*60)
    print("Testing Entity Creation Methods")
    print("="*60)

    config = {
        'extraction': {
            'deduplicate_by_safetyreport_id': True,
            'normalize_drug_names': True
        }
    }

    processor = FAERSProcessor(config)

    # Test AdverseEvent entity creation
    print("\n1. Testing AdverseEvent entity creation...")
    event_data = {
        'safetyreport_id': 'TEST-001',
        'case_number': 'CASE-TEST-001',
        'receive_date': '2024-01-01',
        'serious': True,
        'sex': 'M',
        'age': 55.0,
        'age_unit': 'Year',
        'weight': 75.5,
        'weight_unit': 'kg',
        'report_type': '1.0',
        'reporter_type': '1',
        'outcomes': ['Recovered']
    }

    adverse_event = processor._create_adverse_event_entity('TEST-001', event_data)
    if adverse_event:
        print(f"   Created AdverseEvent: {adverse_event['primary_id']}")
        print(f"   Serious: {adverse_event['properties']['serious']}")
        print(f"   Sex: {adverse_event['properties']['sex']}")
        print(f"   Age: {adverse_event['properties']['age']}")
        print("   ✓ PASSED")
    else:
        print("   ✗ FAILED")

    # Test Condition entity creation
    print("\n2. Testing Condition entity creation...")
    reaction_data = {
        'meddra_code': '10009106',
        'meddra_term': 'Angioedema'
    }

    condition, relationship = processor._create_condition_and_relationship('TEST-001', reaction_data)
    if condition:
        print(f"   Created Condition: {condition['primary_id']}")
        print(f"   MedDRA Code: {condition['properties']['meddra_code']}")
        print(f"   MedDRA Term: {condition['properties']['meddra_term']}")
        print(f"   Relationship type: {relationship['relationship_type']}")
        print("   ✓ PASSED")
    else:
        print("   ✗ FAILED")

    # Test Compound entity creation
    print("\n3. Testing Compound entity creation...")
    drug_data = {
        'drug_name': 'LISINOPRIL',
        'medicinal_product': 'Lisinopril 10mg',
        'drug_seq': '1',
        'drug_characterization': '1',
        'dose': '10 mg',
        'frequency': 'Daily',
        'route': 'Oral'
    }

    compound, relationship = processor._create_compound_and_relationship('TEST-001', drug_data)
    if compound:
        print(f"   Created Compound: {compound['primary_id']}")
        print(f"   Drug name: {compound['properties']['drug_name']}")
        print(f"   Drug role: {compound['properties']['drug_role']}")
        print(f"   Relationship type: {relationship['relationship_type'] if relationship else 'None'}")
        print("   ✓ PASSED")
    else:
        print("   ✗ FAILED")

    print("\n" + "="*60)
    print("Entity Creation Tests Complete")
    print("="*60)

    return 0


def test_data_parsing():
    """Test data parsing helper methods"""
    print("\n" + "="*60)
    print("Testing Data Parsing Methods")
    print("="*60)

    config = {'extraction': {}}
    processor = FAERSProcessor(config)

    # Test date parsing
    print("\n1. Testing date parsing...")
    test_dates = ['20240101', '20231231', 'invalid', None]
    for date_str in test_dates:
        parsed = processor._parse_fda_date(date_str)
        print(f"   '{date_str}' -> '{parsed}'")

    # Test serious parsing
    print("\n2. Testing serious field parsing...")
    test_values = ['Y', 'N', '1', '0', 'Yes', '', None]
    for value in test_values:
        parsed = processor._parse_serious(value)
        print(f"   '{value}' -> {parsed}")

    # Test age parsing
    print("\n3. Testing age parsing...")
    test_ages = ['55', '45.5', 'invalid', None, '']
    for age_str in test_ages:
        parsed = processor._parse_age(age_str)
        print(f"   '{age_str}' -> {parsed}")

    # Test weight parsing
    print("\n4. Testing weight parsing...")
    test_weights = ['75.5', '68.2', 'invalid', None, '']
    for weight_str in test_weights:
        parsed = processor._parse_weight(weight_str)
        print(f"   '{weight_str}' -> {parsed}")

    # Test outcome mapping
    print("\n5. Testing outcome code mapping...")
    outcome_codes = ['1', '2', '3', '4', '5', '6', 'invalid']
    for code in outcome_codes:
        mapped = processor._map_outcome_code(code)
        print(f"   Code '{code}' -> '{mapped}'")

    # Test reporter type mapping
    print("\n6. Testing reporter type mapping...")
    reporter_codes = ['1', '2', '3', '4', '5', '6', 'invalid']
    for code in reporter_codes:
        mapped = processor._map_reporter_type(code)
        print(f"   Code '{code}' -> '{mapped}'")

    # Test drug characterization mapping
    print("\n7. Testing drug characterization mapping...")
    char_codes = ['1', '2', '3', 'invalid']
    for code in char_codes:
        mapped = processor._map_drug_characterization(code)
        print(f"   Code '{code}' -> '{mapped}'")

    # Test drug name normalization
    print("\n8. Testing drug name normalization...")
    drug_names = [
        'lisinopril',
        'LISINOPRIL',
        '  aspirin  ',
        'METFORMIN  HYDROCHLORIDE',
        None
    ]
    for name in drug_names:
        normalized = processor._normalize_drug_name(name)
        print(f"   '{name}' -> '{normalized}'")

    print("\n" + "="*60)
    print("Data Parsing Tests Complete")
    print("="*60)

    return 0


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("FAERS Processor Test Suite")
    print("="*60)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Run tests
        test_result = test_faers_processor()

        print("\n" + "="*60)
        print("Running Additional Tests...")
        print("="*60)

        test_entity_creation()
        test_data_parsing()

        print("\n" + "="*60)
        print("All Tests Complete")
        print("="*60)
        print(f"Overall Result: {'PASSED ✓' if test_result == 0 else 'FAILED ✗'}")
        print(f"Test finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return test_result

    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
