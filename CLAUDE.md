# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based PUBG battle analytics service that provides player statistics and match analysis. The service integrates with the PUBG API to fetch player data and presents it through both REST API endpoints and HTML templates.

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
  - `PUBG_API_KEY`: Required for PUBG API access
  - `OPENAI_API_KEY`: For AI analysis features
  - `SECRET_KEY`: Application secret key

## Architecture

### Directory Structure
```
app/
├── api/           # API route handlers
├── models/        # Pydantic data models
├── services/      # Business logic and external API integration
├── templates/     # Jinja2 HTML templates
└── main.py        # FastAPI application entry point
```

### Key Components

- **PUBGAPIService** (`app/services/pubg_api.py`): Handles all PUBG API interactions including player search, stats retrieval, and match data
- **API Routes** (`app/api/pubg_routes.py`): REST endpoints for player data and HTML template rendering
- **Data Models** (`app/models/pubg_models.py`): Pydantic models for request/response validation and type safety

### API Endpoints

- `POST /api/player/search`: Search for players by name
- `GET /api/player/{player_id}/stats`: Get player statistics
- `GET /api/player/{player_id}/matches`: Get recent match history
- `GET /player/{player_name}`: HTML player profile page
- `GET /health`: Health check endpoint

### External Dependencies

- **PUBG API**: Requires valid API key for player data access
- **httpx**: Async HTTP client for API calls
- **FastAPI/Jinja2**: Web framework and templating