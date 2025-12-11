# World-Class Dataset Plan

## Current Status

### Database Analysis
- **Total Companies**: 5 (WAY TOO FEW!)
- **YC Companies**: 5 (should be 1,000-5,000)
- **Antler Companies**: 1 (should be 1,267)
- **Data Completeness**: 0% (no stage, focus areas, employees, or funding)

## Problem Identified

1. **Portfolio Scraping Not Running**: Only 5 companies in database suggests portfolio scraping hasn't executed successfully
2. **Enrichment Not Comprehensive**: Current enrichment only does basic inference, not deep web crawling
3. **Missing Data Sources**: Need Firecrawl for comprehensive web scraping

## Solution Implemented

### 1. Comprehensive Portfolio Scraper
- **File**: `backend/comprehensive_portfolio_scraper.py`
- **Function**: Scrapes ALL companies from YC (target: 5,000) and Antler (target: 1,267)
- **Status**: Running in background

### 2. Enhanced Enrichment with Firecrawl
- **File**: `backend/enhanced_enrichment.py`
- **Features**:
  - Firecrawl integration for deep web crawling
  - Crawl4AI fallback
  - HTTP fallback
  - Extracts comprehensive attributes:
    - Funding amount & rounds
    - Employee count
    - Founding date
    - Headquarters location
    - Founders
    - Product description
    - Industry
    - Current valuation
    - Key milestones

### 3. Enhanced Enrichment Endpoint
- **Endpoint**: `POST /companies/enrich?batch_size=100&use_firecrawl=true`
- **Features**:
  - Uses Firecrawl when available
  - Falls back to basic enrichment
  - Runs asynchronously in background
  - Processes companies in batches

## Required Attributes (World-Class Dataset)

Based on research, each company should have:

1. ✅ **Company Name** - Already captured
2. ✅ **Domain** - Already captured
3. ✅ **Source** (YC/Antler) - Already captured
4. ✅ **YC Batch** - Already captured
5. 🔄 **Founding Date** - Enhanced enrichment extracts this
6. 🔄 **Founders** - Enhanced enrichment extracts this
7. ✅ **Industry/Sector** - Focus areas (being enriched)
8. 🔄 **Funding Rounds** - Enhanced enrichment extracts this
9. 🔄 **Current Valuation** - Enhanced enrichment extracts this
10. ✅ **Stage** - Being enriched (Seed for portfolio companies)
11. 🔄 **Employee Count** - Enhanced enrichment extracts this
12. 🔄 **Headquarters Location** - Enhanced enrichment extracts this
13. ✅ **Website URL** - Domain (already captured)
14. 🔄 **Product/Service Description** - Enhanced enrichment extracts this
15. 🔄 **Key Milestones** - Enhanced enrichment extracts this
16. ✅ **Accelerator Program** - Source field (YC/Antler)

## Next Steps

1. **Wait for Portfolio Scraping** (30-60 minutes)
   - Monitor `portfolio_scraping_output.log`
   - Check database periodically
   - Should see 1,000-6,000 companies being added

2. **Run Enhanced Enrichment**
   - Set `FIRECRAWL_API_KEY` environment variable (optional but recommended)
   - Call `POST /companies/enrich?batch_size=500&use_firecrawl=true`
   - This will enrich all companies with comprehensive data

3. **Validate Dataset Quality**
   - Check data completeness metrics
   - Verify all required attributes are populated
   - Export to CSV for validation

## Firecrawl Setup (Optional but Recommended)

```bash
# Install Firecrawl
pip install firecrawl-py

# Set API key (get from https://firecrawl.dev)
export FIRECRAWL_API_KEY=your_api_key_here
```

Firecrawl provides:
- Better JavaScript rendering
- Structured data extraction
- Markdown conversion
- Metadata extraction
- Link discovery

## Expected Results

After portfolio scraping completes:
- **YC Companies**: 1,000-5,000
- **Antler Companies**: 1,267
- **Total**: 2,267-6,267 companies

After enrichment completes:
- **Data Completeness**: >80% for all attributes
- **Funding Data**: Available for most companies
- **Employee Count**: Available for most companies
- **Founding Date**: Available for most companies
- **Location**: Available for most companies

## Monitoring

- **Portfolio Scraping**: Check `portfolio_scraping_output.log`
- **Database**: Run `check_database_sources.py` periodically
- **Enrichment**: Check backend logs for enrichment progress






