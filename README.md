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

- **GitHub API**: Engineering activity, commit frequency, repository stars
- **Reddit PRAW**: Social mentions and sentiment analysis
- **Web Scraping**: Careers page analysis, homepage messaging analysis
- **Y Combinator**: Batch scraping for Series A Crunch cohort (W22, S22, W23, S23)

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
```

**Note**: The application works without API keys but will use fallback heuristics. For full functionality, GitHub and Reddit credentials are recommended.

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
2. **Searches GitHub** for organization repositories and activity
3. **Queries Reddit** for mentions in relevant subreddits
4. **Scrapes careers pages** to detect hiring patterns
5. **Estimates traffic** using domain heuristics (can be enhanced with SimilarWeb API)

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
