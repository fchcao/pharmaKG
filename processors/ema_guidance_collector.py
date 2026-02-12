#===========================================================
# PharmaKG EMA Guidance Document Collector
# Pharmaceutical Knowledge Graph - EMA Guidance Collector
#===========================================================
# Version: v1.0
# Description: Collect EMA guidance documents from ema.europa.eu
#              and save them in unified regulatory schema format
#===========================================================

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class EMADocumentType(str, Enum):
    """EMA document types"""
    GUIDELINE = "guideline"
    REFERRAL = "referral"
    SCIENTIFIC_GUIDELINE = "scientific_guideline"
    OPINION = "opinion"
    ASSESSMENT_REPORT = "assessment_report"
    ANNUAL_REPORT = "annual_report"
    POSITION_STATEMENT = "position_statement"
    PROCEDURAL_HELP = "procedural_help"
    QUESTION_ANSWER = "question_answer"
    SAFETY_UPDATE = "safety_update"
    PRODUCT_INFORMATION = "product_information"
    OTHER = "other"


class EMACommittee(str, Enum):
    """EMA Scientific Committees"""
    CHMP = "CHMP"  # Committee for Medicinal Products for Human Use
    CVMP = "CVMP"  # Committee for Medicinal Products for Veterinary Use
    PRAC = "PRAC"  # Pharmacovigilance Risk Assessment Committee
    COMP = "COMP"  # Committee for Orphan Medicinal Products
    CAT = "CAT"  # Committee for Advanced Therapies
    HMPC = "HMPC"  # Committee on Herbal Medicinal Products
    PDCO = "PDCO"  # Paediatric Committee
    OTHER = "Other"


class EMATherapeuticArea(str, Enum):
    """EMA therapeutic areas (MeSH categories)"""
    ONCOLOGY = "oncology"
    ENDOCRINE = "endocrinology"
    CARDIOVASCULAR = "cardiology"
    NEUROLOGY = "neurology"
    INFECTIOUS_DISEASES = "infectious_diseases"
    RESPIRATORY = "respiratory"
    GASTROINTESTINAL = "gastrointestinal"
    DERMATOLOGY = "dermatology"
    HEMATOLOGY = "hematology"
    IMMUNOLOGY = "immunology"
    VACCINES = "vaccines"
    RARE_DISEASE = "rare_disease"
    PAEDIATRICS = "paediatrics"
    PHARMACOLOGY = "pharmacology"
    TOXICOLOGY = "toxicology"
    ANTIINFECTIVES = "anti-infectives"
    CARDIOVASCULAR_HAEMATOLOGY = "cardiovascular_haematology"
    DIABETES = "diabetes"
    OBESITY = "obesity"
    TRANSPLANT = "transplant"
    GENITOURINARY = "genitourinary"
    OPHTHALMOLOGY = "ophthalmology"
    PSYCHIATRY = "psychiatry"
    PAIN = "pain"
    OTHER = "other"


