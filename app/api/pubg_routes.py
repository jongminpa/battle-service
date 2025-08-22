from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.services.pubg_api import PUBGAPIService
from app.services.ai_analysis import AIAnalysisService
from app.models.pubg_models import PlayerSearchRequest, PlayerInfo, PlayerStats
from app.utils.display_utils import get_korean_game_mode, get_korean_map_name, get_rank_color
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
        
        # 매치 상세 정보 가져오기
        detailed_matches = []
        if recent_matches:
            for match in recent_matches[:20]:  # 최근 20경기
                match_details = await pubg_service.get_match_details(match["id"])
                if match_details:
                    detailed_matches.append(match_details)
        
        return templates.TemplateResponse("player_profile.html", {
            "request": request,
            "player": player_data,
            "stats": stats_data,
            "matches": recent_matches,
            "detailed_matches": detailed_matches,
            "get_korean_game_mode": get_korean_game_mode,
            "get_korean_map_name": get_korean_map_name,
            "get_rank_color": get_rank_color
        })
        
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"오류가 발생했습니다: {str(e)}"
        })

@router.post("/api/match/{match_id}/analyze")
@router.get("/api/match/{match_id}/analyze")
async def analyze_match(match_id: str, player_id: str, platform: str = "steam"):
    """매치 AI 분석 API"""
    print(f"[API DEBUG] AI 분석 요청 받음 - Match ID: {match_id}, Player ID: {player_id}")
    try:
        # 매치 상세 정보 가져오기
        print(f"[API DEBUG] 매치 상세 정보 가져오는 중...")
        match_details = await pubg_service.get_match_details(match_id, platform)
        
        if not match_details:
            raise HTTPException(status_code=404, detail="매치 정보를 찾을 수 없습니다.")
        
        # 매치 데이터에서 필요한 정보 추출
        match_data = match_details["data"]
        participants = [item for item in match_details["included"] if item["type"] == "participant"]
        
        if not participants:
            raise HTTPException(status_code=404, detail="매치 참가자 정보를 찾을 수 없습니다.")
        
        # 특정 플레이어 찾기
        player_participant = next(
            (p for p in participants if p["attributes"]["stats"]["playerId"] == player_id), 
            None
        )
        
        if not player_participant:
            raise HTTPException(status_code=404, detail="해당 플레이어의 매치 정보를 찾을 수 없습니다.")
        
        player_stats = player_participant["attributes"]["stats"]
        
        # 팀원 찾기 (같은 winPlace를 가진 플레이어들)
        teammates = [
            p for p in participants 
            if p["attributes"]["stats"]["winPlace"] == player_stats["winPlace"] 
            and p["attributes"]["stats"]["playerId"] != player_stats["playerId"]
        ]
        
        # AI 분석 실행 - 매번 새로운 인스턴스 생성
        print(f"[API DEBUG] AI 서비스 인스턴스 생성 중...")
        ai_service = AIAnalysisService()
        print(f"[API DEBUG] AI 분석 실행 중...")
        analysis = await ai_service.analyze_match_performance(
            player_stats=player_stats,
            teammates_stats=teammates,
            match_info=match_data["attributes"]
        )
        print(f"[API DEBUG] AI 분석 완료: {len(analysis) if analysis else 0} 글자")
        
        return {
            "match_id": match_id,
            "analysis": analysis,
            "player_stats": player_stats,
            "teammates_count": len(teammates)
        }
        
    except Exception as e:
        print(f"[API DEBUG] AI 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")

@router.get("/api/player/{player_id}/trend-analysis")
async def get_trend_analysis(player_id: str, platform: str = "steam"):
    """플레이어 트렌드 분석 API"""
    try:
        # 최근 매치들 가져오기
        recent_matches = await pubg_service.get_recent_matches(player_id, platform)
        
        if not recent_matches:
            raise HTTPException(status_code=404, detail="매치 정보를 찾을 수 없습니다.")
        
        # 매치 상세 정보들 수집
        matches_data = []
        for match in recent_matches[:10]:  # 최근 10경기만
            match_details = await pubg_service.get_match_details(match["id"], platform)
            if match_details:
                participants = [item for item in match_details["included"] if item["type"] == "participant"]
                player_participant = next(
                    (p for p in participants if p["attributes"]["stats"]["playerId"] == player_id), 
                    None
                )
                
                if player_participant:
                    stats = player_participant["attributes"]["stats"]
                    matches_data.append({
                        "kills": stats.get("kills", 0),
                        "damage": stats.get("damageDealt", 0),
                        "rank": stats.get("winPlace", 100),
                        "survival_time": stats.get("timeSurvived", 0),
                        "dbnos": stats.get("dBNOs", 0),
                        "revives": stats.get("revives", 0),
                        "assists": stats.get("assists", 0),
                        "headshots": stats.get("headshotKills", 0)
                    })
        
        if not matches_data:
            raise HTTPException(status_code=404, detail="분석할 매치 데이터가 없습니다.")
        
        # AI 트렌드 분석 실행 - 매번 새로운 인스턴스 생성
        ai_service = AIAnalysisService()
        trend_analysis = await ai_service.analyze_player_trends(matches_data)
        
        return {
            "player_id": player_id,
            "matches_analyzed": len(matches_data),
            "trend_analysis": trend_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"트렌드 분석 중 오류가 발생했습니다: {str(e)}")

@router.get("/api/test")
async def test_endpoint():
    print("[TEST] 테스트 엔드포인트 호출됨!")
    return {"message": "테스트 성공!"}