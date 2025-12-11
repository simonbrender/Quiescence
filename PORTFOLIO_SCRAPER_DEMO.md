# Portfolio Scraper Demo

## Overview

The Celerio Scout system now includes an intelligent portfolio scraper that:
1. **Automatically discovers VCs** by crawling the web and analyzing VC directories
2. **Groups VCs by stage and focus areas** for easy navigation
3. **Maintains an up-to-date database** of all known VC firms
4. **Allows users to add custom VCs** through the UI
5. **Scrapes company data** from selected portfolios
6. **Automatically analyzes** all scraped companies using the 3M Revenue Architecture framework
7. **Stores results** in the database for viewing and filtering

## How It Works

### 1. Backend API Endpoints

#### `GET /portfolios`
Returns a list of available VC portfolios from the database, with optional filtering by stage, focus area, or type.

**Query Parameters:**
- `stage` - Filter by investment stage (e.g., "Seed", "Series A")
- `focus_area` - Filter by focus area (e.g., "AI/ML", "B2B SaaS")
- `vc_type` - Filter by VC type ("VC", "Accelerator", "Studio")

**Response:** List of portfolios grouped by stage and focus areas.

#### `POST /portfolios/discover`
Discovers new VCs from web sources and adds them to the database.

**Response:**
```json
{
  "discovered": 25,
  "added": 12,
  "message": "Discovered 25 VCs, added 12 new ones"
}
```

#### `POST /portfolios/add`
Adds a custom VC portfolio entered by the user.

**Request:**
```json
{
  "firm_name": "Example Ventures",
  "url": "https://example.com",
  "portfolio_url": "https://example.com/portfolio",
  "type": "VC",
  "stage": "Seed",
  "focus_areas": ["AI/ML", "B2B SaaS"]
}
```

#### `GET /portfolios/stages`
Returns list of unique investment stages in the database.

#### `GET /portfolios/focus-areas`
Returns list of unique focus areas in the database.

**Response:**
```json
[
  {
    "firm_name": "Y Combinator",
    "url": "https://www.ycombinator.com/companies",
    "type": "Accelerator",
    "stage": "Pre-Seed/Seed"
  },
  {
    "firm_name": "NFX",
    "url": "https://www.nfx.com/portfolio",
    "type": "VC",
    "stage": "Seed"
  }
  // ... more portfolios
]
```

#### `POST /portfolios/scrape`
Scrapes selected portfolios and analyzes companies.

**Request:**
```json
{
  "portfolio_names": ["Y Combinator", "NFX", "Antler"]
}
```

**Response:**
```json
{
  "scraped_count": 150,
  "analyzed_count": 145,
  "portfolios": ["Y Combinator", "NFX", "Antler"],
  "companies": [
    {
      "id": 123456,
      "name": "Example Startup",
      "domain": "examplestartup.com",
      "messaging_score": 75.5,
      "motion_score": 68.2,
      "market_score": 72.1,
      "stall_probability": "low",
      // ... more fields
    }
    // ... more companies
  ]
}
```

### 2. VC Discovery System

The `backend/vc_discovery.py` module handles:
- **Web crawling** to discover VCs from directories and lists
- **Automatic categorization** by stage and focus areas
- **Metadata extraction** from VC websites
- **Focus area detection** using keyword matching
- **Stage determination** based on website content

### 3. Portfolio Scraper Module

The `backend/portfolio_scraper.py` module handles:
- **Loading available portfolios** from database (with fallback to seed data)
- **Scraping portfolio pages** using Crawl4AI for JavaScript-heavy sites
- **Extracting company information** with specialized parsers for:
  - Y Combinator (batch-aware)
  - NFX (structured portfolio)
  - Antler (JavaScript-rendered)
  - Generic portfolios (fallback parser)

### 4. Frontend UI Components

#### PortfolioSelector Component
The `PortfolioSelector` component (`frontend/src/components/PortfolioSelector.jsx`) provides:
- **Portfolio list** grouped by **stage** (Pre-Seed, Seed, Series A, etc.)
- **Filtering** by stage, focus area, type, and search
- **Multi-select checkboxes** for portfolio selection
- **"Discover VCs" button** to automatically find new VCs
- **"Add VC" button** to add custom portfolios
- **Scrape button** that triggers analysis
- **Progress indicators** during scraping
- **Results display** showing:
  - Number of portfolios scraped
  - Companies found
  - Companies successfully analyzed

#### AddVCForm Component
The `AddVCForm` component (`frontend/src/components/AddVCForm.jsx`) provides:
- **Form fields** for firm name, URL, portfolio URL
- **Type selection** (VC, Accelerator, Studio)
- **Stage selection** dropdown
- **Focus area management** with quick-add buttons
- **Validation** and error handling

### 5. Integration Flow

