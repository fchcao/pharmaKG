#!/usr/bin/env python3
"""
Add test relationships between existing compounds and targets
This creates BINDS_TO relationships for testing cross-domain queries
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Direct import to avoid conda issues
from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "pharmaKG2024!"
NEO4J_DATABASE = "neo4j"


def add_test_relationships():
    """Create BINDS_TO relationships between compounds and targets"""
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            # Get compounds and targets
            result = session.run("""
                MATCH (c:Compound)
                RETURN c.chembl_id as id, c.name as name
                LIMIT 20
            """)
            compounds = list(result)

            result = session.run("""
                MATCH (t:Target)
                RETURN t.chembl_id as id, t.name as name
                LIMIT 20
            """)
            targets = list(result)

            print(f"Found {len(compounds)} compounds and {len(targets)} targets")

            if not compounds or not targets:
                print("No entities found!")
                return

            # Create relationships between compounds and targets
            created = 0
            for i, compound in enumerate(compounds):
                # Connect each compound to multiple targets
                for j in range(min(3, len(targets))):
                    target = targets[(i + j) % len(targets)]

                    # Check if relationship already exists
                    check = session.run("""
                        MATCH (c:Compound {chembl_id: $cid})-[r:BINDS_TO]->(t:Target {chembl_id: $tid})
                        RETURN r
                    """, cid=compound["id"], tid=target["id"])

                    if not check.peek():  # No existing relationship
                        # Create BINDS_TO relationship
                        session.run("""
                            MATCH (c:Compound {chembl_id: $cid})
                            MATCH (t:Target {chembl_id: $tid})
                            CREATE (c)-[r:BINDS_TO]->(t)
                            SET r.confidence = 0.85,
                                r.activity_type = 'inhibitor',
                                r.created_at = datetime()
                            RETURN r
                        """, cid=compound["id"], tid=target["id"])
                        created += 1
                        if created <= 10:
                            print(f"  Created: {compound['name']} → {target['name']}")
                        elif created == 20:
                            print(f"  ... and {created - 10} more")
                        elif created % 50 == 0:
                            print(f"  Created {created} relationships so far...")

            print(f"\nTotal relationships created: {created}")

            # Verify
            result = session.run("""
                MATCH ()-[r:BINDS_TO]->()
                RETURN count(r) as total
            """)
            print(f"Total BINDS_TO relationships in database: {result.single()['total']}")

    finally:
        driver.close()


if __name__ == "__main__":
    add_test_relationships()
