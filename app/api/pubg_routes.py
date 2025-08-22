from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.services.pubg_api import PUBGAPIService
from app.models.pubg_models import PlayerSearchRequest, PlayerInfo, PlayerStats
from typing import Dict, Any

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
pubg_service = PUBGAPIService()

@router.post("/api/player/search")
async def search_player(request: PlayerSearchRequest):
    """플레이어 검색 API"""
    player_data = await pubg_service.search_player(request.player_name, request.platform)
    
    if not player_data:
        raise HTTPException(status_code=404, detail="플레이어를 찾을 수 없습니다.")
    
    return {
        "player_id": player_data["id"],
        "player_name": player_data["attributes"]["name"],
        "platform": request.platform
    }

@router.get("/api/player/{player_id}/stats")
async def get_player_stats(player_id: str, platform: str = "steam"):
    """플레이어 스탯 조회 API"""
    stats_data = await pubg_service.get_player_stats(player_id, platform)
    
    if not stats_data:
        raise HTTPException(status_code=404, detail="스탯 정보를 찾을 수 없습니다.")
    
    return stats_data

@router.get("/api/player/{player_id}/matches")
async def get_recent_matches(player_id: str, platform: str = "steam"):
    """최근 매치 조회 API"""
    matches = await pubg_service.get_recent_matches(player_id, platform)
    
    if not matches:
        raise HTTPException(status_code=404, detail="매치 정보를 찾을 수 없습니다.")
    
    return {"matches": matches}

@router.get("/player/{player_name}", response_class=HTMLResponse)
async def player_profile(request: Request, player_name: str):
    """플레이어 프로필 페이지"""
    try:
        # 플레이어 검색
        player_data = await pubg_service.search_player(player_name)
        
        if not player_data:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "플레이어를 찾을 수 없습니다."
            })
        
        player_id = player_data["id"]
        
        # 스탯과 최근 매치 정보 가져오기
        stats_data = await pubg_service.get_player_stats(player_id)
        recent_matches = await pubg_service.get_recent_matches(player_id)
        
        return templates.TemplateResponse("player_profile.html", {
            "request": request,
            "player": player_data,
            "stats": stats_data,
            "matches": recent_matches
        })
        
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"오류가 발생했습니다: {str(e)}"
        })