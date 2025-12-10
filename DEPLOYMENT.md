# Celerio Scout - Deployment Guide

## GitHub Setup

### 1. Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it `celerio-scout` or your preferred name
3. **Do not** initialize with README (we already have one)

### 2. Add Remote and Push

```bash
# Navigate to project directory
cd C:\Users\simon\Repos\Quiescence

# Add GitHub remote (replace <repo-url> with your actual repository URL)
git remote add origin <repo-url>

# Stage all changes
git add .

# Commit changes
git commit -m "MVP: Complete OSINT-powered startup stall detection with API integrations"

# Push to GitHub
git push -u origin main
```

**Example repository URL format:**
- HTTPS: `https://github.com/yourusername/celerio-scout.git`
- SSH: `git@github.com:yourusername/celerio-scout.git`

## Environment Variables Setup

### Backend Environment Variables

1. Copy the example file:
   ```bash
   cd backend
   copy .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```env
   # Reddit API (get at https://www.reddit.com/prefs/apps)
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   
   # GitHub API (create token at https://github.com/settings/tokens)
   GITHUB_TOKEN=your_github_token
   
   # SimilarWeb API (get at https://www.similarweb.com/corp/api/)
   SIMILARWEB_API_KEY=your_similarweb_api_key
   
   # LinkedIn API (requires OAuth2 setup)
   LINKEDIN_CLIENT_ID=your_linkedin_client_id
   LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
   ```

**Note:** The `.env` file is already in `.gitignore` and will not be committed to GitHub.

## Testing Real Scanning

### 1. Start Backend

```bash
cd backend
venv\Scripts\activate
python main.py
```

### 2. Start Frontend

In a new terminal:
```bash
cd frontend
npm run dev
```

### 3. Test Scanning

1. Open `http://localhost:5173` in your browser
2. Click on any company card or use the scan form
3. Enter a company domain (e.g., `langdb.ai`, `anthropic.com`)
4. Click "Analyze" and wait for results

The system will:
- Fetch homepage and analyze messaging
- Query Wayback Machine for historical data
- Search GitHub for engineering activity
- Query Reddit for social mentions
- Fetch SimilarWeb traffic data (if API key provided)
- Scrape careers pages for hiring signals
- Calculate 3M vector scores

## API Integrations Status

### ✅ Fully Implemented

- **GitHub API**: Engineering signals (commits, stars, repos)
- **Reddit PRAW**: Social mentions and sentiment
- **Wayback Machine**: Historical H1 volatility (free, no key needed)
- **Web Scraping**: Careers pages, homepage analysis

### ⚠️ Requires API Keys

- **SimilarWeb API**: Traffic data (falls back to heuristics if not available)
- **LinkedIn API**: Company insights (requires OAuth2 setup - see below)

### LinkedIn OAuth2 Setup

LinkedIn API requires OAuth2 authentication:

1. Create LinkedIn App at [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Get Client ID and Client Secret
3. Set up OAuth2 redirect URLs
4. Implement OAuth2 flow to get access tokens
5. Update `osint_sources.py` `get_linkedin_company_data()` function

**Note:** For MVP, LinkedIn integration is scaffolded but requires full OAuth2 implementation for production use.

## Production Deployment

### Backend (FastAPI)

1. **Environment Setup:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run with Production Server:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

3. **Update CORS Settings:**
   Edit `backend/main.py` and add your production frontend URL to `allow_origins`

### Frontend (React/Vite)

1. **Build for Production:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy `dist/` folder** to your hosting service (Vercel, Netlify, etc.)

3. **Update API URL:**
   Edit `frontend/src/services/api.js` and update `API_BASE_URL` to your production backend URL

## Security Notes

- ✅ `.env` file is in `.gitignore` - API keys won't be committed
- ✅ Database files (`*.db`) are in `.gitignore`
- ⚠️ Never commit API keys or secrets
- ⚠️ Use environment variables for all sensitive data
- ⚠️ Set up proper CORS policies for production

## Troubleshooting

### GitHub Push Issues

- **Authentication:** Use GitHub Personal Access Token or SSH keys
- **Branch name:** Ensure you're pushing to `main` (not `master`)
- **Large files:** Check `.gitignore` is working correctly

### API Integration Issues

- **Rate Limits:** All APIs have rate limits - implement caching if needed
- **CORS Errors:** Ensure backend CORS settings include frontend URL
- **API Errors:** Check API keys are correct and have proper permissions

### Database Issues

- **Reset Database:** Delete `backend/celerio_scout.db` and restart backend
- **Migration:** Database schema is auto-created on first run

## Next Enhancements

- [ ] Add caching layer for API responses
- [ ] Implement rate limiting for API calls
- [ ] Add database migrations system
- [ ] Set up monitoring and logging
- [ ] Add unit tests for scoring logic
- [ ] Implement batch scanning for YC companies
- [ ] Add export functionality (CSV, JSON)

