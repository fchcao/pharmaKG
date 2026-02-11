# PharmaKG Data Collection & Extraction Plan
## Building a Complete Pharmaceutical Knowledge Graph

---

## Context

### Current Situation Analysis

**Current State:**
- 2,994 nodes, 1,972 relationships, 64% connectivity
- Heavily focused on regulatory documents (Chinese FDA standards) and FDA CRLs
- Missing critical R&D entities (assays, pathways), clinical entities (subjects, interventions, biomarkers), and supply chain entities

**Root Cause of Disconnected Graph:**

1. **Data Distribution Problem** - NOT a lack of data
   - 1.07GB of raw data available across clinical (28MB), regulatory (460MB), R&D (168MB), technical documents (420MB)
   - Only 13% of available data has been processed

2. **Entity Type Coverage Gap**
   - Ontology defines 40+ entity types
   - Only 51% of entity types are being extracted (10/20 main categories)
   - Critical gaps: ASSAY, PATHWAY, SUBJECT, INTERVENTION, ADVERSE_EVENT, BIOMARKER, MANUFACTURER, SUPPLIER, FACILITY, DRUG_SHORTAGE

3. **Relationship Coverage Gap**
   - Ontology defines 100+ relationship types
   - Only 30% of relationship types are being extracted (6/20 main categories)
   - Critical gaps: Most R&D relationships (ACTIVATES, BINDS_TO, TARGETS), clinical relationships (ENROLLS, EXPERIENCES_EVENT), regulatory relationships (SUBMITTED_FOR_APPROVAL, APPROVED_PRODUCT), supply chain relationships (SUPPLIES_TO, EXPERIENCES_SHORTAGE)

4. **Cross-Domain Integration Missing**
   - Compound → ClinicalTrial → Submission → Approval chain is broken
   - Compound → Target → Pathway relationships missing
   - Manufacturer → Inspection → ComplianceAction → DrugShortage chain missing

### Why This Matters

A knowledge graph with only regulatory documents and scattered connections cannot support:
- Drug discovery and repurposing queries
- Supply chain risk analysis
- Competitive intelligence
- Regulatory pathway prediction
- Safety signal detection

---

## Recommended Approach

### Strategic Vision

Transform PharmaKG from a regulatory document repository into a **comprehensive pharmaceutical knowledge graph** by:

1. **Prioritizing high-value data sources** that fill entity/relationship gaps
2. **Building cross-domain connections** between R&D → Clinical → Regulatory → Supply Chain
3. **Creating a data ingestion pipeline** that continuously updates from public APIs
4. **Implementing proper identifier mapping** to link entities across sources

### Implementation Phases

---

## Phase 1: Critical R&D Data (Weeks 1-4)

### Objective
Establish compound, target, and bioactivity foundations - the core of any pharma KG

### Data Sources to Process

#### 1.1 ChEMBL Database Processing (Already Available)
**Location:** `/root/autodl-tmp/pj-pharmaKG/data/sources/rd/chembl_34/chembl_34_sqlite/chembl_34.db`

**Entity Types to Extract:**
- `rd:Compound` - 2M+ compounds with SMILES, InChIKey, molecular properties
- `rd:Target` - 12K+ protein targets with UniProt IDs
- `rd:Assay` - 1M+ bioassays with protocols
- `rd:Pathway` - KEGG/Reactome pathway mappings

**Relationship Types to Extract:**
- `rel:INHIBITS` - Compound → Target (IC50, Ki values)
- `rel:ACTIVATES` - Compound → Target
- `rel:BINDS_TO` - Compound → Target
- `rel:TARGETS` - Target → Pathway
- `rel:PARTICIPATES_IN` - Target → Pathway
- `rel:TESTS_COMPOUND` - Assay → Compound
- `rel:TESTS_TARGET` - Assay → Target

**Implementation:**
- Create `processors/chembl_processor.py`
- Use SQLite queries to extract:
  - `molecule_dictionary` → Compound entities
  - `target_components` + `component_sequences` → Target entities
  - `assays` → Assay entities
  - `activities` → Activity relationships (with pchembl_value for IC50/Ki)
  - `component_go` → Target → Pathway relationships

