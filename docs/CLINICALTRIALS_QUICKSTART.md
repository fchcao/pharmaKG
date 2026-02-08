# ClinicalTrials.gov API v2 Processor - Quick Start Guide

## Overview

The ClinicalTrialsProcessor is a comprehensive data processor for extracting clinical trial data from ClinicalTrials.gov API v2. It supports full download, conditional queries, incremental updates, and cross-domain mapping.

## Installation

No additional installation is required beyond the existing PharmaKG dependencies. The processor uses the `requests` library which should already be installed.

```bash
# Install requests if needed
pip install requests
```

## Quick Start Examples

### 1. Import and Initialize

```python
from processors.clinicaltrials_processor import ClinicalTrialsProcessor

# Create processor with default settings
processor = ClinicalTrialsProcessor()

# Or with custom configuration
config = {
    'extraction': {
        'page_size': 100,
        'rate_limit_per_second': 2.0,
        'max_studies': 1000
    }
}
processor = ClinicalTrialsProcessor(config)
```

### 2. Fetch Data

#### Full Download (Limited)
```python
# Download first 100 studies
raw_data = processor.fetch_all_studies(max_studies=100)
```

#### Query by Disease
```python
# Get diabetes-related studies
raw_data = processor.fetch_by_query("diabetes", max_studies=50)
```

#### Fetch Single Study
```python
# Get specific study by NCT ID
study_data = processor.fetch_by_nct_id("NCT00001234")
if study_data:
    raw_data = {'studies': [study_data]}
```

### 3. Transform and Save

```python
# Transform data to knowledge graph format
transformed_data = processor.transform(raw_data)

# Validate data
if processor.validate(transformed_data):
    # Save results
    entities = transformed_data['entities']
    relationships = transformed_data['relationships']
    output_path = processor.save_results(entities, relationships)
    print(f"Results saved to: {output_path}")
```

## Command Line Usage

### Basic Commands

```bash
# Download first 100 studies
python -m processors.clinicaltrials_processor --mode full_download --max-studies 100

# Query by disease
python -m processors.clinicaltrials_processor --mode query_by_disease --query-term "cancer"

# Get single study
python -m processors.clinicaltrials_processor --mode nct_id --nct-id "NCT00001234"

# Incremental update since a date
python -m processors.clinicaltrials_processor --mode incremental --last-update-date "2024-01-01"
```

### Common Options

- `--max-studies N`: Limit number of studies to fetch
- `--page-size N`: Number of results per page (max: 100)
- `--rate-limit N`: Requests per second (max: 2.0)
- `--output PATH`: Custom output directory
- `--no-dedup`: Disable deduplication
- `--no-cross-domain`: Disable cross-domain mapping
- `--verbose`: Enable verbose output

## Data Output

### Entity Types

1. **ClinicalTrial**: Main trial information
2. **Intervention**: Drugs, procedures, etc.
3. **Condition**: Diseases/conditions being studied
4. **StudySite**: Locations where trial is conducted
5. **Investigator**: Principal and sub-investigators
6. **Sponsor**: Lead sponsors and collaborators
7. **Outcome**: Primary and secondary outcomes
8. **EligibilityCriteria**: Inclusion/exclusion criteria

### Relationship Types

- `TESTS_INTERVENTION`: Trial → Intervention
- `TRIAL_FOR_DISEASE`: Trial → Condition
- `CONDUCTED_AT_SITE`: Trial → StudySite
- `HAS_PRINCIPAL_INVESTIGATOR`: Trial → Investigator
- `SPONSORED_BY`: Trial → Sponsor
- `HAS_OUTCOME`: Trial → Outcome
- `HAS_ELIGIBILITY`: Trial → EligibilityCriteria

### Output Files

Files are saved in `data/processed/` directory:

```
data/processed/
├── entities/clinicaltrials/
│   ├── clinicaltrials_trials_YYYYMMDD_HHMMSS.json
│   ├── clinicaltrials_interventions_YYYYMMDD_HHMMSS.json
│   ├── clinicaltrials_conditions_YYYYMMDD_HHMMSS.json
│   ├── clinicaltrials_sites_YYYYMMDD_HHMMSS.json
│   ├── clinicaltrials_investigators_YYYYMMDD_HHMMSS.json
│   ├── clinicaltrials_sponsors_YYYYMMDD_HHMMSS.json
│   ├── clinicaltrials_outcomes_YYYYMMDD_HHMMSS.json
│   └── clinicaltrials_eligibility_YYYYMMDD_HHMMSS.json
├── relationships/clinicaltrials/
│   └── clinicaltrials_relationships_YYYYMMDD_HHMMSS.json
└── documents/clinicaltrials/
    └── clinicaltrials_summary_YYYYMMDD_HHMMSS.json
```

## API Rate Limiting

ClinicalTrials.gov API v2 has a rate limit of **2 requests per second**. The processor automatically handles this:

- Default rate: 2.0 requests/second
- Delay between requests: 0.5 seconds
- Automatic retry on failure

**Estimated time for full download:**
- 400,000 studies ÷ 100 per page ÷ 2 per second ≈ 33 hours

## Configuration Options

```python
config = {
    'extraction': {
        # API settings
        'api_base_url': 'https://clinicaltrials.gov/api/v2/studies',
        'request_timeout': 30,

        # Rate limiting
        'rate_limit_per_second': 2.0,
        'rate_limit_delay': 0.5,

        # Pagination
        'page_size': 100,
        'max_studies': None,
        'max_pages': None,

        # Retry
        'max_retries': 3,
        'retry_backoff_factor': 2.0,

        # Deduplication
        'deduplicate_by_nct_id': True,

        # Cross-domain mapping
        'map_to_chembl': True,
        'map_to_mondo': True,

        # Output
        'save_raw_response': False,
        'save_intermediate_batches': True
    }
}
```

## Testing

Run the test suite:

```bash
python scripts/test_clinicaltrials_processor.py
```

The test suite includes:
- Processor initialization tests
- Configuration tests
- Data transformation tests
- Helper method tests
- Save/load tests
- API integration tests (requires network)

## Troubleshooting

### Rate Limit Errors

If you get 429 errors:
- Reduce `rate_limit_per_second` to 1.0 or lower
- Increase `rate_limit_delay` to 1.0 or higher

### Timeout Errors

If requests timeout:
- Increase `request_timeout` to 60 seconds
- Check your network connection
- Reduce `page_size` to get faster responses

### Memory Issues

If you run out of memory:
- Set `max_studies` to process in batches
- Enable `save_intermediate_batches`
- Process smaller subsets at a time

## Cross-Domain Integration

The processor can map:
- **Interventions → ChEMBL compounds** (if implemented)
- **Conditions → MONDO diseases** (if implemented)

Enable/disable with:
```python
config = {
    'extraction': {
        'map_to_chembl': True,  # Enable ChEMBL mapping
        'map_to_mondo': True    # Enable MONDO mapping
    }
}
```

## Best Practices

1. **Start Small**: Test with `max_studies=10` first
2. **Use Filters**: Query by disease/phase/status to reduce dataset size
3. **Save Progress**: The processor supports resume capability
4. **Monitor Logs**: Use `--verbose` for detailed logging
5. **Respect Rate Limits**: Don't increase rate beyond 2.0 req/s

## Further Reading

- Full documentation: `docs/CLINICALTRIALS_PROCESSOR.md`
- API reference: https://clinicaltrials.gov/api/v2/
- Study data structure: https://clinicaltrials.gov/data-api/about-api/study-data-structure

## Support

For issues or questions:
- Check the test suite for examples
- Review the full documentation
- Check processor logs for error details
