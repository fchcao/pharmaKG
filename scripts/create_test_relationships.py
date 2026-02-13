#!/usr/bin/env python3
"""
Create test relationships between compounds and targets
This script creates sample TARGETS relationships for testing cross-domain queries
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.database import Neo4jConnection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_relationships():
    """Create test relationships between compounds and targets"""
    db = Neo4jConnection()

    logger.info("Creating test relationships...")

    # Get some compounds and targets
    compounds_result = db.execute_query("""
        MATCH (c:Compound)
        RETURN c.chembl_id as id, c.name as name
        LIMIT 10
    """)

    targets_result = db.execute_query("""
        MATCH (t:Target)
        RETURN t.chembl_id as id, t.name as name
        LIMIT 10
    """)

    compounds = [dict(record) for record in compounds_result.records]
    targets = [dict(record) for record in targets_result.records]

    logger.info(f"Found {len(compounds)} compounds and {len(targets)} targets")

    if not compounds or not targets:
        logger.error("No compounds or targets found in database!")
        return

    # Create relationships between compounds and targets
    created_count = 0
    for i, compound in enumerate(compounds):
        # Connect each compound to 2-3 targets
        for j in range(min(3, len(targets))):
            target = targets[(i + j) % len(targets)]

            # Check if relationship already exists
            check_result = db.execute_query(f"""
                MATCH (c:Compound {{chembl_id: '{compound['id']}'}})-[r:TARGETS]->(t:Target {{chembl_id: '{target['id']}'}})
                RETURN r
            """)

            if not check_result.records:
                # Create TARGETS relationship
                db.execute_query(f"""
                    MATCH (c:Compound {{chembl_id: '{compound['id']}'}})
                    MATCH (t:Target {{chembl_id: '{target['id']}'}})
                    CREATE (c)-[r:TARGETS]->(t)
                    SET r.confidence = 0.8 + (j * 0.05),
                        r.activity_type = CASE WHEN j % 2 = 0 THEN 'inhibitor' ELSE 'activator' END,
                        r.created_at = datetime()
                    RETURN r
                """)
                created_count += 1
                logger.info(f"Created TARGETS: {compound['name']} → {target['name']}")

    # Create some cross-domain relationships for testing
    logger.info("Creating cross-domain relationships...")

    # Connect compounds to clinical trials (if any exist)
    trials_result = db.execute_query("""
        MATCH (t:ClinicalTrial)
        RETURN t.id as id, t.brief_title as name
        LIMIT 5
    """)

    trials = [dict(record) for record in trials_result.records]

    if trials:
        for i, compound in enumerate(compounds[:5]):
            trial = trials[i % len(trials)]
            db.execute_query(f"""
                MATCH (c:Compound {{chembl_id: '{compound['id']}'}})
                MATCH (t:ClinicalTrial {{id: '{trial['id']}'}})
                CREATE (c)-[r:TESTED_IN_CLINICAL_TRIAL]->(t)
                SET r.phase = 'Phase ' + str((i % 3) + 1),
                    r.status = 'completed',
                    r.created_at = datetime()
                RETURN r
            """)
            created_count += 1
            logger.info(f"Created TESTED_IN_CLINICAL_TRIAL: {compound['name']} → {trial['name']}")

    logger.info(f"Total relationships created: {created_count}")

    # Verify relationships were created
    verify_result = db.execute_query("""
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY count DESC
        LIMIT 10
    """)

    logger.info("Relationship statistics:")
    for record in verify_result.records:
        logger.info(f"  {record['rel_type']}: {record['count']}")


if __name__ == "__main__":
    create_test_relationships()