**Expected Output:** ~2M compounds, 12K targets, 1M assays, 5M+ bioactivity relationships

---

#### 1.2 UniProt API Integration (External - High Priority)
**API:** https://rest.uniprot.org/uniprotkb/
**Rate Limit:** Unlimited (but be reasonable)
**Format:** JSON/XML

**Entity Types to Extract:**
- `rd:Target` with enhanced properties:
  - Gene symbol, protein name
  - Organism, cellular location
  - GO annotations (molecular function, biological process)
  - Druggability classification
  - Associated diseases

**Relationship Types:**
- `rel:ASSOCIATED_WITH_DISEASE` - Target → Disease
- `rel:BIOMARKER_FOR` - Target → Disease

**Implementation:**
- Create `processors/uniprot_processor.py`
- Query by organism (human, mouse, rat)
- Batch query by UniProt IDs from ChEMBL
- Map to ChEMBL targets using UniProt ID

**Expected Output:** ~20K enhanced target records with disease associations

---

#### 1.3 KEGG Pathway API Integration (External)
**API:** http://rest.kegg.jp/
**License:** Academic use free (verify terms)
**Format:** JSON/XML

**Entity Types to Extract:**
- `rd:Pathway` - Human pathways (hsa map IDs)
  - Pathway name, type (metabolic, signaling, disease)
  - Associated genes/proteins

**Relationship Types:**
- `rel:PARTICIPATES_IN` - Target → Pathway
- `rel:REGULATES_PATHWAY` - Target → Pathway

**Implementation:**
- Create `processors/kegg_processor.py`
- Fetch pathway list: `list/pathway/hsa`
- Fetch pathway details: `get/hsaXXXXX`
- Map proteins to UniProt IDs

**Expected Output:** ~400 human pathways with 8K+ pathway-participant relationships

---

### Phase 1 Deliverables
- **Processor:** `processors/chembl_processor.py`
- **Processor:** `processors/uniprot_processor.py`
- **Processor:** `processors/kegg_processor.py`
- **Data:** ChEMBL SQLite extraction (2M compounds, 12K targets, 1M assays)
- **Data:** UniProt enhanced target data (20K targets)
- **Data:** KEGG pathway data (400 pathways)
- **Impact:** +2M entities, +5M relationships, establishes R&D foundation

---

## Phase 2: Clinical Trial Data (Weeks 5-8)

### Objective
Connect compounds and targets to clinical trials, establishing development pipelines

### Data Sources to Process

#### 2.1 ClinicalTrials.gov API Enhancement (External)
**API:** https://clinicaltrials.gov/api/v2/
**Rate Limit:** 1 request per 0.5 seconds
**Format:** JSON (Study Fields: NCTId, Phase, Status, Interventions, Conditions)

**Entity Types to Extract:**
- `clinical:ClinicalTrial` - All studies (400K+)
- `clinical:Arm` - Trial arms/groups
- `clinical:Intervention` - Drugs, procedures, behaviors
- `clinical:Condition` - Diseases/conditions being studied
- `clinical:Outcome` - Primary/secondary endpoints
- `clinical:EligibilityCriteria` - Inclusion/exclusion criteria
- `clinical:StudySite` - Research locations
- `clinical:Investigator` - Principal investigators and staff
- `clinical:Sponsor` - Industry/NIH/Other sponsors

**Relationship Types:**
- `rel:TESTS_INTERVENTION` - ClinicalTrial → Intervention
- `rel:ENROLLS` - ClinicalTrial → Subject (aggregate count)
- `rel:HAS_PRINCIPAL_INVESTIGATOR` - ClinicalTrial → Investigator
- `rel:CONDUCTED_AT_SITE` - ClinicalTrial → StudySite
- `rel:SPONSORED_BY` - ClinicalTrial → Sponsor
- `rel:TRIAL_FOR_DISEASE` - ClinicalTrial → Condition

**Cross-Domain Relationships:**
- Map `Intervention.name` to ChEMBL Compound using InChIKey/SMILES
- Map `Condition.name` to MONDO disease IDs
- Create: `rel:TESTED_IN_CLINICAL_TRIAL` - Compound → ClinicalTrial

