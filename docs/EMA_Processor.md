# EMA Guidance Processor Documentation

## Overview

The EMA (European Medicines Agency) Guidance Processor is a comprehensive tool for collecting regulatory guidance documents from EMA. It supports web scraping, structured data extraction, and integration with the PharmaKG knowledge graph.

## Features

- **Web Scraping**: Automated collection from EMA's public guidance repository
- **Category Classification**: Automatic categorization of documents by therapeutic area
- **Committee Detection**: Identification of responsible EMA committees (CHMP, PRAC, etc.)
- **Deduplication**: Content-based deduplication to avoid duplicate entries
- **Rate Limiting**: Built-in rate limiting to respect EMA's servers
- **Caching**: URL and content hash caching for incremental updates
- **Multi-format Support**: PDF, DOC, DOCX, XLS, XLSX

## Installation

### Requirements

```bash
pip install requests beautifulsoup4 lxml
```

### Quick Start

```python
from processors.ema_processor import collect_ema_guidance

# Collect 100 recent EMA guidance documents
results = collect_ema_guidance(
    limit=100,
    lookback_days=90,
    output_file="data/processed/regulatory/EMA/ema_guidance.json"
)

print(f"Collected {results['collected']} documents")
```

## Usage

### Basic Usage

```python
from processors.ema_processor import EMAProcessor

# Initialize processor
processor = EMAProcessor()

# Scrape all guidance documents
documents = list(processor.scrape_guidance_list(limit=50))

# Save to file
processor.save_documents(documents, "output.json")
```

### Filter by Category

```python
from processors.ema_processor import EMAProcessor, EMAGuidanceCategory

processor = EMAProcessor()

# Collect only clinical trial guidelines
documents = list(processor.scrape_guidance_list(
    category=EMAGuidanceCategory.CLINICAL_TRIALS,
    limit=50
))
```

### Filter by Therapeutic Area

```python
# Collect oncology guidance documents
documents = list(processor.scrape_by_therapeutic_area(
    therapeutic_area="oncology",
    limit=50
))
```

### Download Full Documents

```python
# Download PDF content for each document
for doc in documents:
    local_path = processor.download_document_content(doc)
    if local_path:
        print(f"Downloaded: {local_path}")
```

## EMA Guidance Categories

### Priority Categories (High)

1. **Clinical Trials** (`clinical_trials`)
   - First-in-human trials
   - GCP guidelines
   - Investigational medicinal products
   - Clinical study design

2. **Quality** (`quality`)
   - GMP guidelines
   - Pharmaceutical quality
   - Impurities
   - Validation requirements
   - Manufacturing

3. **Pharmacovigilance** (`pharmacovigilance`)
   - Adverse reaction reporting
   - Risk management
   - PSUR/PBRER requirements
   - Signal detection

4. **Biosimilars** (`biosimilars`)
   - Biosimilar development
   - Comparability exercises
   - Immunogenicity

5. **Advanced Therapies** (`advanced_therapies`)
   - Gene therapy
   - Cell therapy
   - Tissue engineered products
   - ATMP requirements

### Secondary Categories

6. **Paediatrics** (`paediatrics`)
   - PIP requirements
   - Paediatric investigation plans
   - Formulation considerations

7. **Orphan Drugs** (`orphan_drugs`)
   - Orphan designation
   - Rare disease criteria

8. **Oncology** (`oncology`)
   - Cancer therapies
   - Companion diagnostics
   - Biomarker-driven development

9. **Pharmacogenetics** (`pharmacogenetics`)
   - Biomarker qualification
   - Companion diagnostics
   - Personalized medicine

10. **Generics** (`generics`)
    - Bioequivalence
    - Generic drug development

11. **Herbal** (`herbal`)
    - Traditional herbal medicines
    - Herbal monographs

12. **Veterinary** (`veterinary`)
    - Veterinary medicine guidelines
    - MRL requirements

## EMA Committees

| Committee | Full Name | Responsibility |
|-----------|------------|----------------|
| CHMP | Committee for Medicinal Products for Human Use | Human medicines marketing authorization |
| CVMP | Committee for Medicinal Products for Veterinary Use | Veterinary medicines |
| PRAC | Pharmacovigilance Risk Assessment Committee | Drug safety monitoring |
| COMP | Committee for Orphan Medicinal Products | Orphan drug designation |
| PDCO | Paediatric Committee | Paediatric requirements |
| CAT | Committee for Advanced Therapies | ATMP assessment |
| HMPC | Committee on Herbal Medicinal Products | Herbal medicines |

## Document Types

- **Guideline**: Full regulatory guidance documents
- **Reflection Paper**: Discussion documents on emerging topics
- **Guidance**: General guidance documents
- **Question & Answer**: FAQ-style guidance
- **Opinion**: Committee opinions on specific topics
- **Statement**: Official statements on regulatory issues
- **Concept Paper**: Early-stage guidance proposals
- **Revised Guideline**: Updated versions of guidelines
- **Addendum**: Additional guidance to existing documents

