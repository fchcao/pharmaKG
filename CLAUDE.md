# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PharmaKG** is a Pharmaceutical Knowledge Graph covering the entire pharmaceutical industry workflow, integrating four core business domains: Research & Development (R&D), Clinical Trials, Supply Chain Management, and Regulatory Compliance.

- **Version**: v1.0
- **Status**: Technical Implementation Phase (Phase 1)
- **Language**: Python 3.8+
- **Primary Technologies**: Neo4j 5.x, FastAPI, Turtle/OWL/SHACL ontologies

## Development Commands

### Environment Setup
```bash
# Activate the existing conda environment (AutoDL server)
conda activate pharmakg-api

# Install Python dependencies (if needed)
pip install -r api/requirements.txt

# Create .env file for local development (optional - defaults are provided)
cp api/.env.example api/.env  # Edit with your settings

# Start Neo4j (if using Docker)
docker-compose up -d neo4j
```

**Note**: This project has a dedicated conda environment `pharmakg-api` pre-configured on AutoDL servers. Always activate this environment before running any commands.

### API Service
```bash
# Start FastAPI server
cd api
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Access API documentation
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)

# Health check
curl http://localhost:8000/health
```

### ETL Pipelines
```bash
# Run specific domain pipeline
python3 -m etl.cli run rd --limit-compounds 1000
python3 -m etl.cli run clinical --query "cancer" --limit 500
python3 -m etl.cli run regulatory --data-file /path/to/fda.zip
python3 -m etl.cli run supply-chain --source fda_shortages

# Run all pipelines
python3 -m etl.cli run-all

# Check pipeline status
python3 -m etl.cli status

# Validate configuration
python3 -m etl.cli validate
```

### Testing
```bash
# Run tests (if test suite is implemented)
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=api --cov=etl --cov-report=html

# Note: Test files may need to be created - check CHECKLIST.md for test coverage status
```

### Data Collection Processors (NEW)
```bash
# ChEMBL 36 SQLite processor (tested with 28GB database)
python3 -m processors.chembl_processor /path/to/chembl_36.db --limit-compounds 1000

# UniProt API processor (with rate limiting)
python3 -m processors.uniprot_processor uniprot_ids.txt --organism human

# KEGG pathway processor
python3 -m processors.kegg_processor --organism human --limit 50

# ClinicalTrials.gov API v2 (with study limits)
python3 -m processors.clinicaltrials_processor --mode query_by_disease --query-term "cancer"

# FDA Drugs@FDA processor
python3 -m processors.drugsatfda_processor --mode all --max-applications 100

# Run all data collection pipelines
python3 scripts/run_full_pipeline.py
```

### Project Validation
```bash
# Automated validation
python3 scripts/check_project.py
# or
chmod +x scripts/check_project.sh && ./scripts/check_project.sh
```

### Neo4j Access
```bash
# Neo4j Browser: http://localhost:7474
# Username: neo4j
# Password: pharmaKG2024!

# Cypher Shell
cypher-shell -a bolt://localhost:7687 -u neo4j -p pharmaKG2024!
```

### Deployment
```bash
# Docker deployment
cd deploy && chmod +x deploy.sh && ./deploy.sh

# AutoDL cloud deployment
cd deploy && chmod +x deploy-autodl.sh && ./deploy-autodl.sh
```

### Neo4j Schema Initialization
```bash
# Initialize constraints and indexes (run once after Neo4j setup)
cypher-shell -a bolt://localhost:7687 -u neo4j -p pharmaKG2024! < deploy/scripts/init_constraints.cypher

# Or via the API after startup (if schema initialization endpoint is available)
curl -X POST http://localhost:8000/api/v1/admin/init-schema
```

## Architecture Overview

### Layered Architecture
```
Application Layer: Query UI | API Service | Data Import
Service Layer:      Neo4j (Graph DB) | PostgreSQL (Meta DB) | Redis (Cache)
Data Layer:         Knowledge Graph (70+ entities, 100+ relations)
```

