#!/usr/bin/env python3
#===========================================================
# PharmaKG FDA FAERS Adverse Events Processor
# Pharmaceutical Knowledge Graph - FDA FAERS Adverse Events Processor
#===========================================================
# Version: v1.0
# Description: Process FDA FAERS (FDA Adverse Event Reporting System) quarterly ASCII/CSV data
#===========================================================

import logging
import csv
import json
import re
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from collections import defaultdict

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus, ProcessingMetrics

logger = logging.getLogger(__name__)


#===========================================================
# Enumerations
#===========================================================

class FAERSDataType(str, Enum):
    """FAERS Data File Types"""
    DEMOGRAPHIC = "DEMO"  # Patient demographic information
    DRUG = "DRUG"  # Drug information
    REACTION = "REAC"  # Adverse reaction information
    OUTCOME = "OUTC"  # Patient outcome information
    REPORT_SOURCE = "RPSR"  # Report source information
    THERAPY = "THER"  # Drug therapy start and end dates
    INDICATION = "INDI"  # Drug indications

class DrugCharacterization(str, Enum):
    """Drug Characterization Codes"""
    SUSPECT = "1"  # Suspect drug
    CONCOMITANT = "2"  # Concomitant drug
    INTERACTING = "3"  # Interacting drug

class ReporterType(str, Enum):
    """Reporter Types"""
    PHYSICIAN = "Physician"
    PHARMACIST = "Pharmacist"
    OTHER_HEALTH_PROFESSIONAL = "Other Health Professional"
    LAWYER = "Lawyer"
    CONSUMER = "Consumer"
    FOREIGN = "Foreign"

class OutcomeType(str, Enum):
    """Patient Outcome Types"""
    RECOVERED = "Recovered"
    RECOVERING = "Recovering"
    NOT_RECOVERED = "Not Recovered"
    RECOVERED_WITH_SEQUELAE = "Recovered with Sequelae"
    FATAL = "Fatal"
    UNKNOWN = "Unknown"


#===========================================================
# Configuration Classes
#===========================================================

@dataclass
class FAERSExtractionConfig:
    """FAERS Extraction Configuration"""
    # File processing configuration
    batch_size: int = 1000
    max_reports: Optional[int] = None
    skip_existing: bool = True

    # Data quality configuration
    require_primary_id: bool = True
    validate_meddra_codes: bool = True
    normalize_drug_names: bool = True

    # Cross-domain mapping
    map_to_chembl: bool = True
    map_to_unii: bool = True

    # Deduplication
    deduplicate_by_safetyreport_id: bool = True

    # Processing options
    save_intermediate_batches: bool = True
    include_non_serious: bool = False  # Only include serious adverse events


@dataclass
class FAERSStats:
    """FAERS Processing Statistics"""
    # File statistics
    files_scanned: int = 0
    files_processed: int = 0
    files_failed: int = 0

    # Entity extraction statistics
    adverse_events_extracted: int = 0
    conditions_extracted: int = 0
    compounds_extracted: int = 0

    # Relationship statistics
    relationships_created: int = 0
    cross_domain_relationships: int = 0

    # Data quality statistics
    duplicate_reports_skipped: int = 0
    invalid_records_skipped: int = 0
    records_with_missing_drugs: int = 0

    # Processing time
    processing_time_seconds: float = 0.0

    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Data coverage
    total_reports_in_files: int = 0
    unique_safetyreport_ids: Set[str] = field(default_factory=set)


#===========================================================
# Main Processor Class
#===========================================================

