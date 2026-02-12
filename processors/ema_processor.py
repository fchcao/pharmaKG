#===========================================================
# PharmaKG EMA Guidance Processor
# Pharmaceutical Knowledge Graph - EMA Guidance Document Collector
#===========================================================
# Version: v1.0
# Description: Collect regulatory guidance documents from the
#              European Medicines Agency (EMA)
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
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, Union
from urllib.parse import urljoin, urlparse
import hashlib

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# EMA Guidance Categories
class EMAGuidanceCategory(str, Enum):
    """EMA guidance document categories"""
    CLINICAL_TRIALS = "clinical_trials"
    QUALITY = "quality"
    NON_CLINICAL = "non_clinical"
    PHARMACOVIGILANCE = "pharmacovigilance"
    BIOSIMILARS = "biosimilars"
    ADVANCED_THERAPIES = "advanced_therapies"
    PAEDIATRICS = "paediatrics"
    ORPHAN_DRUGS = "orphan_drugs"
    ONCOLOGY = "oncology"
    PHARMACOGENETICS = "pharmacogenetics"
    GENERICS = "generics"
    HERBAL = "herbal"
    VETERINARY = "veterinary"
    POST_AUTHORIZATION = "post_authorization"
    MARKETING_AUTHORIZATION = "marketing_authorization"
    INSPECTIONS = "inspections"
    OTHER = "other"


class EMADocumentType(str, Enum):
    """EMA document types"""
    GUIDELINE = "guideline"
    REFLECTION_PAPER = "reflection_paper"
    GUIDANCE = "guidance"
    QUESTION_ANSWER = "question_answer"
    OPINION = "opinion"
    STATEMENT = "statement"
    CONCEPT_PAPER = "concept_paper"
    REVISED_GUIDELINE = "revised_guideline"
    ADDENDUM = "addendum"
    OTHER = "other"


class EMACommittee(str, Enum):
    """EMA committees and working parties"""
    CHMP = "CHMP"  # Committee for Medicinal Products for Human Use
    CVMP = "CVMP"  # Committee for Medicinal Products for Veterinary Use
    PRAC = "PRAC"  # Pharmacovigilance Risk Assessment Committee
    COMP = "COMP"  # Committee for Orphan Medicinal Products
    PDCO = "PDCO"  # Paediatric Committee
    CAT = "CAT"  # Committee for Advanced Therapies
    HMPC = "HMPC"  # Committee on Herbal Medicinal Products
    OTHER = "OTHER"