@dataclass
class EMAGuidanceDocument:
    """EMA guidance document data model"""
    # Core fields
    document_id: str
    title: str
    url: str
    publication_date: str  # ISO format YYYY-MM-DD

    # Optional fields
    document_type: EMADocumentType = EMADocumentType.OTHER
    committee: Optional[EMACommittee] = None
    therapeutic_area: Optional[str] = None
    active_substance: Optional[str] = None
    inn: Optional[str] = None  # International Non-Proprietary Name
    procedure_number: Optional[str] = None
    marketing_authorisation_date: Optional[str] = None

    # Content
    summary: Optional[str] = None
    pdf_url: Optional[str] = None

    # Metadata
    status: str = "active"  # active, withdrawn, etc.
    revision: Optional[str] = None
    category: Optional[str] = None  # Corporate, Herbal, Human, Veterinary

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "document_id": self.document_id,
            "title": self.title,
            "url": self.url,
            "publication_date": self.publication_date,
            "document_type": self.document_type.value,
            "committee": self.committee.value if self.committee else None,
            "therapeutic_area": self.therapeutic_area,
            "active_substance": self.active_substance,
            "inn": self.inn,
            "procedure_number": self.procedure_number,
            "marketing_authorisation_date": self.marketing_authorisation_date,
            "summary": self.summary,
            "pdf_url": self.pdf_url,
            "status": self.status,
            "revision": self.revision,
            "category": self.category,
        }

    def to_unified_schema(self) -> Dict[str, Any]:
        """Convert to unified regulatory schema"""
        from processors.regulatory_aggregator import (
            Agency, DocumentType, TherapeuticArea, UnifiedRegulatoryDocument
        )

        # Map EMA therapeutic area to unified area
        therapeutic_area = self._map_therapeutic_area()

        # Detect document type
        doc_type = self._map_document_type()

        # Generate unified document ID
        unified_id = f"REG-EMA-{self.document_id}"

        return UnifiedRegulatoryDocument(
            document_id=unified_id,
            source_agency=Agency.EMA,
            title=self.title,
            publish_date=self.publication_date,
            url=self.url,
            document_type=doc_type,
            therapeutic_area=therapeutic_area,
            summary=self.summary,
            content=self.summary,  # Use summary as content placeholder
            keywords=[self.therapeutic_area] if self.therapeutic_area else [],
            status=self.status,
            language="en",
            source_id=self.document_id,
            category=self.category,
            subcategory=self.committee.value if self.committee else None,
        ).to_dict()

    def _map_therapeutic_area(self):
        """Map EMA therapeutic area to unified schema"""
        # Import here to avoid circular dependency
        from processors.regulatory_aggregator import TherapeuticArea as UnifiedTherapeuticArea

        if not self.therapeutic_area:
            return UnifiedTherapeuticArea.GENERAL

        area_lower = self.therapeutic_area.lower()

        # Direct mappings
        if "oncolog" in area_lower or "cancer" in area_lower:
            return UnifiedTherapeuticArea.ONCOLOGY
        elif "cardio" in area_lower:
            return UnifiedTherapeuticArea.CARDIOVASCULAR
        elif "neuro" in area_lower:
            return UnifiedTherapeuticArea.NEUROLOGY
        elif "infectious" in area_lower:
            return UnifiedTherapeuticArea.INFECTIOUS_DISEASE
        elif "paediatric" in area_lower:
            return UnifiedTherapeuticArea.PEDIATRICS
        elif "rare" in area_lower:
            return UnifiedTherapeuticArea.RARE_DISEASE
        elif "vaccine" in area_lower:
            return UnifiedTherapeuticArea.IMMUNOLOGY
        elif "diabetes" in area_lower or "endocrin" in area_lower:
            return UnifiedTherapeuticArea.ENDOCRINE
        elif "haemat" in area_lower:
            return UnifiedTherapeuticArea.HEMATOLOGY
        elif "immunolog" in area_lower:
            return UnifiedTherapeuticArea.IMMUNOLOGY
        elif "pain" in area_lower:
            return UnifiedTherapeuticArea.PSYCHIATRY  # Closest match

        return UnifiedTherapeuticArea.GENERAL

    def _map_document_type(self):
        """Map EMA document type to unified schema"""
        # Import here to avoid circular dependency
        from processors.regulatory_aggregator import DocumentType as UnifiedDocumentType

        type_lower = self.document_type.value.lower()

        if "guideline" in type_lower:
            return UnifiedDocumentType.GUIDELINE
        elif "opinion" in type_lower:
            return UnifiedDocumentType.OPINION
        elif "question" in type_lower or "answer" in type_lower:
            return UnifiedDocumentType.QUESTION_ANSWER
        elif "assessment" in type_lower or "report" in type_lower:
            return UnifiedDocumentType.GUIDANCE
        elif "position" in type_lower:
            return UnifiedDocumentType.POLICY

        return UnifiedDocumentType.OTHER


