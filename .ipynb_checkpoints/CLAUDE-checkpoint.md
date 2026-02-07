# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PharmaKG** is a Pharmaceutical Knowledge Graph covering the entire pharmaceutical industry workflow, integrating four core business domains: Research & Development (R&D), Clinical Trials, Supply Chain Management, and Regulatory Compliance.

- **Version**: v1.0
- **Status**: Technical Implementation Phase (Phase 1)
- **Language**: Python 3.8+
- **Primary Technologies**: Neo4j 5.x, FastAPI, Turtle/OWL/SHACL ontologies

## Development Commands

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
# Run tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=api --cov=etl --cov-report=html
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
  └── check_project.sh        # Bash validation script

docs/                         # Documentation
  ├── schema/                 # Schema design documents
  ├── interview-notes/        # Domain interview notes (3 rounds)
  └── data-sources/           # Data source documentation

deploy/                       # Deployment configuration
  ├── deploy.sh               # Docker deployment script
  ├── deploy-autodl.sh        # AutoDL deployment script
  └── QUICKSTART_AUTODL.md    # AutoDL quick start guide
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

## Data Sources

- **ChEMBL**: Bioactivity data for compounds and targets
- **ClinicalTrials.gov**: Clinical trial registry
- **FDA**: Drug products, applications, and regulatory information
- **DrugBank**: Comprehensive drug data (file-based extraction)

## Project Status

### Completed
- Three rounds of domain interviews (56 questions, 71 decisions)
- Technology stack selection (Neo4j, Turtle+OWL+SHACL)
- Deployment configuration for Docker and AutoDL
- Core API structure with domain services
- ETL pipeline framework
- Graph analytics and ML analytics modules
- Ontology definitions and schema design documentation

### In Progress (Phase 1)
- R&D core entity modeling
- Clinical core entity modeling
- Supply chain & regulatory core entity modeling
- Identifier mapping service
- Basic query API development

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

- **`api/main.py`**: Main FastAPI application with all REST endpoints
- **`api/database.py`**: Neo4j connection management
- **`etl/cli.py`**: Command-line interface for ETL operations
- **`graph_analytics/algorithms.py`**: Graph algorithms (centrality, community detection, path finding)
- **`docs/schema/制药行业知识图谱Schema设计文档.md`**: Schema design document
- **`docs/schema/实施路线图.md`**: Implementation roadmap (12 months, 3 phases)
- **`CHECKLIST.md`**: Project validation checklist (139 items)
