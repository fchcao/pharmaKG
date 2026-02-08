#!/usr/bin/env python3
#===========================================================
# PharmaKG FDA Drug Shortages Database Processor
# Pharmaceutical Knowledge Graph - FDA Drug Shortages Database Processor
#===========================================================
# Version: v1.0
# Description: Fetch and process FDA Drug Shortages API data
#===========================================================

import logging
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from urllib.parse import urlencode

import requests

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus, ProcessingMetrics

logger = logging.getLogger(__name__)


#===========================================================
# Enumerations
#===========================================================

class ShortageStatus(str, Enum):
    """Drug Shortage Status"""
    CURRENT = "Current Shortage"
    RESOLVED = "Resolved"
    UNKNOWN = "Unknown"

class ShortageType(str, Enum):
    """Drug Shortage Type"""
    SHORTAGE = "Shortage"
    SUPPLY_DISRUPTION = "Supply Disruption"

class CompanyType(str, Enum):
    """Company/Facility Type"""
    MANUFACTURER = "Manufacturer"
    REPACKAGER = "Repackager"
    DISTRIBUTOR = "Distributor"


#===========================================================
# Configuration Classes
#===========================================================

@dataclass
class ShortageExtractionConfig:
    """Drug Shortage Extraction Configuration"""
    # API configuration
    api_base_url: str = "https://api.fda.gov/drug/shortages.json"
    api_version: str = "v1"
    request_timeout: int = 30

    # Rate limiting
    rate_limit_per_second: float = 1.0  # Conservative rate limit
    rate_limit_delay: float = 1.0

    # Query parameters
    search_query: Optional[str] = None
    shortage_status: Optional[str] = None
    date_range: Optional[Dict[str, str]] = None
    limit: int = 100  # Default limit per request

    # Retry configuration
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    retry_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])

    # Data processing
    deduplicate_by_shortage_id: bool = True
    map_to_chembl: bool = True
    map_to_unii: bool = True

    # Output options
    save_raw_response: bool = False


@dataclass
class ShortageStats:
    """Drug Shortage Processing Statistics"""
    # API request statistics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    retried_requests: int = 0

    # Entity extraction statistics
    shortages_extracted: int = 0
    compounds_extracted: int = 0
    manufacturers_extracted: int = 0
    facilities_extracted: int = 0

    # Relationship statistics
    relationships_created: int = 0
    cross_domain_relationships: int = 0

    # Deduplication statistics
    duplicate_shortages_skipped: int = 0

    # Processing time
    processing_time_seconds: float = 0.0
    api_request_time_seconds: float = 0.0

    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Data tracking
    last_processed_shortage_id: Optional[str] = None
    total_shortages_available: Optional[int] = None


#===========================================================
# Main Processor Class
#===========================================================