class EMAGuidanceCollector:
    """
    EMA Guidance Document Collector

    Collects guidance documents from EMA.europa.eu website
    """

    # Base URLs
    BASE_URL = "https://www.ema.europa.eu"
    SEARCH_URL = "https://www.ema.europa.eu/en/search"
    HUMAN_REGULATORY_URL = "https://www.ema.europa.eu/en/human-regulatory"

    # Request headers
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/html",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Rate limiting
    REQUEST_DELAY = 2  # seconds between requests

    # EMA document type categories
    DOC_TYPES = [
        "Regulatory and procedural guideline",
        "Scientific guideline",
        "Opinion",
        "Assessment report",
        "Annual report",
        "Position statement",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize EMA guidance collector

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.output_dir = Path(self.config.get(
            "output_dir",
            "/root/autodl-tmp/pj-pharmaKG/data/sources/regulatory/EMA/guidance"
        ))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Collection settings
        self.max_documents = self.config.get("max_documents", 1000)
        self.start_date = self.config.get("start_date")  # YYYY-MM-DD format
        self.end_date = self.config.get("end_date")  # YYYY-MM-DD format

        # Statistics
        self.stats = {
            "total_collected": 0,
            "by_document_type": {},
            "by_committee": {},
            "by_therapeutic_area": {},
            "by_category": {},
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
        committee: Optional[str] = None,
        topic: Optional[str] = None,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[EMAGuidanceDocument]:
        """
        Search for EMA guidance documents

        Args:
            keywords: Search keywords
            committee: Committee filter (CHMP, PRAC, etc.)
            topic: Topic/therapeutic area filter
            document_type: Document type filter
            category: Category filter (Human, Herbal, Veterinary)
            limit: Maximum results

        Returns:
            List of guidance documents
        """
        logger.info(f"Searching EMA guidance documents: keywords={keywords}, limit={limit}")

        documents = []

        try:
            # Build search parameters
            # EMA uses a complex form-based search
            # We'll use the search endpoint with query parameters
            params = {}
            if keywords:
                params["search_api_views_fulltext"] = keywords

            # Filter by content type
            params["type"] = "Guidance and information"

            # Additional filters
            if category:
                params["category"] = category

            # Make request
            response = self._make_request(self.SEARCH_URL, params=params)
            if not response:
                return documents

            # Parse HTML response
            soup = BeautifulSoup(response.text, "html.parser")

            # Find document entries
            # EMA search results are in a list format
            items = soup.find_all("div", class_="search-result-item")

            for item in items[:limit]:
                doc = self._parse_search_item(item)
                if doc and doc.url not in self.collected_urls:
                    documents.append(doc)
                    self.collected_urls.add(doc.url)

            logger.info(f"Found {len(documents)} documents via search")

        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.stats["errors"].append(f"Search error: {str(e)}")

        return documents

    def _parse_search_item(self, item) -> Optional[EMAGuidanceDocument]:
        """
        Parse a search result item

        Args:
            item: BeautifulSoup element

        Returns:
            EMAGuidanceDocument or None
        """
        try:
            # Extract title and link
            title_elem = item.find("a")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")
            if url and not url.startswith("http"):
                url = urljoin(self.BASE_URL, url)

            # Extract metadata
            # EMA displays various metadata fields
            date_elem = item.find(class_="date")
            date_text = date_elem.get_text(strip=True) if date_elem else None
            pub_date = self._parse_date(date_text) if date_text else None

            # Extract document type
            type_elem = item.find(class_="document-type")
            doc_type = type_elem.get_text(strip=True) if type_elem else None
            ema_doc_type = self._parse_document_type(doc_type)

            # Extract committee
            committee_elem = item.find(class_="committee")
            committee = self._parse_committee(committee_elem.get_text(strip=True)) if committee_elem else None

            # Extract therapeutic area
            area_elem = item.find(class_="therapeutic-area")
            therapeutic_area = area_elem.get_text(strip=True) if area_elem else None

            # Extract summary/description
            summary_elem = item.find(class_="description")
            summary = summary_elem.get_text(strip=True) if summary_elem else None

            # Generate document ID
            doc_id = self._generate_document_id(url, title, pub_date)

            return EMAGuidanceDocument(
                document_id=doc_id,
                title=title,
                url=url,
                publication_date=pub_date or "",
                document_type=ema_doc_type,
                committee=committee,
                therapeutic_area=therapeutic_area,
                summary=summary,
            )

        except Exception as e:
            logger.warning(f"Failed to parse search item: {e}")
            return None

    def _parse_document_type(self, type_str: Optional[str]) -> EMADocumentType:
        """Parse document type string"""
        if not type_str:
            return EMADocumentType.OTHER

        type_lower = type_str.lower()

        if "guideline" in type_lower:
            return EMADocumentType.GUIDELINE
        elif "referral" in type_lower:
            return EMADocumentType.REFERRAL
        elif "opinion" in type_lower:
            return EMADocumentType.OPINION
        elif "assessment" in type_lower or "report" in type_lower:
            return EMADocumentType.ASSESSMENT_REPORT
        elif "annual" in type_lower:
            return EMADocumentType.ANNUAL_REPORT
        elif "position" in type_lower:
            return EMADocumentType.POSITION_STATEMENT

        return EMADocumentType.OTHER

    def _parse_committee(self, committee_str: Optional[str]) -> Optional[EMACommittee]:
        """Parse committee string"""
        if not committee_str:
            return None

        committee_upper = committee_str.upper()

        for committee in EMACommittee:
            if committee.value in committee_upper:
                return committee

        return EMACommittee.OTHER

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

        # Common EMA date formats
        formats = [
            "%d %B %Y",
            "%d %b %Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _generate_document_id(self, url: str, title: str, date: Optional[str]) -> str:
        """Generate unique document ID"""
        # Extract ID from URL if possible
        url_path = urlparse(url).path

        # Try to extract document number from URL
        # EMA URLs often contain document numbers
        match = re.search(r'/(\d+)', url_path)
        if match:
            return match.group(1)

        # Use hash fallback
        hash_content = f"{url}_{title}_{date or ''}"
        return hashlib.md5(hash_content.encode()).hexdigest()[:12]

    def collect_by_committee(
        self,
        committee: EMACommittee,
        limit: int = 100,
    ) -> List[EMAGuidanceDocument]:
        """
        Collect all guidance documents from a specific committee

        Args:
            committee: EMA committee
            limit: Maximum documents to collect

        Returns:
            List of guidance documents
        """
        logger.info(f"Collecting guidance documents from {committee.value}")

        documents = self.search_guidance_documents(
            committee=committee.value,
            limit=limit,
        )

        logger.info(f"Collected {len(documents)} documents from {committee.value}")
        return documents

    def collect_by_topic(
        self,
        topic: str,
        limit: int = 100,
    ) -> List[EMAGuidanceDocument]:
        """
        Collect guidance documents by topic/therapeutic area

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
    ) -> List[EMAGuidanceDocument]:
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
            cutoff_date = datetime.now() - timedelta(days=days_back)
            documents = [
                doc for doc in documents
                if doc.publication_date and datetime.fromisoformat(doc.publication_date) >= cutoff_date
            ]

        logger.info(f"Collected {len(documents)} recent documents")
        return documents

    def save_documents(
        self,
        documents: List[EMAGuidanceDocument],
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
            filename = f"ema_guidance_{suffix}{timestamp}.json"
            filepath = self.output_dir / filename

            output_data = {
                "metadata": {
                    "source": "EMA",
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

            filename = f"ema_guidance_{suffix}{timestamp}.csv"
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
            doc_type = doc.document_type.value
            committee = doc.committee.value if doc.committee else "Unknown"
            area = doc.therapeutic_area or "Unknown"
            category = doc.category or "Unknown"

            self.stats["by_document_type"][doc_type] = self.stats["by_document_type"].get(doc_type, 0) + 1
            self.stats["by_committee"][committee] = self.stats["by_committee"].get(committee, 0) + 1
            self.stats["by_therapeutic_area"][area] = self.stats["by_therapeutic_area"].get(area, 0) + 1
            self.stats["by_category"][category] = self.stats["by_category"].get(category, 0) + 1

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
            "source": "EMA Guidance Documents",
            "base_url": self.BASE_URL,
            "statistics": self.stats,
            "summary": {
                "total_collected": self.stats["total_collected"],
                "by_document_type": self.stats["by_document_type"],
                "by_committee": self.stats["by_committee"],
                "by_therapeutic_area": self.stats["by_therapeutic_area"],
                "by_category": self.stats["by_category"],
                "errors_count": len(self.stats["errors"]),
            },
        }


def collect_ema_guidance(
    keywords: Optional[str] = None,
    committee: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = 100,
    output_dir: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[List[EMAGuidanceDocument], Dict[str, Any]]:
    """
    Convenience function to collect EMA guidance documents

    Args:
        keywords: Search keywords
        committee: Committee filter
        topic: Topic filter
        limit: Maximum documents
        output_dir: Output directory
        config: Configuration dictionary

    Returns:
        Tuple of (documents, report)
    """
    collector = EMAGuidanceCollector(config)

    if output_dir:
        collector.output_dir = Path(output_dir)

    # Collect documents
    documents = collector.search_guidance_documents(
        keywords=keywords,
        committee=committee,
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
    # Test EMA guidance collector
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    config = {
        "max_documents": 50,
        "output_dir": "/root/autodl-tmp/pj-pharmaKG/data/sources/regulatory/EMA/guidance",
    }

    collector = EMAGuidanceCollector(config)

    print("=== EMA Guidance Document Collector ===\n")

    # Collect recent guidance documents
    print("Collecting recent guidance documents...")
    documents = collector.collect_recent(days_back=90, limit=20)

    print(f"\nCollected {len(documents)} documents")
    for doc in documents[:5]:
        print(f"  - {doc.title[:60]}... ({doc.publication_date})")

    # Save documents
    if documents:
        output_path = collector.save_documents(documents, unified_schema=True)
        print(f"\nSaved to: {output_path}")

    # Generate report
    report = collector.generate_report()
    print(f"\n=== Collection Report ===")
    print(f"Total collected: {report['summary']['total_collected']}")
    print(f"By document type: {report['summary']['by_document_type']}")
    print(f"By committee: {report['summary']['by_committee']}")
