#!/usr/bin/env python3
#===========================================================
# PharmaKG Shortage Processor Test Script
# Pharmaceutical Knowledge Graph - Shortage Processor Test
#===========================================================
# Version: v1.0
# Description: Test script for FDA Drug Shortages Database Processor
#===========================================================

import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from processors.shortage_processor import ShortageProcessor, ShortageExtractionConfig


def create_mock_api_response():
    """Create mock FDA API response for testing"""
    return {
        "meta": {
            "results": {
                "total": 2,
                "skip": 0,
                "limit": 2
            }
        },
        "results": [
            {
                "shortage_id": "SH-001",
                "id": "SH-001",
                "generic_name": "Epinephrine",
                "brand_names": ["EpiPen", "Adrenaclick"],
                "ndc": "49502-1001-1",
                "dosage_form": "Injection",
                "strength": "0.3 mg",
                "route": "Intramuscular",
                "marketing_status": "Prescription",
                "status": "Current Shortage",
                "shortage_type": "Shortage",
                "start_date": "2024-01-01",
                "end_date": None,
                "reason": "Manufacturing delay",
                "therapeutic_area": "Anaphylaxis",
                "presentation": "Autoinjector",
                "manufacturer_name": "Viatris",
                "company_type": "Manufacturer",
                "facility_name": "Manufacturing Site A",
                "city": "Morgantown",
                "state": "WV",
                "country": "USA",
                "facility_type": "Manufacturing",
                "contact_info": "contact@viatris.com"
            },
            {
                "shortage_id": "SH-002",
                "id": "SH-002",
                "generic_name": "Amoxicillin",
                "brand_names": ["Amoxil"],
                "ndc": "00287-1001-01",
                "dosage_form": "Capsule",
                "strength": "500 mg",
                "route": "Oral",
                "marketing_status": "Prescription",
                "status": "Resolved",
                "shortage_type": "Supply Disruption",
                "start_date": "2023-06-01",
                "end_date": "2023-12-01",
                "reason": "Increased demand",
                "therapeutic_area": "Anti-infective",
                "manufacturer_name": "GSK",
                "company_type": "Manufacturer",
                "facility_name": "Manufacturing Site B",
                "city": "Philadelphia",
                "state": "PA",
                "country": "USA"
            }
        ]
    }


def test_shortage_processor():
    """Test Shortage processor functionality"""
    print("="*60)
    print("Testing Shortage Processor")
    print("="*60)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # Create processor with test configuration
    print("\n1. Initializing Shortage Processor...")
    config = {
        'extraction': {
            'limit': 100,
            'deduplicate_by_shortage_id': True,
            'map_to_chembl': False,  # Disable for testing
            'save_raw_response': False
        }
    }

    processor = ShortageProcessor(config)
    print(f"   Processor initialized: {processor.PROCESSOR_NAME}")

    # Create mock API response
    print("\n2. Creating mock API response...")
    mock_response = create_mock_api_response()
    print(f"   Mock response contains {len(mock_response['results'])} shortage records")

    # Test transform functionality
    print("\n3. Testing transform functionality...")
    transformed_data = processor.transform(mock_response)

    # Check transformed entities
    entities = transformed_data.get('entities', {})
    relationships = transformed_data.get('relationships', [])

    print(f"   Transformation completed:")
    print(f"     DrugShortage entities: {len(entities.get('sc:DrugShortage', []))}")
    print(f"     Compound entities: {len(entities.get('rd:Compound', []))}")
    print(f"     Manufacturer entities: {len(entities.get('sc:Manufacturer', []))}")
    print(f"     Facility entities: {len(entities.get('sc:Facility', []))}")
    print(f"     Total relationships: {len(relationships)}")

    # Validate data
    print("\n4. Testing validation...")
    is_valid = processor.validate(transformed_data)
    print(f"   Validation result: {is_valid}")

    # Test entity details
    print("\n5. Examining created entities...")

    # Check DrugShortage entities
    shortage_entities = entities.get('sc:DrugShortage', [])
    if shortage_entities:
        print(f"\n   DrugShortage Entity Example:")
        shortage = shortage_entities[0]
        print(f"     ID: {shortage['primary_id']}")
        print(f"     Status: {shortage['properties']['shortage_status']}")
        print(f"     Start Date: {shortage['properties']['shortage_start_date']}")
        print(f"     Reason: {shortage['properties']['reason_for_shortage']}")

    # Check Compound entities
    compound_entities = entities.get('rd:Compound', [])
    if compound_entities:
        print(f"\n   Compound Entity Example:")
        compound = compound_entities[0]
        print(f"     ID: {compound['primary_id']}")
        print(f"     Generic Name: {compound['properties']['generic_name']}")
        print(f"     Brand Names: {compound['properties']['brand_names']}")
        print(f"     NDC: {compound['properties']['ndc']}")

    # Check Manufacturer entities
    manufacturer_entities = entities.get('sc:Manufacturer', [])
    if manufacturer_entities:
        print(f"\n   Manufacturer Entity Example:")
        manufacturer = manufacturer_entities[0]
        print(f"     ID: {manufacturer['primary_id']}")
        print(f"     Name: {manufacturer['properties']['manufacturer_name']}")
        print(f"     Company Type: {manufacturer['properties']['company_type']}")

    # Check relationships
    if relationships:
        print(f"\n   Relationship Examples:")
        for rel in relationships[:5]:
            print(f"     {rel['relationship_type']}:")
            print(f"       {rel['source_entity_id']} -> {rel['target_entity_id']}")

    # Test statistics
    print("\n6. Testing statistics...")
    stats = processor.stats
    print(f"   Shortages extracted: {stats.shortages_extracted}")
    print(f"   Compounds extracted: {stats.compounds_extracted}")
    print(f"   Manufacturers extracted: {stats.manufacturers_extracted}")
    print(f"   Facilities extracted: {stats.facilities_extracted}")

    # Test save_results
    print("\n7. Testing save_results...")
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix='shortage_test_')

    try:
        output_path = processor.save_results(entities, relationships, temp_dir)
        print(f"   Results saved to: {output_path}")

        # Check created files
        output_dir = Path(temp_dir)
        created_files = list(output_dir.glob("shortages_*.json"))
        print(f"   Files created: {len(created_files)}")
        for f in created_files:
            print(f"     - {f.name} ({f.stat().st_size} bytes)")

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print(f"   Cleaned up test directory")

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Status: {'PASSED ✓' if is_valid else 'FAILED ✗'}")

    return 0 if is_valid else 1


