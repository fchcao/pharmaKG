# Data Collection Environment Setup

## Virtual Environments

### data-spider Environment
Primary environment for all data collection spiders and processors.

```bash
# Activate data collection environment
conda activate data-spider

# Install required dependencies
pip install playwright scrapy requests beautifulsoup4 lxml

# Install Playwright browsers (first time only)
playwright install chromium
```

### playwright-env Environment
Dedicated Playwright browser testing environment.

```bash
# Activate Playwright testing environment
source /root/miniconda3/etc/profile.d/conda.sh
conda activate playwright-env

# Run browser automation tests
python your_playwright_test.py
```

## Usage Guidelines

When running any data collection processor or spider:

1. **Always activate `data-spider` environment first**
2. **Use `playwright-env` for browser automation tasks**
3. **Check environment before running**: `conda env list`

## Current Spiders and Processors

| Spider/Processor | Environment | Status |
|------------------|-------------|--------|
| CDE Spider | data-spider | Active - HTTP 400 issues |
| NMPA Spider | data-spider | Blocked by anti-bot |
| ChEMBL Processor | data-spider | Working |
| ClinicalTrials Processor | data-spider | Working |
| UniProt Processor | data-spider | Working |

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError`:
```bash
# Ensure correct environment is activated
conda activate data-spider
pip install -r requirements.txt
```

### Playwright Browser Issues
```bash
# Reinstall browsers
playwright install --force chromium

# Or use dedicated environment
conda activate playwright-env
```

### Cookie/Session Issues
- Clear cookies: `rm -f data/sources/regulations/cde/cookies.json`
- Re-run spider to generate fresh cookies

## Anti-Crawler Status

| Website | Protection Level | Status | Alternative |
|----------|----------------|---------|-------------|
| NMPA.gov.cn | High (AliYun) | Blocked | data.nmpa.gov.cn API |
| CDE.org.cn | High | HTTP 400 | Commercial APIs |
| FDA.gov | Medium | Working | N/A |
| ClinicalTrials.gov | Low | Working | N/A |

## Next Steps

1. Consider commercial APIs for blocked sites
2. Manual data collection for small datasets
3. Official API requests where available