@dataclass
class EMAGuidanceDocument:
    """EMA guidance document data model"""
    # Core fields
    ema_id: str  # Unique EMA identifier (e.g., EMA/CHMP/...)
    title: str
    url: str
    publish_date: Optional[str] = None
    last_update: Optional[str] = None

    # Document classification
    document_type: EMADocumentType = EMADocumentType.OTHER
    category: EMAGuidanceCategory = EMAGuidanceCategory.OTHER
    committee: EMACommittee = EMACommittee.OTHER

    # Content fields
    summary: Optional[str] = None
    content: Optional[str] = None
    keywords: List[str] = field(default_factory=list)

    # Related information
    related_documents: List[str] = field(default_factory=list)
    replaces: List[str] = field(default_factory=list)
    replaced_by: Optional[str] = None

    # Status and version
    status: str = "active"  # active, draft, superseded, withdrawn
    version: Optional[str] = None
    effective_date: Optional[str] = None
    superseded_date: Optional[str] = None

    # Additional metadata
    therapeutic_area: Optional[str] = None
    procedure_number: Optional[str] = None
    adoption_date: Optional[str] = None
    comments_deadline: Optional[str] = None

    # Document details
    file_format: str = "pdf"
    file_size: Optional[int] = None
    pages: Optional[int] = None
    language: str = "en"

    # Source tracking
    source_hash: Optional[str] = None
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "ema_id": self.ema_id,
            "title": self.title,
            "url": self.url,
            "publish_date": str(self.publish_date) if self.publish_date else None,
            "last_update": str(self.last_update) if self.last_update else None,
            "document_type": self.document_type.value,
            "category": self.category.value,
            "committee": self.committee.value,
            "summary": self.summary,
            "content": self.content,
            "keywords": self.keywords,
            "related_documents": self.related_documents,
            "replaces": self.replaces,
            "replaced_by": self.replaced_by,
            "status": self.status,
            "version": self.version,
            "effective_date": str(self.effective_date) if self.effective_date else None,
            "superseded_date": str(self.superseded_date) if self.superseded_date else None,
            "therapeutic_area": self.therapeutic_area,
            "procedure_number": self.procedure_number,
            "adoption_date": str(self.adoption_date) if self.adoption_date else None,
            "comments_deadline": str(self.comments_deadline) if self.comments_deadline else None,
            "file_format": self.file_format,
            "file_size": self.file_size,
            "pages": self.pages,
            "language": self.language,
            "source_hash": self.source_hash,
            "scraped_at": self.scraped_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EMAGuidanceDocument":
        """Create from dictionary"""
        return cls(
            ema_id=data["ema_id"],
            title=data["title"],
            url=data["url"],
            publish_date=data.get("publish_date"),
            last_update=data.get("last_update"),
            document_type=EMADocumentType(data.get("document_type", "other")),
            category=EMAGuidanceCategory(data.get("category", "other")),
            committee=EMACommittee(data.get("committee", "OTHER")),
            summary=data.get("summary"),
            content=data.get("content"),
            keywords=data.get("keywords", []),
            related_documents=data.get("related_documents", []),
            replaces=data.get("replaces", []),
            replaced_by=data.get("replaced_by"),
            status=data.get("status", "active"),
            version=data.get("version"),
            effective_date=data.get("effective_date"),
            superseded_date=data.get("superseded_date"),
            therapeutic_area=data.get("therapeutic_area"),
            procedure_number=data.get("procedure_number"),
            adoption_date=data.get("adoption_date"),
            comments_deadline=data.get("comments_deadline"),
            file_format=data.get("file_format", "pdf"),
            file_size=data.get("file_size"),
            pages=data.get("pages"),
            language=data.get("language", "en"),
            source_hash=data.get("source_hash"),
            scraped_at=data.get("scraped_at", datetime.now().isoformat()),
        )


