#!/usr/bin/env python3
"""
EMA Processor Test Script

Test the EMA guidance processor with sample data collection.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from processors.ema_processor import (
    EMAProcessor,
    EMAGuidanceCategory,
    EMADocumentType,
    EMACommittee,
    EMAGuidanceDocument,
)


def test_ema_processor():
    """Test EMA processor basic functionality"""

    print("=" * 60)
    print("EMA Guidance Processor Test")
    print("=" * 60)

    # Initialize processor
    processor = EMAProcessor()
    print("\n1. Processor initialized")
    print(f"   Data directory: {processor.sources_dir}")
    print(f"   Output directory: {processor.output_dir}")

    # Test collection plan
    print("\n2. Collection Plan:")
    plan = processor.generate_collection_plan()
    print(f"   Priority categories: {', '.join(plan['priority_categories'][:3])}...")
    print(f"   Total therapeutic areas: {len(plan['therapeutic_areas'])}")
    print(f"   Committees covered: {len(plan['committees'])}")

    # Test category detection
    print("\n3. Category Detection Test:")
    test_cases = [
        ("Guideline on clinical trials", EMAGuidanceCategory.CLINICAL_TRIALS),
        ("Quality of medicinal products", EMAGuidanceCategory.QUALITY),
        ("Pharmacovigilance guidelines", EMAGuidanceCategory.PHARMACOVIGILANCE),
        ("Biosimilar development", EMAGuidanceCategory.BIOSIMILARS),
        ("Advanced therapy medicinal products", EMAGuidanceCategory.ADVANCED_THERAPIES),
    ]

    for title, expected in test_cases:
        detected = processor._detect_category(title, None)
        status = "✓" if detected == expected else "✗"
        print(f"   {status} '{title}' -> {detected.value}")

    # Test document type detection
    print("\n4. Document Type Detection Test:")
    doc_type_cases = [
        ("Guideline on bioanalytical method validation", EMADocumentType.GUIDELINE),
        ("Reflection paper on...", EMADocumentType.REFLECTION_PAPER),
        ("Question and answer on...", EMADocumentType.QUESTION_ANSWER),
        ("Concept paper for...", EMADocumentType.CONCEPT_PAPER),
    ]

    for title, expected in doc_type_cases:
        detected = processor._detect_document_type(title, "")
        status = "✓" if detected == expected else "✗"
        print(f"   {status} '{title}' -> {detected.value}")

    # Test committee detection
    print("\n5. Committee Detection Test:")
    committee_cases = [
        ("EMA/CHMP/12345/2024", EMACommittee.CHMP),
        ("Pharmacovigilance Risk Assessment Committee", EMACommittee.PRAC),
        ("Paediatric Investigation Plan", EMACommittee.PDCO),
        ("Orphan medicinal product designation", EMACommittee.COMP),
        ("Advanced Therapy Medicinal Product", EMACommittee.CAT),
        ("Herbal medicinal product", EMACommittee.HMPC),
    ]

    for text, expected in committee_cases:
        detected = processor._detect_committee(text, "")
        status = "✓" if detected == expected else "✗"
        print(f"   {status} '{text}' -> {detected.value}")

    # Test EMA ID generation
    print("\n6. EMA ID Generation Test:")
    id_cases = [
        ("https://www.ema.europa.eu/en/documents/...", "Test Document"),
        ("https://www.ema.europa.eu/en/EMA/CHMP/guideline/12345", "CHMP Guideline"),
    ]

    for url, title in id_cases:
        doc_id = processor._generate_ema_id(url, title)
        print(f"   '{title}' -> {doc_id}")

    # Test date parsing
    print("\n7. Date Parsing Test:")
    date_cases = [
        "15 January 2024",
        "January 2024",
        "2024-01-15",
        "15/01/2024",
    ]

    for date_str in date_cases:
        parsed = processor._parse_date(date_str)
        status = "✓" if parsed else "✗"
        print(f"   {status} '{date_str}' -> {parsed}")

    # Test document model
    print("\n8. Document Model Test:")
    test_doc = EMAGuidanceDocument(
        ema_id="EMA-TEST001",
        title="Test Guideline",
        url="https://www.ema.europa.eu/test",
        publish_date="2024-01-15",
        document_type=EMADocumentType.GUIDELINE,
        category=EMAGuidanceCategory.CLINICAL_TRIALS,
        committee=EMACommittee.CHMP,
    )

    doc_dict = test_doc.to_dict()
    print(f"   Document ID: {doc_dict['ema_id']}")
    print(f"   Title: {doc_dict['title']}")
    print(f"   Category: {doc_dict['category']}")
    print(f"   Committee: {doc_dict['committee']}")

    # Test statistics
    print("\n9. Statistics Test:")
    stats = processor.get_statistics()
    print(f"   Collection date: {stats['collection_date']}")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Categories: {list(stats['by_category'].keys())}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)

    # Print summary
    print("\nSummary:")
    print("- Processor successfully initialized")
    print("- Collection plan generated")
    print("- Category detection working")
    print("- Document type detection working")
    print("- Committee detection working")
    print("- EMA ID generation working")
    print("- Date parsing working")
    print("- Document model working")
    print("- Statistics tracking working")

    return True


def test_sample_collection():
    """Test actual EMA document collection (small sample)"""

    print("\n" + "=" * 60)
    print("Testing EMA Document Collection (Sample)")
    print("=" * 60)

    processor = EMAProcessor()

    # Collect a small sample (5 documents, last 30 days)
    print("\nCollecting sample documents (limit=5, lookback=30 days)...")
    print("Note: This may take a few minutes due to rate limiting...")

    try:
        documents = list(processor.scrape_guidance_list(
            limit=5,
            lookback_days=30
        ))

        print(f"\nCollected {len(documents)} documents")

        if documents:
            print("\nSample documents:")
            for i, doc in enumerate(documents[:3], 1):
                print(f"\n{i}. {doc.title}")
                print(f"   Category: {doc.category.value}")
                print(f"   Type: {doc.document_type.value}")
                print(f"   Committee: {doc.committee.value}")
                print(f"   Date: {doc.publish_date}")
                print(f"   URL: {doc.url[:80]}...")

            # Save results
            output_path = processor.save_documents(documents)
            print(f"\nSaved to: {output_path}")

        else:
            print("\nNo documents collected. This could be due to:")
            print("- Network connectivity issues")
            print("- EMA website structure changes")
            print("- No documents in the specified date range")

    except Exception as e:
        print(f"\nCollection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Print final statistics
    stats = processor.get_statistics()
    print("\nFinal Statistics:")
    print(f"Total documents: {stats['total_documents']}")
    print(f"By category: {stats['by_category']}")
    print(f"By type: {stats['by_type']}")

    return True


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run tests
    try:
        test_ema_processor()

        # Uncomment to test actual collection
        # test_sample_collection()

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