**Implementation:**
- Create `processors/clinicaltrials_processor.py`
- Full API download (400K+ studies) over 1-2 weeks
- Store in processed/documents/clinical_trials/
- Extract all intervention and condition names
- Build fuzzy match to ChEMBL compounds

**Expected Output:** ~400K clinical trials with full entity/relationship extraction

---

#### 2.2 FDA Drugs@FDA Data (External - API Available)
**API:** https://api.fda.gov/drug/drugsfda/
**Format:** JSON

**Entity Types to Extract:**
- `regulatory:Approval` - Drug approvals with products
- `regulatory:Submission` - NDA/ANDA/BLA submissions
- `rd:Compound` - Approved drugs

**Relationship Types:**
- `rel:SUBMITTED_FOR_APPROVAL` - Submission → Approval
- `rel:APPROVED_PRODUCT` - RegulatoryAgency → Compound
- `rel:APPROVAL_FOR` - Approval → Compound
- `rel:HAS_MARKETING_AUTHORIZATION` - Compound → DrugProduct

**Cross-Domain Integration:**
- Map products to ChEMBL compounds via UNII
- Map submissions to clinical trials via NCT number

**Implementation:**
- Create `processors/drugsatfda_processor.py`
- Download all approved products
- Extract UNII identifiers
- Link to ChEMBL and clinical trials

**Expected Output:** ~40K approvals with product and submission data

---

### Phase 2 Deliverables
- **Processor:** `processors/clinicaltrials_processor.py`
- **Processor:** `processors/drugsatfda_processor.py`
- **Data:** 400K+ clinical trials with full entity extraction
- **Data:** 40K+ FDA approvals linked to submissions
- **Cross-Domain:** Compound → ClinicalTrial → Submission → Approval chains
- **Impact:** +1.5M entities, +3M relationships, establishes development pipeline view

---

## Phase 3: Safety & Supply Chain Data (Weeks 9-12)

### Objective
Complete the picture with adverse events, shortages, and manufacturing data

### Data Sources to Process

#### 3.1 FDA FAERS Adverse Events (External - Quarterly)
**Source:** https://fis.fda.gov/sense/app/d10be4bb-5284-4fc1-8f92-8b5f4f763062/page/FAERS/
**Format:** ASCII/CSV (quarterly extracts)
**Update:** Quarterly

**Entity Types to Extract:**
- `clinical:AdverseEvent` - Individual AE reports
- `clinical:Condition` - Adverse reactions (MedDRA coded)
- `rd:Compound` - Suspect drugs

**Relationship Types:**
- `rel:CAUSED_ADVERSE_EVENT` - Compound → AdverseEvent
- `rel:SERIOUS_ADVERSE_EVENT` - AdverseEvent → ClinicalTrial (if trial-related)
- `rel:HAS_SAFETY_SIGNAL` - Compound → SafetySignal

**Implementation:**
- Create `processors/faers_processor.py`
- Parse quarterly ASCII files
- Extract MedDRA-coded reactions
- Map drug names to ChEMBL compounds

**Expected Output:** ~20M AE reports (start with latest 2 quarters = 10M records)

---

#### 3.2 FDA Drug Shortages Database (External - API Available)
**API:** https://api.fda.gov/drug/drugsfda/
**Endpoint:** /drug/shortages.json
**Update:** Daily

**Entity Types to Extract:**
- `sc:DrugShortage` - Shortage events
- `rd:Compound` - Affected drugs
- `sc:Manufacturer` - Affected manufacturers
- `sc:Facility` - Manufacturing facilities

**Relationship Types:**
- `rel:EXPERIENCES_SHORTAGE` - Compound → DrugShortage
- `rel:CAUSED_BY_QUALITY_ISSUE` - DrugShortage → Manufacturer
- `rel:MANUFACTURES` - Manufacturer → Compound
- `rel:HAS_FACILITY` - Manufacturer → Facility

**Implementation:**
- Create `processors/shortage_processor.py`
- Fetch from openFDA API
- Link to ChEMBL compounds via generic name
- Link to manufacturer data

**Expected Output:** ~5K shortage events with manufacturer links