class EMAProcessor:
    """
    EMA Guidance Document Processor

    Collects regulatory guidance documents from EMA (European Medicines Agency).
    Supports web scraping of EMA's public guidance document repository.
    """

    # EMA base URLs
    EMA_BASE_URL = "https://www.ema.europa.eu"
    EMA_SEARCH_URL = "https://www.ema.europa.eu/en/search"
    EMA_SCIENTIFIC_GUIDELINES_URL = "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines"
    EMA_COMMITTEES = {
        "CHMP": "Committee for Medicinal Products for Human Use",
        "CVMP": "Committee for Medicinal Products for Veterinary Use",
        "PRAC": "Pharmacovigilance Risk Assessment Committee",
        "COMP": "Committee for Orphan Medicinal Products",
        "PDCO": "Paediatric Committee",
        "CAT": "Committee for Advanced Therapies",
        "HMPC": "Committee on Herbal Medicinal Products",
    }

    # Key guidance categories to prioritize
    PRIORITY_CATEGORIES = [
        EMAGuidanceCategory.CLINICAL_TRIALS,
        EMAGuidanceCategory.QUALITY,
        EMAGuidanceCategory.PHARMACOVIGILANCE,
        EMAGuidanceCategory.BIOSIMILARS,
        EMAGuidanceCategory.ADVANCED_THERAPIES,
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize EMA processor

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.project_root = Path(__file__).parent.parent
        self.data_root = self.project_root / "data"
        self.logger = logging.getLogger(self.__class__.__name__)

        # Directory paths
        self.sources_dir = self.data_root / "sources" / "regulatory" / "EMA"
        self.output_dir = self.data_root / "processed" / "regulatory" / "EMA"
        self.cache_dir = self.sources_dir / "cache"

        # Create directories
        for dir_path in [self.sources_dir, self.output_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Session configuration
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })

        # Rate limiting
        self.request_delay = self.config.get("request_delay", 2)
        self.max_retries = self.config.get("max_retries", 3)
        self.last_request_time = 0

        # Deduplication
        self.seen_urls: Set[str] = set()
        self.seen_hashes: Set[str] = set()

        # Statistics
        self.stats = {
            "total_documents": 0,
            "by_category": {},
            "by_type": {},
            "by_committee": {},
            "downloads_successful": 0,
            "downloads_failed": 0,
            "errors": [],
        }

        # Load cache if exists
        self._load_cache()

    def _load_cache(self):
        """Load cached document URLs and hashes"""
        cache_file = self.cache_dir / "url_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                    self.seen_urls = set(cache.get("urls", []))
                    self.seen_hashes = set(cache.get("hashes", []))
                self.logger.info(f"Loaded cache: {len(self.seen_urls)} URLs, {len(self.seen_hashes)} hashes")
            except Exception as e:
                self.logger.warning(f"Failed to load cache: {e}")

    def _save_cache(self):
        """Save cache to disk"""
        cache_file = self.cache_dir / "url_cache.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "urls": list(self.seen_urls),
                    "hashes": list(self.seen_hashes),
                    "updated_at": datetime.now().isoformat(),
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save cache: {e}")

    def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """
        Make HTTP request with rate limiting and retry logic

        Args:
            url: URL to request
            method: HTTP method
            **kwargs: Additional arguments for requests

        Returns:
            Response object or None if failed
        """
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)

        for attempt in range(self.max_retries):
            try:
                self.last_request_time = time.time()
                response = self.session.request(method, url, timeout=30, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    self.stats["errors"].append(f"Request failed for {url}: {e}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parse date string to ISO format

        Args:
            date_str: Date string in various formats

        Returns:
            ISO format date string or None
        """
        if not date_str:
            return None

        # Common EMA date formats
        date_formats = [
            "%d %B %Y",  # "15 January 2024"
            "%B %Y",  # "January 2024"
            "%Y-%m-%d",  # "2024-01-15"
            "%d/%m/%Y",  # "15/01/2024"
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.isoformat()
            except ValueError:
                continue

        return None

    def _detect_document_type(self, title: str, url: str) -> EMADocumentType:
        """
        Detect document type from title and URL

        Args:
            title: Document title
            url: Document URL

        Returns:
            Detected document type
        """
        title_lower = title.lower()
        url_lower = url.lower()

        # Check for specific document type keywords
        if "reflection paper" in title_lower or "reflection-paper" in url_lower:
            return EMADocumentType.REFLECTION_PAPER
        elif "question and answer" in title_lower or "question-and-answer" in url_lower or "q&a" in title_lower:
            return EMADocumentType.QUESTION_ANSWER
        elif "concept paper" in title_lower or "concept-paper" in url_lower:
            return EMADocumentType.CONCEPT_PAPER
        elif "guideline" in title_lower:
            if "revised" in title_lower or "revision" in title_lower:
                return EMADocumentType.REVISED_GUIDELINE
            return EMADocumentType.GUIDELINE
        elif "guidance" in title_lower:
            return EMADocumentType.GUIDANCE
        elif "opinion" in title_lower:
            return EMADocumentType.OPINION
        elif "statement" in title_lower:
            return EMADocumentType.STATEMENT
        elif "addendum" in title_lower:
            return EMADocumentType.ADDENDUM

        return EMADocumentType.OTHER

    def _detect_category(self, title: str, summary: Optional[str] = None) -> EMAGuidanceCategory:
        """
        Detect guidance category from title and summary

        Args:
            title: Document title
            summary: Document summary

        Returns:
            Detected category
        """
        text = (title + " " + (summary or "")).lower()

        # Category keyword mappings
        category_keywords = {
            EMAGuidanceCategory.CLINICAL_TRIALS: [
                "clinical trial", "first-in-human", "fi h", "gcp",
                "investigational medicinal product", "imp", "clinical study",
                "临床试验", "人体试验"
            ],
            EMAGuidanceCategory.QUALITY: [
                "quality", "gmp", "gcp", "glp", "validation",
                "manufacturing", "pharmaceutical quality", "impurities",
                "质量", "生产", "验证"
            ],
            EMAGuidanceCategory.NON_CLINICAL: [
                "non-clinical", "preclinical", "toxicology", "pharmacology",
                "animal", "safety pharmacology", "非临床", "毒理"
            ],
            EMAGuidanceCategory.PHARMACOVIGILANCE: [
                "pharmacovigilance", "adverse reaction", "safety monitoring",
                "risk management", "pas", "psur", "药物警戒", "安全"
            ],
            EMAGuidanceCategory.BIOSIMILARS: [
                "biosimilar", "similar biological", "biological medicinal product",
                "生物类似药", "仿生"
            ],
            EMAGuidanceCategory.ADVANCED_THERAPIES: [
                "advanced therapy", "atmp", "gene therapy", "cell therapy",
                "tissue engineered", "先进疗法", "基因治疗", "细胞治疗"
            ],
            EMAGuidanceCategory.PAEDIATRICS: [
                "paediatric", "pediatric", "children", "pip",
                "儿科", "儿童"
            ],
            EMAGuidanceCategory.ORPHAN_DRUGS: [
                "orphan", "rare disease", "罕见病", "孤儿药"
            ],
            EMAGuidanceCategory.ONCOLOGY: [
                "oncology", "cancer", "tumour", "malignant", "肿瘤", "癌"
            ],
            EMAGuidanceCategory.PHARMACOGENETICS: [
                "pharmacogenetic", "pharmacogenomic", "biomarker",
                "药物遗传", "生物标记"
            ],
            EMAGuidanceCategory.GENERICS: [
                "generic", "hybrid", "仿制药"
            ],
            EMAGuidanceCategory.HERBAL: [
                "herbal", "traditional", "phytotherapy", "草药", "中药"
            ],
            EMAGuidanceCategory.VETERINARY: [
                "veterinary", "animal", "兽医"
            ],
        }

        # Score each category
        scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[category] = score

        # Return highest scoring category
        if scores:
            return max(scores, key=scores.get)

        return EMAGuidanceCategory.OTHER

    def _detect_committee(self, title: str, url: str) -> EMACommittee:
        """
        Detect responsible committee from title and URL

        Args:
            title: Document title
            url: Document URL

        Returns:
            Detected committee
        """
        text = (title + " " + url).lower()

        # Check for committee codes
        for committee_code in ["CHMP", "CVMP", "PRAC", "COMP", "PDCO", "CAT", "HMPC"]:
            if committee_code.lower() in text:
                try:
                    return EMACommittee(committee_code)
                except ValueError:
                    pass

        # Check for committee names
        if "human" in text or "human medicine" in text:
            return EMACommittee.CHMP
        elif "veterinary" in text:
            return EMACommittee.CVMP
        elif "pharmacovigilance" in text or "risk assessment" in text:
            return EMACommittee.PRAC
        elif "orphan" in text or "rare disease" in text:
            return EMACommittee.COMP
        elif "paediatric" in text or "pediatric" in text:
            return EMACommittee.PDCO
        elif "advanced therapy" in text or "atmp" in text:
            return EMACommittee.CAT
        elif "herbal" in text or "traditional" in text:
            return EMACommittee.HMPC

        return EMACommittee.OTHER

    def _generate_ema_id(self, url: str, title: str) -> str:
        """
        Generate EMA document ID

        Args:
            url: Document URL
            title: Document title

        Returns:
            EMA document ID
        """
        # Extract ID from URL if possible
        # EMA URLs often contain IDs like: EMA/CHMP/BWP/...
        match = re.search(r'(?:EMA/CHMP/|EMA/CVMP/|EMA/COMP/|/documents/)([^/]+)', url)
        if match:
            return f"EMA-{match.group(1)}".replace("/", "-")

        # Generate hash-based ID
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"EMA-{url_hash}"

    def _extract_document_from_page(self, url: str, soup: BeautifulSoup) -> Optional[EMAGuidanceDocument]:
        """
        Extract document data from EMA page

        Args:
            url: Page URL
            soup: BeautifulSoup object

        Returns:
            EMAGuidanceDocument or None
        """
        try:
            # Extract title
            title_elem = soup.find("h1") or soup.find("title")
            title = title_elem.get_text(strip=True) if title_elem else "Untitled"

            # Extract document ID from URL or page
            ema_id = self._generate_ema_id(url, title)

            # Extract dates
            publish_date = None
            last_update = None

            # Look for date fields
            for label in ["Publish date", "Publication date", "Date", "Last updated"]:
                date_elem = soup.find(string=re.compile(label, re.I))
                if date_elem:
                    date_parent = date_elem.parent
                    if date_parent:
                        date_str = date_parent.get_text(strip=True)
                        parsed_date = self._parse_date(date_str.replace(label, "").strip())
                        if not publish_date:
                            publish_date = parsed_date
                        elif label == "Last updated":
                            last_update = parsed_date

            # Extract summary/content
            summary = None
            content_elem = soup.find("div", class_=["field--name-body", "content", "document-content"])
            if content_elem:
                # Get first paragraph as summary
                first_p = content_elem.find("p")
                if first_p:
                    summary = first_p.get_text(strip=True)

                # Get full content
                content = content_elem.get_text(separator="\n", strip=True)
            else:
                content = None

            # Extract metadata
            document_type = self._detect_document_type(title, url)
            category = self._detect_category(title, summary)
            committee = self._detect_committee(title, url)

            # Extract file information
            file_url = None
            file_format = "pdf"

            # Look for download links
            download_link = soup.find("a", href=re.compile(r'\.(pdf|doc|docx|xls|xlsx)$', re.I))
            if download_link:
                file_url = urljoin(self.EMA_BASE_URL, download_link["href"])
                # Determine file format
                if ".pdf" in file_url.lower():
                    file_format = "pdf"
                elif ".doc" in file_url.lower():
                    file_format = "doc"
                elif ".xls" in file_url.lower():
                    file_format = "xls"

            # Generate content hash for deduplication
            content_hash = hashlib.md5(f"{title}{url}{publish_date}".encode()).hexdigest()

            return EMAGuidanceDocument(
                ema_id=ema_id,
                title=title,
                url=file_url or url,
                publish_date=publish_date,
                last_update=last_update,
                document_type=document_type,
                category=category,
                committee=committee,
                summary=summary,
                content=content[:5000] if content else None,  # Limit content size
                file_format=file_format,
                source_hash=content_hash,
            )

        except Exception as e:
            self.logger.error(f"Failed to extract document from {url}: {e}")
            return None

    def scrape_guidance_list(
        self,
        category: Optional[EMAGuidanceCategory] = None,
        limit: int = 100,
        lookback_days: int = 365
    ) -> Generator[EMAGuidanceDocument, None, None]:
        """
        Scrape EMA guidance list

        Args:
            category: Filter by category (optional)
            limit: Maximum number of documents to collect
            lookback_days: Only collect documents from last N days

        Yields:
            EMAGuidanceDocument objects
        """
        self.logger.info(f"Starting EMA guidance scraping (category={category}, limit={limit})")

        # Build search URL with filters
        params = {
            "type": "guidance",  # Document type filter
            "sort": "date",  # Sort by date
            "items_per_page": min(limit, 50),  # EMA typically returns 50 items max
        }

        # Add category filter if specified
        if category:
            params["category"] = category.value

        # Calculate date threshold
        date_threshold = datetime.now() - timedelta(days=lookback_days)

        collected = 0
        page = 0

        while collected < limit:
            params["page"] = page
            response = self._make_request(
                self.EMA_SEARCH_URL,
                params=params
            )

            if not response:
                self.logger.warning(f"Failed to fetch page {page}")
                break

            soup = BeautifulSoup(response.text, "html.parser")

            # Find document links
            document_links = soup.find_all("a", href=re.compile(r'/en/documents/'))

            if not document_links:
                self.logger.info("No more documents found")
                break

            for link in document_links:
                if collected >= limit:
                    break

                doc_url = urljoin(self.EMA_BASE_URL, link["href"])

                # Check cache
                if doc_url in self.seen_urls:
                    continue

                # Fetch document page
                doc_response = self._make_request(doc_url)
                if not doc_response:
                    continue

                doc_soup = BeautifulSoup(doc_response.text, "html.parser")
                document = self._extract_document_from_page(doc_url, doc_soup)

                if document:
                    # Check date threshold
                    if document.publish_date:
                        try:
                            pub_date = datetime.fromisoformat(document.publish_date)
                            if pub_date < date_threshold:
                                self.logger.info(f"Document outside date range: {document.title}")
                                continue
                        except ValueError:
                            pass

                    # Check duplicates
                    if document.source_hash in self.seen_hashes:
                        continue

                    # Update tracking
                    self.seen_urls.add(doc_url)
                    self.seen_hashes.add(document.source_hash)

                    # Update statistics
                    self.stats["total_documents"] += 1
                    cat = document.category.value
                    self.stats["by_category"][cat] = self.stats["by_category"].get(cat, 0) + 1
                    doc_type = document.document_type.value
                    self.stats["by_type"][doc_type] = self.stats["by_type"].get(doc_type, 0) + 1
                    comm = document.committee.value
                    self.stats["by_committee"][comm] = self.stats["by_committee"].get(comm, 0) + 1

                    collected += 1
                    yield document

            page += 1

            # Check if there are more pages
            next_link = soup.find("a", {"rel": "next"})
            if not next_link:
                break

        # Save cache
        self._save_cache()

        self.logger.info(f"Completed scraping: collected {collected} documents")

    def scrape_by_therapeutic_area(
        self,
        therapeutic_area: str,
        limit: int = 50
    ) -> Generator[EMAGuidanceDocument, None, None]:
        """
        Scrape EMA guidance by therapeutic area

        Args:
            therapeutic_area: Therapeutic area name (e.g., "oncology", "cardiology")
            limit: Maximum number of documents

        Yields:
            EMAGuidanceDocument objects
        """
        self.logger.info(f"Scraping EMA guidance for therapeutic area: {therapeutic_area}")

        # EMA therapeutic area search URL pattern
        search_url = f"{self.EMA_SEARCH_URL}?therapeutic_area={therapeutic_area}"

        collected = 0
        page = 0

        while collected < limit:
            url = f"{search_url}&page={page}"
            response = self._make_request(url)

            if not response:
                break

            soup = BeautifulSoup(response.text, "html.parser")
            document_links = soup.find_all("a", href=re.compile(r'/en/documents/'))

            if not document_links:
                break

            for link in document_links:
                if collected >= limit:
                    break

                doc_url = urljoin(self.EMA_BASE_URL, link["href"])

                if doc_url in self.seen_urls:
                    continue

                doc_response = self._make_request(doc_url)
                if doc_response:
                    doc_soup = BeautifulSoup(doc_response.text, "html.parser")
                    document = self._extract_document_from_page(doc_url, doc_soup)

                    if document:
                        document.therapeutic_area = therapeutic_area
                        self.seen_urls.add(doc_url)
                        collected += 1
                        self.stats["total_documents"] += 1
                        yield document

            page += 1

        self._save_cache()

    def download_document_content(self, document: EMAGuidanceDocument) -> Optional[str]:
        """
        Download full document content (PDF/text)

        Args:
            document: EMA guidance document

        Returns:
            Local file path or None
        """
        if not document.url:
            return None

        # Check if already downloaded
        url_hash = hashlib.md5(document.url.encode()).hexdigest()
        local_path = self.sources_dir / "documents" / f"{url_hash}.{document.file_format}"

        if local_path.exists():
            return str(local_path)

        # Download document
        response = self._make_request(document.url)
        if not response:
            self.stats["downloads_failed"] += 1
            return None

        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(response.content)

            self.stats["downloads_successful"] += 1
            return str(local_path)

        except Exception as e:
            self.logger.error(f"Failed to save document: {e}")
            self.stats["downloads_failed"] += 1
            return None

    def save_documents(self, documents: List[EMAGuidanceDocument], output_file: Optional[str] = None):
        """
        Save collected documents to JSON file

        Args:
            documents: List of EMA guidance documents
            output_file: Output file path (optional)
        """
        if output_file:
            output_path = Path(output_file)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"ema_guidance_{timestamp}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_documents": len(documents),
                "source": "EMA (European Medicines Agency)",
                "categories_covered": list(set(d.category.value for d in documents)),
                "committees_covered": list(set(d.committee.value for d in documents)),
            },
            "statistics": self.stats,
            "documents": [doc.to_dict() for doc in documents],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Saved {len(documents)} documents to {output_path}")
        return output_path

    def generate_collection_plan(self) -> Dict[str, Any]:
        """
        Generate a prioritized collection plan for EMA guidance

        Returns:
            Collection plan dictionary
        """
        plan = {
            "priority_categories": [cat.value for cat in self.PRIORITY_CATEGORIES],
            "collection_schedule": {
                "high_priority": "weekly",  # Clinical trials, quality, pharmacovigilance
                "medium_priority": "monthly",  # Biosimilars, advanced therapies
                "low_priority": "quarterly",  # Other categories
            },
            "therapeutic_areas": [
                "oncology",
                "cardiology",
                "neurology",
                "infectious_diseases",
                "immunology",
                "endocrinology",
                "respiratory",
                "gastroenterology",
                "dermatology",
                "haematology",
            ],
            "document_types": [
                "guideline",
                "reflection_paper",
                "question_answer",
                "guidance",
            ],
            "committees": [
                "CHMP",  # Human medicines
                "CVMP",  # Veterinary medicines
                "PRAC",  # Pharmacovigilance
                "COMP",  # Orphan drugs
                "PDCO",  # Paediatrics
                "CAT",  # Advanced therapies
                "HMPC",  # Herbal medicines
            ],
            "estimated_collection_size": {
                "guidelines_total": 500,  # Approximate total guidelines
                "annual_updates": 50,  # New/revised guidelines per year
                "priority_category_size": 100,  # Per priority category
            },
        }

        return plan

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get collection statistics

        Returns:
            Statistics dictionary
        """
        return {
            "collection_date": datetime.now().isoformat(),
            "total_documents": self.stats["total_documents"],
            "by_category": self.stats["by_category"],
            "by_type": self.stats["by_type"],
            "by_committee": self.stats["by_committee"],
            "downloads": {
                "successful": self.stats["downloads_successful"],
                "failed": self.stats["downloads_failed"],
            },
            "error_count": len(self.stats["errors"]),
            "recent_errors": self.stats["errors"][-10:] if self.stats["errors"] else [],
        }


def collect_ema_guidance(
    category: Optional[str] = None,
    limit: int = 100,
    lookback_days: int = 365,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to collect EMA guidance documents

    Args:
        category: Filter by category (optional)
        limit: Maximum number of documents to collect
        lookback_days: Only collect documents from last N days
        output_file: Output file path (optional)

    Returns:
        Collection results
    """
    processor = EMAProcessor()
    documents = list(processor.scrape_guidance_list(
        category=EMAGuidanceCategory(category) if category else None,
        limit=limit,
        lookback_days=lookback_days
    ))

    output_path = processor.save_documents(documents, output_file)

    return {
        "collected": len(documents),
        "output_file": str(output_path) if output_path else None,
        "statistics": processor.get_statistics(),
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Test EMA processor
    processor = EMAProcessor()

    # Generate collection plan
    plan = processor.generate_collection_plan()
    print("\n=== EMA Guidance Collection Plan ===")
    print(f"Priority categories: {plan['priority_categories']}")
    print(f"Collection schedule: {plan['collection_schedule']}")
    print(f"Therapeutic areas: {plan['therapeutic_areas']}")
    print(f"Committees: {plan['committees']}")

    # Collect sample documents (limit to 10 for testing)
    print("\n=== Collecting EMA Guidance Documents ===")
    results = collect_ema_guidance(limit=10, lookback_days=90)

    print(f"\nCollected: {results['collected']} documents")
    print(f"Output: {results['output_file']}")
    print(f"\nStatistics:")
    for key, value in results['statistics'].items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")