### Domain-Driven Design
Code is organized by business domains, each with dedicated services:
- **Research Domain**: Compounds, targets, pathways, assays
- **Clinical Domain**: Trials, subjects, interventions, outcomes
- **Supply Chain Domain**: Manufacturers, suppliers, facilities, shortages
- **Regulatory Domain**: Submissions, approvals, agencies, compliance

### Key Design Patterns

1. **Service Pattern**: Each domain has a dedicated service class in `api/services/`
2. **ETL Pipeline Pattern**: Extract-Transform-Load with configurable pipelines in `etl/pipelines/`
3. **Multi-dimensional Classification**: Entities classified along multiple dimensions (not single hierarchy)
4. **Context-dependent Relations**: Relationships carry rich properties (activity values, confidence scores, temporal validity)

### API Endpoint Structure
The API is organized under `/api/v1/` with domain-specific prefixes:
- `/api/v1/rd/*` - Research & Development endpoints (compounds, targets, pathways)
- `/api/v1/clinical/*` - Clinical trial endpoints (trials, subjects, outcomes)
- `/api/v1/supply/*` - Supply chain endpoints (manufacturers, shortages)
- `/api/v1/regulatory/*` - Regulatory endpoints (submissions, approvals)
- `/api/v1/cross/*` - Cross-domain query endpoints
- `/api/v1/advanced/*` - Advanced multi-hop and aggregation queries
- `/health` - Health check endpoint

### Error Handling
The API uses a global exception handler that returns structured error responses:
```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "details": {}
}
```

## Directory Structure

```
api/                          # FastAPI REST API service
  ├── main.py                 # Main application (888 lines)
  ├── config.py               # API configuration (Pydantic Settings)
  ├── database.py             # Neo4j connection management
  ├── models.py               # Pydantic data models
  └── services/               # Domain services
      ├── research_domain.py  # R&D domain service
      ├── clinical_domain.py  # Clinical domain service
      ├── supply_regulatory.py # Supply chain & regulatory
      ├── advanced_queries.py # Multi-hop queries
      └── aggregate_queries.py # Statistical queries

processors/                   # NEW: Data collection processors (Phase 1-5)
  ├── base.py                # Base processor class
  ├── chembl_processor.py    # ChEMBL 36 SQLite processor
  ├── uniprot_processor.py    # UniProt API processor
  ├── kegg_processor.py      # KEGG pathway processor
  ├── clinicaltrials_processor.py # ClinicalTrials.gov processor
  ├── drugsatfda_processor.py # FDA Drugs@FDA processor
  ├── faers_processor.py     # FAERS adverse events processor
  ├── shortage_processor.py   # Drug shortage processor
  ├── pda_pdf_processor.py   # PDA technical report processor
  ├── drugbank_processor.py  # DrugBank XML processor
  ├── dailymed_processor.py  # DailyMed SPL processor
  ├── rd_processor.py         # R&D domain processor
  ├── clinical_processor.py   # Clinical domain processor
  ├── regulatory_processor.py # Regulatory domain processor
  └── ...

tools/                        # NEW: Integration and inference tools
  ├── build_master_entity_map.py # Identifier mapping system
  ├── infer_cross_domain_relationships.py # Cross-domain inference
  ├── comprehensive_import.py  # Data import orchestration
  └── ...

etl/                          # Extract-Transform-Load pipeline
  ├── cli.py                  # Command-line interface (414 lines)
  ├── config.py               # ETL configuration with predefined pipelines
  ├── extractors/             # Data extractors (ChEMBL, ClinicalTrials.gov, FDA, DrugBank)
  ├── transformers/           # Data transformers
  ├── loaders/                # Neo4j data loaders
  ├── pipelines/              # Domain-specific ETL pipelines
  └── quality/                # Data quality validation

graph_analytics/              # Graph analysis algorithms
  ├── algorithms.py           # Graph algorithms (1117 lines)
  ├── inference.py            # Relationship inference
  ├── embeddings.py           # Graph embeddings
  └── visualization.py        # Graph visualization

ml_analytics/                 # Machine learning models
  ├── models.py               # ML model definitions
  ├── predictors.py           # Prediction models
  └── reasoning.py            # Reasoning engine

ontologies/                   # Ontology definitions (Turtle format)
  ├── pharma-rd-core.ttl      # R&D domain ontology
  ├── pharma-clinical-core.ttl # Clinical domain ontology
  ├── pharma-sc-regulatory-core.ttl # SC & regulatory ontology
  ├── pharma-relationship-semantics.ttl # Relationship definitions
  └── pharma-constraints-rules.shacl   # SHACL constraints

scripts/                      # Utility scripts
  ├── check_project.py        # Python validation script
  ├── check_project.sh        # Bash validation script
  ├── import_chembl_to_neo4j.py # NEW: Neo4j import for ChEMBL
  ├── run_full_pipeline.py   # NEW: Pipeline orchestration
  ├── extract_uniprot_from_chembl.py # NEW: UniProt ID extraction
  └── test_*.py              # NEW: Processor test scripts

docs/                         # Documentation
  ├── schema/                 # Schema design documents
  ├── interview-notes/        # Domain interview notes (3 rounds)
  ├── data-sources/           # Data source documentation
  ├── CHEMBL_PROCESSOR.md     # NEW: ChEMBL processor documentation
  ├── UNIPROT_PROCESSOR.md    # NEW: UniProt processor documentation
  ├── KEGG_PROCESSOR.md      # NEW: KEGG processor documentation
  ├── CLINICALTRIALS_PROCESSOR.md # NEW: ClinicalTrials processor
  ├── DRUGSATFDA_PROCESSOR.md # NEW: Drugs@FDA processor documentation
  ├── COMPLETE_IMPLEMENTATION_SUMMARY.md # NEW: Overall summary
  ├── QUICK_START_GUIDE.md    # NEW: Usage guide
  └── ...                     # 32+ documentation files

deploy/                       # Deployment configuration
  ├── deploy.sh               # Docker deployment script
  ├── deploy-autodl.sh        # AutoDL deployment script
  └── QUICKSTART_AUTODL.md    # AutoDL quick start guide

tests/                        # Test suite (if implemented)
  ├── test_api.py             # API endpoint tests
  ├── test_etl.py             # ETL pipeline tests
  └── conftest.py             # Pytest configuration
```

