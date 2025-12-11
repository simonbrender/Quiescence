# Comprehensive VC Discovery Strategy

## Current Problem
- Only discovering 10 VCs (should be 25,000-30,000 globally)
- 0 VCs being added (likely duplicates or workflow failure)
- Discovery method is too limited

## Target Volumes (2024/2025)
- **Venture Capital Firms**: 25,000-30,000 globally (~8,000-10,000 active)
- **Venture Studios**: 1,100+ (fastest growing)
- **Accelerators**: 3,000+ active programs
- **Incubators**: 7,000+ (many government/university-backed)

## Multi-Layered Discovery Strategy

### Layer 1: Comprehensive Directory Crawling
**Sources:**
1. **Crunchbase** (API + scraping)
   - VC firm directory
   - Filter: Active in last 12 months
   - Expected: ~8,000-10,000 active firms

2. **PitchBook** (API if available, else scraping)
   - Most comprehensive VC database
   - Expected: ~15,000+ firms

3. **CB Insights** (Scraping)
   - Research reports and directories
   - Expected: ~5,000+ firms

4. **AngelList** (API + scraping)
   - Startup ecosystem data
   - Expected: ~3,000+ VCs

5. **VentureSource** (Scraping)
   - Historical VC data
   - Expected: ~10,000+ firms

### Layer 2: Specialized Directories
**VC-Specific:**
- TheVC.com
- VCList.com
- VCNewsDaily.com
- Crunchbase VC Directory
- PitchBook VC Directory

**Studio-Specific:**
- StudioHub.io
- Startup Studio Map
- Studio Founders Network
- Individual studio websites

**Accelerator-Specific:**
- F6S.com (largest accelerator database)
- Seed-DB.com
- AcceleratorList.com
- YC, Techstars, 500 Global directories

**Incubator-Specific:**
- University incubator directories
- Government innovation hub listings
- Regional startup ecosystem maps

### Layer 3: Web Search Discovery
**Search Strategies:**
1. **Google Search API** (or scraping)
   - Queries: "venture capital firms [country]", "VC firms [city]"
   - Queries: "venture studios [region]", "startup studios"
   - Queries: "accelerators [vertical]", "incubators [region]"

2. **LinkedIn Scraping**
   - Search: "Venture Capital" companies
   - Search: "Startup Studio" companies
   - Filter by company type and size

3. **GitHub Discovery**
   - Organizations tagged as VC/Studio
   - Portfolio company repositories (trace back to investors)

### Layer 4: Regional & Vertical Discovery
**Geographic Coverage:**
- US: State-by-state directories
- Europe: Country-specific directories (UK, France, Germany, etc.)
- Asia: China, India, Southeast Asia directories
- Other: Latin America, Middle East, Africa

**Vertical Focus:**
- FinTech VCs
- BioTech VCs
- AI/ML VCs
- ClimateTech VCs
- Enterprise SaaS VCs

### Layer 5: Social Media & Community Discovery
**Sources:**
- Twitter/X: VC firm accounts, #venturecapital hashtag
- LinkedIn: VC firm pages, investor profiles
- Reddit: r/venturecapital, r/startups
- Discord/Slack: VC communities

### Layer 6: Portfolio-Based Discovery
**Strategy:**
1. Start with known portfolio companies
2. Extract investor information from:
   - Company websites (investors page)
   - Crunchbase funding rounds
   - Press releases
   - SEC filings (for US companies)

### Layer 7: API-Based Discovery
**APIs to Integrate:**
1. **Crunchbase API** (if available)
2. **PitchBook API** (if available)
3. **Clearbit API** (company data)
4. **FullContact API** (company enrichment)
5. **Google Places API** (physical locations)

## Implementation Priority

### Phase 1: Foundation (Week 1)
- [ ] Fix duplicate detection logic
- [ ] Implement Crunchbase scraping (comprehensive)
- [ ] Implement F6S accelerator directory scraping
- [ ] Add Google Search API integration
- [ ] Implement LinkedIn company search

### Phase 2: Expansion (Week 2)
- [ ] Add PitchBook scraping
- [ ] Implement StudioHub.io scraping
- [ ] Add regional directory scraping
- [ ] Implement portfolio-based discovery

### Phase 3: Enhancement (Week 3)
- [ ] Add API integrations (where available)
- [ ] Implement social media discovery
- [ ] Add vertical-specific discovery
- [ ] Implement continuous discovery (scheduled)

## Technical Requirements

### Crawling Infrastructure
- **Rate Limiting**: Respect robots.txt, implement delays
- **Retry Logic**: Exponential backoff for failed requests
- **Parallel Processing**: Process multiple sources concurrently
- **Error Handling**: Graceful degradation, continue on failures
- **Deduplication**: Smart matching (fuzzy matching for names/domains)

### Data Quality
- **Validation**: Verify domains, check for active websites
- **Enrichment**: Add missing data (domain, type, stage, focus areas)
- **Verification**: Mark verified vs unverified entries
- **Zombie Detection**: Identify inactive firms (no recent investments)

### Storage & Indexing
- **Database**: Store all discovered entities
- **Search Index**: Fast lookup by name, domain, type
- **Deduplication**: Track by domain, firm_name hash, URL

## Expected Results

### Conservative Estimate
- **VCs**: 5,000-8,000 discovered
- **Studios**: 500-800 discovered
- **Accelerators**: 1,500-2,000 discovered
- **Incubators**: 2,000-3,000 discovered
- **Total**: ~9,000-14,000 investment vehicles

### Optimistic Estimate (with all sources)
- **VCs**: 15,000-20,000 discovered
- **Studios**: 800-1,100 discovered
- **Accelerators**: 2,500-3,000 discovered
- **Incubators**: 4,000-5,000 discovered
- **Total**: ~22,000-29,000 investment vehicles

## Next Steps
1. Investigate why 0 VCs were added (duplicate detection issue)
2. Implement comprehensive Crunchbase scraping
3. Add F6S accelerator directory
4. Implement Google Search discovery
5. Add LinkedIn company search
6. Build deduplication system
7. Add continuous discovery scheduler



