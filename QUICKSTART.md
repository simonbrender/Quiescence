# Celerio Scout - Quick Start Guide

## Prerequisites

- Python 3.9+ installed
- Node.js 18+ and npm installed

## Setup Instructions

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
python main.py
```

The backend will start on `http://localhost:8000`

### 2. Frontend Setup

Open a **new terminal window**:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will start on `http://localhost:5173`

## Using the Application

1. **View Companies**: The dashboard loads with 5 mock companies showing different failure modes
2. **Filter**: Use the sidebar filters to filter by YC batch, source, or vector weakness
3. **View Details**: Click any company card to see detailed analysis including:
   - Celerio Radar visualization
   - Revenue Architecture Bowtie diagram
   - Signal details
   - Remediation recommendations
4. **Scan New Company**: Use the scan form in the detail view to analyze a new company URL

## Mock Data

The application comes pre-loaded with 5 sample companies:

1. **StagnantAI** - High risk (messaging failure)
2. **RocketShip.io** - Medium risk (motion failure)
3. **TechJargon Inc** - High risk (messaging + market issues)
4. **SilentGrowth** - High risk (market failure)
5. **HealthyScale** - Low risk (healthy signals)

## API Endpoints

- `GET http://localhost:8000/companies` - Get all companies
- `GET http://localhost:8000/stats` - Get aggregate statistics
- `POST http://localhost:8000/scan` - Scan a new company (body: `{"url": "example.com"}`)

## Troubleshooting

- **Backend won't start**: Make sure port 8000 is not in use
- **Frontend won't connect**: Ensure backend is running first
- **Database errors**: Delete `celerio_scout.db` and restart backend
- **CORS errors**: Check that backend CORS settings include `http://localhost:5173`

## Next Steps

For production use, replace mock implementations in `backend/scorer.py` with real API integrations:
- SimilarWeb API for traffic data
- PRAW (Reddit API) for social signals
- GitHub API for engineering signals
- BuiltWith API for technographic data