class ShortageProcessor(BaseProcessor):
    """
    FDA Drug Shortages Database Processor

    Fetches Content from FDA Drug Shortages API:
    - sc:DrugShortage - Drug shortage records with status and dates
    - rd:Compound - Affected drug products
    - sc:Manufacturer - Manufacturing companies
    - sc:Facility - Manufacturing facilities

    Relationship Types:
    - EXPERIENCES_SHORTAGE - Compound → DrugShortage
    - CAUSED_BY_QUALITY_ISSUE - DrugShortage → Manufacturer
    - MANUFACTURES - Manufacturer → Compound
    - HAS_FACILITY - Manufacturer → Facility
    - REPORTED_TO_AGENCY - DrugShortage → RegulatoryAgency

    Cross-Domain Relationships:
    - Maps generic names to ChEMBL compounds via UNII
    - Links to regulatory submissions

    API Endpoint:
    - GET /drug/shortages.json
    - Search parameters for filtering
    - Pagination support via skip/limit
    """

    PROCESSOR_NAME = "ShortageProcessor"
    SUPPORTED_FORMATS = []  # API processor
    OUTPUT_SUBDIR = "shortages"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Drug Shortage Processor

        Args:
            config: Processor configuration dictionary
        """
        super().__init__(config)

        # Initialize extraction configuration
        extraction_config = config.get('extraction', {}) if config else {}
        self.extraction_config = ShortageExtractionConfig(**extraction_config)

        # Statistics
        self.stats = ShortageStats()

        # Deduplication tracking
        self.seen_shortage_ids: Set[str] = set()

        # Cross-domain mapping cache
        self.chembl_cache: Dict[str, Optional[str]] = {}
        self.unii_cache: Dict[str, Optional[str]] = {}

        # Progress tracking
        self._progress_file = self.data_root / "cache" / f"{self.OUTPUT_SUBDIR}_progress.json"
        self._progress_file.parent.mkdir(parents=True, exist_ok=True)

        # Output file paths
        timestamp = datetime.now().strftime("%Y%m%d")
        self.output_shortages = self.entities_output_dir / f"shortages_shortages_{timestamp}.json"
        self.output_compounds = self.entities_output_dir / f"shortages_compounds_{timestamp}.json"
        self.output_manufacturers = self.entities_output_dir / f"shortages_manufacturers_{timestamp}.json"
        self.output_facilities = self.entities_output_dir / f"shortages_facilities_{timestamp}.json"
        self.output_relationships = self.relationships_output_dir / f"shortages_relationships_{timestamp}.json"
        self.output_summary = self.documents_output_dir / f"shortages_summary_{timestamp}.json"

        # Raw response output directory
        if self.extraction_config.save_raw_response:
            self.raw_output_dir = self.data_root / "sources" / "shortages" / "raw_responses"
            self.raw_output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized {self.PROCESSOR_NAME} with config: {self.extraction_config}")

    #===========================================================
    # BaseProcessor Abstract Method Implementation
    #===========================================================

    def scan(self, source_path: Path) -> List[Path]:
        """API processor does not scan files"""
        logger.info("API processor does not scan files")
        return []

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """API processor does not extract from files"""
        logger.warning("Use fetch_shortages() for API extraction")
        return {}

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform extracted API data into knowledge graph format

        Args:
            raw_data: Raw API response data

        Returns:
            Transformed entities and relationships
        """
        if 'error' in raw_data:
            return raw_data

        logger.info("Transforming shortage data")

        transformed = {
            'entities': {
                'sc:DrugShortage': [],
                'rd:Compound': [],
                'sc:Manufacturer': [],
                'sc:Facility': []
            },
            'relationships': []
        }

        # Process each shortage record
        shortage_records = raw_data.get('results', [])

        for record in shortage_records:
            try:
                # Deduplication check
                shortage_id = record.get('shortage_id') or record.get('id')
                if not shortage_id:
                    self.stats.warnings.append("Record missing shortage_id")
                    continue

                if self.extraction_config.deduplicate_by_shortage_id:
                    if shortage_id in self.seen_shortage_ids:
                        self.stats.duplicate_shortages_skipped += 1
                        continue
                    self.seen_shortage_ids.add(shortage_id)

                self.stats.last_processed_shortage_id = shortage_id

                # Create entities and relationships
                entities, relationships = self._transform_shortage_record(record)

                # Add entities to corresponding type lists
                for entity in entities:
                    entity_type = entity.get('entity_type')
                    if entity_type in transformed['entities']:
                        transformed['entities'][entity_type].append(entity)

                # Add relationships
                transformed['relationships'].extend(relationships)

            except Exception as e:
                logger.warning(f"Failed to transform record: {e}")
                self.stats.warnings.append(f"Transform failed: {str(e)}")

        # Create cross-domain relationships
        if self.extraction_config.map_to_chembl:
            cross_domain_rels = self._create_cross_domain_relationships(shortage_records)
            transformed['relationships'].extend(cross_domain_rels)

        logger.info(f"Transformed {len(shortage_records)} records into "
                   f"{sum(len(v) for v in transformed['entities'].values())} entities "
                   f"and {len(transformed['relationships'])} relationships")

        return transformed

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate transformed data

        Args:
            data: Data to validate

        Returns:
            True if valid
        """
        if 'error' in data:
            return False

        entities = data.get('entities', {})
        relationships = data.get('relationships', [])

        # Check for entities
        total_entities = sum(len(v) for v in entities.values())
        if total_entities == 0:
            self.stats.warnings.append("No entities extracted")
            return False

        # Validate entities have required fields
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                if not self._validate_entity(entity):
                    self.stats.warnings.append(f"Invalid entity in {entity_type}")
                    return False

        logger.info(f"Validation passed: {total_entities} entities, {len(relationships)} relationships")
        return True

    #===========================================================
    # API Data Fetching Methods
    #===========================================================

    def fetch_shortages(
        self,
        search_query: Optional[str] = None,
        shortage_status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch drug shortage data from FDA API

        Args:
            search_query: Search query string
            shortage_status: Filter by shortage status
            limit: Maximum number of records to fetch

        Returns:
            API response data
        """
        logger.info("Fetching drug shortages from FDA API")

        # Use config or parameters
        search_query = search_query or self.extraction_config.search_query
        shortage_status = shortage_status or self.extraction_config.shortage_status
        limit = limit or self.extraction_config.limit

        # Build query parameters
        params = {
            'limit': str(limit)
        }

        # Add search query
        if search_query:
            params['search'] = search_query

        # Add status filter
        if shortage_status:
            params['search'] = f"{params.get('search', '')} status:{shortage_status}".strip()

        # Add date range filter if configured
        if self.extraction_config.date_range:
            date_filter = self._build_date_filter(self.extraction_config.date_range)
            if date_filter:
                params['search'] = f"{params.get('search', '')} {date_filter}".strip()

        # Build URL
        url = f"{self.extraction_config.api_base_url}?{urlencode(params)}"

        # Make request
        response = self._make_request(url)

        if response and 'results' in response:
            total_records = response.get('meta', {}).get('results', {}).get('total', 0)
            self.stats.total_shortages_available = total_records

            logger.info(f"Successfully fetched {len(response['results'])} shortage records "
                       f"(total available: {total_records})")

            return {
                'results': response['results'],
                'meta': response.get('meta', {}),
                'extraction_timestamp': datetime.now().isoformat()
            }

        logger.error("Failed to fetch shortage data")
        return {'error': 'Failed to fetch data from FDA API'}

    def fetch_all_shortages(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        Fetch all drug shortage records using pagination

        Args:
            batch_size: Number of records per batch

        Returns:
            All shortage records
        """
        logger.info("Fetching all drug shortages (with pagination)")

        all_records = []
        skip = 0

        while True:
            # Build URL for this batch
            params = {
                'skip': str(skip),
                'limit': str(batch_size)
            }

            url = f"{self.extraction_config.api_base_url}?{urlencode(params)}"

            # Make request
            response = self._make_request(url)

            if not response or 'results' not in response:
                logger.info(f"No more records or error at skip={skip}")
                break

            records = response.get('results', [])
            if not records:
                logger.info(f"No more records at skip={skip}")
                break

            all_records.extend(records)
            logger.info(f"Fetched batch: {len(records)} records (total: {len(all_records)})")

            # Check if we've fetched all records
            total_available = response.get('meta', {}).get('results', {}).get('total', 0)
            if len(all_records) >= total_available:
                logger.info(f"Fetched all {total_available} available records")
                break

            skip += batch_size

            # Rate limiting
            time.sleep(self.extraction_config.rate_limit_delay)

        return {
            'results': all_records,
            'extraction_timestamp': datetime.now().isoformat()
        }

    #===========================================================
    # API Request Methods
    #===========================================================

    def _make_request(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Make API request with retry logic

        Args:
            url: Request URL

        Returns:
            Response data or None
        """
        max_retries = self.extraction_config.max_retries
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            # Rate limiting
            if self.stats.total_requests > 0:
                time.sleep(self.extraction_config.rate_limit_delay)

            try:
                request_start = time.time()

                response = requests.get(
                    url,
                    timeout=self.extraction_config.request_timeout
                )

                request_time = time.time() - request_start
                self.stats.api_request_time_seconds += request_time
                self.stats.total_requests += 1

                # Check response status
                if response.status_code == 200:
                    self.stats.successful_requests += 1

                    # Save raw response if configured
                    if self.extraction_config.save_raw_response:
                        self._save_raw_response(response)

                    return response.json()

                # Handle retryable errors
                if response.status_code in self.extraction_config.retry_status_codes:
                    retry_count += 1
                    self.stats.retried_requests += 1

                    backoff_delay = self.extraction_config.retry_backoff_factor ** retry_count
                    logger.warning(f"Request failed with status {response.status_code}, "
                                 f"retrying in {backoff_delay}s (attempt {retry_count}/{max_retries})")
                    time.sleep(backoff_delay)
                    continue

                # Other errors
                error_msg = f"Request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                self.stats.errors.append(error_msg)
                self.stats.failed_requests += 1
                return None

            except requests.exceptions.Timeout:
                last_error = "Request timed out"
                retry_count += 1
                self.stats.retried_requests += 1
                logger.warning(f"{last_error}, retrying (attempt {retry_count}/{max_retries})")
                time.sleep(self.extraction_config.retry_backoff_factor ** retry_count)
                continue

            except requests.exceptions.RequestException as e:
                last_error = f"Request error: {str(e)}"
                retry_count += 1
                self.stats.retried_requests += 1
                logger.warning(f"{last_error}, retrying (attempt {retry_count}/{max_retries})")
                time.sleep(self.extraction_config.retry_backoff_factor ** retry_count)
                continue

            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(last_error)
                self.stats.errors.append(last_error)
                return None

        # All retries failed
        error_msg = f"Request failed after {max_retries} retries: {last_error}"
        logger.error(error_msg)
        self.stats.errors.append(error_msg)
        self.stats.failed_requests += 1
        return None

    def _build_date_filter(self, date_range: Dict[str, str]) -> Optional[str]:
        """Build date range filter for API query"""
        start_date = date_range.get('start_date')
        end_date = date_range.get('end_date')

        filters = []
        if start_date:
            filters.append(f"start_date:[{start_date} TO *]")
        if end_date:
            filters.append(f"end_date:[* TO {end_date}]")

        return ' AND '.join(filters) if filters else None

    def _save_raw_response(self, response: requests.Response):
        """Save raw API response"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"shortages_response_{timestamp}.json"
            filepath = self.raw_output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved raw response to: {filepath}")

        except Exception as e:
            logger.warning(f"Failed to save raw response: {e}")

    #===========================================================
    # Data Transformation Methods
    #===========================================================

    def _transform_shortage_record(self, record: Dict[str, Any]) -> Tuple[List[Dict], List[Dict]]:
        """
        Transform a single shortage record

        Args:
            record: Raw shortage record

        Returns:
            (entities list, relationships list)
        """
        entities = []
        relationships = []

        # Generate shortage ID
        shortage_id = record.get('shortage_id') or record.get('id', '')
        shortage_primary_id = f"DrugShortage-{shortage_id}"

        # 1. Create DrugShortage entity
        shortage_entity = self._create_shortage_entity(shortage_id, record)
        if shortage_entity:
            entities.append(shortage_entity)
            self.stats.shortages_extracted += 1

        # 2. Create Compound entity (affected drug)
        compound_entity, shortage_rel = self._create_compound_entity(shortage_id, record)
        if compound_entity:
            entities.append(compound_entity)
            self.stats.compounds_extracted += 1
        if shortage_rel:
            relationships.append(shortage_rel)

        # 3. Create Manufacturer entity
        manufacturer_entity, facility_rels = self._create_manufacturer_entity(shortage_id, record)
        if manufacturer_entity:
            entities.append(manufacturer_entity)
            self.stats.manufacturers_extracted += 1
        if facility_rels:
            relationships.extend(facility_rels)

        # 4. Create Facility entities
        facility_entities, facility_rels = self._create_facility_entities(shortage_id, record)
        entities.extend(facility_entities)
        self.stats.facilities_extracted += len(facility_entities)
        relationships.extend(facility_rels)

        # 5. Create additional relationships
        additional_rels = self._create_additional_relationships(shortage_id, record)
        relationships.extend(additional_rels)

        return entities, relationships

    def _create_shortage_entity(self, shortage_id: str, record: Dict) -> Optional[Dict]:
        """Create DrugShortage entity"""
        try:
            primary_id = f"DrugShortage-{shortage_id}"

            # Parse dates
            start_date = self._parse_date(record.get('start_date'))
            end_date = self._parse_date(record.get('end_date'))

            # Map status
            status_str = record.get('status', 'Unknown')
            status = self._map_shortage_status(status_str)

            entity = {
                'primary_id': primary_id,
                'identifiers': {
                    'shortage_id': shortage_id
                },
                'properties': {
                    'shortage_id': shortage_id,
                    'shortage_status': status,
                    'shortage_start_date': start_date,
                    'shortage_end_date': end_date,
                    'shortage_type': record.get('shortage_type', 'Shortage'),
                    'reason_for_shortage': record.get('reason'),
                    'therapeutic_area': record.get('therapeutic_area'),
                    'presentation': record.get('presentation'),
                    'strength': record.get('strength'),
                    'data_source': 'FDA Drug Shortages Database',
                    'extraction_timestamp': datetime.now().isoformat()
                },
                'entity_type': 'sc:DrugShortage'
            }

            return entity

        except Exception as e:
            logger.warning(f"Failed to create DrugShortage entity: {e}")
            return None

    def _create_compound_entity(self, shortage_id: str, record: Dict) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Create Compound entity and EXPERIENCES_SHORTAGE relationship"""
        try:
            generic_name = record.get('generic_name')
            brand_names = record.get('brand_names', [])

            if not generic_name:
                return None, None

            # Create compound ID
            compound_id = f"Compound-{generic_name}".replace(' ', '_').replace('/', '-')

            entity = {
                'primary_id': compound_id,
                'identifiers': {
                    'generic_name': generic_name,
                    'brand_names': brand_names,
                    'ndc': record.get('ndc')
                },
                'properties': {
                    'generic_name': generic_name,
                    'brand_names': brand_names,
                    'ndc': record.get('ndc'),
                    'dosage_form': record.get('dosage_form'),
                    'strength': record.get('strength'),
                    'route': record.get('route'),
                    'marketing_status': record.get('marketing_status'),
                    'data_source': 'FDA Drug Shortages Database'
                },
                'entity_type': 'rd:Compound'
            }

            # Create relationship
            relationship = {
                'relationship_type': 'EXPERIENCES_SHORTAGE',
                'source_entity_id': compound_id,
                'target_entity_id': f"DrugShortage-{shortage_id}",
                'properties': {
                    'shortage_status': record.get('status'),
                    'data_source': 'FDA Drug Shortages Database'
                },
                'source': 'FDA Drug Shortages Database'
            }

            return entity, relationship

        except Exception as e:
            logger.warning(f"Failed to create Compound entity: {e}")
            return None, None

    def _create_manufacturer_entity(self, shortage_id: str, record: Dict) -> Tuple[Optional[Dict], List[Dict]]:
        """Create Manufacturer entity and relationships"""
        relationships = []

        try:
            manufacturer_name = record.get('manufacturer_name')
            if not manufacturer_name:
                return None, []

            manufacturer_id = f"Manufacturer-{manufacturer_name}".replace(' ', '_').replace('/', '-')

            entity = {
                'primary_id': manufacturer_id,
                'identifiers': {
                    'name': manufacturer_name
                },
                'properties': {
                    'manufacturer_name': manufacturer_name,
                    'company_type': record.get('company_type', 'Manufacturer'),
                    'contact_info': record.get('contact_info'),
                    'data_source': 'FDA Drug Shortages Database'
                },
                'entity_type': 'sc:Manufacturer'
            }

            # Create CAUSED_BY_QUALITY_ISSUE relationship
            relationship = {
                'relationship_type': 'CAUSED_BY_QUALITY_ISSUE',
                'source_entity_id': f"DrugShortage-{shortage_id}",
                'target_entity_id': manufacturer_id,
                'properties': {
                    'reason': record.get('reason'),
                    'data_source': 'FDA Drug Shortages Database'
                },
                'source': 'FDA Drug Shortages Database'
            }

            relationships.append(relationship)

            return entity, relationships

        except Exception as e:
            logger.warning(f"Failed to create Manufacturer entity: {e}")
            return None, []

    def _create_facility_entities(self, shortage_id: str, record: Dict) -> Tuple[List[Dict], List[Dict]]:
        """Create Facility entities and HAS_FACILITY relationships"""
        entities = []
        relationships = []

        try:
            manufacturer_name = record.get('manufacturer_name')
            if not manufacturer_name:
                return [], []

            # Extract facility information if available
            facility_name = record.get('facility_name')
            if facility_name:
                facility_id = f"Facility-{facility_name}".replace(' ', '_').replace('/', '-')

                entity = {
                    'primary_id': facility_id,
                    'identifiers': {
                        'name': facility_name
                    },
                    'properties': {
                        'facility_name': facility_name,
                        'address': {
                            'city': record.get('city'),
                            'state': record.get('state'),
                            'country': record.get('country')
                        },
                        'facility_type': record.get('facility_type', 'Manufacturing'),
                        'data_source': 'FDA Drug Shortages Database'
                    },
                    'entity_type': 'sc:Facility'
                }

                entities.append(entity)

                # Create HAS_FACILITY relationship
                manufacturer_id = f"Manufacturer-{manufacturer_name}".replace(' ', '_').replace('/', '-')

                relationship = {
                    'relationship_type': 'HAS_FACILITY',
                    'source_entity_id': manufacturer_id,
                    'target_entity_id': facility_id,
                    'properties': {
                        'data_source': 'FDA Drug Shortages Database'
                    },
                    'source': 'FDA Drug Shortages Database'
                }

                relationships.append(relationship)

        except Exception as e:
            logger.warning(f"Failed to create Facility entities: {e}")

        return entities, relationships

    def _create_additional_relationships(self, shortage_id: str, record: Dict) -> List[Dict]:
        """Create additional relationships"""
        relationships = []

        try:
            # Create REPORTED_TO_AGENCY relationship
            relationship = {
                'relationship_type': 'REPORTED_TO_AGENCY',
                'source_entity_id': f"DrugShortage-{shortage_id}",
                'target_entity_id': "RegulatoryAgency-FDA",
                'properties': {
                    'agency': 'FDA',
                    'report_date': record.get('start_date'),
                    'data_source': 'FDA Drug Shortages Database'
                },
                'source': 'FDA Drug Shortages Database'
            }

            relationships.append(relationship)

        except Exception as e:
            logger.warning(f"Failed to create additional relationships: {e}")

        return relationships

    def _create_cross_domain_relationships(self, records: List[Dict]) -> List[Dict]:
        """Create cross-domain relationships to ChEMBL"""
        relationships = []

        for record in records:
            try:
                generic_name = record.get('generic_name')
                shortage_id = record.get('shortage_id') or record.get('id', '')

                if not generic_name:
                    continue

                # Map to ChEMBL via UNII
                chembl_id = self._map_generic_to_chembl(generic_name)
                if chembl_id:
                    relationship = {
                        'relationship_type': 'EXPERIENCES_SHORTAGE',
                        'source_entity_id': f"Compound-{chembl_id}",
                        'target_entity_id': f"DrugShortage-{shortage_id}",
                        'properties': {
                            'generic_name': generic_name,
                            'mapping_confidence': 'high',
                            'data_source': 'FDA Shortages-ChEMBL-Mapping'
                        },
                        'source': 'FDA Shortages-ChEMBL-Mapping'
                    }

                    relationships.append(relationship)
                    self.stats.cross_domain_relationships += 1

            except Exception as e:
                logger.warning(f"Failed to create cross-domain relationship: {e}")

        return relationships

    #===========================================================
    # Cross-Domain Mapping Methods
    #===========================================================

    def _map_generic_to_chembl(self, generic_name: str) -> Optional[str]:
        """
        Map generic drug name to ChEMBL compound ID via UNII

        Args:
            generic_name: Generic drug name

        Returns:
            ChEMBL ID or None
        """
        # Check cache
        if generic_name in self.chembl_cache:
            return self.chembl_cache[generic_name]

        # TODO: Implement actual mapping
        # This could:
        # 1. Lookup UNII from FDA substance registration system
        # 2. Map UNII to ChEMBL via cross-reference
        # 3. Use pre-computed mapping table

        chembl_id = None

        # Cache result
        self.chembl_cache[generic_name] = chembl_id

        return chembl_id

    #===========================================================
    # Data Parsing Helper Methods
    #===========================================================

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse various date formats"""
        if not date_str:
            return None

        # Try common date formats
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%Y%m%d'
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _map_shortage_status(self, status_str: str) -> str:
        """Map shortage status string to standardized value"""
        status_lower = status_str.lower()

        if 'current' in status_lower or 'active' in status_lower:
            return ShortageStatus.CURRENT.value
        elif 'resolved' in status_lower or 'recovered' in status_lower:
            return ShortageStatus.RESOLVED.value

        return ShortageStatus.UNKNOWN.value

    def _validate_entity(self, entity: Dict) -> bool:
        """Validate entity has required fields"""
        if 'primary_id' not in entity:
            return False

        if 'properties' not in entity:
            return False

        if 'entity_type' not in entity:
            return False

        return True

    #===========================================================
    # Results Saving Methods
    #===========================================================

    def save_results(
        self,
        entities: Dict[str, List[Dict]],
        relationships: List[Dict],
        output_to: Optional[str] = None
    ) -> Path:
        """
        Save drug shortage processing results

        Args:
            entities: Dictionary of entity type to entity list
            relationships: List of relationships
            output_to: Custom output directory

        Returns:
            Path to summary file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Determine output directory
        if output_to:
            output_dir = Path(output_to)
        else:
            output_dir = self.documents_output_dir

        output_dir.mkdir(parents=True, exist_ok=True)

        # Save each entity type
        for entity_type, entity_list in entities.items():
            if not entity_list:
                continue

            type_name = entity_type.replace(':', '_').lower()
            entities_file = output_dir / f"shortages_{type_name}s_{timestamp}.json"

            with open(entities_file, 'w', encoding='utf-8') as f:
                json.dump(entity_list, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(entity_list)} {entity_type} entities to: {entities_file}")

        # Save relationships
        if relationships:
            relationships_file = output_dir / f"shortages_relationships_{timestamp}.json"

            with open(relationships_file, 'w', encoding='utf-8') as f:
                json.dump(relationships, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(relationships)} relationships to: {relationships_file}")

        # Save processing summary
        summary = {
            "processor": self.PROCESSOR_NAME,
            "source": "FDA Drug Shortages Database API",
            "timestamp": timestamp,
            "extraction_config": {
                'api_version': self.extraction_config.api_version,
                'search_query': self.extraction_config.search_query,
                'shortage_status': self.extraction_config.shortage_status,
                'limit': self.extraction_config.limit,
                'map_to_chembl': self.extraction_config.map_to_chembl
            },
            "statistics": {
                "shortages_extracted": self.stats.shortages_extracted,
                "compounds_extracted": self.stats.compounds_extracted,
                "manufacturers_extracted": self.stats.manufacturers_extracted,
                "facilities_extracted": self.stats.facilities_extracted,
                "relationships_created": len(relationships),
                "cross_domain_relationships": self.stats.cross_domain_relationships,
                "duplicate_shortages_skipped": self.stats.duplicate_shortages_skipped,
                "processing_time_seconds": self.stats.processing_time_seconds,
                "api_request_time_seconds": self.stats.api_request_time_seconds,
                "total_requests": self.stats.total_requests,
                "successful_requests": self.stats.successful_requests,
                "failed_requests": self.stats.failed_requests,
                "retried_requests": self.stats.retried_requests
            },
            "entities_by_type": {
                entity_type: len(entity_list)
                for entity_type, entity_list in entities.items()
            },
            "total_entities": sum(len(entity_list) for entity_list in entities.values()),
            "total_relationships": len(relationships),
            "total_shortages_available": self.stats.total_shortages_available,
            "errors": self.stats.errors[:10],
            "warnings": self.stats.warnings[:10]
        }

        summary_file = output_dir / f"shortages_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved processing summary to: {summary_file}")

        return summary_file


