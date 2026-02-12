#===========================================================
# PharmaKG FDA Guidance Document Processor
# Pharmaceutical Knowledge Graph - FDA Guidance Collector
#===========================================================
# Version: v1.0
# Description: FDA guidance document scraper and processor
#              Collects guidance from FDA CBER, CDER, and Oncology
#===========================================================

import hashlib
import json
import logging
import re
import time
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, Union
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus, ProcessingMetrics

logger = logging.getLogger(__name__)


class FDACenter(str, Enum):
    """FDA Center/Office codes"""
    CBER = "CBER"  # Center for Biologics Evaluation and Research
    CDER = "CDER"  # Center for Drug Evaluation and Research
    CDRH = "CDRH"  # Center for Devices and Radiological Health
    OCE = "OCE"  # Oncology Center of Excellence
    GENERAL = "General"  # General/FDA-wide guidances
    OTHER = "Other"


class GuidanceCategory(str, Enum):
    """FDA guidance document categories"""
    # CMC/Manufacturing
    CMC = "CMC"  # Chemistry, Manufacturing, and Controls
    GMP = "GMP"  # Good Manufacturing Practice
    MANUFACTURING = "Manufacturing"
    QUALITY = "Quality"

    # Clinical
    CLINICAL_TRIAL_DESIGN = "Clinical Trial Design"
    BIOSTATISTICS = "Biostatistics"
    GCP = "GCP"  # Good Clinical Practice
    EFFICACY = "Efficacy"

    # Safety/Pharmacology
    BIOANALYTICAL = "Bioanalytical"
    PHARMACOKINETICS = "Pharmacokinetics"
    SAFETY_PHARMACOLOGY = "Safety Pharmacology"
    TOXICOLOGY = "Toxicology"

    # Therapeutic Areas
    ONCOLOGY = "Oncology"
    RARE_DISEASE = "Rare Disease"
    PEDIATRICS = "Pediatrics"
    GERIATRICS = "Geriatrics"

    # Regulatory
    REGULATORY = "Regulatory"
    LABELING = "Labeling"
    POSTMARKET = "Postmarket"

    # Other
    GENERAL = "General"
    OTHER = "Other"


@dataclass
class FDAGuidanceDocument:
    """FDA guidance document data model"""

    # Core fields
    title: str
    url: str
    publish_date: Optional[str] = None
    guidance_status: str = "Final"  # Final, Draft, Retired

    # Classification
    center: FDACenter = FDACenter.OTHER
    category: GuidanceCategory = GuidanceCategory.OTHER
    docket_number: Optional[str] = None

    # Content
    summary: Optional[str] = None
    content: Optional[str] = None
    attachments: List[Dict[str, str]] = field(default_factory=list)

    # Metadata
    open_for_comment: bool = False
    comment_closing_date: Optional[str] = None
    effective_date: Optional[str] = None
    repeal_date: Optional[str] = None

    # Source tracking
    source_id: Optional[str] = None
    source_hash: Optional[str] = None

    # Additional metadata
    keywords: List[str] = field(default_factory=list)
    therapeutic_area: Optional[str] = None
    document_type: str = "guidance"  # guidance, guidance-for-industry, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "title": self.title,
            "url": self.url,
            "publish_date": self.publish_date,
            "guidance_status": self.guidance_status,
            "center": self.center.value,
            "category": self.category.value,
            "docket_number": self.docket_number,
            "summary": self.summary,
            "content": self.content,
            "attachments": self.attachments,
            "open_for_comment": self.open_for_comment,
            "comment_closing_date": self.comment_closing_date,
            "effective_date": self.effective_date,
            "repeal_date": self.repeal_date,
            "source_id": self.source_id,
            "source_hash": self.source_hash,
            "keywords": self.keywords,
            "therapeutic_area": self.therapeutic_area,
            "document_type": self.document_type,
        }


