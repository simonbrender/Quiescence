# Browser Agent Testing Guide - Portfolio Scraping Observability

## Implementation Complete ✅

Full observability has been implemented for portfolio scraping with:
- Real-time progress tracking via WebSocket
- Screenshot capture during scraping
- Picture-in-picture monitor UI
- Event logging
- Browser visibility (non-headless mode)

## Current Status

- **Backend**: Running and ready
- **Frontend**: Monitor component integrated
- **Database**: 1,248 companies currently stored
- **Observability**: Fully implemented and ready to test

## Testing Steps

### 1. Navigate to Frontend
```
URL: http://localhost:5173
```

### 2. Open Advanced Search
- Click the "Advanced Search" button in the navigation bar
- The Advanced Search modal will open

### 3. Enter Portfolio Query
- In the "Natural Language Search" textarea, enter:
  ```
  retrieve the YC and Antler portfolios
  ```

### 4. Start Search
- Click the "Search Companies" button
- The scraping will begin automatically

### 5. Observe Monitor Window
A picture-in-picture style monitor window will appear showing:

#### Real-Time Stats
- **YC Companies**: Count updates as companies are discovered
- **Antler Companies**: Count updates as companies are discovered
- **Scrolls/Clicks**: Progress indicators

#### Screenshot Preview
- Latest screenshot from the scraping browser
- Updates automatically as scraping progresses

#### Event Log
- All scraping events in real-time:
  - `start`: Scraping started
  - `navigate`: Navigation to portfolio page
  - `progress`: Progress update with counts
  - `screenshot`: Screenshot captured
  - `complete`: Scraping completed
  - `error`: Error occurred

#### Monitor Controls
- **Minimize/Maximize**: Toggle window size
- **Close**: Close monitor (scraping continues in background)

## Expected Results

### YC Portfolio
- **Expected**: 1,000-5,000 companies
- **Method**: Infinite scroll
- **Time**: 10-15 minutes
- **Screenshots**: Captured every 10 scrolls

### Antler Portfolio
- **Expected**: 1,267 companies (confirmed on website)
- **Method**: "Load More" button clicks
- **Time**: 5-10 minutes
- **Screenshots**: Captured every 5 clicks

### Total
- **Expected**: ~2,267-6,267 companies
- **Total Time**: 15-25 minutes

## Verification

### During Scraping
1. Monitor window shows real-time progress
2. Screenshots update showing browser state
3. Company counts increase steadily
4. Event log shows all actions

### After Completion
1. Monitor shows "Scraping completed!"
2. Final company counts displayed
3. Results appear in main UI
4. All companies stored in database

## Troubleshooting

### Monitor Not Appearing
- Check browser console for errors
- Verify WebSocket connection: `ws://localhost:8000/api/ws/portfolio-scraping/{session_id}`
- Check backend logs for session creation

### No Progress Updates
- Verify backend is running
- Check WebSocket connection status
- Review backend logs for scraping progress

### Screenshots Not Updating
- Check `artifacts/portfolio_scraping/` directory
- Verify Playwright is installed
- Check browser visibility settings

## Architecture

```
Frontend (React)
    ↓ WebSocket
Backend API (FastAPI)
    ↓ Progress Callback
Observable Scraper (Playwright)
    ↓ Screenshots & Events
Portfolio Websites (YC, Antler)
```

## Files Created

### Backend
- `backend/portfolio_scraper_observable.py`: Observable scraper with screenshot capture
- `backend/portfolio_scraping_monitor.py`: WebSocket/SSE endpoints
- Updated `backend/web_company_discovery.py`: Progress callback support
- Updated `backend/main.py`: Monitor router integration

### Frontend
- `frontend/src/components/PortfolioScrapingMonitor.jsx`: Monitor component
- Updated `frontend/src/components/AdvancedSearch.jsx`: Monitor integration
- Updated `frontend/src/services/api.js`: Session ID handling

## Next Steps

1. ✅ Observability implemented
2. ✅ Monitor component created
3. ✅ Integration complete
4. 🔄 **Ready for browser agent testing**
5. ⏳ Verify full scrape (15-25 minutes)
6. ⏳ Confirm company counts match expectations
7. ⏳ Validate data quality

## Notes

- The scraping runs in **visible browser mode** for full observability
- Screenshots are saved to `artifacts/portfolio_scraping/`
- Progress events are streamed via WebSocket in real-time
- The monitor can be minimized but scraping continues
- Multiple scraping sessions can run concurrently