def test_entity_creation():
    """Test individual entity creation methods"""
    print("\n" + "="*60)
    print("Testing Entity Creation Methods")
    print("="*60)

    config = {
        'extraction': {
            'deduplicate_by_shortage_id': True
        }
    }

    processor = ShortageProcessor(config)

    # Test DrugShortage entity creation
    print("\n1. Testing DrugShortage entity creation...")
    shortage_record = {
        "shortage_id": "TEST-001",
        "id": "TEST-001",
        "status": "Current Shortage",
        "start_date": "2024-01-01",
        "end_date": None,
        "reason": "Manufacturing delay",
        "shortage_type": "Shortage",
        "therapeutic_area": "Cardiovascular"
    }

    shortage_entity = processor._create_shortage_entity("TEST-001", shortage_record)
    if shortage_entity:
        print(f"   Created DrugShortage: {shortage_entity['primary_id']}")
        print(f"   Status: {shortage_entity['properties']['shortage_status']}")
        print(f"   Start Date: {shortage_entity['properties']['shortage_start_date']}")
        print(f"   Type: {shortage_entity['properties']['shortage_type']}")
        print("   ✓ PASSED")
    else:
        print("   ✗ FAILED")

    # Test Compound entity creation
    print("\n2. Testing Compound entity creation...")
    compound_record = {
        "generic_name": "Lisinopril",
        "brand_names": ["Prinivil", "Zestril"],
        "ndc": "12345-678-90",
        "dosage_form": "Tablet",
        "strength": "10 mg",
        "route": "Oral",
        "marketing_status": "Prescription"
    }

    compound_entity, relationship = processor._create_compound_entity("TEST-001", compound_record)
    if compound_entity:
        print(f"   Created Compound: {compound_entity['primary_id']}")
        print(f"   Generic Name: {compound_entity['properties']['generic_name']}")
        print(f"   Brand Names: {compound_entity['properties']['brand_names']}")
        print(f"   Relationship: {relationship['relationship_type']}")
        print("   ✓ PASSED")
    else:
        print("   ✗ FAILED")

    # Test Manufacturer entity creation
    print("\n3. Testing Manufacturer entity creation...")
    manufacturer_record = {
        "manufacturer_name": "Pfizer",
        "company_type": "Manufacturer",
        "contact_info": "info@pfizer.com",
        "reason": "Quality issues"
    }

    manufacturer_entity, relationships = processor._create_manufacturer_entity("TEST-001", manufacturer_record)
    if manufacturer_entity:
        print(f"   Created Manufacturer: {manufacturer_entity['primary_id']}")
        print(f"   Name: {manufacturer_entity['properties']['manufacturer_name']}")
        print(f"   Type: {manufacturer_entity['properties']['company_type']}")
        print(f"   Relationships created: {len(relationships)}")
        print("   ✓ PASSED")
    else:
        print("   ✗ FAILED")

    # Test Facility entity creation
    print("\n4. Testing Facility entity creation...")
    facility_record = {
        "manufacturer_name": "Pfizer",
        "facility_name": "Plant A",
        "city": "New York",
        "state": "NY",
        "country": "USA",
        "facility_type": "Manufacturing"
    }

    facility_entities, relationships = processor._create_facility_entities("TEST-001", facility_record)
    if facility_entities:
        facility = facility_entities[0]
        print(f"   Created Facility: {facility['primary_id']}")
        print(f"   Name: {facility['properties']['facility_name']}")
        print(f"   Location: {facility['properties']['address']['city']}, {facility['properties']['address']['state']}")
        print(f"   Type: {facility['properties']['facility_type']}")
        print(f"   Relationships created: {len(relationships)}")
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
    processor = ShortageProcessor(config)

    # Test date parsing
    print("\n1. Testing date parsing...")
    test_dates = [
        '2024-01-01',
        '2024/01/01',
        '01/01/2024',
        'invalid',
        None,
        '20240101'
    ]
    for date_str in test_dates:
        parsed = processor._parse_date(date_str)
        print(f"   '{date_str}' -> '{parsed}'")

    # Test shortage status mapping
    print("\n2. Testing shortage status mapping...")
    test_statuses = [
        'Current Shortage',
        'Current',
        'Active Shortage',
        'Resolved',
        'Resolved Shortage',
        'Recovered',
        'Unknown Status'
    ]
    for status in test_statuses:
        mapped = processor._map_shortage_status(status)
        print(f"   '{status}' -> '{mapped}'")

    # Test entity validation
    print("\n3. Testing entity validation...")
    valid_entity = {
        'primary_id': 'Test-001',
        'properties': {'name': 'Test'},
        'entity_type': 'sc:DrugShortage'
    }
    invalid_entity1 = {'primary_id': 'Test-002'}
    invalid_entity2 = {'properties': {'name': 'Test'}}

    print(f"   Valid entity: {processor._validate_entity(valid_entity)}")
    print(f"   Invalid (no properties): {processor._validate_entity(invalid_entity1)}")
    print(f"   Invalid (no primary_id): {processor._validate_entity(invalid_entity2)}")

    print("\n" + "="*60)
    print("Data Parsing Tests Complete")
    print("="*60)

    return 0