---

#### 3.3 PDA Technical Reports Processing (Already Available)
**Location:** `/root/autodl-tmp/pj-pharmaKG/data/sources/documents/PDA TR 全集/`
**Files:** 108 PDFs on pharmaceutical manufacturing

**Entity Types to Extract:**
- `sc:Facility` - Clean rooms, manufacturing areas
- `sc:Manufacturer` - Equipment types, systems
- `sc:QualityStandard` - GMP requirements, validation protocols
- `rd:Assay` - Quality control test methods

**Relationship Types:**
- `rel:MANUFACTURES` - Manufacturer → DrugProduct
- `rel:SUBJECT_TO_INSPECTION` - Manufacturer → Inspection
- `rel:PASSED_INSPECTION` - Manufacturer → Inspection

**Implementation:**
- Create `processors/pda_pdf_processor.py`
- Extract equipment, processes, test methods from PDFs
- Build manufacturing knowledge base

**Expected Output:** ~500 facility, equipment, and quality standard entities

---

### Phase 3 Deliverables
- **Processor:** `processors/faers_processor.py`
- **Processor:** `processors/shortage_processor.py`
- **Processor:** `processors/pda_pdf_processor.py`
- **Data:** 10M+ adverse event reports
- **Data:** 5K+ shortage events
- **Data:** 500+ manufacturing entities
- **Impact:** +10.5M entities, +25M relationships, completes safety/supply chain view

---

## Phase 4: High-Value External Datasets (Weeks 13-16)

### Objective
Add drug-drug interactions, biomarkers, and pathway enrichment

### Data Sources to Collect

#### 4.1 DrugBank Integration (External - License Required)
**Action Required:** Apply for academic license (free for researchers, 1-2 week approval)
**API:** https://go.drugbank.com/
**Format:** XML (download) or JSON (API)

**Entity Types to Extract:**
- `rd:Compound` with enhanced properties:
  - DrugBank ID, ATC codes, approval status
  - Mechanism of action
  - Drug-drug interactions (DDI)
  - Pharmacokinetics, metabolism, toxicity

**Relationship Types:**
- `rel:INTERACTS_WITH` - Compound → Compound (DDI)
- `rel:METABOLIZED_BY` - Compound → Target (enzyme)
- `rel:TRANSPORTED_BY` - Compound → Target (transporter)

**Implementation:**
- Apply for DrugBank academic license immediately
- Create `processors/drugbank_processor.py`
- Download full XML dataset
- Map to ChEMBL via InChIKey

**Expected Output:** ~15K enhanced drug records with DDI network

---

#### 4.2 DailyMed SPL Labels (External - Daily)
**API:** https://dailymed.nlm.nih.gov/dailymed/
**Format:** XML (Structured Product Labels)

**Entity Types to Extract:**
- `rd:Compound` - FDA-approved drugs
- `clinical:Condition` - Indications and contraindications
- `clinical:Biomarker` - Pharmacogenomic markers
- `clinical:AdverseEvent` - Boxed warnings, reactions

**Relationship Types:**
- `rel:TREATS` - Compound → Condition (indication)
- `rel:CONTRAINDICATED_FOR` - Compound → Condition
- `rel:HAS_BIOMARKER` - Compound → Biomarker (pharmacogenomics)

**Implementation:**
- Create `processors/dailymed_processor.py`
- Download SPL XML files
- Extract indications, contraindications, pharmacogenomics

**Expected Output:** ~150K product labels with indication/biomarker data

---

### Phase 4 Deliverables
- **Processor:** `processors/drugbank_processor.py`
- **Processor:** `processors/dailymed_processor.py`
- **Data:** 15K DrugBank drug records
- **Data:** 150K DailyMed labels
- **Cross-Domain:** DDI network, pharmacogenomics relationships
- **Impact:** +200K entities, +2M relationships, adds drug interactions and biomarkers

---

## Phase 5: Identifier Mapping & Cross-Source Integration (Weeks 17-20)

### Objective
Create unified entity view across all data sources

### Implementation

#### 5.1 Build Master Identifier Mapping System

**Create:** `tools/build_master_entity_map.py`

