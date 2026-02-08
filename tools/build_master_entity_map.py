#!/usr/bin/env python3
#===========================================================
# 制药行业知识图谱 - 主实体映射系统
# Pharmaceutical Knowledge Graph - Master Entity Mapping System
#===========================================================
# 版本: v1.0
# 创建日期: 2025-02-08
#===========================================================
# 描述/Description:
# 该工具创建跨所有数据源的统一实体视图，通过链接不同的标识符系统
# This tool creates a unified entity view across all data sources
# by linking different identifier systems
#===========================================================

import argparse
import json
import logging
import sqlite3
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database import Neo4jConnection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IdentifierMappingConfig:
    """标识符映射配置 / Identifier Mapping Configuration"""

    # Compound identifiers
    COMPOUND_PRIMARY = "inchikey"
    COMPOUND_SECONDARY = [
        "chembl_id", "drugbank_id", "pubchem_cid", "unii", "cas",
        "smiles", "pref_name", "generic_name", "brand_name"
    ]

    # Target/Protein identifiers
    TARGET_PRIMARY = "uniprot_id"
    TARGET_SECONDARY = [
        "entrez_id", "ensembl_id", "hgnc_symbol", "refseq_id",
        "gene_symbol", "protein_name"
    ]

    # Disease identifiers
    DISEASE_PRIMARY = "mondo_id"
    DISEASE_SECONDARY = [
        "icd10", "doid", "mesh", "omim", "snomed_ct",
        "disease_name", "condition_name"
    ]

    # ClinicalTrial identifiers
    TRIAL_PRIMARY = "nct_id"
    TRIAL_SECONDARY = [
        "eudract", "chict", "jma_ct", "kct", "trial_name"
    ]

    # Company/Organization identifiers
    COMPANY_PRIMARY = "grid_id"
    COMPANY_SECONDARY = [
        "ror_id", "duns", "lei", "company_name", "organization_name"
    ]

    # External mapping services
    UNIPROT_ID_MAPPING = "https://rest.uniprot.org/idmapping/run"
    UNIPROT_ID_MAPPING_STATUS = "https://rest.uniprot.org/idmapping/status/"
    MYCHEM_API = "https://mychem.info/v1"
    MYDISEASE_API = "https://mydisease.info/v1"
    IDENTIFIERS_ORG = "https://identifiers.org/rest"