## Configuration

### API Configuration (`api/config.py`)
- Uses Pydantic Settings for configuration
- Environment variables can be loaded from `.env` file
- Key settings: Neo4j URI/user/password, CORS, pagination, rate limiting

### ETL Configuration (`etl/config.py`)
- Uses Pydantic BaseModel for configuration
- Predefined pipeline configurations: RD_PIPELINE_CONFIG, CLINICAL_PIPELINE_CONFIG, SC_PIPELINE_CONFIG, REGULATORY_PIPELINE_CONFIG
- Configurable: batch size, retry logic, API rate limits, data quality settings

## Code Conventions

- **File names**: snake_case (e.g., `research_domain.py`)
- **Class names**: PascalCase (e.g., `ResearchDomainService`)
- **Function names**: snake_case (e.g., `get_compound_by_id`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `NEO4J_URI`)
- **Database queries**: Cypher language for Neo4j
- **Bilingual documentation**: Documentation in Chinese and English

## Important Notes

- **Ontology Standards**: Uses W3C standards (Turtle, OWL, SHACL) for ontology definitions
- **Connection Management**: Neo4j connections managed centrally via `Neo4jConnection` class in `api/database.py`
- **Quality Validation**: ETL includes built-in data quality validation in `etl/quality/`
- **AutoDL Deployment**: Special deployment script for AutoDL cloud service (direct installation, no Docker required)
- **Validation**: Automated validation scripts check project completeness (139 items in CHECKLIST.md)
- **Global Error Handling**: FastAPI includes a global exception handler in `api/main.py` that standardizes error responses across all endpoints
- **Schema Initialization**: Neo4j constraints and indexes should be initialized after first deployment (see deployment commands above)

## Data Sources

