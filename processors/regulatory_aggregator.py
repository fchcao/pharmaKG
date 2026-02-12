#===========================================================
# PharmaKG Regulatory Data Aggregator
# Pharmaceutical Knowledge Graph - Regulatory Data Aggregator
#===========================================================
# Version: v1.0
# Description: Aggregate and merge regulatory guidance documents
#              from multiple agencies (FDA, EMA, NMPA, CDE, etc.)
#===========================================================

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class Agency(str, Enum):
    """Regulatory agency codes"""
    FDA = "FDA"
    EMA = "EMA"
    NMPA = "NMPA"
    CDE = "CDE"
    PMDA = "PMDA"
    HEALTH_CANADA = "HealthCanada"
    TGA = "TGA"
    ICH = "ICH"
    OTHER = "Other"


class DocumentType(str, Enum):
    """Regulatory document types"""
    GUIDANCE = "guidance"
    REGULATION = "regulation"
    POLICY = "policy"
    STANDARD = "standard"
    GUIDELINE = "guideline"
    NOTICE = "notice"
    OPINION = "opinion"
    QUESTION_ANSWER = "qa"
    PROTOCOL = "protocol"
    OTHER = "other"


class TherapeuticArea(str, Enum):
    """Therapeutic area classifications"""
    ONCOLOGY = "oncology"
    CARDIOVASCULAR = "cardiovascular"
    NEUROLOGY = "neurology"
    INFECTIOUS_DISEASE = "infectious_disease"
    RESPIRATORY = "respiratory"
    GASTROINTESTINAL = "gastrointestinal"
    ENDOCRINE = "endocrine"
    DERMATOLOGY = "dermatology"
    HEMATOLOGY = "hematology"
    IMMUNOLOGY = "immunology"
    NEPHROLOGY = "nephrology"
    RHEUMATOLOGY = "rheumatology"
    PSYCHIATRY = "psychiatry"
    PEDIATRICS = "pediatrics"
    GERIATRICS = "geriatrics"
    WOMENS_HEALTH = "womens_health"
    ORPHAN_DISEASE = "orphan_disease"
    RARE_DISEASE = "rare_disease"
    GENERAL = "general"
    QUALITY = "quality"
    MANUFACTURING = "manufacturing"
    CLINICAL = "clinical"
    PHARMACOLOGY = "pharmacology"
    TOXICOLOGY = "toxicology"
    OTHER = "other"