**Mapping Strategy:**
- **Compounds:** InChIKey (primary) → ChEMBL ID, DrugBank ID, PubChem CID, UNII
- **Targets:** UniProt Accession (primary) → Entrez ID, Ensembl ID, HGNC Symbol
- **Diseases:** MONDO ID (primary) → ICD-10, DOID, MeSH, SNOMED-CT
- **ClinicalTrials:** NCT Number (primary) → EudraCT, ChiCTR
- **Companies:** GRID ID (primary) → ROR ID, DUNS

**Implementation:**
1. Extract all identifiers from each source
2. Build mapping tables using external services:
   - UniProt ID mapping: https://rest.uniprot.org/idmapping/
   - MyChem.info for compound cross-references
3. Store in Neo4j as `MERGED_TO` relationships between variant entities

**Expected Output:** Master entity map linking all identifier systems

---

#### 5.2 Cross-Domain Relationship Inference

**Create:** `tools/infer_cross_domain_relationships.py`

**Inference Rules:**
- **Drug Repurposing:**
  - If Compound INHIBITS Target AND Target ASSOCIATED_WITH_DISEASE
  - → Create `rel:POTENTIALLY_TREATS` (Compound → Disease)

- **Safety Signals:**
  - If Compound HAS_SAFETY_SIGNAL AND multiple SERIOUS_ADVERSE_EVENT
  - → Create `rel:CONFIRMED_RISK` (Compound → Condition)

- **Supply Chain Risk:**
  - If Manufacturer FAILED_INSPECTION (≥2 times)
  - → Create `rel:POTENTIAL_QUALITY_ISSUE` (Manufacturer → Inspection)

- **Competition:**
  - If Compound_A INHIBITS Target AND Compound_B INHIBITS same Target
  - → Create `rel:COMPETES_WITH` (Compound_A ↔ Compound_B)

**Implementation:**
1. Query Neo4j for relationship patterns
2. Apply inference rules with confidence scores
3. Create inferred relationships with evidence_level = "D" (inferred)

**Expected Output:** ~1M+ inferred cross-domain relationships

---

### Phase 5 Deliverables
- **Tool:** `tools/build_master_entity_map.py`
- **Tool:** `tools/infer_cross_domain_relationships.py`
- **Data:** Master identifier map across all sources
- **Data:** 1M+ inferred relationships
- **Impact:** Unified entity view, enables complex cross-domain queries

---

## Data Collection Schedule Summary

| Phase | Duration | Data Sources | Entities Added | Relationships Added | Priority |
|-------|----------|--------------|----------------|-------------------|----------|
| 1 | Weeks 1-4 | ChEMBL, UniProt, KEGG | 2M+ | 5M+ | CRITICAL |
| 2 | Weeks 5-8 | ClinicalTrials.gov, Drugs@FDA | 1.5M+ | 3M+ | HIGH |
| 3 | Weeks 9-12 | FAERS, Drug Shortages, PDA TRs | 10.5M+ | 25M+ | HIGH |
| 4 | Weeks 13-16 | DrugBank, DailyMed | 200K+ | 2M+ | MEDIUM |
| 5 | Weeks 17-20 | ID Mapping, Inference | Unified | 1M+ | HIGH |

**Total After Phase 5:** ~14M+ entities, ~36M+ relationships

---

## Technical Implementation Details

### New Processors to Create

```
processors/
├── chembl_processor.py          # Phase 1 - ChEMBL SQLite extraction
├── uniprot_processor.py          # Phase 1 - UniProt API integration
├── kegg_processor.py              # Phase 1 - KEGG pathway API
├── clinicaltrials_processor.py    # Phase 2 - ClinicalTrials.gov API v2
├── drugsatfda_processor.py        # Phase 2 - FDA Drugs@FDA API
├── faers_processor.py             # Phase 3 - FDA FAERS quarterly data
├── shortage_processor.py          # Phase 3 - FDA Drug Shortages API
├── pda_pdf_processor.py           # Phase 3 - PDA technical reports
├── drugbank_processor.py          # Phase 4 - DrugBank XML processing
├── dailymed_processor.py          # Phase 4 - DailyMed SPL XML
```

### New Tools to Create