### R&D Domain
- **ChEMBL 36**: Bioactivity data for compounds and targets (2.8M+ compounds, 28GB SQLite)
- **UniProt**: Protein sequence and function data (enhanced target information)
- **KEGG**: Biological pathway data (metabolic, signaling, disease pathways)

### Clinical Domain
- **ClinicalTrials.gov**: Clinical trial registry (400K+ studies, API v2)
- **FDA Drugs@FDA**: Drug approval and submission data

### Safety & Supply Chain Domain
- **FAERS**: FDA Adverse Event Reporting System (quarterly data, 10M+ reports)
- **Drug Shortages**: FDA drug shortage database (daily updates)

### High-Value Datasets
- **DrugBank**: Comprehensive drug data (requires academic license)
- **DailyMed**: FDA product labels with SPL XML format

### Document Sources
- **FDA CRLs**: Complete Response Letters (regulatory decisions)
- **PDA Technical Reports**: Pharmaceutical manufacturing standards (108 PDFs)

## Project Status

### Completed
- Three rounds of domain interviews (56 questions, 71 decisions)
- Technology stack selection (Neo4j, Turtle+OWL+SHACL)
- Deployment configuration for Docker and AutoDL
- Core API structure with domain services
- ETL pipeline framework
- Graph analytics and ML analytics modules
- Ontology definitions and schema design documentation
- **NEW**: Phase 1-5 data collection processors (17 processors implemented)
- **NEW**: Identifier mapping and cross-domain inference tools
- **NEW**: ChEMBL 36 integration tested and verified
- **NEW**: Neo4j knowledge graph with 1.89M+ nodes

### In Progress (Phase 1)
- R&D core entity modeling
- Clinical core entity modeling
- Supply chain & regulatory core entity modeling
- Full-scale data collection execution (test dataset completed)

### Planned (Phase 2-3)
- Uncertainty data representation
- RWE data integration
- Quality management framework
- Cross-domain query optimization
- Version control implementation
- Adaptive trial modeling
- Intelligent alert system
- Performance optimization

## Key Files

### Core Application
- **`api/main.py`**: Main FastAPI application with all REST endpoints
- **`api/database.py`**: Neo4j connection management
- **`etl/cli.py`**: Command-line interface for ETL operations

### Data Collection (NEW)
- **`processors/chembl_processor.py`**: ChEMBL 36 SQLite processor (56KB, 1,200+ lines)
- **`processors/uniprot_processor.py`**: UniProt REST API processor (50KB, 1,100+ lines)
- **`processors/kegg_processor.py`**: KEGG pathway API processor (65KB, 1,400+ lines)
- **`processors/clinicaltrials_processor.py`**: ClinicalTrials.gov API v2 processor (76KB, 2,000+ lines)

### Integration Tools (NEW)
- **`tools/build_master_entity_map.py`**: Master identifier mapping system (42KB, 1,100+ lines)
- **`tools/infer_cross_domain_relationships.py`**: Cross-domain inference engine (32KB, 900+ lines)
- **`scripts/import_chembl_to_neo4j.py`**: Neo4j import with optimized batching (23KB, 600+ lines)

### Documentation
- **`docs/COMPLETE_IMPLEMENTATION_SUMMARY.md`**: Overall implementation summary
- **`docs/QUICK_START_GUIDE.md`**: Comprehensive usage guide
- **`docs/DATA_COLLECTION_PLAN.md`**: 5-phase data collection plan
- **`docs/CHEMBL36_TEST_REPORT.md`**: ChEMBL 36 test verification report

### Schema & Architecture
- **`docs/schema/制药行业知识图谱Schema设计文档.md`**: Schema design document
- **`docs/schema/实施路线图.md`**: Implementation roadmap (12 months, 3 phases)
- **`CHECKLIST.md`**: Project validation checklist (139 items)

### Analytics
- **`graph_analytics/algorithms.py`**: Graph algorithms (centrality, community detection, path finding)
- **`ml_analytics/reasoning.py`**: ML-based reasoning engine