class FDAGuidanceProcessor(BaseProcessor):
    """
    FDA Guidance Document Processor

    Collects guidance documents from:
    - FDA CBER (Biologics)
    - FDA CDER (Drugs)
    - FDA Oncology Center of Excellence

    Features:
    - Web scraping with rate limiting
    - Incremental updates
    - Deduplication
    - Category classification
    """

    PROCESSOR_NAME = "FDA_Guidance_Processor"
    SUPPORTED_FORMATS = ["html", "json", "txt"]
    OUTPUT_SUBDIR = "fda_guidance"

    # FDA URLs
    FDA_GUIDANCE_SEARCH = "https://www.fda.gov/regulatory-information/search-fda-guidance-documents"
    CBER_GUIDANCE_URL = "https://www.fda.gov/vaccines-blood-biologics/guidance-compliance-regulatory-information-biologics/biologics-guidances"
    ONCOLOGY_GUIDANCE_URL = "https://www.fda.gov/about-fda/oncology-center-excellence/oncology-center-excellence-guidance-documents"

    # Request configuration
    REQUEST_DELAY = 2  # seconds between requests
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    USER_AGENT = "Mozilla/5.0 (compatible; PharmaKG-FDA-Collector/1.0; +https://github.com/fchcao/pharmaKG)"

    # Collection limits
    DEFAULT_LOOKBACK_DAYS = 365  # Collect guidance from past year by default

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize FDA guidance processor"""
        super().__init__(config)

        # Collection settings
        self.lookback_days = self.config.get("lookback_days", self.DEFAULT_LOOKBACK_DAYS)
        self.collect_draft = self.config.get("collect_draft", True)
        self.collect_final = self.config.get("collect_final", True)
        self.centers_filter = self.config.get("centers_filter", list(FDACenter))

        # Output directory for FDA guidance
        self.fda_output_dir = self.data_root / "sources" / "regulatory" / "FDA"
        self.fda_output_dir.mkdir(parents=True, exist_ok=True)

        # Deduplication tracking
        self.seen_urls: Set[str] = set()
        self.seen_hashes: Set[str] = set()

        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

    def scan(self, source_path: Union[str, Path]) -> List[Path]:
        """
        Scan for guidance documents (web-based)

        Args:
            source_path: URL or directory path

        Returns:
            List of source URLs (as Path objects for compatibility)
        """
        source_str = str(source_path)

        # If it's a URL, return as single-item list
        if source_str.startswith(("http://", "https://")):
            return [Path(source_str)]

        # Otherwise scan local directory
        source_path = Path(source_path)
        if not source_path.exists():
            logger.warning(f"Source path not found: {source_path}")
            return []

        files = []
        for ext in ["*.html", "*.json", "*.txt"]:
            files.extend(source_path.rglob(ext))

        return files

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract guidance document data

        Args:
            file_path: URL or file path

        Returns:
            Extracted data dictionary
        """
        source_str = str(file_path)

        # If it's a URL, scrape from web
        if source_str.startswith(("http://", "https://")):
            return self._scrape_guidance_page(source_str)

        # Otherwise read from file
        return self._read_guidance_file(file_path)

    def _scrape_guidance_page(self, url: str) -> Dict[str, Any]:
        """Scrape guidance page from FDA website"""
        try:
            time.sleep(self.REQUEST_DELAY)

            response = self.session.get(
                url,
                timeout=self.REQUEST_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")

            # Detect page type and route to appropriate parser
            if "oncology-center-excellence-guidance-documents" in url:
                return self._parse_oncology_guidance_page(soup, url)
            elif "biologics-guidances" in url or "cber" in url.lower():
                return self._parse_cber_guidance_page(soup, url)
            else:
                return self._parse_generic_guidance_page(soup, url)

        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return {}

    def _parse_oncology_guidance_page(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Parse FDA Oncology Center guidance page"""
        guidances = []

        # Find the guidance table
        table = soup.find("table")
        if not table:
            logger.warning(f"No table found on oncology guidance page")
            return {"documents": guidances}

        # Parse table rows
        for row in table.find_all("tr")[1:]:  # Skip header
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            # Extract title and link
            title_cell = cells[0]
            link_tag = title_cell.find("a")
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            url = urljoin(base_url, link_tag.get("href", ""))

            # Extract type and date
            doc_type = cells[1].get_text(strip=True) if len(cells) > 1 else "Unknown"
            date_str = cells[2].get_text(strip=True) if len(cells) > 2 else None

            # Parse date
            publish_date = self._parse_date(date_str) if date_str else None

            # Determine category
            category = self._classify_oncology_guidance(title)

            guidance = FDAGuidanceDocument(
                title=title,
                url=url,
                publish_date=publish_date,
                guidance_status=self._extract_status(title),
                center=FDACenter.OCE,
                category=category,
                document_type="guidance",
            )

            guidances.append(guidance.to_dict())

        return {"documents": guidances}

    def _parse_cber_guidance_page(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Parse FDA CBER guidance page"""
        guidances = []

        # CBER page uses dynamic JavaScript table
        # Look for guidance links in the page
        guidance_links = soup.find_all("a", href=re.compile(r"/regulatory-information/search-fda-guidance-documents/"))

        for link in guidance_links:
            title = link.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            url = urljoin(base_url, link.get("href", ""))

            guidance = FDAGuidanceDocument(
                title=title,
                url=url,
                center=FDACenter.CBER,
                category=self._classify_cber_guidance(title),
                document_type="guidance",
            )

            guidances.append(guidance.to_dict())

        return {"documents": guidances}

    def _parse_generic_guidance_page(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Parse generic FDA guidance page"""
        guidances = []

        # Try to find guidance links
        for link in soup.find_all("a", href=re.compile(r"guidance")):
            title = link.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            full_url = urljoin(url, link.get("href", ""))

            guidance = FDAGuidanceDocument(
                title=title,
                url=full_url,
                center=FDACenter.GENERAL,
                category=GuidanceCategory.OTHER,
                document_type="guidance",
            )

            guidances.append(guidance.to_dict())

        return {"documents": guidances}

    def _read_guidance_file(self, file_path: Path) -> Dict[str, Any]:
        """Read guidance from local file"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Detect file type
            if file_path.suffix == ".json":
                data = json.loads(content)
                if isinstance(data, list):
                    return {"documents": data}
                return data
            else:
                # Text/HTML file
                title = file_path.stem.replace("_", " ").replace("-", " ").title()
                # 读取完整文件内容
                with open(file_path, "r", encoding="utf-8") as f:
                    full_content = f.read()
                # 对于HTML页面，尝试提取完整内容
                if file_path.suffix == ".html":
                    soup = BeautifulSoup(full_content, "html.parser")
                    # 提取body内容
                    body = soup.find("body")
                    if body:
                        full_content = body.get_text()[:10000]
                    else:
                        full_content = full_content[:10000]
                return {
                    "documents": [{
                        "title": title,
                        "url": f"file://{file_path}",
                        "content": full_content,
                    }]
                }
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return {}

    def _classify_oncology_guidance(self, title: str) -> GuidanceCategory:
        """Classify oncology guidance by category"""
        title_lower = title.lower()

        if any(kw in title_lower for kw in ["clinical trial", "study design", "endpoint"]):
            return GuidanceCategory.CLINICAL_TRIAL_DESIGN
        elif any(kw in title_lower for kw in ["dosage", "pharmacokinetic", "pk"]):
            return GuidanceCategory.PHARMACOKINETICS
        elif any(kw in title_lower for kw in ["safety", "toxic", "adverse"]):
            return GuidanceCategory.SAFETY_PHARMACOLOGY
        elif "pediatric" in title_lower:
            return GuidanceCategory.PEDIATRICS
        elif "rare" in title_lower or "orphan" in title_lower:
            return GuidanceCategory.RARE_DISEASE
        else:
            return GuidanceCategory.ONCOLOGY

    def _classify_cber_guidance(self, title: str) -> GuidanceCategory:
        """Classify CBER guidance by category"""
        title_lower = title.lower()

        if any(kw in title_lower for kw in ["cmc", "manufacturing", "production"]):
            return GuidanceCategory.CMC
        elif "gmp" in title_lower:
            return GuidanceCategory.GMP
        elif any(kw in title_lower for kw in ["clinical", "study"]):
            return GuidanceCategory.CLINICAL_TRIAL_DESIGN
        elif any(kw in title_lower for kw in ["bioanalytical", "validation"]):
            return GuidanceCategory.BIOANALYTICAL
        elif "vaccine" in title_lower:
            return GuidanceCategory.OTHER
        else:
            return GuidanceCategory.OTHER

    def _extract_status(self, title: str) -> str:
        """Extract guidance status from title"""
        title_lower = title.lower()
        if "draft" in title_lower:
            return "Draft"
        elif "final" in title_lower:
            return "Final"
        elif "revised" in title_lower or "update" in title_lower:
            return "Revised"
        else:
            return "Final"

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format"""
        if not date_str:
            return None

        # Common FDA date formats
        formats = [
            "%B %Y",  # "December 2025"
            "%b %Y",   # "Dec 2025"
            "%B %d, %Y",  # "December 15, 2025"
            "%Y-%m-%d",  # ISO format
            "%m/%Y",  # "12/2025"
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str.strip(), fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform extracted data to standard format

        Args:
            raw_data: Raw extracted data

        Returns:
            Transformed data with entities and relationships
        """
        documents = raw_data.get("documents", [])

        if not documents:
            return {"entities": [], "relationships": []}

        entities = []
        relationships = []

        for doc in documents:
            # Ensure it's a dict
            if isinstance(doc, FDAGuidanceDocument):
                doc_dict = doc.to_dict()
            else:
                doc_dict = doc

            # Generate hash for deduplication
            if doc_dict.get("content"):
                # 如果有HTML内容，使用前1000字符
                content_for_hash = doc_dict.get("content")[:1000] if doc_dict.get("content") else ""
            else:
                content_for_hash = ""
            content_str = f"{doc_dict.get('title', '')}{doc_dict.get('url', '')}{doc_dict.get('publish_date', '')}{content_for_hash}"
            doc_hash = hashlib.md5(content_str.encode()).hexdigest()
            doc_dict["source_hash"] = doc_hash

            # Check for duplicate
            if doc_hash in self.seen_hashes:
                continue

            self.seen_hashes.add(doc_hash)
            if doc_dict.get("url"):
                self.seen_urls.add(doc_dict["url"])

            # Create guidance entity
            entity = self._create_guidance_entity(doc_dict)
            entities.append(entity)

            # Create category relationships
            category = doc_dict.get("category", "Other")
            relationships.append({
                "source": entity["id"],
                "target": f"REG_CATEGORY_{category.upper()}",
                "type": "HAS_CATEGORY",
                "properties": {
                    "confidence": 0.9,
                }
            })

            # Create center relationships
            center = doc_dict.get("center", "Other")
            relationships.append({
                "source": entity["id"],
                "target": f"REG_AGENCY_FDA_{center.upper()}",
                "type": "ISSUED_BY",
                "properties": {
                    "confidence": 1.0,
                }
            })

        return {
            "entities": entities,
            "relationships": relationships,
        }

    def _create_guidance_entity(self, doc_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Create guidance document entity for knowledge graph"""
        # Generate ID
        doc_id = doc_dict.get("source_id") or f"REG_FDA_{doc_dict.get('source_hash', '')[:8]}"

        return {
            "id": doc_id,
            "type": "RegulatoryGuidance",
            "properties": {
                "title": doc_dict.get("title", ""),
                "url": doc_dict.get("url", ""),
                "publish_date": doc_dict.get("publish_date"),
                "status": doc_dict.get("guidance_status", "Final"),
                "category": doc_dict.get("category", "Other"),
                "center": doc_dict.get("center", "FDA"),
                "docket_number": doc_dict.get("docket_number"),
                "summary": doc_dict.get("summary"),
                "therapeutic_area": doc_dict.get("therapeutic_area"),
                "language": "en",
                "source_agency": "FDA",
            },
            "labels": ["RegulatoryDocument", "Guidance", "FDA"],
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate transformed data

        Args:
            data: Transformed data

        Returns:
            True if valid
        """
        entities = data.get("entities", [])

        if not entities:
            logger.warning("No entities to validate")
            return False

        valid_count = 0
        for entity in entities:
            # Check required fields
            if not entity.get("properties", {}).get("title"):
                logger.warning(f"Entity missing title: {entity.get('id')}")
                continue

            if not entity.get("properties", {}).get("url"):
                logger.warning(f"Entity missing URL: {entity.get('id')}")
                continue

            valid_count += 1

        validation_rate = valid_count / len(entities) if entities else 0
        logger.info(f"Validation: {valid_count}/{len(entities)} entities passed")

        return validation_rate >= 0.5

    def collect_guidance(
        self,
        source_urls: Optional[List[str]] = None,
        max_documents: Optional[int] = None,
    ) -> ProcessingResult:
        """
        Collect FDA guidance documents

        Args:
            source_urls: List of URLs to scrape
            max_documents: Maximum number of documents to collect

        Returns:
            Processing result
        """
        if source_urls is None:
            source_urls = [
                self.ONCOLOGY_GUIDANCE_URL,
                self.CBER_GUIDANCE_URL,
            ]

        logger.info(f"Starting FDA guidance collection from {len(source_urls)} sources")

        # Process each source URL
        all_guidances = []

        for url in source_urls:
            try:
                logger.info(f"Scraping: {url}")
                raw_data = self._scrape_guidance_page(url)

                documents = raw_data.get("documents", [])
                logger.info(f"Found {len(documents)} guidances from {url}")

                all_guidances.extend(documents)

                if max_documents and len(all_guidances) >= max_documents:
                    logger.info(f"Reached max documents limit: {max_documents}")
                    break

            except Exception as e:
                logger.error(f"Failed to collect from {url}: {e}")
                self._errors.append(f"{url}: {str(e)}")

        # Transform to entities
        transformed = self.transform({"documents": all_guidances})

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.fda_output_dir / f"fda_guidance_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "metadata": {
                    "collected_at": timestamp,
                    "source_urls": source_urls,
                    "total_documents": len(all_guidances),
                },
                "documents": all_guidances,
                "entities": transformed.get("entities", []),
                "relationships": transformed.get("relationships", []),
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(all_guidances)} guidances to {output_file}")

        return ProcessingResult(
            status=ProcessingStatus.COMPLETED,
            processor_name=self.PROCESSOR_NAME,
            source_path="FDA Guidance Collection",
            metrics=ProcessingMetrics(
                files_processed=len(all_guidances),
                entities_extracted=len(transformed.get("entities", [])),
                relationships_extracted=len(transformed.get("relationships", [])),
            ),
            entities=transformed.get("entities", []),
            relationships=transformed.get("relationships", []),
            output_path=str(output_file),
        )


def collect_fda_guidance(
    source_urls: Optional[List[str]] = None,
    max_documents: Optional[int] = None,
    config: Optional[Dict[str, Any]] = None,
    use_cache: bool = True,  # 默认使用缓存避免重复采集
) -> ProcessingResult:
    """
    Convenience function to collect FDA guidance documents

    Args:
        source_urls: List of URLs to scrape (default: OCE + CBER)
        max_documents: Maximum number of documents to collect
        config: Processor configuration

    Returns:
        Processing result
    """
    processor = FDAGuidanceProcessor(config)
    return processor.collect_guidance(source_urls, max_documents, use_cache=True)  # 使用缓存避免重复采集


# Key guidance categories to prioritize for collection
PRIORITY_CATEGORIES = {
    # CMC/Manufacturing (highest priority for pharmaceutical development)
    "CMC_Guidance": [
        "chemistry manufacturing and controls",
        "cmc",
        "drug substance",
        "drug product",
        "manufacturing",
        "process validation",
        "stability testing",
    ],

    # Bioanalytical Method Validation (critical for clinical trials)
    "Bioanalytical": [
        "bioanalytical method validation",
        "biomarker",
        "bioanalysis",
        "analytical validation",
    ],

    # Clinical Trial Design (core for drug development)
    "Clinical_Trial_Design": [
        "clinical trial design",
        "clinical trial endpoints",
        "adaptive design",
        "master protocol",
        "basket trial",
        "umbrella trial",
    ],

    # Pharmacokinetics (critical for dosing)
    "Pharmacokinetics": [
        "pharmacokinetics",
        "pk studies",
        "bioavailability",
        "bioequivalence",
        "drug interaction",
    ],

    # Safety Pharmacology (critical for safety assessment)
    "Safety_Pharmacology": [
        "safety pharmacology",
        "toxicology",
        "genotoxicity",
        "carcinogenicity",
        "reproductive toxicology",
    ],

    # Oncology-specific (high therapeutic area priority)
    "Oncology": [
        "oncology",
        "cancer",
        "tumor",
        "malignant",
        "chemotherapy",
        "immunotherapy",
    ],

    # Rare Disease (important for orphan drugs)
    "Rare_Disease": [
        "rare disease",
        "orphan drug",
    ],
}


# Collection schedule recommendations
COLLECTION_SCHEDULE = {
    "full_collection": {
        "frequency": "quarterly",
        "description": "Complete collection of all FDA guidance documents",
        "recommended_months": [1, 4, 7, 10],  # Jan, Apr, Jul, Oct
    },
    "incremental_update": {
        "frequency": "monthly",
        "description": "Collect newly issued guidances in past 30 days",
        "recommended_day": 1,  # First of each month
    },
    "priority_categories": {
        "frequency": "weekly",
        "description": "Monitor priority categories for new guidances",
        "categories": ["CMC", "Bioanalytical", "Clinical Trial Design", "Oncology"],
    },
}


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run FDA guidance collection
    result = collect_fda_guidance(max_documents=100)

    print("\n=== FDA Guidance Collection Results ===")
    print(f"Status: {result.status}")
    print(f"Documents processed: {result.metrics.files_processed}")
    print(f"Entities extracted: {result.metrics.entities_extracted}")
    print(f"Relationships extracted: {result.metrics.relationships_extracted}")
    print(f"Output: {result.output_path}")
