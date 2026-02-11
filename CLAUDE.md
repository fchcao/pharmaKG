# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PharmaKG** is a Pharmaceutical Knowledge Graph covering the entire pharmaceutical industry workflow, integrating four core business domains: Research & Development (R&D), Clinical Trials, Supply Chain Management, and Regulatory Compliance.

- **Version**: v1.0
- **Status**: Technical Implementation Phase (Phase 1) - Frontend & Backend Integration Complete
- **Backend Language**: Python 3.8+
- **Frontend Language**: TypeScript + React
- **Primary Technologies**: Neo4j 5.x, FastAPI, React, Vite, Ant Design, Turtle/OWL/SHACL ontologies

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
# Start FastAPI server (from project root)
conda activate pharmakg-api
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Access API documentation
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)

# Health check
curl http://localhost:8000/health
```

### Frontend Service
```bash
# Start Vite dev server
cd frontend
npm install  # First time only
npm run dev

# Frontend runs on http://localhost:3000
# API calls are proxied to backend via /api prefix

# Build for production
npm run build

# Preview production build
npm run preview
```

### Quick Test Data Import
```bash
# Import small test dataset (100 compounds, 50 targets)
python3 scripts/quick_test_data.py
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
The API uses flat path structure without `/api/v1/` prefix in backend routes:
- `/rd/*` - Research & Development endpoints (compounds, targets, pathways, assays)
- `/clinical/*` - Clinical trial endpoints (trials, subjects, outcomes)
- `/supply/*` - Supply chain endpoints (manufacturers, shortages, facilities)
- `/sc/*` - Supply chain alternate path
- `/regulatory/*` - Regulatory endpoints (submissions, approvals, inspections)
- `/cross/*` - Cross-domain query endpoints
- `/advanced/*` - Advanced multi-hop and aggregation queries
- `/statistics/*` - Statistical aggregation endpoints
- `/health` - Health check endpoint
- `/overview` - Overview statistics

**Frontend Integration**: Frontend uses `/api` prefix for all API calls (e.g., `/api/rd/compounds`), which is proxied to backend via Vite dev server configuration.

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
  ├── main.py                 # Main application (1500+ lines)
  ├── config.py               # API configuration (Pydantic Settings)
  ├── database.py             # Neo4j connection management
  ├── models.py               # Pydantic data models
  └── services/               # Domain services
      ├── __init__.py         # Service module initialization
      ├── research_domain.py  # R&D domain service
      ├── clinical_domain.py  # Clinical domain service
      ├── supply_regulatory.py # Supply chain & regulatory
      ├── advanced_queries.py # Multi-hop queries
      ├── aggregate_queries.py # Statistical queries
      └── search_service.py   # Full-text search service

frontend/                     # React + Vite + TypeScript frontend
  ├── src/
  │   ├── App.tsx             # Main application with routes
  │   ├── main.tsx            # Application entry point
  │   ├── pages/              # Page components (Dashboard, Admin, etc.)
  │   ├── domains/            # Domain-specific pages
  │   │   ├── research/       # R&D domain pages (Compounds, Targets, etc.)
  │   │   ├── clinical/       # Clinical domain pages (Trials, etc.)
  │   │   ├── supply/         # Supply chain pages (Manufacturers, etc.)
  │   │   └── regulatory/     # Regulatory pages (Submissions, etc.)
  │   ├── layouts/            # Layout components (MainLayout, etc.)
  │   ├── shared/             # Shared components and utilities
  │   │   ├── api/            # API client (uses /api prefix)
  │   │   ├── components/     # Reusable components
  │   │   └── types/          # TypeScript type definitions
  │   └── TestApi.tsx         # API connection test component
  ├── vite.config.ts          # Vite configuration with proxy setup
  ├── package.json            # NPM dependencies
  └── .env.development        # Development environment variables

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
  ├── quick_test_data.py      # Quick test data import (100 compounds, 50 targets)
  ├── import_chembl_to_neo4j.py # Neo4j import for ChEMBL
  ├── run_full_pipeline.py   # Pipeline orchestration
  ├── extract_uniprot_from_chembl.py # UniProt ID extraction
  └── test_*.py              # Processor test scripts

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
  - Use `db.execute_query()` for queries, NOT `run_query()`
  - Access results via `result.records` array
- **Quality Validation**: ETL includes built-in data quality validation in `etl/quality/`
- **AutoDL Deployment**: Special deployment script for AutoDL cloud service (direct installation, no Docker required)
- **Validation**: Automated validation scripts check project completeness (139 items in CHECKLIST.md)
- **Global Error Handling**: FastAPI includes a global exception handler in `api/main.py` that standardizes error responses across all endpoints
- **Schema Initialization**: Neo4j constraints and indexes should be initialized after first deployment (see deployment commands above)
- **Frontend API Integration**:
  - Frontend uses `/api` prefix for all API calls
  - Vite proxy configuration in `frontend/vite.config.ts` routes `/api/*` to backend
  - SPA routing is handled by React Router - page routes (`/rd`, `/clinical`, etc.) are NOT proxied
  - Environment variable `VITE_API_BASE_URL=/api` must be set in `.env.development`
- **Service Module Imports**:
  - Always use relative imports from parent package: `from ..database import get_db`
  - `api/services/__init__.py` must exist for proper module resolution

## Documentation Maintenance Rules

### When to Update Documentation

