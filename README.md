# Celerio Scout

OSINT-powered startup stall detection application that identifies stalling B2B AI startups by triangulating signals from free public sources.

## Architecture

- **Frontend**: React (Vite) + Tailwind CSS + Recharts
- **Backend**: Python (FastAPI) + DuckDB
- **OSINT Sources**: GitHub API, Reddit PRAW, Web Scraping

## Features

### 3M Vector Scoring

Each company is scored on three vectors based on the Celerio Revenue Architecture framework:

1. **Messaging Vector**: Narrative consistency, positioning, jargon density
2. **Motion Vector**: GTM velocity, hiring activity, traffic signals
3. **Market Vector**: PMF proxies, social sentiment, engineering pulse

### Real OSINT Data Collection

- **GitHub API**: Engineering activity, commit frequency, repository stars (with enhanced org detection)
- **Reddit PRAW**: Social mentions and sentiment analysis
- **SimilarWeb API**: Traffic data, global rankings, monthly visits
- **Wayback Machine**: Historical H1 volatility, snapshot analysis
- **LinkedIn API**: Company insights, employee count, industry data
- **Web Scraping**: Careers page analysis, homepage messaging analysis
  - Uses **Crawl4AI** for JavaScript-heavy sites (automatic fallback)
  - Simple HTTP requests for standard sites
- **Y Combinator**: Batch scraping for Series A Crunch cohort (W22, S22, W23, S23)
- **VC Portfolio Scraping**: Antler, NFX, and other VC portfolios using Crawl4AI

### Performance & Reliability

- **Caching Layer**: In-memory cache with TTL to reduce API calls and improve response times
- **Rate Limiting**: Token bucket algorithm prevents hitting API rate limits
- **Graceful Fallbacks**: System continues to work even when APIs are unavailable

### Celerio Radar Visualization

Interactive radar charts show the health of each vector, allowing instant visual diagnosis of where companies are stalling.

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- (Optional) Reddit API credentials for social signals
- (Optional) GitHub token for engineering signals

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env and add your API keys (optional)

python main.py
```

Backend runs on `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

## Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Optional: Reddit API for social signals
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# Optional: GitHub API for engineering signals
GITHUB_TOKEN=your_github_token

# Optional: SimilarWeb API for traffic data
SIMILARWEB_API_KEY=your_similarweb_api_key

# Optional: LinkedIn API for company insights (requires OAuth2 setup)
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
```

**Note**: The application works without API keys but will use fallback heuristics. For full functionality:
- **GitHub** and **Reddit** credentials are recommended for core signals
- **SimilarWeb** provides accurate traffic data (falls back to heuristics if not available)
- **Wayback Machine** is free and requires no API key (rate limited)
- **LinkedIn** requires OAuth2 setup - see [LinkedIn API documentation](https://docs.microsoft.com/en-us/linkedin/) for details

## API Endpoints

- `GET /companies` - Get all companies with optional filters
  - Query params: `yc_batch`, `source`, `vector`, `min_score`
- `POST /scan` - Scan a new company URL
  - Body: `{"url": "example.com"}`
- `{"url": "example.com"}`
- `GET /stats` - Get aggregate market health statistics

## Data Sources

### Mock Data

The application comes with 5 sample companies demonstrating different failure modes for immediate testing.

### Real Data Collection

When scanning real companies, the system:

1. **Fetches homepage** to analyze messaging (H1, title, jargon density)
2. **Queries Wayback Machine** for historical H1 volatility and snapshot analysis
3. **Searches GitHub** for organization repositories and activity
4. **Queries Reddit** for mentions in relevant subreddits
5. **Fetches SimilarWeb data** for traffic metrics and global rankings
6. **Retrieves LinkedIn data** for company insights (if configured)
7. **Scrapes careers pages** to detect hiring patterns
8. **Calculates 3M vector scores** based on all collected signals

## Development

### Project Structure

```
Quiescence/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── scorer.py         # 3M vector scoring logic
│   ├── osint_sources.py  # Real OSINT data collection
│   ├── seeds.py          # Data ingestion (YC, Antler, etc.)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # Main application
│   │   ├── components/   # React components
│   │   └── services/     # API client
│   └── package.json
└── README.md
```

### Adding New Data Sources

1. Add collection function to `backend/osint_sources.py`
2. Update corresponding check function in `backend/scorer.py`
3. Add environment variables if needed
4. Update `.env.example`

## Design

The UI follows Celerio's design principles:
- Clean, minimal interface
- Professional typography (Inter font)
- Dark theme with subtle accents
- Data-driven presentation
- Focus on clarity and usability

## License

MIT

## Contributing

This is a private project for Celerio. For questions or contributions, contact the maintainers.