```
tools/
├── build_master_entity_map.py     # Phase 5 - Identifier mapping
├── infer_cross_domain_relationships.py  # Phase 5 - Relationship inference
├── continuous_data_updater.py     # Automated updates from APIs
└── validate_kg_completeness.py    # Coverage analysis vs ontologies
```

### Infrastructure Requirements

**API Rate Limiting:**
- ClinicalTrials.gov: 1 req/0.5sec = 7,200 req/hour = 172K/day
- PubChem: 5 req/sec = 18,000 req/hour
- UniProt: No limit (but use reasonable batching)

**Storage Requirements:**
- ChEMBL extraction: ~50GB processed data
- ClinicalTrials full download: ~20GB
- FAERS quarterly: ~10GB per quarter
- DrugBank: ~5GB
- DailyMed: ~30GB
- **Total:** ~115GB processed data storage needed

**Neo4j Configuration:**
- Current: 2,994 nodes, 1,972 relationships
- Target: 14M+ nodes, 36M+ relationships
- **Recommendation:** Upgrade to Neo4j Enterprise or increase heap to 16GB+

---

## Verification & Success Metrics

### Coverage Metrics (vs Ontologies)

| Domain | Entity Coverage Target | Relationship Coverage Target |
|--------|----------------------|-------------------------------|
| R&D | 90% (all compound, target, assay types) | 80% (all key R&D relationships) |
| Clinical | 85% (trial, intervention, AE types) | 75% (enrollment, intervention relationships) |
| Regulatory | 95% (maintain current) | 85% (add submission/approval chains) |
| Supply Chain | 70% (manufacturer, shortage types) | 60% (manufacturing, inspection) |

### Query Capabilities to Enable

**After implementation, should support:**

1. **Drug Discovery Queries:**
   - "Find all compounds that inhibit target X and are in Phase 2+ trials"
   - "What pathways does target Y participate in that are associated with disease Z?"

2. **Supply Chain Queries:**
   - "Which manufacturers of drug X have failed inspection in the past 2 years?"
   - "What drugs are experiencing shortages and what facilities manufacture them?"

3. **Safety Queries:**
   - "What adverse events are associated with compounds that target protein P?"
   - "Which drugs have safety signals for elderly patients?"

4. **Regulatory Intelligence:**
   - "Show me the complete development path from compound X through clinical trials to approval"
   - "What competitors are targeting the same pathway as compound Y?"

### Connection Rate Target

- **Current:** 64% (1,915/2,994)
- **Target Phase 1:** 75% (after R&D data)
- **Target Phase 2:** 80% (after clinical data)
- **Target Phase 3:** 85% (after safety/supply chain)
- **Target Final:** 90%+ (after cross-domain integration)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| DrugBank license not approved | Medium | Use PubChem + DailyMed as fallback |
| API rate limits exceeded | High | Implement queuing, distribute over time |
| Storage insufficient | Medium | Use Neo4j data eviction policy, archive old data |
| Entity resolution challenges | High | Invest in identifier mapping system (Phase 5) |
| ChEMBL database corruption | Low | Use official ChEMBL 34 download |

---

## Critical Files for Implementation

### Files to Create
- `processors/chembl_processor.py` - Highest priority
- `processors/clinicaltrials_processor.py` - Highest priority
- `tools/build_master_entity_map.py` - Critical for integration

### Files to Modify
- `extractors/base.py` - Add missing entity types (ASSAY, PATHWAY, etc.)
- `extractors/relationship.py` - Add missing relationship types
- `mappers/entity_mapper.py` - Support new entity types
- `tools/comprehensive_import.py` - Add new data sources

---

## Next Steps After Approval

1. **Week 1:** Start ChEMBL processor development (already have data)
2. **Week 1:** Apply for DrugBank academic license
3. **Week 2:** Start ClinicalTrials.gov API integration
4. **Week 2:** Set up UniProt API integration
5. **Week 3:** Begin identifier mapping system design

This plan transforms PharmaKG from a regulatory document repository into a comprehensive pharmaceutical knowledge graph capable of supporting drug discovery, clinical intelligence, regulatory affairs, and supply chain analytics.
