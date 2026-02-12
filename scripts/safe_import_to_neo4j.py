#!/usr/bin/env python3
"""
PharmaKG - Safe Data Import to Neo4j
安全数据导入到Neo4j - 避免重复导入

This script safely imports processed data to Neo4j without duplicating existing records.
此脚本安全地将处理后的数据导入到Neo4j，不会创建重复记录。

Usage:
    python scripts/safe_import_to_neo4j.py [--source SOURCE] [--dry-run]

Examples:
    # Import all data types
    python scripts/safe_import_to_neo4j.py

    # Import only regulatory documents
    python scripts/safe_import_to_neo4j.py --source regulatory

    # Dry run to check what would be imported
    python scripts/safe_import_to_neo4j.py --dry-run
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('safe_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SafeNeo4jImporter:
    """Safe Neo4j importer that prevents duplicate imports"""

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "pharmaKG2024!",
        neo4j_database: str = "neo4j",
        batch_size: int = 100
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
            "nodes_merged": 0,
            "nodes_skipped": 0,
            "relationships_created": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }

        # Track imported IDs for deduplication
        self.imported_ids: Set[str] = set()

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

    def get_existing_ids(self, label: str, id_property: str) -> Set[str]:
        """Get existing IDs from database to avoid duplicates"""
        query = f"MATCH (n:{label}) RETURN n.{id_property} as id"
        ids = set()
        with self._get_driver().session(database=self.neo4j_database) as session:
            result = session.run(query)
            for record in result:
                if record["id"]:
                    ids.add(record["id"])
        logger.info(f"Found {len(ids)} existing {label} nodes")
        return ids

    def import_regulatory_documents(
        self,
        data_file: str = "/root/autodl-tmp/pj-pharmaKG/data/processed/regulatory_aggregated/regulatory_aggregated_20260212_103108.json",
        dry_run: bool = False
    ):
        """Import regulatory documents safely"""
        logger.info(f"Importing regulatory documents from {data_file}")

        if not os.path.exists(data_file):
            logger.error(f"Data file not found: {data_file}")
            return

        with open(data_file, 'r') as f:
            data = json.load(f)

        documents = data.get("documents", [])
        logger.info(f"Found {len(documents)} documents to process")

        # Get existing document IDs
        existing_ids = self.get_existing_ids("RegulatoryDocument", "document_id")

        with self._get_driver().session(database=self.neo4j_database) as session:
            batch = []
            skipped = 0

            for doc in documents:
                doc_id = doc.get("document_id")
                if not doc_id:
                    continue

                # Skip if already exists
                if doc_id in existing_ids:
                    skipped += 1
                    continue

                batch.append({
                    "document_id": doc_id,
                    "source_agency": doc.get("source_agency", ""),
                    "title": doc.get("title", "")[:500],  # Truncate long titles
                    "publish_date": doc.get("publish_date"),
                    "url": doc.get("url", "")[:1000],
                    "document_type": doc.get("document_type", ""),
                    "therapeutic_area": doc.get("therapeutic_area", ""),
                    "summary": (doc.get("summary") or "")[:2000],
                    "content": (doc.get("content") or "")[:5000],
                    "effective_date": doc.get("effective_date"),
                    "status": doc.get("status", "active"),
                    "language": doc.get("language", "en"),
                    "validation_score": doc.get("validation_score", 0),
                    "last_updated": doc.get("last_updated")
                })

                if len(batch) >= self.batch_size:
                    if not dry_run:
                        self._batch_create_regulatory_docs(session, batch)
                    self.stats["nodes_created"] += len(batch)
                    logger.info(f"Processed batch: {len(batch)} documents (skipped: {skipped})")
                    batch = []

            if batch and not dry_run:
                self._batch_create_regulatory_docs(session, batch)
                self.stats["nodes_created"] += len(batch)

        self.stats["nodes_skipped"] += skipped
        logger.info(f"Regulatory documents import completed: {len(documents) - skipped} new, {skipped} skipped")

    def _batch_create_regulatory_docs(self, session, batch: List[Dict]):
        """Batch create regulatory documents using MERGE"""
        query = """
        UNWIND $batch AS row
        MERGE (d:RegulatoryDocument {document_id: row.document_id})
        ON CREATE SET
            d.source_agency = row.source_agency,
            d.title = row.title,
            d.publish_date = row.publish_date,
            d.url = row.url,
            d.document_type = row.document_type,
            d.therapeutic_area = row.therapeutic_area,
            d.summary = row.summary,
            d.content = row.content,
            d.effective_date = row.effective_date,
            d.status = row.status,
            d.language = row.language,
            d.validation_score = row.validation_score,
            d.last_updated = row.last_updated,
            d.imported_at = $imported_at
        ON MATCH SET
            d.last_updated = row.last_updated
        """
        session.run(query, batch=batch, imported_at=datetime.now().isoformat())

    def import_chembl_data(
        self,
        db_path: str = "/root/autodl-tmp/pj-pharmaKG/data/sources/rd/chembl_36/chembl_36_sqlite/chembl_36.db",
        limit: int = 10000,
        dry_run: bool = False
    ):
        """Import ChEMBL data safely"""
        logger.info(f"Importing ChEMBL data from {db_path}")

        if not os.path.exists(db_path):
            logger.error(f"ChEMBL database not found: {db_path}")
            return

        # This is a placeholder - use the chembl_processor for actual import
        logger.info("ChEMBL import should be done via: python -m processors.chembl_processor")
        logger.info(f"Recommended command: python -m processors.chembl_processor {db_path} --limit-compounds {limit}")

    def import_tcm_policy_documents(
        self,
        data_file: str = "/root/autodl-tmp/pj-pharmaKG/data/processed/tcm_wps_processed.json",
        dry_run: bool = False
    ):
        """Import TCM policy documents safely"""
        logger.info(f"Importing TCM policy documents from {data_file}")

        if not os.path.exists(data_file):
            logger.error(f"Data file not found: {data_file}")
            return

        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        documents = data if isinstance(data, list) else data.get("documents", [])
        logger.info(f"Found {len(documents)} TCM policy documents")

        # Get existing IDs - use page_id as the ID field
        existing_ids = self.get_existing_ids("PolicyDocument", "page_id")

        with self._get_driver().session(database=self.neo4j_database) as session:
            batch = []
            skipped = 0

            for doc in documents:
                # TCM data uses page_id, not primary_id
                doc_id = doc.get("page_id") or doc.get("primary_id") or doc.get("id")
                if not doc_id:
                    continue

                # Convert to string for consistency
                doc_id_str = str(doc_id)
                if doc_id_str in existing_ids:
                    skipped += 1
                    continue

                # TCM data uses offical_release_date (note the typo in source)
                release_date = doc.get("official_release_date") or doc.get("offical_release_date")

                # Join subject words into string for storage
                subject_words = doc.get("subject_words", [])
                if isinstance(subject_words, list):
                    subject_words = ", ".join(subject_words)

                batch.append({
                    "page_id": doc_id_str,
                    "title_cn": doc.get("title_cn", "")[:500],
                    "title_en": doc.get("title_en", "")[:500],
                    "organization": doc.get("organization", ""),
                    "official_release_date": release_date,
                    "effective_date": doc.get("effective_date") or doc.get("abolish_date"),
                    "repeal_date": doc.get("repeal_date"),
                    "status": doc.get("status", ""),
                    "url": doc.get("url", "")[:1000],
                    "subject_words": subject_words[:2000] if subject_words else "",
                    "document_type": "TCM Policy"
                })

                if len(batch) >= self.batch_size:
                    if not dry_run:
                        self._batch_create_policy_docs(session, batch)
                    self.stats["nodes_created"] += len(batch)
                    batch = []

            if batch and not dry_run:
                self._batch_create_policy_docs(session, batch)
                self.stats["nodes_created"] += len(batch)

        self.stats["nodes_skipped"] += skipped
        logger.info(f"TCM policy documents import completed: {len(documents) - skipped} new, {skipped} skipped")

    def _batch_create_policy_docs(self, session, batch: List[Dict]):
        """Batch create policy documents using MERGE"""
        query = """
        UNWIND $batch AS row
        MERGE (p:PolicyDocument {page_id: row.page_id})
        ON CREATE SET
            p.title_cn = row.title_cn,
            p.title_en = row.title_en,
            p.organization = row.organization,
            p.official_release_date = row.official_release_date,
            p.effective_date = row.effective_date,
            p.repeal_date = row.repeal_date,
            p.status = row.status,
            p.url = row.url,
            p.document_type = row.document_type,
            p.subject_words = row.subject_words,
            p.imported_at = $imported_at
        ON MATCH SET
            p.last_updated = $imported_at
        """
        session.run(query, batch=batch, imported_at=datetime.now().isoformat())

    def import_crl_data(
        self,
        data_file: str = "/root/autodl-tmp/pj-pharmaKG/data/sources/reviews_crl/transparency-crl-0001-of-0001.json",
        dry_run: bool = False
    ):
        """Import Complete Response Letters safely"""
        logger.info(f"Importing CRL data from {data_file}")

        if not os.path.exists(data_file):
            logger.error(f"Data file not found: {data_file}")
            return

        with open(data_file, 'r') as f:
            data = json.load(f)

        results = data.get("results", [])
        logger.info(f"Found {len(results)} CRL records")

        # Get existing CRL IDs (using file_name as ID)
        existing_ids = self.get_existing_ids("CompleteResponseLetter", "file_name")

        with self._get_driver().session(database=self.neo4j_database) as session:
            batch = []
            skipped = 0

            for crl in results:
                file_name = crl.get("file_name")
                if not file_name:
                    continue

                if file_name in existing_ids:
                    skipped += 1
                    continue

                batch.append({
                    "file_name": file_name,
                    "letter_date": crl.get("letter_date", ""),
                    "letter_year": crl.get("letter_year"),
                    "letter_type": crl.get("letter_type", ""),
                    "approval_status": crl.get("approval_status", ""),
                    "application_number": ", ".join(crl.get("application_number", [])) if isinstance(crl.get("application_number"), list) else crl.get("application_number", ""),
                    "company_name": crl.get("company_name", ""),
                    "company_address": crl.get("company_address", ""),
                    "approver_name": crl.get("approver_name", ""),
                    "approver_title": crl.get("approver_title", ""),
                    "text_preview": (crl.get("text", "") or "")[:500]
                })

                if len(batch) >= self.batch_size:
                    if not dry_run:
                        self._batch_create_crls(session, batch)
                    self.stats["nodes_created"] += len(batch)
                    batch = []

            if batch and not dry_run:
                self._batch_create_crls(session, batch)
                self.stats["nodes_created"] += len(batch)

        self.stats["nodes_skipped"] += skipped
        logger.info(f"CRL import completed: {len(results) - skipped} new, {skipped} skipped")

    def _batch_create_crls(self, session, batch: List[Dict]):
        """Batch create CRL documents using MERGE"""
        query = """
        UNWIND $batch AS row
        MERGE (c:CompleteResponseLetter {file_name: row.file_name})
        ON CREATE SET
            c.letter_date = row.letter_date,
            c.letter_year = row.letter_year,
            c.letter_type = row.letter_type,
            c.approval_status = row.approval_status,
            c.application_number = row.application_number,
            c.company_name = row.company_name,
            c.company_address = row.company_address,
            c.approver_name = row.approver_name,
            c.approver_title = row.approver_title,
            c.text_preview = row.text_preview,
            c.source = 'FDA',
            c.imported_at = $imported_at
        """
        session.run(query, batch=batch, imported_at=datetime.now().isoformat())

    def verify_import(self):
        """Verify and display import results"""
        with self._get_driver().session(database=self.neo4j_database) as session:
            # Count all nodes
            result = session.run("MATCH (n) RETURN count(n) as total")
            total = result.single()["total"]

            # Count by label
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(*) as count
                ORDER BY count DESC
            """)

            logger.info("\n" + "=" * 60)
            logger.info("Import Verification Summary")
            logger.info("=" * 60)
            logger.info(f"Total nodes in database: {total}")
            logger.info("\nNodes by type:")

            for record in result:
                logger.info(f"  {record['label']}: {record['count']}")

            logger.info("\nImport statistics:")
            logger.info(f"  Nodes created: {self.stats['nodes_created']}")
            logger.info(f"  Nodes merged: {self.stats['nodes_merged']}")
            logger.info(f"  Nodes skipped (already exist): {self.stats['nodes_skipped']}")
            logger.info(f"  Errors: {self.stats['errors']}")
            logger.info("=" * 60)

    def run_import(self, source: Optional[str] = None, dry_run: bool = False):
        """Run the import process"""
        self.stats["start_time"] = datetime.now()

        logger.info("=" * 60)
        logger.info("Safe Data Import Starting")
        logger.info("=" * 60)
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")

        try:
            if source is None or source == "regulatory":
                self.import_regulatory_documents(dry_run=dry_run)

            if source is None or source == "tcm":
                self.import_tcm_policy_documents(dry_run=dry_run)

            if source is None or source == "crl":
                self.import_crl_data(dry_run=dry_run)

            if source is None or source == "chembl":
                self.import_chembl_data(dry_run=dry_run)

            if not dry_run:
                self.verify_import()

        finally:
            self.stats["end_time"] = datetime.now()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Safe data import to Neo4j",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import all data types
  python scripts/safe_import_to_neo4j.py

  # Import only regulatory documents
  python scripts/safe_import_to_neo4j.py --source regulatory

  # Import only TCM policy documents
  python scripts/safe_import_to_neo4j.py --source tcm

  # Import only CRL data
  python scripts/safe_import_to_neo4j.py --source crl

  # Dry run to check what would be imported
  python scripts/safe_import_to_neo4j.py --dry-run
        """
    )

    parser.add_argument(
        "--source",
        type=str,
        choices=["regulatory", "tcm", "crl", "chembl"],
        help="Import only specific data source (default: all)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate import without making changes"
    )

    parser.add_argument(
        "--neo4j-uri",
        type=str,
        default="bolt://localhost:7687",
        help="Neo4j URI"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for Neo4j operations"
    )

    args = parser.parse_args()

    # Create importer
    importer = SafeNeo4jImporter(
        neo4j_uri=args.neo4j_uri,
        batch_size=args.batch_size
    )

    try:
        importer.run_import(source=args.source, dry_run=args.dry_run)

        duration = (importer.stats["end_time"] - importer.stats["start_time"]).total_seconds()
        logger.info(f"\nImport completed in {duration:.1f} seconds")

        if args.dry_run:
            logger.info("DRY RUN completed - no changes were made")

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