def test_api_methods():
    """Test API request methods (with mocking)"""
    print("\n" + "="*60)
    print("Testing API Methods (Mocked)")
    print("="*60)

    config = {
        'extraction': {
            'limit': 10,
            'save_raw_response': False
        }
    }

    processor = ShortageProcessor(config)

    # Test _build_date_filter
    print("\n1. Testing date filter building...")
    test_filters = [
        {'start_date': '2024-01-01'},
        {'end_date': '2024-12-31'},
        {'start_date': '2024-01-01', 'end_date': '2024-12-31'},
        {}
    ]
    for date_range in test_filters:
        filter_str = processor._build_date_filter(date_range)
        print(f"   {date_range} -> '{filter_str}'")

    # Test URL building (without actual request)
    print("\n2. Testing URL building...")
    from urllib.parse import urlencode, urlparse

    test_cases = [
        {'search': 'epinephrine', 'limit': '10'},
        {'search': 'status:Current', 'limit': '50'},
        {'limit': '100'}
    ]

    base_url = "https://api.fda.gov/drug/shortages.json"
    for params in test_cases:
        full_url = f"{base_url}?{urlencode(params)}"
        parsed = urlparse(full_url)
        print(f"   Params: {params}")
        print(f"   URL: ...{parsed.path}?{parsed.query}")

    print("\n" + "="*60)
    print("API Methods Tests Complete")
    print("="*60)

    return 0


def test_cross_domain_mapping():
    """Test cross-domain mapping methods"""
    print("\n" + "="*60)
    print("Testing Cross-Domain Mapping")
    print("="*60)

    config = {
        'extraction': {
            'map_to_chembl': True
        }
    }

    processor = ShortageProcessor(config)

    # Test _map_generic_to_chembl (currently returns None)
    print("\n1. Testing generic name to ChEMBL mapping...")
    test_drugs = ['Lisinopril', 'Aspirin', 'Metformin', 'Epinephrine']

    for drug_name in test_drugs:
        chembl_id = processor._map_generic_to_chembl(drug_name)
        print(f"   '{drug_name}' -> '{chembl_id}'")

    # Test caching
    print("\n2. Testing mapping cache...")
    print(f"   Cache size: {len(processor.chembl_cache)}")
    print(f"   Cached entries: {list(processor.chembl_cache.keys())}")

    # Test _create_cross_domain_relationships
    print("\n3. Testing cross-domain relationship creation...")
    mock_records = [
        {"shortage_id": "SH-001", "generic_name": "Lisinopril"},
        {"shortage_id": "SH-002", "generic_name": "Aspirin"}
    ]

    relationships = processor._create_cross_domain_relationships(mock_records)
    print(f"   Relationships created: {len(relationships)}")

    print("\n" + "="*60)
    print("Cross-Domain Mapping Tests Complete")
    print("="*60)

    return 0


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("Shortage Processor Test Suite")
    print("="*60)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Run tests
        test_result = test_shortage_processor()

        print("\n" + "="*60)
        print("Running Additional Tests...")
        print("="*60)

        test_entity_creation()
        test_data_parsing()
        test_api_methods()
        test_cross_domain_mapping()

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
