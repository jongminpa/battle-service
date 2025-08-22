from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class PlayerSearchRequest(BaseModel):
    player_name: str
    platform: str = "steam"

class PlayerInfo(BaseModel):
    id: str
    name: str
    platform: str
    created_at: datetime
    
class PlayerStats(BaseModel):
    kills: int
    deaths: int
    assists: int
    wins: int
    top10s: int
    rounds_played: int
    damage_dealt: float
    kd_ratio: float
    win_ratio: float
    avg_damage: float

class MatchSummary(BaseModel):
    match_id: str
    game_mode: str
    map_name: str
    duration: int
    created_at: datetime
    rank: int
    kills: int
    damage: float
    survival_time: float

class PlayerAnalysis(BaseModel):
    player_name: str
    overall_rating: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    recent_performance: str