#===========================================================
# PharmaKG FDA Guidance Document Collector
# Pharmaceutical Knowledge Graph - FDA Guidance Collector
#===========================================================
# Version: v1.0
# Description: Collect FDA guidance documents from fda.gov
#              and save them in unified regulatory schema format
#===========================================================

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class FDAGuidanceStatus(str, Enum):
    """FDA guidance document status"""
    DRAFT = "draft"
    FINAL = "final"
    REVISION = "revision"
    WITHDRAWN = "withdrawn"


class FDAOrganization(str, Enum):
    """FDA organizational units"""
    CBER = "CBER"  # Center for Biologics Evaluation and Research
    CDER = "CDER"  # Center for Drug Evaluation and Research
    CDRH = "CDRH"  # Center for Devices and Radiological Health
    CFSAN = "CFSAN"  # Center for Food Safety and Applied Nutrition
    CVM = "CVM"  # Center for Veterinary Medicine
    CTP = "CTP"  # Center for Tobacco Products
    OCR = "OCR"  # Office of Counterterrorism and Emerging Threats
    ORA = "ORA"  # Office of Regulatory Affairs
    OCP = "OCP"  # Office of Clinical Policy
    OTHER = "Other"


@dataclass
class FDAGuidanceDocument:
    """FDA guidance document data model"""
    # Core fields
    document_id: str
    title: str
    url: str
    issue_date: str  # ISO format YYYY-MM-DD

    # Optional fields
    guidance_status: FDAGuidanceStatus = FDAGuidanceStatus.FINAL
    fda_organization: FDAOrganization = FDAOrganization.OTHER
    product_area: Optional[str] = None
    topic: Optional[str] = None
    docket_number: Optional[str] = None
    comment_open_date: Optional[str] = None
    comment_close_date: Optional[str] = None

    # Content
    summary: Optional[str] = None
    pdf_url: Optional[str] = None

    # Metadata
    opens_for_comment: bool = False
    guidance_type: Optional[str] = None  # Guidance, Notice, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "document_id": self.document_id,
            "title": self.title,
            "url": self.url,
            "issue_date": self.issue_date,
            "guidance_status": self.guidance_status.value,
            "fda_organization": self.fda_organization.value,
            "product_area": self.product_area,
            "topic": self.topic,
            "docket_number": self.docket_number,
            "comment_open_date": self.comment_open_date,
            "comment_close_date": self.comment_close_date,
            "summary": self.summary,
            "pdf_url": self.pdf_url,
            "opens_for_comment": self.opens_for_comment,
            "guidance_type": self.guidance_type,
        }

    def to_unified_schema(self) -> Dict[str, Any]:
        """Convert to unified regulatory schema"""
        from processors.regulatory_aggregator import (
            Agency, DocumentType, TherapeuticArea, UnifiedRegulatoryDocument
        )

        # Map FDA organization to agency
        agency = Agency.FDA

        # Detect document type
        doc_type = DocumentType.GUIDANCE
        if self.guidance_status == FDAGuidanceStatus.DRAFT:
            doc_type = DocumentType.GUIDANCE
        elif "notice" in (self.guidance_type or "").lower():
            doc_type = DocumentType.NOTICE

        # Classify therapeutic area from topic and title
        therapeutic_area = self._classify_therapeutic_area()

        # Generate unified document ID
        unified_id = f"REG-FDA-{self.document_id}"

        return UnifiedRegulatoryDocument(
            document_id=unified_id,
            source_agency=agency,
            title=self.title,
            publish_date=self.issue_date,
            url=self.url,
            document_type=doc_type,
            therapeutic_area=therapeutic_area,
            summary=self.summary,
            content=self.summary,  # Use summary as content placeholder
            keywords=[self.topic] if self.topic else [],
            status="active" if self.guidance_status != FDAGuidanceStatus.WITHDRAWN else "withdrawn",
            language="en",
            source_id=self.document_id,
            category=self.product_area,
            subcategory=self.topic,
        ).to_dict()

    def _classify_therapeutic_area(self):
        """Classify therapeutic area from topic/title"""
        from processors.regulatory_aggregator import TherapeuticArea

        text = " ".join(filter(None, [self.topic or "", self.title or "", self.product_area or ""])).lower()

        # Keyword matching for therapeutic areas
        if any(kw in text for kw in ["oncology", "cancer", "tumor", "malignant"]):
            return TherapeuticArea.ONCOLOGY
        elif any(kw in text for kw in ["cardio", "heart", "cardiac", "hypertension"]):
            return TherapeuticArea.CARDIOVASCULAR
        elif any(kw in text for kw in ["neuro", "cns", "brain", "neural"]):
            return TherapeuticArea.NEUROLOGY
        elif any(kw in text for kw in ["infect", "viral", "bacterial", "antibiotic"]):
            return TherapeuticArea.INFECTIOUS_DISEASE
        elif any(kw in text for kw in["pediatric", "children", "infant", "neonatal"]):
            return TherapeuticArea.PEDIATRICS
        elif any(kw in text for kw in ["geriatric", "elderly", "aging"]):
            return TherapeuticArea.GERIATRICS
        elif any(kw in text for kw in ["quality", "gmp", "cmc", "manufacturing"]):
            return TherapeuticArea.QUALITY
        elif any(kw in text for kw in ["clinical", "trial", "study"]):
            return TherapeuticArea.CLINICAL
        elif any(kw in text for kw in ["pharmacol", "drug", "medicinal"]):
            return TherapeuticArea.PHARMACOLOGY
        elif any(kw in text for kw in ["toxic", "safety", "adverse"]):
            return TherapeuticArea.TOXICOLOGY
        elif any(kw in text for kw in ["biologic", "vaccine", "blood", "gene therapy"]):
            return TherapeuticArea.IMMUNOLOGY

        return TherapeuticArea.GENERAL


