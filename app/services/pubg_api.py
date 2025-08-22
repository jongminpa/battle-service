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