class RetryableSession:
    """支持重试的HTTP会话 / HTTP Session with Retry Support"""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 0.3):
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, url: str, **kwargs) -> requests.Response:
        """GET请求 with retry / GET request with retry"""
        return self.session.get(url, timeout=30, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """POST请求 with retry / POST request with retry"""
        return self.session.post(url, timeout=30, **kwargs)


class MasterEntityMapper:
    """主实体映射器 / Master Entity Mapper"""

    def __init__(
        self,
        data_dir: Path,
        output_dir: Path,
        cache_dir: Optional[Path] = None,
        batch_size: int = 100
    ):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.cache_dir = cache_dir or output_dir / "cache"
        self.batch_size = batch_size
        self.http_session = RetryableSession()

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite database
        self.db_path = self.output_dir / "master_entity_map.db"
        self._init_database()

        # Mapping statistics
        self.stats = {
            "compounds": {"total": 0, "mapped": 0, "unmapped": 0},
            "targets": {"total": 0, "mapped": 0, "unmapped": 0},
            "diseases": {"total": 0, "mapped": 0, "unmapped": 0},
            "trials": {"total": 0, "mapped": 0, "unmapped": 0},
            "companies": {"total": 0, "mapped": 0, "unmapped": 0},
            "api_calls": 0,
            "cache_hits": 0
        }

        # Neo4j connection
        self.neo4j = Neo4jConnection()

    def _init_database(self):
        """初始化SQLite数据库 / Initialize SQLite Database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Compound mapping table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compound_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inchikey TEXT,
                chembl_id TEXT,
                drugbank_id TEXT,
                pubchem_cid TEXT,
                unii TEXT,
                cas TEXT,
                smiles TEXT,
                pref_name TEXT,
                generic_name TEXT,
                brand_name TEXT,
                canonical_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(inchikey, chembl_id, drugbank_id)
            )
        """)

        # Target mapping table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS target_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uniprot_id TEXT,
                entrez_id TEXT,
                ensembl_id TEXT,
                hgnc_symbol TEXT,
                refseq_id TEXT,
                gene_symbol TEXT,
                protein_name TEXT,
                canonical_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(uniprot_id, entrez_id, ensembl_id)
            )
        """)

        # Disease mapping table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS disease_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mondo_id TEXT,
                icd10 TEXT,
                doid TEXT,
                mesh TEXT,
                omim TEXT,
                snomed_ct TEXT,
                disease_name TEXT,
                condition_name TEXT,
                canonical_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(mondo_id, icd10, doid)
            )
        """)

        # Trial mapping table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trial_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nct_id TEXT,
                eudract TEXT,
                chict TEXT,
                jma_ct TEXT,
                kct TEXT,
                trial_name TEXT,
                canonical_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(nct_id, eudract, chict)
            )
        """)

        # Company mapping table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grid_id TEXT,
                ror_id TEXT,
                duns TEXT,
                lei TEXT,
                company_name TEXT,
                organization_name TEXT,
                canonical_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(grid_id, ror_id, duns)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_compound_inchikey ON compound_mapping(inchikey)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_compound_chembl ON compound_mapping(chembl_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_target_uniprot ON target_mapping(uniprot_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_target_entrez ON target_mapping(entrez_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_disease_mondo ON disease_mapping(mondo_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trial_nct ON trial_mapping(nct_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_grid ON company_mapping(grid_id)")

        conn.commit()
        conn.close()

        logger.info(f"Database initialized at {self.db_path}")

    def extract_identifiers_from_files(self) -> Dict[str, List[Dict]]:
        """从处理后的文件中提取标识符 / Extract identifiers from processed files"""
        logger.info("Extracting identifiers from processed files...")

        extracted_data = {
            "compounds": [],
            "targets": [],
            "diseases": [],
            "trials": [],
            "companies": []
        }

        # Scan all JSON files in processed directories
        entities_dir = self.data_dir / "entities"

        if not entities_dir.exists():
            logger.warning(f"Entities directory not found: {entities_dir}")
            return extracted_data

        # Process each entity type directory
        for entity_type_dir in entities_dir.iterdir():
            if not entity_type_dir.is_dir():
                continue

            entity_type = entity_type_dir.name
            logger.info(f"Processing entity type: {entity_type}")

            # Process JSON files
            for json_file in entity_type_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Handle different file structures
                    if isinstance(data, list):
                        entities = data
                    elif isinstance(data, dict):
                        if "data" in data:
                            entities = data["data"]
                        elif "results" in data:
                            entities = data["results"]
                        else:
                            entities = [data]
                    else:
                        logger.warning(f"Unexpected data structure in {json_file}")
                        continue

                    # Categorize entities
                    for entity in entities:
                        categorized = self._categorize_entity(entity, entity_type)
                        if categorized:
                            entity_type_name, entity_data = categorized
                            extracted_data[entity_type_name].append(entity_data)

                except Exception as e:
                    logger.error(f"Error processing {json_file}: {str(e)}")

        # Log statistics
        for entity_type, entities in extracted_data.items():
            self.stats[entity_type]["total"] = len(entities)
            logger.info(f"Extracted {len(entities)} {entity_type}")

        return extracted_data

    def _categorize_entity(self, entity: Dict, source: str) -> Optional[Tuple[str, Dict]]:
        """对实体进行分类 / Categorize entity"""
        entity_lower = {k.lower(): v for k, v in entity.items()}

        # Compound detection
        if any(k in entity_lower for k in ['inchikey', 'chembl_id', 'drugbank_id', 'smiles']):
            return "compounds", {
                "inchikey": entity.get("inchikey") or entity_lower.get("inchikey"),
                "chembl_id": entity.get("chembl_id") or entity_lower.get("chembl_id"),
                "drugbank_id": entity.get("drugbank_id") or entity_lower.get("drugbank_id"),
                "pubchem_cid": entity.get("pubchem_cid") or entity_lower.get("pubchem_cid"),
                "unii": entity.get("unii") or entity_lower.get("unii"),
                "cas": entity.get("cas") or entity_lower.get("cas"),
                "smiles": entity.get("smiles") or entity_lower.get("smiles"),
                "pref_name": entity.get("pref_name") or entity.get("name"),
                "generic_name": entity.get("generic_name"),
                "brand_name": entity.get("brand_name"),
                "source": source
            }

        # Target detection
        if any(k in entity_lower for k in ['uniprot_id', 'uniprot_accession', 'gene_symbol', 'protein_name']):
            return "targets", {
                "uniprot_id": entity.get("uniprot_id") or entity.get("uniprot_accession"),
                "entrez_id": entity.get("entrez_id") or entity_lower.get("entrez"),
                "ensembl_id": entity.get("ensembl_id") or entity_lower.get("ensembl"),
                "hgnc_symbol": entity.get("hgnc_symbol") or entity.get("gene_symbol"),
                "refseq_id": entity.get("refseq_id"),
                "gene_symbol": entity.get("gene_symbol"),
                "protein_name": entity.get("protein_name") or entity.get("name"),
                "source": source
            }

        # Disease detection
        if any(k in entity_lower for k in ['mondo_id', 'icd10', 'doid', 'mesh', 'disease']):
            return "diseases", {
                "mondo_id": entity.get("mondo_id"),
                "icd10": entity.get("icd10") or entity_lower.get("icd10_code"),
                "doid": entity.get("doid"),
                "mesh": entity.get("mesh") or entity_lower.get("mesh_id"),
                "omim": entity.get("omim"),
                "snomed_ct": entity.get("snomed_ct"),
                "disease_name": entity.get("disease_name") or entity.get("name"),
                "condition_name": entity.get("condition_name"),
                "source": source
            }

        # Clinical trial detection
        if any(k in entity_lower for k in ['nct_id', 'nct_number', 'eudract']):
            return "trials", {
                "nct_id": entity.get("nct_id") or entity.get("nct_number"),
                "eudract": entity.get("eudract"),
                "chict": entity.get("chict"),
                "jma_ct": entity.get("jma_ct"),
                "kct": entity.get("kct"),
                "trial_name": entity.get("trial_name") or entity.get("brief_title"),
                "source": source
            }

        # Company detection
        if any(k in entity_lower for k in ['grid_id', 'ror_id', 'company_name', 'manufacturer']):
            return "companies", {
                "grid_id": entity.get("grid_id"),
                "ror_id": entity.get("ror_id"),
                "duns": entity.get("duns"),
                "lei": entity.get("lei"),
                "company_name": entity.get("company_name") or entity.get("manufacturer"),
                "organization_name": entity.get("organization_name"),
                "source": source
            }

        return None

    def map_compound_identifiers(self, compounds: List[Dict]) -> List[Dict]:
        """映射化合物标识符 / Map compound identifiers"""
        logger.info("Mapping compound identifiers...")

        mapped_compounds = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for compound in compounds:
            # Determine canonical ID (prefer InChIKey)
            inchikey = compound.get("inchikey")
            chembl_id = compound.get("chembl_id")

            if inchikey:
                canonical_id = f"COMPOUND:{inchikey}"
            elif chembl_id:
                canonical_id = f"COMPOUND:{chembl_id}"
            else:
                # Generate hash-based ID
                id_string = json.dumps(compound, sort_keys=True)
                hash_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                canonical_id = f"COMPOUND:HASH:{hash_id}"

            compound["canonical_id"] = canonical_id

            # Try external mapping for missing identifiers
            if not inchikey and chembl_id:
                external_mapping = self._query_mychem(chembl_id)
                if external_mapping:
                    compound.update(external_mapping)
                    self.stats["api_calls"] += 1

            # Insert into database
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO compound_mapping
                    (inchikey, chembl_id, drugbank_id, pubchem_cid, unii, cas, smiles,
                     pref_name, generic_name, brand_name, canonical_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    compound.get("inchikey"),
                    compound.get("chembl_id"),
                    compound.get("drugbank_id"),
                    compound.get("pubchem_cid"),
                    compound.get("unii"),
                    compound.get("cas"),
                    compound.get("smiles"),
                    compound.get("pref_name"),
                    compound.get("generic_name"),
                    compound.get("brand_name"),
                    canonical_id
                ))
                self.stats["compounds"]["mapped"] += 1
                mapped_compounds.append(compound)
            except sqlite3.IntegrityError:
                # Record already exists
                pass

        conn.commit()
        conn.close()

        logger.info(f"Mapped {len(mapped_compounds)} compounds")
        return mapped_compounds

    def map_target_identifiers(self, targets: List[Dict]) -> List[Dict]:
        """映射靶标标识符 / Map target identifiers"""
        logger.info("Mapping target identifiers...")

        mapped_targets = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for target in targets:
            # Determine canonical ID (prefer UniProt)
            uniprot_id = target.get("uniprot_id")
            entrez_id = target.get("entrez_id")

            if uniprot_id:
                canonical_id = f"TARGET:{uniprot_id}"
            elif entrez_id:
                canonical_id = f"TARGET:{entrez_id}"
            else:
                # Generate hash-based ID
                id_string = json.dumps(target, sort_keys=True)
                hash_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                canonical_id = f"TARGET:HASH:{hash_id}"

            target["canonical_id"] = canonical_id

            # Try external mapping for missing identifiers
            if not uniprot_id and entrez_id:
                external_mapping = self._query_uniprot(entrez_id, "NCBI GeneID")
                if external_mapping:
                    target.update(external_mapping)
                    self.stats["api_calls"] += 1

            # Insert into database
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO target_mapping
                    (uniprot_id, entrez_id, ensembl_id, hgnc_symbol, refseq_id,
                     gene_symbol, protein_name, canonical_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    target.get("uniprot_id"),
                    target.get("entrez_id"),
                    target.get("ensembl_id"),
                    target.get("hgnc_symbol"),
                    target.get("refseq_id"),
                    target.get("gene_symbol"),
                    target.get("protein_name"),
                    canonical_id
                ))
                self.stats["targets"]["mapped"] += 1
                mapped_targets.append(target)
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        conn.close()

        logger.info(f"Mapped {len(mapped_targets)} targets")
        return mapped_targets

    def map_disease_identifiers(self, diseases: List[Dict]) -> List[Dict]:
        """映射疾病标识符 / Map disease identifiers"""
        logger.info("Mapping disease identifiers...")

        mapped_diseases = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for disease in diseases:
            # Determine canonical ID (prefer MONDO)
            mondo_id = disease.get("mondo_id")
            doid = disease.get("doid")

            if mondo_id:
                canonical_id = f"DISEASE:{mondo_id}"
            elif doid:
                canonical_id = f"DISEASE:{doid}"
            else:
                # Generate hash-based ID
                id_string = json.dumps(disease, sort_keys=True)
                hash_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                canonical_id = f"DISEASE:HASH:{hash_id}"

            disease["canonical_id"] = canonical_id

            # Try external mapping for missing identifiers
            disease_name = disease.get("disease_name")
            if not mondo_id and disease_name:
                external_mapping = self._query_mydisease(disease_name)
                if external_mapping:
                    disease.update(external_mapping)
                    self.stats["api_calls"] += 1

            # Insert into database
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO disease_mapping
                    (mondo_id, icd10, doid, mesh, omim, snomed_ct,
                     disease_name, condition_name, canonical_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    disease.get("mondo_id"),
                    disease.get("icd10"),
                    disease.get("doid"),
                    disease.get("mesh"),
                    disease.get("omim"),
                    disease.get("snomed_ct"),
                    disease.get("disease_name"),
                    disease.get("condition_name"),
                    canonical_id
                ))
                self.stats["diseases"]["mapped"] += 1
                mapped_diseases.append(disease)
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        conn.close()

        logger.info(f"Mapped {len(mapped_diseases)} diseases")
        return mapped_diseases

    def map_trial_identifiers(self, trials: List[Dict]) -> List[Dict]:
        """映射临床试验标识符 / Map clinical trial identifiers"""
        logger.info("Mapping clinical trial identifiers...")

        mapped_trials = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for trial in trials:
            # Determine canonical ID (prefer NCT)
            nct_id = trial.get("nct_id")

            if nct_id:
                canonical_id = f"TRIAL:{nct_id}"
            else:
                # Generate hash-based ID
                id_string = json.dumps(trial, sort_keys=True)
                hash_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                canonical_id = f"TRIAL:HASH:{hash_id}"

            trial["canonical_id"] = canonical_id

            # Insert into database
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO trial_mapping
                    (nct_id, eudract, chict, jma_ct, kct, trial_name, canonical_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    trial.get("nct_id"),
                    trial.get("eudract"),
                    trial.get("chict"),
                    trial.get("jma_ct"),
                    trial.get("kct"),
                    trial.get("trial_name"),
                    canonical_id
                ))
                self.stats["trials"]["mapped"] += 1
                mapped_trials.append(trial)
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        conn.close()

        logger.info(f"Mapped {len(mapped_trials)} trials")
        return mapped_trials

    def map_company_identifiers(self, companies: List[Dict]) -> List[Dict]:
        """映射公司标识符 / Map company identifiers"""
        logger.info("Mapping company identifiers...")

        mapped_companies = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for company in companies:
            # Determine canonical ID (prefer GRID)
            grid_id = company.get("grid_id")
            ror_id = company.get("ror_id")

            if grid_id:
                canonical_id = f"COMPANY:{grid_id}"
            elif ror_id:
                canonical_id = f"COMPANY:{ror_id}"
            else:
                # Generate hash-based ID based on company name
                company_name = company.get("company_name") or company.get("organization_name")
                if company_name:
                    hash_id = hashlib.md5(company_name.encode()).hexdigest()[:16]
                    canonical_id = f"COMPANY:HASH:{hash_id}"
                else:
                    hash_id = hashlib.md5(json.dumps(company, sort_keys=True).encode()).hexdigest()[:16]
                    canonical_id = f"COMPANY:HASH:{hash_id}"

            company["canonical_id"] = canonical_id

            # Insert into database
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO company_mapping
                    (grid_id, ror_id, duns, lei, company_name, organization_name, canonical_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    company.get("grid_id"),
                    company.get("ror_id"),
                    company.get("duns"),
                    company.get("lei"),
                    company.get("company_name"),
                    company.get("organization_name"),
                    canonical_id
                ))
                self.stats["companies"]["mapped"] += 1
                mapped_companies.append(company)
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        conn.close()

        logger.info(f"Mapped {len(mapped_companies)} companies")
        return mapped_companies

    def _query_mychem(self, chembl_id: str) -> Optional[Dict]:
        """查询MyChem.info获取化合物交叉引用 / Query MyChem.info for compound cross-references"""
        cache_key = f"mychem_{chembl_id}"
        cached = self._get_from_cache(cache_key)
        if cached:
            self.stats["cache_hits"] += 1
            return cached

        try:
            url = f"{IdentifierMappingConfig.MYCHEM_API}/chembl/{chembl_id}"
            response = self.http_session.get(url)
            if response.status_code == 200:
                data = response.json()
                result = {
                    "inchikey": data.get("inchikey"),
                    "pubchem_cid": data.get("pubchem"),
                    "unii": data.get("unii"),
                    "drugbank_id": data.get("drugbank")
                }
                self._save_to_cache(cache_key, result)
                return result
        except Exception as e:
            logger.warning(f"Error querying MyChem for {chembl_id}: {str(e)}")

        return None

    def _query_uniprot(self, identifier: str, from_db: str = "UniProtKB_AC-ID") -> Optional[Dict]:
        """查询UniProt ID映射服务 / Query UniProt ID mapping service"""
        cache_key = f"uniprot_{identifier}_{from_db}"
        cached = self._get_from_cache(cache_key)
        if cached:
            self.stats["cache_hits"] += 1
            return cached

        try:
            # Submit mapping job
            url = IdentifierMappingConfig.UNIPROT_ID_MAPPING
            data = {
                "from": from_db,
                "to": "UniProtKB,Ensembl,NCBI GeneID,HGNC",
                "ids": identifier
            }
            response = self.http_session.post(url, data=data)

            if response.status_code == 200:
                job_id = response.json().get("jobId")

                # Poll for results
                status_url = f"{IdentifierMappingConfig.UNIPROT_ID_MAPPING_STATUS}{job_id}"
                for _ in range(30):  # Max 30 seconds
                    time.sleep(1)
                    status_response = self.http_session.get(status_url)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("status") == "finished":
                            results = status_data.get("results", {})
                            if results and identifier in results:
                                result_data = results[identifier]
                                result = {
                                    "uniprot_id": result_data.get("UniProtKB"),
                                    "ensembl_id": result_data.get("Ensembl"),
                                    "entrez_id": result_data.get("NCBI GeneID"),
                                    "hgnc_symbol": result_data.get("HGNC")
                                }
                                self._save_to_cache(cache_key, result)
                                return result
                            break

        except Exception as e:
            logger.warning(f"Error querying UniProt for {identifier}: {str(e)}")

        return None

    def _query_mydisease(self, disease_name: str) -> Optional[Dict]:
        """查询MyDisease.info获取疾病交叉引用 / Query MyDisease.info for disease cross-references"""
        cache_key = f"mydisease_{disease_name}"
        cached = self._get_from_cache(cache_key)
        if cached:
            self.stats["cache_hits"] += 1
            return cached

        try:
            url = f"{IdentifierMappingConfig.MYDISEASE_API}/query"
            params = {"q": disease_name, "fields": "mondo,doid,icd10,mesh,omim"}
            response = self.http_session.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    top_result = data[0]
                    result = {
                        "mondo_id": top_result.get("mondo"),
                        "doid": top_result.get("doid"),
                        "icd10": top_result.get("icd10"),
                        "mesh": top_result.get("mesh"),
                        "omim": top_result.get("omim")
                    }
                    self._save_to_cache(cache_key, result)
                    return result

        except Exception as e:
            logger.warning(f"Error querying MyDisease for {disease_name}: {str(e)}")

        return None

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取数据 / Get data from cache"""
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None

    def _save_to_cache(self, key: str, data: Any):
        """保存数据到缓存 / Save data to cache"""
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Error saving to cache {key}: {str(e)}")

    def generate_neo4j_merge_queries(self) -> Path:
        """生成Neo4j合并查询 / Generate Neo4j merge queries"""
        logger.info("Generating Neo4j merge queries...")

        output_file = self.output_dir / "neo4j_merge_queries.cypher"

        queries = []
        queries.append("// ========================================")
        queries.append("// PharmaKG - Master Entity Merge Queries")
        queries.append(f"// Generated: {datetime.now().isoformat()}")
        queries.append("// ========================================\n")

        # Read mappings from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Compound MERGE_TO relationships
        cursor.execute("SELECT * FROM compound_mapping")
        compounds = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        queries.append("// Compound MERGE_TO relationships")
        for compound in compounds:
            compound_dict = dict(zip(columns, compound))
            canonical_id = compound_dict.get("canonical_id")

            # Find all non-null identifiers
            identifiers = {k: v for k, v in compound_dict.items()
                          if v is not None and k not in ["id", "canonical_id", "created_at", "updated_at"]}

            for id_type, id_value in identifiers.items():
                if id_value and canonical_id:
                    queries.append(f"""
// Merge {id_type} {id_value} to canonical {canonical_id}
MATCH (c:Compound {{{id_type}: '{id_value}'}})
WHERE NOT c:Canonical
MATCH (canonical:Compound:Canonical {{id: '{canonical_id}'}})
MERGE (c)-[:MERGED_TO {{source: 'master_mapping', confidence: 1.0, evidence_level: 'A', merged_at: datetime()}}]->(canonical);
""")

        # Target MERGE_TO relationships
        cursor.execute("SELECT * FROM target_mapping")
        targets = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        queries.append("\n// Target MERGE_TO relationships")
        for target in targets:
            target_dict = dict(zip(columns, target))
            canonical_id = target_dict.get("canonical_id")

            identifiers = {k: v for k, v in target_dict.items()
                          if v is not None and k not in ["id", "canonical_id", "created_at", "updated_at"]}

            for id_type, id_value in identifiers.items():
                if id_value and canonical_id:
                    queries.append(f"""
// Merge {id_type} {id_value} to canonical {canonical_id}
MATCH (t:Target {{{id_type}: '{id_value}'}})
WHERE NOT t:Canonical
MATCH (canonical:Target:Canonical {{id: '{canonical_id}'}})
MERGE (t)-[:MERGED_TO {{source: 'master_mapping', confidence: 1.0, evidence_level: 'A', merged_at: datetime()}}]->(canonical);
""")

        # Disease MERGE_TO relationships
        cursor.execute("SELECT * FROM disease_mapping")
        diseases = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        queries.append("\n// Disease MERGE_TO relationships")
        for disease in diseases:
            disease_dict = dict(zip(columns, disease))
            canonical_id = disease_dict.get("canonical_id")

            identifiers = {k: v for k, v in disease_dict.items()
                          if v is not None and k not in ["id", "canonical_id", "created_at", "updated_at"]}

            for id_type, id_value in identifiers.items():
                if id_value and canonical_id:
                    queries.append(f"""
// Merge {id_type} {id_value} to canonical {canonical_id}
MATCH (d:Disease {{{id_type}: '{id_value}'}})
WHERE NOT d:Canonical
MATCH (canonical:Disease:Canonical {{id: '{canonical_id}'}})
MERGE (d)-[:MERGED_TO {{source: 'master_mapping', confidence: 1.0, evidence_level: 'A', merged_at: datetime()}}]->(canonical);
""")

        conn.close()

        # Write queries to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(queries))

        logger.info(f"Generated {output_file}")
        return output_file

    def generate_summary_report(self) -> Dict:
        """生成汇总报告 / Generate summary report"""
        # Calculate unmapped counts
        for entity_type in ["compounds", "targets", "diseases", "trials", "companies"]:
            total = self.stats[entity_type]["total"]
            mapped = self.stats[entity_type]["mapped"]
            self.stats[entity_type]["unmapped"] = total - mapped

        summary = {
            "generated_at": datetime.now().isoformat(),
            "database_path": str(self.db_path),
            "statistics": self.stats,
            "coverage": {
                "compounds": self._calculate_coverage("compounds"),
                "targets": self._calculate_coverage("targets"),
                "diseases": self._calculate_coverage("diseases"),
                "trials": self._calculate_coverage("trials"),
                "companies": self._calculate_coverage("companies")
            },
            "identifier_systems": {
                "compounds": {
                    "primary": IdentifierMappingConfig.COMPOUND_PRIMARY,
                    "secondary": IdentifierMappingConfig.COMPOUND_SECONDARY
                },
                "targets": {
                    "primary": IdentifierMappingConfig.TARGET_PRIMARY,
                    "secondary": IdentifierMappingConfig.TARGET_SECONDARY
                },
                "diseases": {
                    "primary": IdentifierMappingConfig.DISEASE_PRIMARY,
                    "secondary": IdentifierMappingConfig.DISEASE_SECONDARY
                },
                "trials": {
                    "primary": IdentifierMappingConfig.TRIAL_PRIMARY,
                    "secondary": IdentifierMappingConfig.TRIAL_SECONDARY
                },
                "companies": {
                    "primary": IdentifierMappingConfig.COMPANY_PRIMARY,
                    "secondary": IdentifierMappingConfig.COMPANY_SECONDARY
                }
            }
        }

        # Save summary to JSON
        summary_file = self.output_dir / "mapping_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Generated summary report: {summary_file}")
        return summary

    def _calculate_coverage(self, entity_type: str) -> Dict[str, float]:
        """计算标识符覆盖率 / Calculate identifier coverage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        table_map = {
            "compounds": "compound_mapping",
            "targets": "target_mapping",
            "diseases": "disease_mapping",
            "trials": "trial_mapping",
            "companies": "company_mapping"
        }

        table = table_map.get(entity_type)
        if not table:
            return {}

        cursor.execute(f"SELECT * FROM {table}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        coverage = {}
        for col in columns:
            if col in ["id", "canonical_id", "created_at", "updated_at"]:
                continue
            non_null = sum(1 for row in rows if row[columns.index(col)] is not None)
            coverage[col] = round(non_null / len(rows) * 100, 2) if rows else 0

        conn.close()
        return coverage

    def run(self, incremental: bool = False) -> Dict:
        """运行主实体映射流程 / Run master entity mapping pipeline"""
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("Starting Master Entity Mapping Pipeline")
        logger.info("=" * 60)

        # Step 1: Extract identifiers from files
        extracted_data = self.extract_identifiers_from_files()

        # Step 2: Map identifiers for each entity type
        if extracted_data["compounds"]:
            self.map_compound_identifiers(extracted_data["compounds"])

        if extracted_data["targets"]:
            self.map_target_identifiers(extracted_data["targets"])

        if extracted_data["diseases"]:
            self.map_disease_identifiers(extracted_data["diseases"])

        if extracted_data["trials"]:
            self.map_trial_identifiers(extracted_data["trials"])

        if extracted_data["companies"]:
            self.map_company_identifiers(extracted_data["companies"])

        # Step 3: Generate Neo4j merge queries
        self.generate_neo4j_merge_queries()

        # Step 4: Generate summary report
        summary = self.generate_summary_report()

        elapsed_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"Pipeline completed in {elapsed_time:.2f} seconds")
        logger.info(f"API calls made: {self.stats['api_calls']}")
        logger.info(f"Cache hits: {self.stats['cache_hits']}")
        logger.info("=" * 60)

        return summary


def main():
    """主函数 / Main function"""
    parser = argparse.ArgumentParser(
        description="Build Master Entity Map for PharmaKG"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("/root/autodl-tmp/pj-pharmaKG/data/processed"),
        help="Path to processed data directory"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/root/autodl-tmp/pj-pharmaKG/data/validated"),
        help="Path to output directory"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Path to cache directory (default: output_dir/cache)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for processing"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Incremental update mode"
    )

    args = parser.parse_args()

    # Create mapper instance
    mapper = MasterEntityMapper(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        cache_dir=args.cache_dir,
        batch_size=args.batch_size
    )

    # Run pipeline
    summary = mapper.run(incremental=args.incremental)

    # Print summary
    print("\n" + "=" * 60)
    print("MAPPING SUMMARY")
    print("=" * 60)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