@dataclass
class ValidationResult:
    """Data validation result"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    score: float = 0.0  # 0.0 to 1.0


@dataclass
class UnifiedRegulatoryDocument:
    """Unified regulatory document schema"""
    # Required fields
    document_id: str  # Unique identifier (e.g., "REG-FDA-2025-001")
    source_agency: Agency  # Agency code
    title: str  # Document title
    publish_date: Optional[str]  # ISO format date (YYYY-MM-DD)
    url: str  # Source URL

    # Optional fields
    document_type: DocumentType = DocumentType.OTHER
    therapeutic_area: TherapeuticArea = TherapeuticArea.GENERAL
    summary: Optional[str] = None
    content: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    related_documents: List[str] = field(default_factory=list)
    attachments: List[Dict[str, str]] = field(default_factory=list)

    # Metadata
    effective_date: Optional[str] = None
    repeal_date: Optional[str] = None
    status: str = "active"  # active, repealed, draft, withdrawn
    version: Optional[str] = None
    language: str = "en"  # en, zh, ja, etc.
    file_format: str = "txt"

    # Source tracking
    source_id: Optional[str] = None  # Original ID from source
    source_hash: Optional[str] = None  # Content hash for deduplication

    # Classification
    category: Optional[str] = None  # Broad category
    subcategory: Optional[str] = None  # Specific subcategory

    # Quality metrics
    validation_score: float = 0.0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "document_id": self.document_id,
            "source_agency": self.source_agency.value,
            "title": self.title,
            "publish_date": self.publish_date,
            "url": self.url,
            "document_type": self.document_type.value,
            "therapeutic_area": self.therapeutic_area.value,
            "summary": self.summary,
            "content": self.content,
            "keywords": self.keywords,
            "related_documents": self.related_documents,
            "attachments": self.attachments,
            "effective_date": self.effective_date,
            "repeal_date": self.repeal_date,
            "status": self.status,
            "version": self.version,
            "language": self.language,
            "file_format": self.file_format,
            "source_id": self.source_id,
            "source_hash": self.source_hash,
            "category": self.category,
            "subcategory": self.subcategory,
            "validation_score": self.validation_score,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedRegulatoryDocument":
        """Create from dictionary"""
        # Convert enum strings to enums
        agency = Agency(data.get("source_agency", "Other"))
        doc_type = DocumentType(data.get("document_type", "other"))
        area = TherapeuticArea(data.get("therapeutic_area", "general"))

        return cls(
            document_id=data["document_id"],
            source_agency=agency,
            title=data["title"],
            publish_date=data.get("publish_date"),
            url=data["url"],
            document_type=doc_type,
            therapeutic_area=area,
            summary=data.get("summary"),
            content=data.get("content"),
            keywords=data.get("keywords", []),
            related_documents=data.get("related_documents", []),
            attachments=data.get("attachments", []),
            effective_date=data.get("effective_date"),
            repeal_date=data.get("repeal_date"),
            status=data.get("status", "active"),
            version=data.get("version"),
            language=data.get("language", "en"),
            file_format=data.get("file_format", "txt"),
            source_id=data.get("source_id"),
            source_hash=data.get("source_hash"),
            category=data.get("category"),
            subcategory=data.get("subcategory"),
            validation_score=data.get("validation_score", 0.0),
            last_updated=data.get("last_updated", datetime.now().isoformat()),
        )


class RegulatoryAggregator:
    """
    Regulatory Data Aggregator

    Merges regulatory documents from multiple agencies into a unified schema.
    Provides deduplication, classification, and quality validation.
    """

    # Required fields for validation
    REQUIRED_FIELDS = ["document_id", "source_agency", "title", "url"]

    # Optional but recommended fields
    RECOMMENDED_FIELDS = ["publish_date", "document_type", "therapeutic_area"]

    # Therapeutic area keywords mapping
    THERAPEUTIC_KEYWORDS = {
        TherapeuticArea.ONCOLOGY: ["cancer", "tumor", "oncology", "carcinoma", "malignant", "化疗", "肿瘤", "癌"],
        TherapeuticArea.CARDIOVASCULAR: ["cardio", "heart", "vascular", "hypertension", "cardiac", "心血管", "心脏"],
        TherapeuticArea.NEUROLOGY: ["neuro", "brain", "cns", "neural", "神经", "脑", "中枢神经"],
        TherapeuticArea.INFECTIOUS_DISEASE: ["infect", "viral", "bacterial", "antibiotic", "antiviral", "感染", "抗菌", "抗病毒"],
        TherapeuticArea.RESPIRATORY: ["respiratory", "pulmonary", "lung", "asthma", "呼吸", "肺"],
        TherapeuticArea.GASTROINTESTINAL: ["gi", "gastro", "digestive", "intestinal", "胃肠", "消化"],
        TherapeuticArea.ENDOCRINE: ["endocrine", "diabetes", "thyroid", "hormone", "内分泌", "糖尿病", "甲状腺"],
        TherapeuticArea.DERMATOLOGY: ["dermat", "skin", "cutaneous", "皮肤"],
        TherapeuticArea.HEMATOLOGY: ["hemat", "blood", "anemia", "血液"],
        TherapeuticArea.IMMUNOLOGY: ["immun", "vaccine", "allergy", "免疫", "疫苗", "过敏"],
        TherapeuticArea.PEDIATRICS: ["pediatric", "children", "infant", "儿科", "儿童", "婴儿"],
        TherapeuticArea.GERIATRICS: ["geriatric", "elderly", "老年"],
        TherapeuticArea.QUALITY: ["quality", "gmp", "validation", "compliance", "质量", "验证"],
        TherapeuticArea.MANUFACTURING: ["manufacturing", "production", "facility", "equipment", "生产", "制造", "设施"],
        TherapeuticArea.CLINICAL: ["clinical", "trial", "study", "investigational", "临床", "试验"],
        TherapeuticArea.PHARMACOLOGY: ["pharmac", "drug", "medicinal", "药理", "药物"],
        TherapeuticArea.TOXICOLOGY: ["toxic", "safety", "adverse", "毒理", "安全", "不良"],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the aggregator

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.data_root = Path(__file__).parent.parent / "data" / "sources" / "regulatory"
        self.output_dir = Path(__file__).parent.parent / "data" / "processed" / "regulatory_aggregated"

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            "total_documents": 0,
            "by_agency": {},
            "by_type": {},
            "by_area": {},
            "duplicates_removed": 0,
            "validation_passed": 0,
            "validation_failed": 0,
            "warnings": [],
        }

        # Deduplication tracking
        self.seen_hashes: Set[str] = set()
        self.seen_urls: Set[str] = set()

        # Document mapping for relationship tracking
        self.title_to_ids: Dict[str, List[str]] = {}

    def generate_document_id(
        self,
        agency: Agency,
        source_id: Optional[str] = None,
        title: Optional[str] = None,
        url: Optional[str] = None,
    ) -> str:
        """
        Generate a unique document ID

        Args:
            agency: Source agency
            source_id: Original source ID
            title: Document title
            url: Source URL

        Returns:
            Unique document ID
        """
        # Use source_id if available
        if source_id:
            return f"REG-{agency.value.upper()}-{source_id}"

        # Generate from URL
        if url:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            return f"REG-{agency.value.upper()}-{url_hash}"

        # Generate from title
        if title:
            title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
            return f"REG-{agency.value.upper()}-{title_hash}"

        return f"REG-{agency.value.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def detect_agency(self, source_data: Dict[str, Any]) -> Agency:
        """
        Detect agency from source data

        Args:
            source_data: Raw document data

        Returns:
            Detected agency
        """
        # Check explicit agency field
        if "source_agency" in source_data:
            agency_str = source_data["source_agency"]
            try:
                return Agency(agency_str)
            except ValueError:
                pass

        # Check URL patterns
        url = source_data.get("url", "")
        if "fda.gov" in url.lower():
            return Agency.FDA
        elif "ema.europa.eu" in url.lower():
            return Agency.EMA
        elif "nmpa.gov.cn" in url.lower() or "cde.org.cn" in url.lower():
            if "cde" in url.lower():
                return Agency.CDE
            return Agency.NMPA
        elif "pmda.go.jp" in url.lower():
            return Agency.PMDA
        elif "ich.org" in url.lower():
            return Agency.ICH

        # Check organization field
        organization = source_data.get("organization", "").lower()
        if "fda" in organization:
            return Agency.FDA
        elif "ema" in organization:
            return Agency.EMA
        elif "nmpa" in organization or "药监局" in organization:
            return Agency.NMPA
        elif "cde" in organization or "审评" in organization:
            return Agency.CDE

        # Check path hints
        for key, value in source_data.items():
            if isinstance(value, str):
                if "fda" in value.lower() and "www.fda.gov" in value.lower():
                    return Agency.FDA
                elif "ema" in value.lower() and "ema.europa" in value.lower():
                    return Agency.EMA

        return Agency.OTHER

    def detect_document_type(self, source_data: Dict[str, Any]) -> DocumentType:
        """
        Detect document type from source data

        Args:
            source_data: Raw document data

        Returns:
            Detected document type
        """
        title = source_data.get("title", "").lower()
        category = source_data.get("category", "").lower()
        url = source_data.get("url", "").lower()

        # Check for guidance
        if any(keyword in title or keyword in url for keyword in ["guidance", "guide", "指导原则", "指南"]):
            return DocumentType.GUIDANCE

        # Check for regulation
        if any(keyword in title or keyword in category for keyword in ["regulation", "regulatory", "法规", "条例"]):
            return DocumentType.REGULATION

        # Check for standard
        if any(keyword in title or keyword in category for keyword in ["standard", "标准"]):
            return DocumentType.STANDARD

        # Check for guideline
        if any(keyword in title for keyword in ["guideline", "line"]):
            return DocumentType.GUIDELINE

        # Check for policy
        if any(keyword in title for keyword in ["policy", "政策"]):
            return DocumentType.POLICY

        # Check for notice
        if any(keyword in title for keyword in ["notice", "通告", "公告"]):
            return DocumentType.NOTICE

        # Check for Q&A
        if any(keyword in title for keyword in ["q&a", "question", "faq", "问答"]):
            return DocumentType.QUESTION_ANSWER

        # Check for opinion
        if any(keyword in title for keyword in ["opinion", "意见"]):
            return DocumentType.OPINION

        return DocumentType.OTHER

    def classify_therapeutic_area(self, source_data: Dict[str, Any]) -> TherapeuticArea:
        """
        Classify document by therapeutic area

        Args:
            source_data: Raw document data

        Returns:
            Classified therapeutic area
        """
        title = source_data.get("title", "").lower()
        summary = source_data.get("summary", "").lower()
        content = source_data.get("content", "").lower()
        keywords = [k.lower() for k in source_data.get("keywords", [])]
        subject_words = [k.lower() for k in source_data.get("subject_words", [])]

        # Combine all text for analysis
        text = " ".join([title, summary, content] + keywords + subject_words)

        # Score each area
        scores = {}
        for area, area_keywords in self.THERAPEUTIC_KEYWORDS.items():
            score = sum(1 for kw in area_keywords if kw in text)
            if score > 0:
                scores[area] = score

        # Return highest scoring area, or GENERAL if no match
        if scores:
            return max(scores, key=scores.get)

        return TherapeuticArea.GENERAL

    def generate_content_hash(self, source_data: Dict[str, Any]) -> str:
        """
        Generate content hash for deduplication

        Args:
            source_data: Raw document data

        Returns:
            MD5 hash of key content fields
        """
        # Fields to include in hash
        hash_fields = ["title", "url", "publish_date"]

        hash_content = []
        for field in hash_fields:
            value = source_data.get(field, "")
            # Convert to string safely (handles lists, dicts, etc.)
            if isinstance(value, (list, dict)):
                value = json.dumps(value, sort_keys=True)
            hash_content.append(str(value))

        # Add content sample if available
        content = source_data.get("content", "")
        if content:
            # Use first 500 chars for content matching
            content_str = str(content)[:500] if not isinstance(content, str) else content[:500]
            hash_content.append(content_str)

        hash_str = "|".join(hash_content)
        return hashlib.md5(hash_str.encode()).hexdigest()

    def is_duplicate(self, source_data: Dict[str, Any]) -> bool:
        """
        Check if document is a duplicate

        Args:
            source_data: Raw document data

        Returns:
            True if duplicate detected
        """
        url = source_data.get("url", "")
        content_hash = self.generate_content_hash(source_data)

        # Check URL
        if url and url in self.seen_urls:
            return True

        # Check content hash
        if content_hash in self.seen_hashes:
            return True

        # Check for similar titles (same title, same date)
        title = source_data.get("title", "")
        date = source_data.get("publish_date", "")

        if title and title in self.title_to_ids:
            for existing_id in self.title_to_ids[title]:
                # Same title within 7 days is likely duplicate
                # (This is a simplification; could use fuzzy matching)
                pass

        return False

    def validate_document(self, doc: UnifiedRegulatoryDocument) -> ValidationResult:
        """
        Validate a unified document

        Args:
            doc: Unified document

        Returns:
            Validation result
        """
        errors = []
        warnings = []
        missing_fields = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            value = getattr(doc, field, None)
            if not value:
                missing_fields.append(field)

        # Validate URL
        if doc.url:
            try:
                parsed = urlparse(doc.url)
                if not parsed.scheme or not parsed.netloc:
                    errors.append("Invalid URL format")
            except Exception:
                errors.append("Invalid URL")

        # Validate date
        if doc.publish_date:
            try:
                datetime.fromisoformat(doc.publish_date.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"Invalid date format: {doc.publish_date}")

        # Check recommended fields
        for field in self.RECOMMENDED_FIELDS:
            value = getattr(doc, field, None)
            if not value:
                warnings.append(f"Missing recommended field: {field}")

        # Check content length
        if doc.content and len(doc.content) < 50:
            warnings.append("Content is very short")

        # Calculate validation score
        total_fields = len(self.REQUIRED_FIELDS) + len(self.RECOMMENDED_FIELDS)
        filled_required = sum(1 for f in self.REQUIRED_FIELDS if getattr(doc, f, None))
        filled_recommended = sum(1 for f in self.RECOMMENDED_FIELDS if getattr(doc, f, None))
        score = (filled_required * 2 + filled_recommended) / (total_fields + len(self.REQUIRED_FIELDS))

        return ValidationResult(
            is_valid=len(errors) == 0 and len(missing_fields) == 0,
            errors=errors,
            warnings=warnings,
            missing_fields=missing_fields,
            score=min(score, 1.0),
        )

    def normalize_fda_document(self, source_data: Dict[str, Any]) -> UnifiedRegulatoryDocument:
        """Normalize FDA document to unified schema"""
        agency = Agency.FDA

        # Extract title (try multiple fields)
        title = (
            source_data.get("title") or
            source_data.get("title_cn") or
            source_data.get("title_en") or
            "Untitled"
        )

        # Extract date
        publish_date = source_data.get("publish_date") or source_data.get("date")

        doc_id = self.generate_document_id(
            agency=agency,
            source_id=source_data.get("id"),
            title=title,
            url=source_data.get("url", "")
        )

        return UnifiedRegulatoryDocument(
            document_id=doc_id,
            source_agency=agency,
            title=title,
            publish_date=publish_date,
            url=source_data.get("url", ""),
            document_type=self.detect_document_type(source_data),
            therapeutic_area=self.classify_therapeutic_area(source_data),
            summary=source_data.get("summary"),
            content=source_data.get("content"),
            keywords=source_data.get("keywords", []),
            attachments=source_data.get("attachments", []),
            status=source_data.get("status", "active"),
            language="en",
            source_id=source_data.get("id"),
            source_hash=self.generate_content_hash(source_data),
        )

    def normalize_nmpa_document(self, source_data: Dict[str, Any]) -> UnifiedRegulatoryDocument:
        """Normalize NMPA document to unified schema"""
        # Detect if CDE
        is_cde = "cde" in source_data.get("url", "").lower() or "cde" in source_data.get("source", "").lower()
        agency = Agency.CDE if is_cde else Agency.NMPA

        # Extract title
        title = (
            source_data.get("title") or
            source_data.get("title_cn") or
            source_data.get("title_p") or
            "Untitled"
        )

        # Extract dates
        publish_date = source_data.get("publish_date") or source_data.get("offical_release_date")
        effective_date = source_data.get("effective_date")
        repeal_date = source_data.get("repeal_date") or source_data.get("abolish_date")

        doc_id = self.generate_document_id(
            agency=agency,
            source_id=source_data.get("page_id") or source_data.get("id"),
            title=title,
            url=source_data.get("url", "")
        )

        # Determine status from organization/date
        status = "active"
        if repeal_date:
            status = "repealed"
        elif source_data.get("status") == "N/A":
            status = "draft"

        return UnifiedRegulatoryDocument(
            document_id=doc_id,
            source_agency=agency,
            title=title,
            publish_date=publish_date,
            url=source_data.get("url", ""),
            document_type=self.detect_document_type(source_data),
            therapeutic_area=self.classify_therapeutic_area(source_data),
            summary=source_data.get("summary"),
            content=source_data.get("content"),
            keywords=source_data.get("subject_words", source_data.get("keywords", [])),
            attachments=source_data.get("attachments", []),
            effective_date=effective_date,
            repeal_date=repeal_date,
            status=status,
            language="zh",
            source_id=source_data.get("page_id") or source_data.get("id"),
            source_hash=self.generate_content_hash(source_data),
        )

    def normalize_document(self, source_data: Dict[str, Any]) -> Optional[UnifiedRegulatoryDocument]:
        """
        Normalize document from any source to unified schema

        Args:
            source_data: Raw document data

        Returns:
            Unified document or None if invalid
        """
        # Detect agency
        agency = self.detect_agency(source_data)

        # Route to appropriate normalizer
        if agency == Agency.FDA:
            return self.normalize_fda_document(source_data)
        elif agency in [Agency.NMPA, Agency.CDE]:
            return self.normalize_nmpa_document(source_data)

        # Generic normalization for other agencies
        title = (
            source_data.get("title") or
            source_data.get("title_cn") or
            source_data.get("title_en") or
            "Untitled"
        )

        doc_id = self.generate_document_id(
            agency=agency,
            source_id=source_data.get("id"),
            title=title,
            url=source_data.get("url", "")
        )

        return UnifiedRegulatoryDocument(
            document_id=doc_id,
            source_agency=agency,
            title=title,
            publish_date=source_data.get("publish_date"),
            url=source_data.get("url", ""),
            document_type=self.detect_document_type(source_data),
            therapeutic_area=self.classify_therapeutic_area(source_data),
            summary=source_data.get("summary"),
            content=source_data.get("content"),
            keywords=source_data.get("keywords", []),
            attachments=source_data.get("attachments", []),
            source_id=source_data.get("id"),
            source_hash=self.generate_content_hash(source_data),
        )

    def load_source_data(self, source_dir: str) -> List[Dict[str, Any]]:
        """
        Load source data from directory

        Args:
            source_dir: Source directory path

        Returns:
            List of raw documents
        """
        source_path = Path(source_dir)
        documents = []

        # Load JSON files
        for json_file in source_path.rglob("*.json"):
            # Skip metadata files
            if json_file.name.startswith(".") or "scrape_progress" in json_file.name:
                continue

            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        documents.extend(data)
                    elif isinstance(data, dict):
                        documents.append(data)
            except Exception as e:
                logger.warning(f"Failed to load {json_file}: {e}")
                self.stats["warnings"].append(f"Load error: {json_file}")

        # Load text files (FDA guidance format)
        for txt_file in source_path.rglob("*.txt"):
            if txt_file.name.startswith("."):
                continue

            try:
                with open(txt_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Parse title from first line
                lines = content.split("\n")
                title = lines[0].strip() if lines else txt_file.stem

                documents.append({
                    "title": title,
                    "content": content,
                    "url": f"file://{txt_file}",
                    "file_format": "txt",
                })
            except Exception as e:
                logger.warning(f"Failed to load {txt_file}: {e}")
                self.stats["warnings"].append(f"Load error: {txt_file}")

        logger.info(f"Loaded {len(documents)} documents from {source_dir}")
        return documents

    def process_directory(self, source_dir: str) -> List[UnifiedRegulatoryDocument]:
        """
        Process all documents in a directory

        Args:
            source_dir: Source directory path

        Returns:
            List of unified documents
        """
        source_data = self.load_source_data(source_dir)
        unified_docs = []

        for raw_doc in source_data:
            # Check for duplicates
            if self.is_duplicate(raw_doc):
                self.stats["duplicates_removed"] += 1
                continue

            # Normalize document
            try:
                unified = self.normalize_document(raw_doc)
                if not unified:
                    continue

                # Validate document
                validation = self.validate_document(unified)
                unified.validation_score = validation.score

                if validation.is_valid:
                    self.stats["validation_passed"] += 1
                else:
                    self.stats["validation_failed"] += 1
                    if validation.errors:
                        logger.warning(f"Validation errors for {unified.document_id}: {validation.errors}")

                # Track for deduplication
                self.seen_urls.add(unified.url)
                self.seen_hashes.add(unified.source_hash or "")

                if unified.title not in self.title_to_ids:
                    self.title_to_ids[unified.title] = []
                self.title_to_ids[unified.title].append(unified.document_id)

                unified_docs.append(unified)

            except Exception as e:
                logger.error(f"Failed to process document: {e}")
                self.stats["warnings"].append(f"Processing error: {str(e)}")

        # Update statistics
        for doc in unified_docs:
            self.stats["total_documents"] += 1
            agency = doc.source_agency.value
            self.stats["by_agency"][agency] = self.stats["by_agency"].get(agency, 0) + 1
            doc_type = doc.document_type.value
            self.stats["by_type"][doc_type] = self.stats["by_type"].get(doc_type, 0) + 1
            area = doc.therapeutic_area.value
            self.stats["by_area"][area] = self.stats["by_area"].get(area, 0) + 1

        return unified_docs

    def aggregate(
        self,
        source_dirs: List[str],
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Aggregate documents from multiple sources

        Args:
            source_dirs: List of source directory paths
            output_file: Output file path (optional)

        Returns:
            Aggregation results
        """
        all_docs = []

        for source_dir in source_dirs:
            source_path = Path(source_dir)
            if not source_path.exists():
                logger.warning(f"Source directory not found: {source_dir}")
                continue

            logger.info(f"Processing directory: {source_dir}")
            docs = self.process_directory(source_dir)
            all_docs.extend(docs)
            logger.info(f"Found {len(docs)} documents in {source_dir}")

        # Save results
        if output_file:
            output_path = Path(output_file)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"regulatory_aggregated_{timestamp}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_documents": len(all_docs),
                "agencies_covered": list(self.stats["by_agency"].keys()),
                "source_directories": source_dirs,
            },
            "statistics": self.stats,
            "documents": [doc.to_dict() for doc in all_docs],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(all_docs)} documents to {output_path}")

        return result

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate collection status report

        Returns:
            Status report dictionary
        """
        return {
            "report_generated_at": datetime.now().isoformat(),
            "summary": {
                "total_documents": self.stats["total_documents"],
                "duplicates_removed": self.stats["duplicates_removed"],
                "validation_passed": self.stats["validation_passed"],
                "validation_failed": self.stats["validation_failed"],
                "warnings_count": len(self.stats["warnings"]),
            },
            "by_agency": self.stats["by_agency"],
            "by_document_type": self.stats["by_type"],
            "by_therapeutic_area": dict(sorted(
                self.stats["by_area"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),  # Top 10 areas
            "data_quality": {
                "validation_rate": (
                    self.stats["validation_passed"] / max(self.stats["total_documents"], 1) * 100
                ),
                "average_score": sum(
                    doc.validation_score for doc in []
                ) / max(self.stats["validation_passed"], 1),
            },
            "warnings": self.stats["warnings"][:20],  # First 20 warnings
        }


def aggregate_regulatory_data(
    source_dirs: List[str],
    output_file: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to aggregate regulatory data

    Args:
        source_dirs: List of source directory paths
        output_file: Output file path (optional)
        config: Configuration dictionary

    Returns:
        Aggregation results
    """
    aggregator = RegulatoryAggregator(config)
    return aggregator.aggregate(source_dirs, output_file)


if __name__ == "__main__":
    # Test the aggregator
    logging.basicConfig(level=logging.INFO)

    aggregator = RegulatoryAggregator()

    # Default source directories
    default_sources = [
        "/root/autodl-tmp/pj-pharmaKG/data/sources/regulatory/FDA",
        "/root/autodl-tmp/pj-pharmaKG/data/sources/regulatory/CDE",
        "/root/autodl-tmp/pj-pharmaKG/data/sources/regulatory/中药2025WPS",
    ]

    # Aggregate
    result = aggregator.aggregate(default_sources)

    # Generate report
    report = aggregator.generate_report()

    print("\n=== Regulatory Data Aggregation Report ===")
    print(f"Total documents: {report['summary']['total_documents']}")
    print(f"Duplicates removed: {report['summary']['duplicates_removed']}")
    print(f"Validation passed: {report['summary']['validation_passed']}")
    print(f"Validation failed: {report['summary']['validation_failed']}")
    print(f"\nBy agency:")
    for agency, count in report['by_agency'].items():
        print(f"  {agency}: {count}")
    print(f"\nTop therapeutic areas:")
    for area, count in report['by_therapeutic_area'].items():
        print(f"  {area}: {count}")
