try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

class AIAnalysisService:
    def __init__(self):
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        print(f"[DEBUG] Gemini key: {gemini_key[:10] if gemini_key else 'None'}...")
        print(f"[DEBUG] OpenAI key: {openai_key[:10] if openai_key else 'None'}...")
        print(f"[DEBUG] Gemini available: {GEMINI_AVAILABLE}")
        
        # Gemini를 우선적으로 사용
        if gemini_key and GEMINI_AVAILABLE:
            print("[DEBUG] Configuring Gemini API")
            genai.configure(api_key=gemini_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.use_gemini = True
            self.api_key = gemini_key
            print("[DEBUG] Successfully configured Gemini")
        elif openai_key:
            print("[DEBUG] Configuring OpenAI API")
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=openai_key)
                self.use_gemini = False
                self.api_key = openai_key
                print("[DEBUG] Successfully configured OpenAI")
            except ImportError:
                self.client = None
                self.use_gemini = False
                self.api_key = None
                print("[DEBUG] OpenAI import failed")
        else:
            print("[DEBUG] No API keys available")
            self.model = None
            self.client = None
            self.use_gemini = False
            self.api_key = None
    
    async def analyze_match_performance(self, player_stats: Dict[str, Any], teammates_stats: List[Dict[str, Any]], match_info: Dict[str, Any]) -> Optional[str]:
        """매치 성과 분석"""
        if not self.api_key:
            return "AI 분석을 위한 API 키가 설정되지 않았습니다."
        
        try:
            # 분석을 위한 데이터 구성
            analysis_data = self._prepare_analysis_data(player_stats, teammates_stats, match_info)
            
            # AI 프롬프트 생성
            prompt = self._create_analysis_prompt(analysis_data)
            
            # AI API 호출
            print(f"[DEBUG] Using Gemini: {self.use_gemini}")
            if self.use_gemini:
                print("[DEBUG] Calling Gemini API")
                response = await self._call_gemini_api(prompt)
            else:
                print("[DEBUG] Calling OpenAI API")
                response = await self._call_openai_api(prompt)
            
            return response
            
        except Exception as e:
            print(f"AI 분석 오류: {e}")
            return f"분석 중 오류가 발생했습니다: {str(e)}"
    
    def _prepare_analysis_data(self, player_stats: Dict[str, Any], teammates_stats: List[Dict[str, Any]], match_info: Dict[str, Any]) -> Dict[str, Any]:
        """분석을 위한 데이터 준비"""
        return {
            "player": {
                "kills": player_stats.get("kills", 0),
                "damage": player_stats.get("damageDealt", 0),
                "survival_time": player_stats.get("timeSurvived", 0) / 60,  # 분 단위
                "headshots": player_stats.get("headshotKills", 0),
                "rank": player_stats.get("winPlace", 0),
                "ride_distance": player_stats.get("rideDistance", 0) / 1000,  # km 단위
                "walk_distance": player_stats.get("walkDistance", 0) / 1000,  # km 단위
                "weapons_acquired": player_stats.get("weaponsAcquired", 0),
                "boosts": player_stats.get("boosts", 0),
                "heals": player_stats.get("heals", 0)
            },
            "teammates": [
                {
                    "name": teammate.get("attributes", {}).get("stats", {}).get("name", "Unknown"),
                    "kills": teammate.get("attributes", {}).get("stats", {}).get("kills", 0),
                    "damage": teammate.get("attributes", {}).get("stats", {}).get("damageDealt", 0),
                    "survival_time": teammate.get("attributes", {}).get("stats", {}).get("timeSurvived", 0) / 60,
                    "headshots": teammate.get("attributes", {}).get("stats", {}).get("headshotKills", 0)
                }
                for teammate in teammates_stats
            ],
            "match": {
                "game_mode": match_info.get("gameMode", ""),
                "map_name": match_info.get("mapName", ""),
                "created_at": match_info.get("createdAt", "")
            }
        }
    
    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """AI 분석을 위한 프롬프트 생성"""
        player = data["player"]
        teammates = data["teammates"]
        match = data["match"]
        
        prompt = f"""
PUBG 배틀로얄 게임 매치 분석을 수행해주세요.

## 매치 정보
- 게임 모드: {match["game_mode"]}
- 맵: {match["map_name"]}
- 최종 순위: {player["rank"]}위

## 플레이어 성과
- 킬 수: {player["kills"]}
- 총 데미지: {player["damage"]:.1f}
- 생존 시간: {player["survival_time"]:.1f}분
- 헤드샷: {player["headshots"]}
- 이동 거리: {player["ride_distance"]:.1f}km (차량) + {player["walk_distance"]:.1f}km (도보)
- 무기 획득: {player["weapons_acquired"]}개
- 부스터 사용: {player["boosts"]}개
- 치료 아이템 사용: {player["heals"]}개

## 팀원 성과
"""
        
        for i, teammate in enumerate(teammates, 1):
            prompt += f"""
팀원 {i} ({teammate["name"]}):
- 킬: {teammate["kills"]}, 데미지: {teammate["damage"]:.1f}
- 생존시간: {teammate["survival_time"]:.1f}분, 헤드샷: {teammate["headshots"]}
"""
        
        prompt += """

## 분석 요청
다음 관점에서 상세히 분석해주세요:

1. **전투 성과 분석**: 킬/데미지 효율성, 헤드샷 정확도
2. **생존 전략 분석**: 이동 패턴, 생존 시간 대비 성과
3. **팀워크 평가**: 팀원들과의 성과 비교 및 협력도
4. **개선점 제안**: 구체적이고 실행 가능한 개선 방안
5. **종합 평가**: 이번 매치의 총평 및 등급 (S, A, B, C, D)

한국어로 친근하고 구체적인 조언을 제공해주세요. 각 섹션을 명확히 구분하여 작성해주세요.
"""
        
        return prompt
    
    async def _call_gemini_api(self, prompt: str) -> str:
        """Gemini API 호출"""
        try:
            # Gemini는 동기식 API이므로 비동기 래퍼 사용
            import asyncio
            
            def generate_content():
                response = self.model.generate_content(prompt)
                return response.text
            
            # 동기 함수를 비동기로 실행
            response = await asyncio.get_event_loop().run_in_executor(None, generate_content)
            return response.strip()
            
        except Exception as e:
            return f"Gemini API 호출 실패: {str(e)}"
    
    async def _call_openai_api(self, prompt: str) -> str:
        """OpenAI API 호출"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 PUBG 전문 게임 코치입니다. 플레이어의 성과를 분석하고 개선점을 제안하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"AI 분석 호출 실패: {str(e)}"
    
    async def analyze_player_trends(self, matches_data: List[Dict[str, Any]]) -> Optional[str]:
        """여러 매치의 트렌드 분석"""
        if not self.api_key or not matches_data:
            return None
        
        try:
            # 트렌드 분석을 위한 데이터 집계
            trend_data = self._aggregate_match_data(matches_data)
            
            # 트렌드 분석 프롬프트 생성
            prompt = self._create_trend_analysis_prompt(trend_data)
            
            # AI 분석 실행
            if self.use_gemini:
                response = await self._call_gemini_api(prompt)
            else:
                response = await self._call_openai_api(prompt)
            
            return response
            
        except Exception as e:
            print(f"트렌드 분석 오류: {e}")
            return None
    
    def _aggregate_match_data(self, matches_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """매치 데이터 집계"""
        total_matches = len(matches_data)
        if total_matches == 0:
            return {}
        
        # 기본 통계 계산
        total_kills = sum(match.get("kills", 0) for match in matches_data)
        total_damage = sum(match.get("damage", 0) for match in matches_data)
        avg_rank = sum(match.get("rank", 100) for match in matches_data) / total_matches
        
        return {
            "total_matches": total_matches,
            "avg_kills": total_kills / total_matches,
            "avg_damage": total_damage / total_matches,
            "avg_rank": avg_rank,
            "kill_trend": [match.get("kills", 0) for match in matches_data[-10:]],  # 최근 10경기
            "rank_trend": [match.get("rank", 100) for match in matches_data[-10:]]
        }
    
    def _create_trend_analysis_prompt(self, trend_data: Dict[str, Any]) -> str:
        """트렌드 분석 프롬프트 생성"""
        return f"""
PUBG 플레이어의 최근 {trend_data["total_matches"]}경기 트렌드를 분석해주세요.

## 전체 통계
- 평균 킬: {trend_data["avg_kills"]:.1f}
- 평균 데미지: {trend_data["avg_damage"]:.1f}
- 평균 순위: {trend_data["avg_rank"]:.1f}위

## 최근 추이
- 킬 추이: {trend_data["kill_trend"]}
- 순위 추이: {trend_data["rank_trend"]}

다음 관점에서 분석해주세요:
1. 성과 향상/하락 패턴
2. 일관성 평가
3. 장기적 개선 방향 제안

한국어로 간결하게 작성해주세요.
"""