| 文档 | 更新时机 | 负责判断 |
|------|----------|----------|
| **README.md** | 功能性变更、新特性、架构变化 | ✅ 自动判断 |
| **CHANGELOG.md** | 功能性变更 (新增/修复/优化) | ❌ 不更新日常清理 |
| **CLAUDE.md** | 架构变更、新命令、重要配置变化 | ✅ 自动判断 |
| **CHECKLIST.md** | 项目进度、完成项变更 | ✅ 自动判断 |

### 更新规则细节

#### README.md - 必须更新
- ✅ 最后更新日期 (每次提交时)
- ✅ 项目状态变更 (如: 前后端集成完成)
- ✅ 新增核心功能 (如: 前端应用、新API端点)
- ✅ 架构变化 (如: 技术栈调整)
- ❌ 不更新: 临时文件清理、内部重构

#### CHANGELOG.md - 选择性更新
- ✅ 更新: 新功能 (feat)、问题修复 (fix)、重要优化 (perf)
- ✅ 更新: 文档变更、测试变更
- ❌ 不更新: 项目清理、临时文件删除
- ❌ 不更新: 代码格式化、注释调整

#### CLAUDE.md - 及时更新
- ✅ 更新: 新的开发命令
- ✅ 更新: 新的配置说明
- ✅ 更新: 重要的技术决策
- ✅ 更新: 已知问题和解决方案
- ✅ 更新: 项目里程碑完成

### 自动化检查清单

每次提交代码前，检查以下文档是否需要更新：

```
□ README.md - 最后更新日期是否当前？
□ README.md - 是否有新功能需要记录？
□ CLAUDE.md - 是否有新命令或配置？
□ CHANGELOG.md - 是否是功能性变更？
```

**原则**: 功能性变更更新文档，维护性清理不记录。

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
- Technology stack selection (Neo4j, Turtle+OWL+SHACL, React+Vite)
- Deployment configuration for Docker and AutoDL
- Core API structure with domain services
- ETL pipeline framework
- Graph analytics and ML analytics modules
- Ontology definitions and schema design documentation
- Phase 1-5 data collection processors (17 processors implemented)
- Identifier mapping and cross-domain inference tools
- ChEMBL 36 integration tested and verified
- Neo4j knowledge graph with 1.89M+ nodes
- **NEW**: React frontend with domain-specific pages (R&D, Clinical, Supply, Regulatory)
- **NEW**: Frontend-backend API integration complete
- **NEW**: SPA routing configured (no 404 on page refresh)
- **NEW**: Dashboard pages with statistics and visualizations

### In Progress (Phase 1)
- R&D core entity modeling
- Clinical core entity modeling
- Supply chain & regulatory core entity modeling
- Full-scale data collection execution (test dataset: 100 compounds, 50 targets imported)

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

### Backend Core Application
- **`api/main.py`**: Main FastAPI application (1500+ lines) with all REST endpoints
- **`api/database.py`**: Neo4j connection management via `Neo4jConnection` class
- **`api/services/__init__.py`**: Service module initialization (required for imports)
- **`etl/cli.py`**: Command-line interface for ETL operations

### Frontend Core Application
- **`frontend/src/App.tsx`**: Main React application with route definitions
- **`frontend/vite.config.ts`**: Vite configuration with API proxy setup
- **`frontend/src/shared/api/client.ts`**: Axios-based API client (uses `/api` prefix)
- **`frontend/src/pages/dashboardHooks.tsx`**: React Query hooks for dashboard data
- **`frontend/.env.development`**: Frontend environment variables (`VITE_API_BASE_URL=/api`)

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

---

## Recent Fixes & Improvements (2025-02)

### Backend API Fixes
- **Fixed relative imports**: Changed `from .database import` to `from ..database import` in all service modules
- **Fixed QueryResult access**: Removed references to non-existent `result.success` attribute, use `result.records` directly
- **Fixed method calls**: Changed `db.run_query()` to `db.execute_query()` throughout codebase
- **Added missing endpoints**:
  - `/statistics/timeline` - General timeline statistics
  - `/statistics/domain-breakdown` - Domain breakdown with real data
  - `/clinical/statistics` - Clinical domain statistics
  - `/clinical/trials` - Clinical trials list with pagination
  - `/supply/manufacturers` - Supply chain manufacturers list
  - `/supply/statistics` - Supply chain statistics
  - `/regulatory/statistics` - Regulatory domain statistics
  - `/regulatory/submissions` - Regulatory submissions list
  - `/regulatory/approvals` - Regulatory approvals list

### Frontend Integration Fixes
- **API prefix configuration**: Set `VITE_API_BASE_URL=/api` in `.env.development`
- **Vite proxy setup**: Configure proxy to route `/api/*` to backend port 8000
- **SPA routing**: Page routes (`/rd`, `/clinical`, etc.) handled by React Router, not proxied
- **Fixed component imports**: Replaced invalid Ant Design icons with valid alternatives
- **Fixed hooks**: Updated `useTimelineData` to return `response.data.timeline` instead of full response object
- **Removed invalid components**: Removed `Container` component (not available in Ant Design v5)

### Known Issues (Non-Critical)
- Ant Design deprecation warnings: `Tabs.TabPane`, `Card.bordered`, `Modal.visible`
- React Router future flag warnings (v7 compatibility)
- These warnings do not affect functionality and will be addressed in future updates

### Test Data
- Quick test data import: `scripts/quick_test_data.py`
- Imports 100 compounds and 50 targets from ChEMBL
- Uses `chembl_id` as primary identifier for consistent frontend-backend mapping