class FAERSProcessor(BaseProcessor):
    """
    FDA FAERS Adverse Events Processor

    Extracts Content:
    - clinical:AdverseEvent - Individual adverse event reports with patient demographics
    - clinical:Condition - MedDRA-coded adverse reactions
    - rd:Compound - Suspect and concomitant drugs

    Relationship Types:
    - CAUSED_ADVERSE_EVENT - Compound → AdverseEvent
    - ASSOCIATED_WITH - AdverseEvent → Condition
    - HAS_SAFETY_SIGNAL - Compound → SafetySignal (derived)

    Cross-Domain Relationships:
    - Maps drug names to ChEMBL compounds
    - Maps drugs to UNII (Unique Ingredient Identifier)

    Source Files (Quarterly ASCII/CSV format):
    - DEMO*.txt: Demographic and administrative information
    - DRUG*.txt: Drug information for all reported drugs
    - REAC*.txt: Adverse reaction coded with MedDRA terms
    - OUTC*.txt: Patient outcomes
    """

    PROCESSOR_NAME = "FAERSProcessor"
    SUPPORTED_FORMATS = ["txt", "csv", "ascii"]
    OUTPUT_SUBDIR = "faers"

    # FAERS file naming pattern
    FILE_PATTERN = re.compile(r"^(DEMO|DRUG|REAC|OUTC|RPSR|THER|INDI)\d{2}(Q\d)?\.txt$", re.IGNORECASE)

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize FAERS Processor

        Args:
            config: Processor configuration dictionary
        """
        super().__init__(config)

        # Initialize extraction configuration
        extraction_config = config.get('extraction', {}) if config else {}
        self.extraction_config = FAERSExtractionConfig(**extraction_config)

        # Statistics
        self.stats = FAERSStats()

        # Deduplication tracking
        self.seen_safetyreport_ids: Set[str] = set()

        # Cross-domain mapping cache
        self.chembl_cache: Dict[str, Optional[str]] = {}
        self.unii_cache: Dict[str, Optional[str]] = {}

        # Data storage for processing
        self.adverse_events_data: Dict[str, Dict] = {}  # safetyreport_id -> event data
        self.drugs_data: Dict[str, List[Dict]] = defaultdict(list)  # safetyreport_id -> drugs
        self.reactions_data: Dict[str, List[Dict]] = defaultdict(list)  # safetyreport_id -> reactions
        self.outcomes_data: Dict[str, List[str]] = defaultdict(list)  # safetyreport_id -> outcomes

        # Output file paths
        timestamp = datetime.now().strftime("%Y%m%d")
        self.output_adverse_events = self.entities_output_dir / f"faers_adverse_events_{timestamp}.json"
        self.output_conditions = self.entities_output_dir / f"faers_conditions_{timestamp}.json"
        self.output_compounds = self.entities_output_dir / f"faers_compounds_{timestamp}.json"
        self.output_relationships = self.relationships_output_dir / f"faers_relationships_{timestamp}.json"
        self.output_summary = self.documents_output_dir / f"faers_summary_{timestamp}.json"

        logger.info(f"Initialized {self.PROCESSOR_NAME} with config: {self.extraction_config}")

    #===========================================================
    # BaseProcessor Abstract Method Implementation
    #===========================================================

    def scan(self, source_path: Path) -> List[Path]:
        """
        Scan source directory for FAERS data files

        Args:
            source_path: Source directory path

        Returns:
            List of files to process, grouped by quarter
        """
        logger.info(f"Scanning for FAERS files in: {source_path}")

        source_path = Path(source_path)
        if not source_path.exists():
            logger.error(f"Source path does not exist: {source_path}")
            return []

        # Find all FAERS files
        faers_files = {}
        for file_path in source_path.iterdir():
            if file_path.is_file():
                match = self.FILE_PATTERN.match(file_path.name)
                if match:
                    file_type = match.group(1).upper()

                    # Check if file was already processed
                    if self.extraction_config.skip_existing and self.is_processed(file_path):
                        logger.info(f"Skipping already processed file: {file_path.name}")
                        continue

                    if file_type not in faers_files:
                        faers_files[file_type] = []
                    faers_files[file_type].append(file_path)

        # Log found files
        for file_type, files in faers_files.items():
            logger.info(f"Found {len(files)} {file_type} file(s)")

        # Return list of files to process
        all_files = []
        for files in faers_files.values():
            all_files.extend(files)

        self.stats.files_scanned = len(all_files)
        return sorted(all_files)

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract data from FAERS file

        Args:
            file_path: Path to FAERS data file

        Returns:
            Extracted data dictionary
        """
        logger.info(f"Extracting data from: {file_path.name}")

        try:
            # Determine file type from filename
            file_type = self._determine_file_type(file_path)

            if file_type == FAERSDataType.DEMOGRAPHIC:
                data = self._extract_demographic(file_path)
            elif file_type == FAERSDataType.DRUG:
                data = self._extract_drug(file_path)
            elif file_type == FAERSDataType.REACTION:
                data = self._extract_reaction(file_path)
            elif file_type == FAERSDataType.OUTCOME:
                data = self._extract_outcome(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                return {}

            logger.info(f"Extracted {len(data.get('records', []))} records from {file_path.name}")
            return data

        except Exception as e:
            logger.error(f"Failed to extract from {file_path.name}: {e}")
            self.stats.errors.append(f"{file_path.name}: {str(e)}")
            self.stats.files_failed += 1
            return {}

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform extracted data into knowledge graph format

        Args:
            raw_data: Extracted FAERS data

        Returns:
            Transformed entities and relationships
        """
        logger.info("Transforming FAERS data")

        transformed = {
            'entities': {
                'clinical:AdverseEvent': [],
                'clinical:Condition': [],
                'rd:Compound': []
            },
            'relationships': []
        }

        # Process each adverse event report
        for safetyreport_id, event_data in self.adverse_events_data.items():
            try:
                # Skip if not serious (if configured)
                if not self.extraction_config.include_non_serious:
                    if not event_data.get('serious'):
                        continue

                # Create AdverseEvent entity
                adverse_event_entity = self._create_adverse_event_entity(safetyreport_id, event_data)
                if adverse_event_entity:
                    transformed['entities']['clinical:AdverseEvent'].append(adverse_event_entity)
                    self.stats.adverse_events_extracted += 1

                # Create Condition entities (reactions) and relationships
                reactions = self.reactions_data.get(safetyreport_id, [])
                for reaction_data in reactions:
                    condition_entity, relationship = self._create_condition_and_relationship(
                        safetyreport_id, reaction_data
                    )
                    if condition_entity:
                        transformed['entities']['clinical:Condition'].append(condition_entity)
                        self.stats.conditions_extracted += 1
                    if relationship:
                        transformed['relationships'].append(relationship)

                # Create Compound entities (drugs) and relationships
                drugs = self.drugs_data.get(safetyreport_id, [])
                for drug_data in drugs:
                    compound_entity, relationship = self._create_compound_and_relationship(
                        safetyreport_id, drug_data
                    )
                    if compound_entity:
                        transformed['entities']['rd:Compound'].append(compound_entity)
                        self.stats.compounds_extracted += 1
                    if relationship:
                        transformed['relationships'].append(relationship)

            except Exception as e:
                logger.warning(f"Failed to transform report {safetyreport_id}: {e}")
                self.stats.warnings.append(f"Transform failed for {safetyreport_id}: {str(e)}")

        # Create cross-domain relationships
        if self.extraction_config.map_to_chembl:
            cross_domain_rels = self._create_cross_domain_relationships()
            transformed['relationships'].extend(cross_domain_rels)

        logger.info(f"Transformed {len(self.adverse_events_data)} reports into "
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
    # File Type Detection
    #===========================================================

    def _determine_file_type(self, file_path: Path) -> Optional[FAERSDataType]:
        """Determine FAERS file type from filename"""
        filename = file_path.name.upper()

        if filename.startswith("DEMO"):
            return FAERSDataType.DEMOGRAPHIC
        elif filename.startswith("DRUG"):
            return FAERSDataType.DRUG
        elif filename.startswith("REAC"):
            return FAERSDataType.REACTION
        elif filename.startswith("OUTC"):
            return FAERSDataType.OUTCOME
        elif filename.startswith("RPSR"):
            return FAERSDataType.REPORT_SOURCE
        elif filename.startswith("THER"):
            return FAERSDataType.THERAPY
        elif filename.startswith("INDI"):
            return FAERSDataType.INDICATION

        return None

    #===========================================================
    # Data Extraction Methods
    #===========================================================

    def _extract_demographic(self, file_path: Path) -> Dict[str, Any]:
        """Extract demographic and administrative information"""
        records = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f, delimiter='$')

                for row in reader:
                    safetyreport_id = row.get('safetyreportid', '').strip()

                    if not safetyreport_id:
                        continue

                    # Deduplication check
                    if self.extraction_config.deduplicate_by_safetyreport_id:
                        if safetyreport_id in self.seen_safetyreport_ids:
                            self.stats.duplicate_reports_skipped += 1
                            continue
                        self.seen_safetyreport_ids.add(safetyreport_id)
                        self.stats.unique_safetyreport_ids.add(safetyreport_id)

                    # Store event data
                    self.adverse_events_data[safetyreport_id] = {
                        'safetyreport_id': safetyreport_id,
                        'case_number': row.get('caseid', '').strip(),
                        'receive_date': self._parse_fda_date(row.get('receivedate')),
                        'serious': self._parse_serious(row.get('serious')),
                        'sex': row.get('patientsex', '').strip(),
                        'age': self._parse_age(row.get('patientage')),
                        'age_unit': row.get('patientageunit', '').strip(),
                        'weight': self._parse_weight(row.get('patientweight')),
                        'weight_unit': row.get('patientweightunit', '').strip(),
                        'report_type': row.get('safetyreportversion', '').strip(),
                        'reporter_type': row.get('reportertype', '').strip(),
                        'outcomes': []  # Will be populated from OUTC file
                    }

                    records.append(row)
                    self.stats.total_reports_in_files += 1

        except Exception as e:
            logger.error(f"Error reading DEMO file {file_path.name}: {e}")
            raise

        return {'file_type': 'DEMO', 'records': records}

    def _extract_drug(self, file_path: Path) -> Dict[str, Any]:
        """Extract drug information"""
        records = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f, delimiter='$')

                for row in reader:
                    safetyreport_id = row.get('safetyreportid', '').strip()

                    if not safetyreport_id:
                        continue

                    drug_data = {
                        'safetyreport_id': safetyreport_id,
                        'drug_seq': row.get('drugseq', '').strip(),
                        'drug_characterization': row.get('drugcharacterization', '').strip(),
                        'drug_name': row.get('drugname', '').strip(),
                        'medicinal_product': row.get('medicinalproduct', '').strip(),
                        'dose': row.get('drugdosagetxt', '').strip(),
                        'frequency': row.get('drugadministration', '').strip(),
                        'route': row.get('drugroute', '').strip()
                    }

                    self.drugs_data[safetyreport_id].append(drug_data)
                    records.append(row)

        except Exception as e:
            logger.error(f"Error reading DRUG file {file_path.name}: {e}")
            raise

        return {'file_type': 'DRUG', 'records': records}

    def _extract_reaction(self, file_path: Path) -> Dict[str, Any]:
        """Extract adverse reaction information"""
        records = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f, delimiter='$')

                for row in reader:
                    safetyreport_id = row.get('safetyreportid', '').strip()

                    if not safetyreport_id:
                        continue

                    reaction_data = {
                        'safetyreport_id': safetyreport_id,
                        'drug_seq': row.get('drugcharacterization', '').strip(),
                        'meddra_code': row.get('reactionmeddrapt', '').strip(),
                        'meddra_term': row.get('reactionmeddraversionpt', '').strip()
                    }

                    self.reactions_data[safetyreport_id].append(reaction_data)
                    records.append(row)

        except Exception as e:
            logger.error(f"Error reading REAC file {file_path.name}: {e}")
            raise

        return {'file_type': 'REAC', 'records': records}

    def _extract_outcome(self, file_path: Path) -> Dict[str, Any]:
        """Extract patient outcome information"""
        records = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f, delimiter='$')

                for row in reader:
                    safetyreport_id = row.get('safetyreportid', '').strip()

                    if not safetyreport_id:
                        continue

                    outcome_code = row.get('patientoutcome', '').strip()
                    outcome = self._map_outcome_code(outcome_code)

                    if safetyreport_id in self.adverse_events_data:
                        self.adverse_events_data[safetyreport_id]['outcomes'].append(outcome)

                    records.append(row)

        except Exception as e:
            logger.error(f"Error reading OUTC file {file_path.name}: {e}")
            raise

        return {'file_type': 'OUTC', 'records': records}

    #===========================================================
    # Entity Creation Methods
    #===========================================================

    def _create_adverse_event_entity(self, safetyreport_id: str, event_data: Dict) -> Optional[Dict]:
        """Create AdverseEvent entity"""
        try:
            primary_id = f"AdverseEvent-{safetyreport_id}"

            # Map reporter type
            reporter_type = event_data.get('reporter_type', 'Unknown')
            reporter_type_mapped = self._map_reporter_type(reporter_type)

            entity = {
                'primary_id': primary_id,
                'identifiers': {
                    'safetyreport_id': safetyreport_id,
                    'case_number': event_data.get('case_number')
                },
                'properties': {
                    'safetyreport_id': safetyreport_id,
                    'case_number': event_data.get('case_number'),
                    'receive_date': event_data.get('receive_date'),
                    'serious': event_data.get('serious', False),
                    'sex': event_data.get('sex'),
                    'age': event_data.get('age'),
                    'age_unit': event_data.get('age_unit'),
                    'weight': event_data.get('weight'),
                    'weight_unit': event_data.get('weight_unit'),
                    'report_type': event_data.get('report_type'),
                    'reporter_type': reporter_type_mapped,
                    'outcomes': event_data.get('outcomes', []),
                    'data_source': 'FDA FAERS',
                    'extraction_timestamp': datetime.now().isoformat()
                },
                'entity_type': 'clinical:AdverseEvent'
            }

            return entity

        except Exception as e:
            logger.warning(f"Failed to create AdverseEvent entity for {safetyreport_id}: {e}")
            return None

    def _create_condition_and_relationship(self, safetyreport_id: str, reaction_data: Dict) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Create Condition entity and ASSOCIATED_WITH relationship"""
        try:
            meddra_code = reaction_data.get('meddra_code')
            meddra_term = reaction_data.get('meddra_term')

            if not meddra_code:
                return None, None

            # Create a unique ID for this condition
            condition_id = f"Condition-{meddra_code}"

            entity = {
                'primary_id': condition_id,
                'identifiers': {
                    'meddra_code': meddra_code,
                    'name': meddra_term
                },
                'properties': {
                    'meddra_code': meddra_code,
                    'meddra_term': meddra_term,
                    'condition_type': 'adverse_reaction',
                    'data_source': 'FDA FAERS'
                },
                'entity_type': 'clinical:Condition'
            }

            # Create relationship
            relationship = {
                'relationship_type': 'ASSOCIATED_WITH',
                'source_entity_id': f"AdverseEvent-{safetyreport_id}",
                'target_entity_id': condition_id,
                'properties': {
                    'drug_seq': reaction_data.get('drug_seq'),
                    'data_source': 'FDA FAERS'
                },
                'source': 'FDA FAERS'
            }

            return entity, relationship

        except Exception as e:
            logger.warning(f"Failed to create condition/reaction: {e}")
            return None, None

    def _create_compound_and_relationship(self, safetyreport_id: str, drug_data: Dict) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Create Compound entity and CAUSED_ADVERSE_EVENT relationship"""
        try:
            drug_name = drug_data.get('drug_name') or drug_data.get('medicinal_product')

            if not drug_name:
                return None, None

            # Normalize drug name
            if self.extraction_config.normalize_drug_names:
                drug_name = self._normalize_drug_name(drug_name)

            # Create compound ID
            compound_id = f"Compound-{drug_name}".replace(' ', '_').replace('/', '-')

            # Map drug characterization
            drug_char = drug_data.get('drug_characterization', '2')
            drug_role = self._map_drug_characterization(drug_char)

            entity = {
                'primary_id': compound_id,
                'identifiers': {
                    'name': drug_name,
                    'drug_seq': drug_data.get('drug_seq')
                },
                'properties': {
                    'drug_name': drug_name,
                    'medicinal_product': drug_data.get('medicinal_product'),
                    'dose': drug_data.get('dose'),
                    'frequency': drug_data.get('frequency'),
                    'route': drug_data.get('route'),
                    'drug_role': drug_role,
                    'data_source': 'FDA FAERS'
                },
                'entity_type': 'rd:Compound'
            }

            # Create relationship (only for suspect drugs)
            if drug_role == 'Suspect':
                relationship = {
                    'relationship_type': 'CAUSED_ADVERSE_EVENT',
                    'source_entity_id': compound_id,
                    'target_entity_id': f"AdverseEvent-{safetyreport_id}",
                    'properties': {
                        'drug_characterization': drug_char,
                        'drug_seq': drug_data.get('drug_seq'),
                        'data_source': 'FDA FAERS'
                    },
                    'source': 'FDA FAERS'
                }
            else:
                relationship = None

            return entity, relationship

        except Exception as e:
            logger.warning(f"Failed to create compound/drug: {e}")
            return None, None

    def _create_cross_domain_relationships(self) -> List[Dict]:
        """Create cross-domain relationships to ChEMBL"""
        relationships = []

        for safetyreport_id, drugs in self.drugs_data.items():
            for drug_data in drugs:
                drug_name = drug_data.get('drug_name') or drug_data.get('medicinal_product')

                if not drug_name:
                    continue

                # Map to ChEMBL
                chembl_id = self._map_drug_to_chembl(drug_name)
                if chembl_id:
                    relationship = {
                        'relationship_type': 'TESTED_IN_CLINICAL_TRIAL',
                        'source_entity_id': f"Compound-{chembl_id}",
                        'target_entity_id': f"AdverseEvent-{safetyreport_id}",
                        'properties': {
                            'drug_name': drug_name,
                            'mapping_confidence': 'high',
                            'data_source': 'FDA FAERS-ChEMBL-Mapping'
                        },
                        'source': 'FDA FAERS-ChEMBL-Mapping'
                    }
                    relationships.append(relationship)
                    self.stats.cross_domain_relationships += 1

        return relationships

    #===========================================================
    # Cross-Domain Mapping Methods
    #===========================================================

    def _map_drug_to_chembl(self, drug_name: str) -> Optional[str]:
        """Map drug name to ChEMBL compound ID"""
        # Check cache
        if drug_name in self.chembl_cache:
            return self.chembl_cache[drug_name]

        # TODO: Implement actual mapping logic
        # This could:
        # 1. Query local ChEMBL database
        # 2. Call ChEMBL API
        # 3. Use pre-computed mapping table

        chembl_id = None

        # Cache result
        self.chembl_cache[drug_name] = chembl_id

        return chembl_id

    #===========================================================
    # Data Parsing Helper Methods
    #===========================================================

    def _parse_fda_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse FDA date format (YYYYMMDD)"""
        if not date_str or len(date_str) < 8:
            return None

        try:
            year = date_str[:4]
            month = date_str[4:6]
            day = date_str[6:8]
            return f"{year}-{month}-{day}"
        except Exception:
            return None

    def _parse_serious(self, serious_str: Optional[str]) -> bool:
        """Parse serious field to boolean"""
        if not serious_str:
            return False

        return serious_str.strip().upper() in ['Y', 'YES', '1', 'TRUE']

    def _parse_age(self, age_str: Optional[str]) -> Optional[float]:
        """Parse patient age"""
        if not age_str:
            return None

        try:
            return float(age_str.strip())
        except (ValueError, TypeError):
            return None

    def _parse_weight(self, weight_str: Optional[str]) -> Optional[float]:
        """Parse patient weight"""
        if not weight_str:
            return None

        try:
            return float(weight_str.strip())
        except (ValueError, TypeError):
            return None

    def _map_outcome_code(self, outcome_code: str) -> str:
        """Map outcome code to outcome type"""
        outcome_mapping = {
            '1': OutcomeType.RECOVERED,
            '2': OutcomeType.RECOVERING,
            '3': OutcomeType.NOT_RECOVERED,
            '4': OutcomeType.RECOVERED_WITH_SEQUELAE,
            '5': OutcomeType.FATAL,
            '6': OutcomeType.UNKNOWN
        }

        return outcome_mapping.get(outcome_code.strip(), OutcomeType.UNKNOWN).value

    def _map_reporter_type(self, reporter_type: str) -> str:
        """Map reporter type code to readable format"""
        reporter_mapping = {
            '1': ReporterType.PHYSICIAN.value,
            '2': ReporterType.PHARMACIST.value,
            '3': ReporterType.OTHER_HEALTH_PROFESSIONAL.value,
            '4': ReporterType.LAWYER.value,
            '5': ReporterType.CONSUMER.value,
            '6': ReporterType.FOREIGN.value
        }

        return reporter_mapping.get(reporter_type.strip(), 'Unknown')

    def _map_drug_characterization(self, char_code: str) -> str:
        """Map drug characterization code to role"""
        if char_code == DrugCharacterization.SUSPECT.value:
            return 'Suspect'
        elif char_code == DrugCharacterization.CONCOMITANT.value:
            return 'Concomitant'
        elif char_code == DrugCharacterization.INTERACTING.value:
            return 'Interacting'

        return 'Unknown'

    def _normalize_drug_name(self, drug_name: str) -> str:
        """Normalize drug name for consistent matching"""
        if not drug_name:
            return drug_name

        # Remove extra whitespace
        drug_name = ' '.join(drug_name.split())

        # Convert to title case
        drug_name = drug_name.title()

        return drug_name

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
        Save FAERS processing results

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
            entities_file = output_dir / f"faers_{type_name}s_{timestamp}.json"

            with open(entities_file, 'w', encoding='utf-8') as f:
                json.dump(entity_list, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(entity_list)} {entity_type} entities to: {entities_file}")

        # Save relationships
        if relationships:
            relationships_file = output_dir / f"faers_relationships_{timestamp}.json"

            with open(relationships_file, 'w', encoding='utf-8') as f:
                json.dump(relationships, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(relationships)} relationships to: {relationships_file}")

        # Save processing summary
        summary = {
            "processor": self.PROCESSOR_NAME,
            "source": "FDA FAERS (FDA Adverse Event Reporting System)",
            "timestamp": timestamp,
            "extraction_config": {
                'batch_size': self.extraction_config.batch_size,
                'max_reports': self.extraction_config.max_reports,
                'map_to_chembl': self.extraction_config.map_to_chembl,
                'include_non_serious': self.extraction_config.include_non_serious
            },
            "statistics": {
                "adverse_events_extracted": self.stats.adverse_events_extracted,
                "conditions_extracted": self.stats.conditions_extracted,
                "compounds_extracted": self.stats.compounds_extracted,
                "relationships_created": self.stats.relationships_created,
                "cross_domain_relationships": self.stats.cross_domain_relationships,
                "duplicate_reports_skipped": self.stats.duplicate_reports_skipped,
                "invalid_records_skipped": self.stats.invalid_records_skipped,
                "unique_safetyreport_ids": len(self.stats.unique_safetyreport_ids),
                "processing_time_seconds": self.stats.processing_time_seconds
            },
            "entities_by_type": {
                entity_type: len(entity_list)
                for entity_type, entity_list in entities.items()
            },
            "total_entities": sum(len(entity_list) for entity_list in entities.values()),
            "total_relationships": len(relationships),
            "errors": self.stats.errors[:10],  # Limit to first 10
            "warnings": self.stats.warnings[:10]
        }

        summary_file = output_dir / f"faers_summary_{timestamp}.json"
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
        description='FDA FAERS Adverse Events Processor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Process FAERS quarterly data files
  python -m processors.faers_processor /path/to/faers/data

  # Process with maximum report limit
  python -m processors.faers_processor /path/to/faers/data --max-reports 10000

  # Include non-serious adverse events
  python -m processors.faers_processor /path/to/faers/data --include-non-serious

  # Custom output directory
  python -m processors.faers_processor /path/to/faers/data --output /custom/output/path
        """
    )

    parser.add_argument(
        'source_path',
        help='Path to FAERS data directory containing quarterly files'
    )

    parser.add_argument(
        '--max-reports',
        type=int,
        help='Maximum number of reports to process'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Batch size for processing (default: 1000)'
    )

    parser.add_argument(
        '--include-non-serious',
        action='store_true',
        help='Include non-serious adverse events'
    )

    parser.add_argument(
        '--no-dedup',
        action='store_true',
        help='Disable deduplication by safetyreport_id'
    )

    parser.add_argument(
        '--no-cross-domain',
        action='store_true',
        help='Disable cross-domain mapping to ChEMBL'
    )

    parser.add_argument(
        '--output',
        help='Output directory (default: data/processed/documents/faers/)'
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
            'batch_size': args.batch_size,
            'max_reports': args.max_reports,
            'include_non_serious': args.include_non_serious,
            'deduplicate_by_safetyreport_id': not args.no_dedup,
            'map_to_chembl': not args.no_cross_domain
        }
    }

    # Create processor
    processor = FAERSProcessor(config)

    # Process data
    start_time = datetime.now()
    result = processor.process(args.source_path, output_to=args.output)
    elapsed_time = (datetime.now() - start_time).total_seconds()

    # Output results summary
    print(f"\n{'='*60}")
    print(f"FAERS Processing Complete")
    print(f"{'='*60}")
    print(f"Status: {result.status.value}")
    print(f"Files processed: {result.metrics.files_processed}")
    print(f"Files failed: {result.metrics.files_failed}")
    print(f"Adverse events extracted: {processor.stats.adverse_events_extracted}")
    print(f"Conditions extracted: {processor.stats.conditions_extracted}")
    print(f"Compounds extracted: {processor.stats.compounds_extracted}")
    print(f"Relationships created: {len(result.relationships)}")
    print(f"Processing time: {elapsed_time:.2f} seconds")

    if processor.stats.errors:
        print(f"\nErrors ({len(processor.stats.errors)}):")
        for error in processor.stats.errors[:5]:
            print(f"  - {error}")

    if processor.stats.warnings:
        print(f"\nWarnings ({len(processor.stats.warnings)}):")
        for warning in processor.stats.warnings[:5]:
            print(f"  - {warning}")

    return 0 if result.status == ProcessingStatus.COMPLETED else 1


if __name__ == '__main__':
    exit(main())