class FDAGuidanceCollector:
    """
    FDA Guidance Document Collector

    Collects guidance documents from FDA.gov website
    """

    # Base URLs
    BASE_URL = "https://www.fda.gov"
    SEARCH_URL = "https://www.fda.gov/regulatory-information/search-fda-guidance-documents"
    API_SEARCH_URL = "https://www.fda.gov/api/fdaGuidanceDocuments"

    # Request headers
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/html",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Rate limiting
    REQUEST_DELAY = 2  # seconds between requests

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the FDA guidance collector

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.output_dir = Path(self.config.get(
            "output_dir",
            "/root/autodl-tmp/pj-pharmaKG/data/sources/regulatory/FDA/guidance"
        ))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Collection settings
        self.max_documents = self.config.get("max_documents", 1000)
        self.start_date = self.config.get("start_date")  # YYYY-MM-DD format
        self.end_date = self.config.get("end_date")  # YYYY-MM-DD format
        self.organizations = self.config.get("organizations", [])  # List of FDA org codes

        # Statistics
        self.stats = {
            "total_collected": 0,
            "by_status": {},
            "by_organization": {},
            "by_product": {},
            "errors": [],
            "last_collection_date": None,
        }

        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

        # Track collected URLs
        self.collected_urls: Set[str] = set()

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        Make HTTP request with rate limiting and error handling

        Args:
            url: Target URL
            params: Query parameters

        Returns:
            Response object or None if failed
        """
        try:
            time.sleep(self.REQUEST_DELAY)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            self.stats["errors"].append(f"Request error: {str(e)}")
            return None

    def search_guidance_documents(
        self,
        keywords: Optional[str] = None,
        product: Optional[str] = None,
        organization: Optional[str] = None,
        topic: Optional[str] = None,
        draft_or_final: Optional[str] = None,
        limit: int = 100,
    ) -> List[FDAGuidanceDocument]:
        """
        Search for FDA guidance documents

        Args:
            keywords: Search keywords
            product: Product area filter
            organization: FDA organization filter
            topic: Topic filter
            draft_or_final: Status filter (draft/final)
            limit: Maximum results

        Returns:
            List of guidance documents
        """
        logger.info(f"Searching FDA guidance documents: keywords={keywords}, limit={limit}")

        documents = []

        # Try API first
        api_results = self._search_via_api(
            keywords=keywords,
            product=product,
            organization=organization,
            topic=topic,
            draft_or_final=draft_or_final,
            limit=limit,
        )

        if api_results:
            documents.extend(api_results)
            logger.info(f"Found {len(documents)} documents via API")
        else:
            # Fallback to web scraping
            logger.warning("API search failed, falling back to web scraping")
            documents = self._search_via_web(
                keywords=keywords,
                product=product,
                organization=organization,
                topic=topic,
                draft_or_final=draft_or_final,
                limit=limit,
            )

        return documents

    def _search_via_api(
        self,
        keywords: Optional[str] = None,
        product: Optional[str] = None,
        organization: Optional[str] = None,
        topic: Optional[str] = None,
        draft_or_final: Optional[str] = None,
        limit: int = 100,
    ) -> List[FDAGuidanceDocument]:
        """
        Search using FDA API (if available)

        Note: As of 2026, FDA doesn't provide a public API for guidance documents.
        This method is a placeholder for future API implementation.
        """
        logger.warning("FDA guidance API not currently available, using web scraping")
        return []

    def _search_via_web(
        self,
        keywords: Optional[str] = None,
        product: Optional[str] = None,
        organization: Optional[str] = None,
        topic: Optional[str] = None,
        draft_or_final: Optional[str] = None,
        limit: int = 100,
    ) -> List[FDAGuidanceDocument]:
        """
        Search by scraping FDA website

        Args:
            keywords: Search keywords
            product: Product area filter
            organization: FDA organization filter
            topic: Topic filter
            draft_or_final: Status filter
            limit: Maximum results

        Returns:
            List of guidance documents
        """
        documents = []

        try:
            # Build search parameters
            params = {}
            if keywords:
                params["search"] = keywords
            if product:
                params["product"] = product
            if organization:
                params["organization"] = organization
            if topic:
                params["topic"] = topic
            if draft_or_final:
                params["status"] = draft_or_final

            # Make request to search page
            response = self._make_request(self.SEARCH_URL, params=params)
            if not response:
                return documents

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Find guidance document table
            table = soup.find("table", {"aria-label": "Guidance documents"})
            if not table:
                logger.warning("Could not find guidance documents table")
                return documents

            # Parse table rows
            rows = table.find_all("tr")
            for row in rows[:limit]:
                doc = self._parse_table_row(row)
                if doc and doc.url not in self.collected_urls:
                    documents.append(doc)
                    self.collected_urls.add(doc.url)

                    # Check limit
                    if len(documents) >= limit:
                        break

            logger.info(f"Parsed {len(documents)} documents from web search")

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            self.stats["errors"].append(f"Web search error: {str(e)}")

        return documents

    def _parse_table_row(self, row) -> Optional[FDAGuidanceDocument]:
        """
        Parse a table row into a guidance document

        Args:
            row: BeautifulSoup table row element

        Returns:
            FDAGuidanceDocument or None
        """
        try:
            cells = row.find_all("td")
            if len(cells) < 3:
                return None

            # Extract data from cells
            # Cell order: Summary, Document, Issue Date, FDA Org, Topic, Status, Open for Comment, Comment Closing, Docket #, Type

            summary_cell = cells[0]
            document_cell = cells[1]
            date_cell = cells[2] if len(cells) > 2 else None
            org_cell = cells[3] if len(cells) > 3 else None
            topic_cell = cells[4] if len(cells) > 4 else None
            status_cell = cells[5] if len(cells) > 5 else None
            open_comment_cell = cells[6] if len(cells) > 6 else None
            closing_cell = cells[7] if len(cells) > 7 else None
            docket_cell = cells[8] if len(cells) > 8 else None

            # Extract link and title
            link_tag = document_cell.find("a")
            if not link_tag:
                return None

            url = link_tag.get("href", "")
            if url and not url.startswith("http"):
                url = urljoin(self.BASE_URL, url)

            title = link_tag.get_text(strip=True)

            # Extract date
            issue_date = None
            if date_cell:
                date_text = date_cell.get_text(strip=True)
                issue_date = self._parse_date(date_text)

            # Extract organization
            fda_org = FDAOrganization.OTHER
            if org_cell:
                org_text = org_cell.get_text(strip=True)
                fda_org = self._parse_organization(org_text)

            # Extract status
            guidance_status = FDAGuidanceStatus.FINAL
            if status_cell:
                status_text = status_cell.get_text(strip=True).lower()
                if "draft" in status_text:
                    guidance_status = FDAGuidanceStatus.DRAFT

            # Extract topic
            topic = None
            if topic_cell:
                topic = topic_cell.get_text(strip=True)

            # Extract docket number
            docket_number = None
            if docket_cell:
                docket_number = docket_cell.get_text(strip=True)

            # Generate document ID from URL
            doc_id = self._generate_document_id(url, title, issue_date)

            return FDAGuidanceDocument(
                document_id=doc_id,
                title=title,
                url=url,
                issue_date=issue_date or "",
                guidance_status=guidance_status,
                fda_organization=fda_org,
                topic=topic,
                docket_number=docket_number,
            )

        except Exception as e:
            logger.warning(f"Failed to parse table row: {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse date string to ISO format

        Args:
            date_str: Date string

        Returns:
            ISO format date or None
        """
        if not date_str:
            return None

        # Common FDA date formats
        formats = [
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%Y-%m-%d",
            "%B %d, %Y",
            "%b %d, %Y",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _parse_organization(self, org_text: str) -> FDAOrganization:
        """Parse FDA organization from text"""
        org_upper = org_text.upper()

        for org in FDAOrganization:
            if org.value in org_upper:
                return org

        return FDAOrganization.OTHER

    def _generate_document_id(self, url: str, title: str, date: Optional[str]) -> str:
        """Generate unique document ID"""
        # Extract ID from URL if possible
        url_path = urlparse(url).path

        # Try to extract UCM number (FDA document IDs)
        ucm_match = re.search(r'UCM(\d+)', url, re.IGNORECASE)
        if ucm_match:
            return f"UCM{ucm_match.group(1)}"

        # Use hash fallback
        hash_content = f"{url}_{title}_{date or ''}"
        return hashlib.md5(hash_content.encode()).hexdigest()[:12]

    def collect_by_organization(
        self,
        organization: FDAOrganization,
        limit: int = 100,
    ) -> List[FDAGuidanceDocument]:
        """
        Collect all guidance documents from a specific FDA organization

        Args:
            organization: FDA organization
            limit: Maximum documents to collect

        Returns:
            List of guidance documents
        """
        logger.info(f"Collecting guidance documents from {organization.value}")

        documents = self.search_guidance_documents(
            organization=organization.value,
            limit=limit,
        )

        logger.info(f"Collected {len(documents)} documents from {organization.value}")
        return documents

    def collect_by_topic(
        self,
        topic: str,
        limit: int = 100,
    ) -> List[FDAGuidanceDocument]:
        """
        Collect guidance documents by topic

        Args:
            topic: Topic keyword
            limit: Maximum documents to collect

        Returns:
            List of guidance documents
        """
        logger.info(f"Collecting guidance documents for topic: {topic}")

        documents = self.search_guidance_documents(
            topic=topic,
            limit=limit,
        )

        logger.info(f"Collected {len(documents)} documents for topic {topic}")
        return documents

    def collect_recent(
        self,
        days_back: int = 90,
        limit: int = 100,
    ) -> List[FDAGuidanceDocument]:
        """
        Collect recently issued guidance documents

        Args:
            days_back: Number of days to look back
            limit: Maximum documents to collect

        Returns:
            List of guidance documents
        """
        logger.info(f"Collecting recent guidance documents (last {days_back} days)")

        documents = self.search_guidance_documents(
            limit=limit,
        )

        # Filter by date if specified
        if days_back:
            cutoff_date = datetime.now() - __import__("datetime").timedelta(days=days_back)
            documents = [
                doc for doc in documents
                if doc.issue_date and datetime.fromisoformat(doc.issue_date) >= cutoff_date
            ]

        logger.info(f"Collected {len(documents)} recent documents")
        return documents

    def save_documents(
        self,
        documents: List[FDAGuidanceDocument],
        format: str = "json",
        unified_schema: bool = True,
    ) -> Path:
        """
        Save collected documents to file

        Args:
            documents: List of documents to save
            format: Output format (json, csv)
            unified_schema: Save in unified regulatory schema format

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if unified_schema:
            # Convert to unified schema
            data = [doc.to_unified_schema() for doc in documents]
            suffix = "_unified"
        else:
            # Use native format
            data = [doc.to_dict() for doc in documents]
            suffix = ""

        if format == "json":
            filename = f"fda_guidance_{suffix}{timestamp}.json"
            filepath = self.output_dir / filename

            output_data = {
                "metadata": {
                    "source": "FDA",
                    "collected_at": datetime.now().isoformat(),
                    "total_documents": len(documents),
                    "schema": "unified" if unified_schema else "native",
                },
                "documents": data,
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

        elif format == "csv":
            import csv

            filename = f"fda_guidance_{suffix}{timestamp}.csv"
            filepath = self.output_dir / filename

            if data:
                keys = data[0].keys()
                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(data)

        logger.info(f"Saved {len(documents)} documents to {filepath}")

        # Update statistics
        self.stats["total_collected"] += len(documents)
        for doc in documents:
            status = doc.guidance_status.value
            org = doc.fda_organization.value
            product = doc.product_area or "Unknown"

            self.stats["by_status"][status] = self.stats["by_status"].get(status, 0) + 1
            self.stats["by_organization"][org] = self.stats["by_organization"].get(org, 0) + 1
            self.stats["by_product"][product] = self.stats["by_product"].get(product, 0) + 1

        self.stats["last_collection_date"] = datetime.now().isoformat()

        return filepath

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate collection status report

        Returns:
            Status report dictionary
        """
        return {
            "report_generated_at": datetime.now().isoformat(),
            "source": "FDA Guidance Documents",
            "base_url": self.BASE_URL,
            "statistics": self.stats,
            "summary": {
                "total_collected": self.stats["total_collected"],
                "by_status": self.stats["by_status"],
                "by_organization": self.stats["by_organization"],
                "by_product_area": self.stats["by_product"],
                "errors_count": len(self.stats["errors"]),
            },
        }


def collect_fda_guidance(
    keywords: Optional[str] = None,
    organization: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = 100,
    output_dir: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[List[FDAGuidanceDocument], Dict[str, Any]]:
    """
    Convenience function to collect FDA guidance documents

    Args:
        keywords: Search keywords
        organization: FDA organization filter
        topic: Topic filter
        limit: Maximum documents
        output_dir: Output directory
        config: Configuration dictionary

    Returns:
        Tuple of (documents, report)
    """
    collector = FDAGuidanceCollector(config)

    if output_dir:
        collector.output_dir = Path(output_dir)

    # Collect documents
    documents = collector.search_guidance_documents(
        keywords=keywords,
        organization=organization,
        topic=topic,
        limit=limit,
    )

    # Save documents
    if documents:
        collector.save_documents(documents, unified_schema=True)

    # Generate report
    report = collector.generate_report()

    return documents, report


if __name__ == "__main__":
    # Test FDA guidance collector
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    config = {
        "max_documents": 50,
        "output_dir": "/root/autodl-tmp/pj-pharmaKG/data/sources/regulatory/FDA/guidance",
    }

    collector = FDAGuidanceCollector(config)

    print("=== FDA Guidance Document Collector ===\n")

    # Collect recent guidance documents
    print("Collecting recent guidance documents...")
    documents = collector.collect_recent(days_back=90, limit=20)

    print(f"\nCollected {len(documents)} documents")
    for doc in documents[:5]:
        print(f"  - {doc.title[:60]}... ({doc.issue_date})")

    # Save documents
    if documents:
        output_path = collector.save_documents(documents, unified_schema=True)
        print(f"\nSaved to: {output_path}")

    # Generate report
    report = collector.generate_report()
    print(f"\n=== Collection Report ===")
    print(f"Total collected: {report['summary']['total_collected']}")
    print(f"By status: {report['summary']['by_status']}")
    print(f"By organization: {report['summary']['by_organization']}")
