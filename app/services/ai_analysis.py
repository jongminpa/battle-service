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
            # Gemini Flash 모델 사용 (더 경량화, 할당량 절약)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
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
                "heals": player_stats.get("heals", 0),
                "dbnos": player_stats.get("dBNOs", 0),  # 기절시킨 횟수
                "revives": player_stats.get("revives", 0),  # 부활시킨 횟수
                "team_kills": player_stats.get("teamKills", 0),  # 팀킬 (실수)
                "assists": player_stats.get("assists", 0)  # 어시스트
            },
            "teammates": [
                {
                    "name": teammate.get("attributes", {}).get("stats", {}).get("name", "Unknown"),
                    "kills": teammate.get("attributes", {}).get("stats", {}).get("kills", 0),
                    "damage": teammate.get("attributes", {}).get("stats", {}).get("damageDealt", 0),
                    "survival_time": teammate.get("attributes", {}).get("stats", {}).get("timeSurvived", 0) / 60,
                    "headshots": teammate.get("attributes", {}).get("stats", {}).get("headshotKills", 0),
                    "dbnos": teammate.get("attributes", {}).get("stats", {}).get("dBNOs", 0),
                    "revives": teammate.get("attributes", {}).get("stats", {}).get("revives", 0),
                    "assists": teammate.get("attributes", {}).get("stats", {}).get("assists", 0)
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
- 기절시킨 횟수: {player["dbnos"]}
- 팀원 부활: {player["revives"]}회
- 어시스트: {player["assists"]}
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
- 기절시킨 횟수: {teammate["dbnos"]}, 부활: {teammate["revives"]}회, 어시스트: {teammate["assists"]}
"""
        
        prompt += """

## 분석 요청
다음 관점에서 상세히 분석해주세요:

1. **전투 성과 분석**: 킜/데미지 효율성, 헤드샷 정확도, 기절 vs 확정킬 비율
2. **팀워크 분석**: 부활 횟수, 어시스트 기여도, 팀원들과의 협력 수준
3. **생존 전략 분석**: 이동 패턴, 생존 시간 대비 성과, 아이템 활용도
4. **전술적 분석**: 교전 스타일, 포지셔닝, 상황 판단력
5. **개선점 제안**: 구체적이고 실행 가능한 개선 방안
6. **종합 평가**: 이번 매치의 총평 및 등급 (S, A, B, C, D)

한국어로 친근하고 구체적인 조언을 제공해주세요. 각 섹션을 명확히 구분하여 작성해주세요.
"""
        
        return prompt
    
    async def _call_ollama_api(self, prompt: str) -> str:
        """Ollama 로컬 AI 호출"""
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2:0.5b",
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("response", "")
                if result.strip():
                    return result
                else:
                    raise Exception("Empty response from Ollama")
            else:
                raise Exception(f"Ollama API returned status {response.status_code}")

    async def _call_gemini_api(self, prompt: str) -> str:
        """Gemini API 호출"""
        try:
            # 먼저 로컬 Ollama 시도
            try:
                import httpx
                async with httpx.AsyncClient(timeout=2.0) as client:
                    test_response = await client.get("http://localhost:11434/api/tags")
                    if test_response.status_code == 200:
                        return await self._call_ollama_api(prompt)
            except:
                pass  # Ollama 없으면 Gemini 사용
            
            # Gemini 사용
            import asyncio
            
            def generate_content():
                response = self.model.generate_content(prompt)
                return response.text
            
            response = await asyncio.get_event_loop().run_in_executor(None, generate_content)
            return response.strip()
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                return """
🚫 일일 AI 분석 할당량을 초과했습니다.

📊 기본 분석:
이 매치에서는 게임 통계를 통해 기본적인 성과를 확인할 수 있습니다.
- 순위, 킬 수, 데미지, 생존 시간 등을 참고하여 플레이를 개선해보세요.
- 내일 다시 상세한 AI 분석을 받아보실 수 있습니다.

💡 팁: 할당량 절약을 위해 가장 중요한 매치만 분석해보세요!
"""
            else:
                return f"Gemini API 호출 실패: {error_msg}"
    
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
        total_dbnos = sum(match.get("dbnos", 0) for match in matches_data)
        total_revives = sum(match.get("revives", 0) for match in matches_data)
        total_assists = sum(match.get("assists", 0) for match in matches_data)
        total_headshots = sum(match.get("headshots", 0) for match in matches_data)
        avg_rank = sum(match.get("rank", 100) for match in matches_data) / total_matches
        
        return {
            "total_matches": total_matches,
            "avg_kills": total_kills / total_matches,
            "avg_damage": total_damage / total_matches,
            "avg_dbnos": total_dbnos / total_matches,
            "avg_revives": total_revives / total_matches,
            "avg_assists": total_assists / total_matches,
            "avg_headshots": total_headshots / total_matches,
            "avg_rank": avg_rank,
            "kill_trend": [match.get("kills", 0) for match in matches_data[-10:]],  # 최근 10경기
            "rank_trend": [match.get("rank", 100) for match in matches_data[-10:]],
            "dbnos_trend": [match.get("dbnos", 0) for match in matches_data[-10:]],
            "revives_trend": [match.get("revives", 0) for match in matches_data[-10:]]
        }
    
    def _create_trend_analysis_prompt(self, trend_data: Dict[str, Any]) -> str:
        """트렌드 분석 프롬프트 생성"""
        return f"""
PUBG 플레이어의 최근 {trend_data["total_matches"]}경기 종합 성과 분석을 수행해주세요.

## 📊 전체 통계
- 총 경기 수: {trend_data["total_matches"]}경기
- 평균 킬 수: {trend_data["avg_kills"]:.1f}킬
- 평균 데미지: {trend_data["avg_damage"]:.0f}
- 평균 순위: {trend_data["avg_rank"]:.1f}위
- 평균 기절시킨 횟수: {trend_data["avg_dbnos"]:.1f}
- 평균 팀원 부활: {trend_data["avg_revives"]:.1f}회
- 평균 어시스트: {trend_data["avg_assists"]:.1f}
- 평균 헤드샷: {trend_data["avg_headshots"]:.1f}

## 📈 최근 10경기 추이
- 킬 수 변화: {trend_data["kill_trend"]}
- 순위 변화: {trend_data["rank_trend"]}
- 기절시킨 횟수: {trend_data["dbnos_trend"]}
- 팀원 부활 횟수: {trend_data["revives_trend"]}

## 🎯 상세 분석 요청

다음 관점에서 종합적으로 분석하고 구체적인 개선 방안을 제시해주세요:

### 1. 성과 트렌드 분석
- 최근 성과가 향상되고 있는지, 하락하고 있는지
- 킬과 순위의 상관관계 분석
- 기절 vs 확정킬 효율성 분석
- 일관성 있는 플레이를 하고 있는지 평가

### 2. 팀워크 및 협력 분석
- 팀원 부활 패턴과 팀워크 수준
- 어시스트 기여도와 협력 플레이 능력
- 개인 성과 vs 팀 기여도 균형

### 3. 강점과 약점 파악
- 현재 플레이 스타일의 강점
- 개선이 필요한 약점
- 다른 플레이어 대비 상대적 위치

### 4. 구체적 개선 전략
- 단기적 개선 목표 (1-2주)
- 중장기적 발전 방향 (1-2개월)
- 실행 가능한 구체적 액션 플랜

### 5. 플레이 스타일 추천
- 현재 통계에 맞는 최적 플레이 스타일
- 권장 게임 모드나 전략
- 피해야 할 플레이 패턴

### 6. 목표 설정
- 다음 10경기 목표
- 달성 가능한 현실적 목표 수치

친근하고 동기부여가 되는 톤으로, 실용적인 조언을 중심으로 한국어로 작성해주세요.
각 섹션을 명확히 구분하고, 구체적인 수치와 예시를 포함해주세요.
"""