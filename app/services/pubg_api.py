import httpx
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class PUBGAPIService:
    def __init__(self):
        self.api_key = os.getenv("PUBG_API_KEY")
        self.base_url = "https://api.pubg.com/shards"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/vnd.api+json"
        }
    
    async def search_player(self, player_name: str, platform: str = "steam") -> Optional[Dict[str, Any]]:
        """플레이어 검색"""
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.base_url}/{platform}/players"
                params = {"filter[playerNames]": player_name}
                
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                if data.get("data"):
                    return data["data"][0]
                return None
                
            except Exception as e:
                print(f"플레이어 검색 오류: {e}")
                return None
    
    async def get_player_stats(self, player_id: str, platform: str = "steam") -> Optional[Dict[str, Any]]:
        """플레이어 스탯 조회"""
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.base_url}/{platform}/players/{player_id}/seasons/lifetime"
                
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                return response.json()
                
            except Exception as e:
                print(f"플레이어 스탯 조회 오류: {e}")
                return None
    
    async def get_recent_matches(self, player_id: str, platform: str = "steam") -> Optional[Dict[str, Any]]:
        """최근 매치 조회"""
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.base_url}/{platform}/players/{player_id}"
                
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                matches = data.get("data", {}).get("relationships", {}).get("matches", {}).get("data", [])
                
                return matches[:20]  # 최근 20경기
                
            except Exception as e:
                print(f"최근 매치 조회 오류: {e}")
                return None
    
    async def get_match_details(self, match_id: str, platform: str = "steam") -> Optional[Dict[str, Any]]:
        """매치 상세 정보 조회"""
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.base_url}/{platform}/matches/{match_id}"
                
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                return response.json()
                
            except Exception as e:
                print(f"매치 상세 조회 오류: {e}")
                return None
    
    async def get_weapon_stats(self, player_id: str, platform: str = "steam") -> Optional[Dict[str, Any]]:
        """플레이어 무기별 통계 조회"""
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.base_url}/{platform}/players/{player_id}/weapon_mastery"
                
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                return response.json()
                
            except Exception as e:
                print(f"무기 통계 조회 오류: {e}")
                return None
    
    def extract_match_weapons_data(self, match_details: Dict[str, Any], player_id: str) -> Dict[str, Any]:
        """매치에서 플레이어의 무기 사용 데이터 추출"""
        try:
            participants = [item for item in match_details.get("included", []) if item.get("type") == "participant"]
            player_participant = next(
                (p for p in participants if p.get("attributes", {}).get("stats", {}).get("playerId") == player_id), 
                None
            )
            
            if not player_participant:
                return {}
            
            stats = player_participant.get("attributes", {}).get("stats", {})
            
            # 무기 관련 통계 추출
            weapon_data = {
                "weapons_acquired": stats.get("weaponsAcquired", 0),
                "headshot_kills": stats.get("headshotKills", 0),
                "total_kills": stats.get("kills", 0),
                "longest_kill": stats.get("longestKill", 0),
                "damage_dealt": stats.get("damageDealt", 0),
                "headshot_rate": (stats.get("headshotKills", 0) / max(stats.get("kills", 1), 1)) * 100
            }
            
            return weapon_data
            
        except Exception as e:
            print(f"무기 데이터 추출 오류: {e}")
            return {}