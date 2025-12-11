# Changelog

## [MVP] - 2025-01-XX

### Added
- **Real OSINT Data Collection**
  - GitHub API integration for engineering signals (commits, stars, repo activity)
  - Reddit PRAW integration for social mentions and sentiment
  - Web scraping for careers pages (hiring signals)
  - Y Combinator batch scraping functionality
  - Real-time homepage analysis for messaging vector

- **UI Design System**
  - Aligned with Celerio website design principles
  - Inter font family for professional typography
  - Clean, minimal dark theme
  - Improved card components with hover effects
  - Better color system matching Celerio brand

- **Backend Enhancements**
  - Modular OSINT source integration (`osint_sources.py`)
  - Environment variable support for API keys
  - Graceful fallbacks when APIs unavailable
  - Improved error handling

- **Documentation**
  - Comprehensive README with setup instructions
  - Quick start guide
  - Environment variable documentation
  - API endpoint documentation

### Changed
- UI color scheme from cyberpunk/neon to professional Celerio style
- Component styling to match Celerio's clean aesthetic
- Badge designs for better visual hierarchy
- Typography improvements for readability

### Technical
- Re-added `crawl4ai` dependency for advanced web scraping (JavaScript-heavy sites)
- Added `lxml` for better HTML parsing
- Updated function signatures for consistency
- Improved async/await patterns
- Added in-memory caching layer with TTL support (`cache.py`)
- Added token bucket rate limiter for API calls (`rate_limiter.py`)
- Enhanced GitHub org detection with multiple heuristics
- Added crawl4ai fallback for homepage scraping when simple HTTP fails
- Implemented Antler portfolio scraping using crawl4ai

### Completed (Previously Listed as Next Steps)
- [x] Add SimilarWeb API integration for traffic data (implemented in `osint_sources.py`)
- [x] Implement Wayback Machine API for H1 volatility tracking (implemented in `osint_sources.py`)
- [x] Add caching layer for API responses (implemented in `cache.py` with TTL support)
- [x] Implement rate limiting for API calls (implemented in `rate_limiter.py` with token bucket algorithm)
- [x] Enhance GitHub org detection algorithms (multiple heuristics: domain name, suffix removal, camelCase conversion)

### Next Steps
- [ ] Add LinkedIn API integration for positioning consistency (placeholder exists, needs OAuth2 implementation)
- [ ] Add cache statistics endpoint to API
- [ ] Consider Redis for distributed caching in production
- [ ] Add rate limit headers to API responses