## Collection Schedule

### Recommended Frequency

| Category Priority | Frequency | Rationale |
|------------------|------------|------------|
| High (clinical, quality, PV) | Weekly | Frequently updated |
| Medium (biosimilars, ATMP) | Monthly | Moderate update rate |
| Low (others) | Quarterly | Rarely updated |

### Incremental Updates

The processor includes deduplication caching to support incremental updates:

```python
# Process new documents only (incremental update)
processor = EMAProcessor()
processor._load_cache()  # Load previous URLs

# Only new documents will be collected
documents = list(processor.scrape_guidance_list(limit=100))
```

## Output Format

### Document Structure

```json
{
  "ema_id": "EMA-12345678",
  "title": "Guideline on clinical trials",
  "url": "https://www.ema.europa.eu/...",
  "publish_date": "2024-01-15T00:00:00",
  "last_update": "2024-06-01T00:00:00",
  "document_type": "guideline",
  "category": "clinical_trials",
  "committee": "CHMP",
  "summary": "This guideline provides...",
  "content": "Full text content...",
  "keywords": ["clinical", "trial", "gcp"],
  "related_documents": ["EMA-12345679"],
  "replaces": ["EMA-12345677"],
  "replaced_by": null,
  "status": "active",
  "version": "1.0",
  "effective_date": "2024-03-01T00:00:00",
  "superseded_date": null,
  "therapeutic_area": "general",
  "procedure_number": "EMA/CHMP/12345/2024",
  "adoption_date": "2024-02-01T00:00:00",
  "comments_deadline": "2024-04-01T00:00:00",
  "file_format": "pdf",
  "file_size": 1234567,
  "pages": 45,
  "language": "en",
  "source_hash": "abc123...",
  "scraped_at": "2024-06-15T10:30:00"
}
```

### Aggregated Output

```json
{
  "metadata": {
    "generated_at": "2024-06-15T10:30:00",
    "total_documents": 150,
    "source": "EMA (European Medicines Agency)",
    "categories_covered": ["clinical_trials", "quality", "pharmacovigilance"],
    "committees_covered": ["CHMP", "PRAC", "COMP"]
  },
  "statistics": {
    "total_documents": 150,
    "by_category": {...},
    "by_type": {...},
    "by_committee": {...}
  },
  "documents": [...]
}
```

## Integration with PharmaKG

### Regulatory Domain

The EMA processor integrates with the regulatory domain of PharmaKG:

```python
# Map to PharmaKG regulatory entities
regulatory_entities = []

for doc in documents:
    entity = {
        "type": "RegulatoryGuidance",
        "id": doc.ema_id,
        "title": doc.title,
        "agency": "EMA",
        "category": doc.category.value,
        "committee": doc.committee.value,
        "url": doc.url,
        "publish_date": doc.publish_date,
        "status": doc.status,
    }
    regulatory_entities.append(entity)

# Import to Neo4j via regulatory aggregator
from processors.regulatory_aggregator import RegulatoryAggregator

aggregator = RegulatoryAggregator()
aggregator.process_directory("data/sources/regulatory/EMA")
```

## Error Handling

### Common Issues

1. **Rate Limiting**
   - Symptom: HTTP 429 errors
   - Solution: Increase `request_delay` in config

2. **Missing Content**
   - Symptom: Documents with empty content
   - Solution: Some EMA documents are PDF-only; use `download_document_content()`

3. **Cache Corruption**
   - Symptom: Documents not updating
   - Solution: Clear cache: `rm data/sources/regulatory/EMA/cache/url_cache.json`

## Configuration

```python
config = {
    "request_delay": 2,  # Seconds between requests (default: 2)
    "max_retries": 3,    # Retry attempts (default: 3)
}

processor = EMAProcessor(config)
```

## Best Practices

1. **Start Small**: Begin with a small limit to test configuration
2. **Use Caching**: Enable incremental updates for large collections
3. **Monitor Errors**: Check `stats["errors"]` after collection
4. **Respect Limits**: Use appropriate `request_delay` values
5. **Regular Updates**: Schedule weekly updates for priority categories

## Statistics and Reporting

```python
processor = EMAProcessor()
documents = list(processor.scrape_guidance_list(limit=100))

# Get collection statistics
stats = processor.get_statistics()

print(f"Total documents: {stats['total_documents']}")
print(f"By category: {stats['by_category']}")
print(f"By committee: {stats['by_committee']}")
print(f"Download success rate: {stats['downloads']['successful']}/{stats['downloads']['successful'] + stats['downloads']['failed']}")
```

## References

- EMA Website: https://www.ema.europa.eu
- EMA Guidelines: https://www.ema.europa.eu/en/human-regulatory/research-development/overview/guidelines-human-medicines
- EMA Committees: https://www.ema.europa.eu/about-us/who-we-are/our-committees

## Changelog

### v1.0 (2024-06-15)
- Initial release
- Support for web scraping EMA guidance documents
- Category and committee classification
- Deduplication and caching
- Integration with regulatory aggregator
