# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based PUBG battle analytics service that provides player statistics and match analysis with AI-powered insights. The service integrates with the PUBG API to fetch player data and provides both REST API endpoints and HTML templates for data visualization.

## Development Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app/main.py
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Environment Setup
- Copy `.env.example` to `.env` and configure:
  - `PUBG_API_KEY`: Required for PUBG API access (essential)
  - `GEMINI_API_KEY`: For AI analysis features (primary AI provider)
  - `OPENAI_API_KEY`: Fallback AI provider (optional)
  - `SECRET_KEY`: Application secret key

## Architecture

### Directory Structure
```
app/
├── api/           # API route handlers
├── models/        # Pydantic data models
├── services/      # Business logic and external API integration
├── templates/     # Jinja2 HTML templates
├── utils/         # Utility functions for display formatting
└── main.py        # FastAPI application entry point
```

### Key Components

- **PUBGAPIService** (`app/services/pubg_api.py`): Handles all PUBG API interactions including player search, stats retrieval, and match data
- **AIAnalysisService** (`app/services/ai_analysis.py`): Provides AI-powered match analysis using Gemini (primary) with Ollama fallback
- **API Routes** (`app/api/pubg_routes.py`): REST endpoints for player data, HTML template rendering, and AI analysis
- **Data Models** (`app/models/pubg_models.py`): Pydantic models for request/response validation and type safety
- **Display Utils** (`app/utils/display_utils.py`): Korean localization utilities for game modes, maps, and UI formatting

### AI Analysis Features

The service provides two types of AI analysis:
1. **Individual Match Analysis** (`/api/match/{match_id}/analyze`): Detailed analysis of a specific match performance
2. **Trend Analysis** (`/api/player/{player_id}/trend-analysis`): Multi-match performance trends and recommendations

AI provider hierarchy:
1. **Gemini Flash** (gemini-1.5-flash): Primary provider for lightweight, quota-efficient analysis
2. **Ollama Local** (qwen2:0.5b): Fallback when Gemini quota is exceeded
3. **OpenAI GPT-3.5-turbo**: Alternative fallback (rarely used)

### API Endpoints

#### Player Data
- `POST /api/player/search`: Search for players by name
- `GET /api/player/{player_id}/stats`: Get player statistics
- `GET /api/player/{player_id}/matches`: Get recent match history
- `GET /player/{player_name}`: HTML player profile page

#### AI Analysis
- `GET|POST /api/match/{match_id}/analyze`: AI analysis of specific match
- `GET /api/player/{player_id}/trend-analysis`: Multi-match trend analysis

#### Utility
- `GET /health`: Health check endpoint
- `GET /api/test`: Debug endpoint

### External Dependencies

- **PUBG API**: Requires valid API key for player data access
- **Google Gemini**: Primary AI provider for match analysis
- **Ollama**: Local AI fallback (qwen2:0.5b model)
- **httpx**: Async HTTP client for API calls
- **FastAPI/Jinja2**: Web framework and templating