#### VC Discovery Flow
```
User clicks "Discover VCs" →
  Frontend sends POST /portfolios/discover →
    Backend crawls web sources →
      Categorizes VCs by stage and focus →
        Stores in database →
          Returns discovery results →
            UI refreshes with new VCs
```

#### Adding Custom VC Flow
```
User clicks "Add VC" →
  Opens AddVCForm →
    User fills in VC details →
      Frontend sends POST /portfolios/add →
        Backend validates and stores →
          Returns new VC →
            UI refreshes with new VC
```

#### Portfolio Scraping Flow
```
User selects portfolios →
  Frontend sends POST /portfolios/scrape →
    Backend loads VC URLs from database →
      Scrapes portfolio pages →
        Extracts company names →
          For each company:
            - Calculates 3M scores (Messaging, Motion, Market)
            - Stores in database →
              Returns results to frontend →
                UI updates with new companies
```

## Usage Example

### Step 1: Discover VCs (Optional)
1. Click "Portfolios" in the navigation bar
2. Click "Discover VCs" button
3. System crawls web sources and adds new VCs to database
4. VCs are automatically categorized by stage and focus areas

### Step 2: Add Custom VC (Optional)
1. Click "Add VC" button
2. Fill in form:
   - Firm name (required)
   - Website URL (required)
   - Portfolio URL (optional, defaults to website URL)
   - Type (VC, Accelerator, or Studio)
   - Stage (Pre-Seed, Seed, Series A, etc.)
   - Focus areas (AI/ML, B2B SaaS, Fintech, etc.)
3. Click "Add VC"
4. New VC appears in the list

### Step 3: Filter & Select Portfolios
1. Use filters to narrow down:
   - **Search**: Type to search by firm name or domain
   - **Stage**: Filter by investment stage
   - **Focus Area**: Filter by focus (e.g., AI/ML, B2B SaaS)
   - **Type**: Filter by VC type
2. Browse portfolios grouped by **stage**:
   - **Pre-Seed/Seed**: Early-stage investors
   - **Series A**: Growth-stage investors
   - **Series B+**: Late-stage investors
3. Check boxes next to portfolios you want to scrape
4. Selected count appears in the scrape button

### Step 4: Scrape & Analyze
1. Click "Scrape & Analyze Selected" button
2. System:
   - Scrapes portfolio pages (using Crawl4AI if needed)
   - Extracts company names
   - For each company:
     - Fetches homepage
     - Analyzes messaging (H1, title, jargon)
     - Checks motion signals (traffic, hiring)
     - Evaluates market signals (GitHub, Reddit, sentiment)
     - Calculates stall probability
   - Stores results in database

### Step 5: View Results
1. Modal shows completion summary
2. Companies appear in main dashboard
3. Filter by source, YC batch, or vector weakness
4. Click any company to see detailed analysis

## Technical Details

### Scraping Strategy
- **Crawl4AI** for JavaScript-heavy sites (React/Vue/Angular portfolios)
- **BeautifulSoup** for HTML parsing
- **Rate limiting** to respect API limits
- **Caching** to avoid duplicate requests

### Company Analysis
- **Messaging Vector**: H1 volatility, positioning consistency, jargon density
- **Motion Vector**: Traffic score, hiring status, sales/eng ratio
- **Market Vector**: GitHub activity, Reddit mentions, sentiment

### Error Handling
- Graceful fallbacks if Crawl4AI unavailable
- Continues processing even if individual companies fail
- Error messages displayed in UI

## VC Database Features

### Automatic Discovery
The system automatically discovers VCs from:
- VC directory websites
- VC news sites
- Portfolio listing pages
- Web crawling of known VC sources

### Categorization
VCs are automatically categorized by:
- **Stage**: Pre-Seed, Seed, Series A, Series B, Growth
- **Focus Areas**: AI/ML, B2B SaaS, Fintech, Healthcare, Consumer, Enterprise, DevTools, Security, Climate
- **Type**: VC, Accelerator, Studio

### Seed Data
The system starts with seed portfolios from:
- **Y Combinator** (batches: W22, S22, W23, S23)
- **NFX**
- **Antler**
- **First Round Capital**
- **Precursor Ventures**
- **Techstars**
- **Atomic**
- **Entrepreneur First**
- **Andreessen Horowitz (a16z)**
- **Sequoia Capital**
- **Benchmark**
- **Founders Fund**
- **Lightspeed Venture Partners**
- **Craft Ventures**
- **SignalFire**

### User-Added VCs
Users can add custom VCs through the UI, which are:
- Stored in the database
- Marked as "user_added"
- Available for scraping immediately
- Included in filtering and grouping

## Future Enhancements

- [ ] Batch processing with progress updates
- [ ] Resume interrupted scraping sessions
- [ ] Export scraped companies to CSV/JSON
- [ ] Custom portfolio URL support
- [ ] Scheduled automatic scraping
- [ ] Portfolio comparison analytics

