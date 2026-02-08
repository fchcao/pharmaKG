#!/usr/bin/env python3
"""
PharmaKG - ChEMBL Data Import to Neo4j
将 ChEMBL 提取的数据导入 Neo4j 知识图谱

This script imports the extracted ChEMBL data from JSON files into Neo4j.
此脚本将从 JSON 文件中提取的 ChEMBL 数据导入到 Neo4j。

Usage:
    python scripts/import_chembl_to_neo4j.py [--data-dir PATH] [--batch-size SIZE]

Example:
    python scripts/import_chembl_to_neo4j.py --data-dir data/processed/documents/chembl
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chembl_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ChEMBLNeo4jImporter:
    """ChEMBL数据导入到Neo4j"""

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "pharmaKG2024!",
        neo4j_database: str = "neo4j",
        batch_size: int = 500
    ):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.neo4j_database = neo4j_database
        self.batch_size = batch_size
        self._driver = None

        # Statistics
        self.stats = {
            "nodes_created": 0,
            "relationships_created": 0,
            "nodes_merged": 0,
            "relationships_merged": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }

    def _get_driver(self):
        """Get Neo4j driver"""
        from neo4j import GraphDatabase
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
        return self._driver

    def close(self):
        """Close Neo4j connection"""
        if self._driver:
            self._driver.close()
            self._driver = None

    def create_constraints(self):
        """Create constraints for entity types"""
        logger.info("Creating constraints...")

        constraints = [
            # Compound constraints
            "CREATE CONSTRAINT compound_chembl_id IF NOT EXISTS FOR (c:Compound) REQUIRE c.chembl_id IS UNIQUE",
            "CREATE CONSTRAINT compound_inchikey IF NOT EXISTS FOR (c:Compound) REQUIRE c.inchi_key IS UNIQUE",

            # Target constraints
            "CREATE CONSTRAINT target_chembl_id IF NOT EXISTS FOR (t:Target) REQUIRE t.chembl_id IS UNIQUE",
            "CREATE CONSTRAINT target_uniprot IF NOT EXISTS FOR (t:Target) REQUIRE t.uniprot_id IS UNIQUE",

            # Assay constraints
            "CREATE CONSTRAINT assay_chembl_id IF NOT EXISTS FOR (a:Assay) REQUIRE a.chembl_id IS UNIQUE",

            # Pathway constraints
            "CREATE CONSTRAINT pathway_go_id IF NOT EXISTS FOR (p:Pathway) REQUIRE p.go_id IS UNIQUE",
        ]

        with self._get_driver().session(database=self.neo4j_database) as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"Created constraint: {constraint[:50]}...")
                except Exception as e:
                    if "already exists" in str(e) or "equivalent" in str(e):
                        logger.debug(f"Constraint already exists: {constraint[:50]}...")
                    else:
                        logger.warning(f"Failed to create constraint: {str(e)}")

        logger.info("Constraints created successfully")

    def load_json_file(self, file_path: str) -> List[Dict]:
        """Load JSON data from file"""
        logger.info(f"Loading data from {file_path}...")

        with open(file_path, 'r') as f:
            data = json.load(f)

        logger.info(f"Loaded {len(data)} records from {file_path}")
        return data

    def import_compounds(self, compounds_file: str):
        """Import compound entities"""
        logger.info("Importing compounds...")

        compounds = self.load_json_file(compounds_file)

        # Create compounds in batches
        with self._get_driver().session(database=self.neo4j_database) as session:
            for i in range(0, len(compounds), self.batch_size):
                batch = compounds[i:i + self.batch_size]

                # UNWIND query for batch creation
                query = """
                UNWIND $batch AS row
                MERGE (c:Compound {chembl_id: row.primary_id})
                ON CREATE SET
                    c.entity_type = row.entity_type,
                    c.name = row.properties.name,
                    c.molecule_type = row.properties.molecule_type,
                    c.max_phase = row.properties.max_phase,
                    c.therapeutic_flag = row.properties.therapeutic_flag,
                    c.canonical_smiles = row.properties.canonical_smiles,
                    c.standard_inchi = row.properties.standard_inchi,
                    c.inchi_key = row.identifiers.InChIKey,
                    c.molregno = row.identifiers.molregno,
                    c.molecular_weight = row.properties.molecular_properties.molecular_weight,
                    c.num_ro5_violations = row.properties.molecular_properties.num_ro5_violations,
                    c.hbd = row.properties.molecular_properties.hbd,
                    c.hba = row.properties.molecular_properties.hba,
                    c.logp = row.properties.molecular_properties.logp,
                    c.psa = row.properties.molecular_properties.psa,
                    c.source = row.properties.source,
                    c.version = row.properties.version,
                    c.imported_at = $imported_at
                ON MATCH SET
                    c.last_updated = $updated_at
                """

                try:
                    result = session.run(query, batch=batch, imported_at=datetime.now().isoformat(), updated_at=datetime.now().isoformat())
                    counters = result.consume().counters
                    self.stats["nodes_created"] += getattr(counters, 'nodes_created', 0)
                    self.stats["nodes_merged"] += getattr(counters, 'nodes_merged', 0)
                    logger.info(f"Imported batch {i//self.batch_size + 1}: {len(batch)} compounds")
                except Exception as e:
                    logger.error(f"Error importing compound batch: {str(e)}")
                    self.stats["errors"] += 1

        logger.info(f"Compounds import completed: {len(compounds)} total")

    def import_targets(self, targets_file: str):
        """Import target entities"""
        logger.info("Importing targets...")

        targets = self.load_json_file(targets_file)

        with self._get_driver().session(database=self.neo4j_database) as session:
            for i in range(0, len(targets), self.batch_size):
                batch = targets[i:i + self.batch_size]

                query = """
                UNWIND $batch AS row
                MERGE (t:Target {chembl_id: row.primary_id})
                ON CREATE SET
                    t.entity_type = row.entity_type,
                    t.name = row.properties.name,
                    t.target_type = row.properties.target_type,
                    t.organism = row.properties.organism,
                    t.uniprot_id = row.identifiers.UniProt,
                    t.tid = row.identifiers.tid,
                    t.sequence = row.properties.sequence,
                    t.component_description = row.properties.component_description,
                    t.source = row.properties.source,
                    t.version = row.properties.version,
                    t.imported_at = $imported_at
                ON MATCH SET
                    t.last_updated = $updated_at
                """

                try:
                    result = session.run(query, batch=batch, imported_at=datetime.now().isoformat(), updated_at=datetime.now().isoformat())
                    counters = result.consume().counters
                    self.stats["nodes_created"] += getattr(counters, "nodes_created", 0)
                    self.stats["nodes_merged"] += getattr(counters, "nodes_merged", 0)
                    logger.info(f"Imported batch {i//self.batch_size + 1}: {len(batch)} targets")
                except Exception as e:
                    logger.error(f"Error importing target batch: {str(e)}")
                    self.stats["errors"] += 1

        logger.info(f"Targets import completed: {len(targets)} total")

    def import_assays(self, assays_file: str):
        """Import assay entities"""
        logger.info("Importing assays...")

        assays = self.load_json_file(assays_file)

        with self._get_driver().session(database=self.neo4j_database) as session:
            for i in range(0, len(assays), self.batch_size):
                batch = assays[i:i + self.batch_size]

                query = """
                UNWIND $batch AS row
                MERGE (a:Assay {chembl_id: row.primary_id})
                ON CREATE SET
                    a.entity_type = row.entity_type,
                    a.name = row.properties.name,
                    a.assay_type = row.properties.assay_type,
                    a.assay_category = row.properties.assay_category,
                    a.organism = row.properties.organism,
                    a.confidence_score = row.properties.confidence.score,
                    a.relationship_type = row.properties.relationship_type,
                    a.description = row.properties.description,
                    a.source = row.properties.source,
                    a.version = row.properties.version,
                    a.imported_at = $imported_at
                ON MATCH SET
                    a.last_updated = $updated_at
                """

                try:
                    result = session.run(query, batch=batch, imported_at=datetime.now().isoformat(), updated_at=datetime.now().isoformat())
                    counters = result.consume().counters
                    self.stats["nodes_created"] += getattr(counters, "nodes_created", 0)
                    self.stats["nodes_merged"] += getattr(counters, "nodes_merged", 0)
                    logger.info(f"Imported batch {i//self.batch_size + 1}: {len(batch)} assays")
                except Exception as e:
                    logger.error(f"Error importing assay batch: {str(e)}")
                    self.stats["errors"] += 1

        logger.info(f"Assays import completed: {len(assays)} total")

    def import_pathways(self, pathways_file: str):
        """Import pathway entities"""
        logger.info("Importing pathways...")

        pathways = self.load_json_file(pathways_file)

        with self._get_driver().session(database=self.neo4j_database) as session:
            for i in range(0, len(pathways), self.batch_size):
                batch = pathways[i:i + self.batch_size]

                query = """
                UNWIND $batch AS row
                MERGE (p:Pathway {go_id: row.identifiers.GO})
                ON CREATE SET
                    p.entity_type = row.entity_type,
                    p.primary_id = row.primary_id,
                    p.name = row.properties.name,
                    p.aspect = row.properties.aspect,
                    p.evidence_code = row.properties.evidence_code,
                    p.pathway_type = row.properties.pathway_type,
                    p.component_id = row.identifiers.component_id,
                    p.source = row.properties.source,
                    p.version = row.properties.version,
                    p.imported_at = $imported_at
                ON MATCH SET
                    p.last_updated = $updated_at
                """

                try:
                    result = session.run(query, batch=batch, imported_at=datetime.now().isoformat(), updated_at=datetime.now().isoformat())
                    counters = result.consume().counters
                    self.stats["nodes_created"] += getattr(counters, "nodes_created", 0)
                    self.stats["nodes_merged"] += getattr(counters, "nodes_merged", 0)
                    logger.info(f"Imported batch {i//self.batch_size + 1}: {len(batch)} pathways")
                except Exception as e:
                    logger.error(f"Error importing pathway batch: {str(e)}")
                    self.stats["errors"] += 1

        logger.info(f"Pathways import completed: {len(pathways)} total")

    def import_relationships(self, relationships_file: str):
        """Import relationships"""
        logger.info("Importing relationships...")

        relationships = self.load_json_file(relationships_file)

        # Group relationships by type for efficient processing
        rel_groups = {}
        for rel in relationships:
            rel_type = rel["relationship_type"]
            if rel_type not in rel_groups:
                rel_groups[rel_type] = []
            rel_groups[rel_type].append(rel)

        logger.info(f"Found {len(rel_groups)} relationship types")

        with self._get_driver().session(database=self.neo4j_database) as session:
            for rel_type, rels in rel_groups.items():
                logger.info(f"Processing {rel_type} relationships: {len(rels)} total")

                # Further group by source-target type combination for more efficient queries
                st_groups = {}  # source_type-target_type groups
                for rel in rels:
                    source_parts = rel["source_entity_id"].split("-")
                    target_parts = rel["target_entity_id"].split("-")
                    source_type = source_parts[0]
                    target_type = target_parts[0]
                    key = f"{source_type}-{target_type}"

                    if key not in st_groups:
                        st_groups[key] = []
                    st_groups[key].append({
                        "source_id": "-".join(source_parts[1:]),
                        "target_id": "-".join(target_parts[1:]),
                        "properties": rel.get("properties", {})
                    })

                # Process each source-target type group
                for st_key, st_rels in st_groups.items():
                    source_type, target_type = st_key.split("-")
                    logger.info(f"  Processing {source_type} -> {target_type}: {len(st_rels)} relationships")

                    for i in range(0, len(st_rels), self.batch_size):
                        batch = st_rels[i:i + self.batch_size]

                        # Build optimized query for this specific source-target type
                        query = self._build_optimized_relationship_query(
                            rel_type, source_type, target_type
                        )

                        try:
                            result = session.run(query, batch=batch, imported_at=datetime.now().isoformat(), updated_at=datetime.now().isoformat())
                            result.consume()  # Consume result to execute query
                            logger.info(f"    Batch {i//self.batch_size + 1}: {len(batch)} relationships")
                        except Exception as e:
                            logger.error(f"    Error importing batch: {str(e)}")
                            self.stats["errors"] += 1

        logger.info(f"Relationships import completed: {len(relationships)} total")

    def _build_optimized_relationship_query(self, rel_type: str, source_type: str, target_type: str) -> str:
        """Build optimized Cypher query for specific source-target type combination"""

        # Map relationship type to Cypher syntax
        cypher_rel_type = rel_type.upper().replace(" ", "_")

        # Map entity types to node labels and ID properties
        type_mapping = {
            "Compound": ("Compound", "chembl_id"),
            "Target": ("Target", "chembl_id"),
            "Assay": ("Assay", "chembl_id"),
            "Pathway": ("Pathway", "go_id")
        }

        source_label, source_prop = type_mapping.get(source_type, ("Compound", "chembl_id"))
        target_label, target_prop = type_mapping.get(target_type, ("Target", "chembl_id"))

        return f"""
        UNWIND $batch AS row
        MATCH (source:{source_label} {{{source_prop}: row.source_id}})
        MATCH (target:{target_label} {{{target_prop}: row.target_id}})
        MERGE (source)-[r:{cypher_rel_type}]->(target)
        ON CREATE SET
            r += row.properties,
            r.imported_at = $imported_at
        ON MATCH SET
            r.last_updated = $updated_at
        """

    def run_import(self, data_dir: str):
        """Run full import process"""
        self.stats["start_time"] = datetime.now()
        logger.info(f"Starting ChEMBL data import from {data_dir}")
        logger.info(f"Neo4j: {self.neo4j_uri}")

        try:
            # Step 1: Create constraints
            self.create_constraints()

            # Step 2: Import entities
            compounds_file = os.path.join(data_dir, "chembl_compounds_20260208_122312.json")
            if os.path.exists(compounds_file):
                self.import_compounds(compounds_file)

            targets_file = os.path.join(data_dir, "chembl_targets_20260208_122312.json")
            if os.path.exists(targets_file):
                self.import_targets(targets_file)

            assays_file = os.path.join(data_dir, "chembl_assays_20260208_122312.json")
            if os.path.exists(assays_file):
                self.import_assays(assays_file)

            pathways_file = os.path.join(data_dir, "chembl_pathways_20260208_122312.json")
            if os.path.exists(pathways_file):
                self.import_pathways(pathways_file)

            # Step 3: Import relationships
            relationships_file = os.path.join(data_dir, "chembl_relationships_20260208_122312.json")
            if os.path.exists(relationships_file):
                self.import_relationships(relationships_file)

        finally:
            self.stats["end_time"] = datetime.now()
            self._print_summary()

    def _print_summary(self):
        """Print import summary"""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        logger.info("=" * 80)
        logger.info("ChEMBL Data Import Summary")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Nodes Created: {self.stats['nodes_created']}")
        logger.info(f"Nodes Merged: {self.stats['nodes_merged']}")
        logger.info(f"Total Nodes: {self.stats['nodes_created'] + self.stats['nodes_merged']}")
        logger.info(f"Relationships Created: {self.stats['relationships_created']}")
        logger.info(f"Relationships Merged: {self.stats['relationships_merged']}")
        logger.info(f"Total Relationships: {self.stats['relationships_created'] + self.stats['relationships_merged']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 80)

        # Save summary to file
        summary_file = f"chembl_import_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump({
                **self.stats,
                "start_time": self.stats["start_time"].isoformat(),
                "end_time": self.stats["end_time"].isoformat(),
                "duration_seconds": duration
            }, f, indent=2)
        logger.info(f"Summary saved to {summary_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Import ChEMBL data to Neo4j",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed/documents/chembl",
        help="Directory containing ChEMBL JSON files"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch size for Neo4j operations (default: 500)"
    )

    parser.add_argument(
        "--neo4j-uri",
        type=str,
        default="bolt://localhost:7687",
        help="Neo4j URI (default: bolt://localhost:7687)"
    )

    parser.add_argument(
        "--neo4j-user",
        type=str,
        default="neo4j",
        help="Neo4j username (default: neo4j)"
    )

    parser.add_argument(
        "--neo4j-password",
        type=str,
        default="pharmaKG2024!",
        help="Neo4j password (default: pharmaKG2024!)"
    )

    parser.add_argument(
        "--neo4j-database",
        type=str,
        default="neo4j",
        help="Neo4j database name (default: neo4j)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate data without importing"
    )

    args = parser.parse_args()

    # Validate data directory
    if not os.path.exists(args.data_dir):
        logger.error(f"Data directory not found: {args.data_dir}")
        sys.exit(1)

    # Check for required files
    required_files = [
        "chembl_compounds_20260208_122312.json",
        "chembl_targets_20260208_122312.json",
        "chembl_assays_20260208_122312.json",
        "chembl_pathways_20260208_122312.json",
        "chembl_relationships_20260208_122312.json"
    ]

    missing_files = [f for f in required_files if not os.path.exists(os.path.join(args.data_dir, f))]
    if missing_files:
        logger.warning(f"Missing files: {missing_files}")
        logger.info("Will import available files only")

    # Create importer
    importer = ChEMBLNeo4jImporter(
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password,
        neo4j_database=args.neo4j_database,
        batch_size=args.batch_size
    )

    try:
        if args.dry_run:
            logger.info("DRY RUN MODE - Validating data without importing")
            # Just validate JSON files
            for filename in os.listdir(args.data_dir):
                if filename.endswith(".json") and filename != "chembl_summary_20260208_122312.json":
                    filepath = os.path.join(args.data_dir, filename)
                    try:
                        data = importer.load_json_file(filepath)
                        logger.info(f"✓ {filename}: {len(data)} records")
                    except Exception as e:
                        logger.error(f"✗ {filename}: {str(e)}")
        else:
            importer.run_import(args.data_dir)

    except KeyboardInterrupt:
        logger.info("Import interrupted by user")
    except Exception as e:
        logger.error(f"Import failed: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        importer.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