#===========================================================
# Command-Line Interface
#===========================================================

def main():
    """Command-line main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description='FDA Drug Shortages Database Processor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Fetch all drug shortages
  python -m processors.shortage_processor --mode all

  # Fetch by drug name
  python -m processors.shortage_processor --mode search --query "epinephrine"

  # Fetch only current shortages
  python -m processors.shortage_processor --mode status --status "Current"

  # Fetch with limit
  python -m processors.shortage_processor --mode all --limit 50
        """
    )

    parser.add_argument(
        '--mode',
        choices=['all', 'search', 'status'],
        default='all',
        help='Processing mode (default: all)'
    )

    parser.add_argument(
        '--query',
        help='Search query string'
    )

    parser.add_argument(
        '--status',
        help='Shortage status filter (e.g., "Current", "Resolved")'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Maximum number of records to fetch (default: 100)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for pagination (default: 100)'
    )

    parser.add_argument(
        '--no-dedup',
        action='store_true',
        help='Disable deduplication'
    )

    parser.add_argument(
        '--no-cross-domain',
        action='store_true',
        help='Disable cross-domain mapping'
    )

    parser.add_argument(
        '--save-raw',
        action='store_true',
        help='Save raw API responses'
    )

    parser.add_argument(
        '--output',
        help='Output directory (default: data/processed/documents/shortages/)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # Build configuration
    config = {
        'extraction': {
            'search_query': args.query,
            'shortage_status': args.status,
            'limit': args.limit,
            'deduplicate_by_shortage_id': not args.no_dedup,
            'map_to_chembl': not args.no_cross_domain,
            'save_raw_response': args.save_raw
        }
    }

    # Create processor
    processor = ShortageProcessor(config)

    # Fetch data based on mode
    start_time = datetime.now()

    if args.mode == 'all':
        raw_data = processor.fetch_all_shortages(batch_size=args.batch_size)
    elif args.mode == 'search':
        raw_data = processor.fetch_shortages(search_query=args.query)
    elif args.mode == 'status':
        raw_data = processor.fetch_shortages(shortage_status=args.status)
    else:
        raw_data = processor.fetch_shortages()

    if not raw_data or 'results' not in raw_data:
        logger.error("No data fetched")
        return 1

    # Transform data
    transformed_data = processor.transform(raw_data)

    # Validate data
    if not processor.validate(transformed_data):
        logger.warning("Data validation failed")

    # Save results
    entities = transformed_data.get('entities', {})
    relationships = transformed_data.get('relationships', [])

    output_path = processor.save_results(entities, relationships, args.output)

    # Output results summary
    elapsed_time = (datetime.now() - start_time).total_seconds()

    print(f"\n{'='*60}")
    print(f"Drug Shortages Processing Complete")
    print(f"{'='*60}")
    print(f"Shortages extracted: {processor.stats.shortages_extracted}")
    print(f"Compounds extracted: {processor.stats.compounds_extracted}")
    print(f"Manufacturers extracted: {processor.stats.manufacturers_extracted}")
    print(f"Facilities extracted: {processor.stats.facilities_extracted}")
    print(f"Relationships created: {len(relationships)}")
    print(f"Cross-domain relationships: {processor.stats.cross_domain_relationships}")
    print(f"Processing time: {elapsed_time:.2f} seconds")
    print(f"API request time: {processor.stats.api_request_time_seconds:.2f} seconds")

    if processor.stats.errors:
        print(f"\nErrors ({len(processor.stats.errors)}):")
        for error in processor.stats.errors[:5]:
            print(f"  - {error}")

    if processor.stats.warnings:
        print(f"\nWarnings ({len(processor.stats.warnings)}):")
        for warning in processor.stats.warnings[:5]:
            print(f"  - {warning}")

    print(f"\nOutput files: {output_path}")

    return 0


if __name__ == '__main__':
    exit(main())
