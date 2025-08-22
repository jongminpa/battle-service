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
    
    async def analyze_match_performance(self, player_stats: Dict[str, Any], teammates_stats: List[Dict[str, Any]], match_info: Dict[str, Any], weapon_stats: Optional[Dict[str, Any]] = None, match_weapon_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """매치 성과 분석"""
        if not self.api_key:
            return "AI 분석을 위한 API 키가 설정되지 않았습니다."
        
        try:
            # 분석을 위한 데이터 구성
            analysis_data = self._prepare_analysis_data(player_stats, teammates_stats, match_info, weapon_stats, match_weapon_data)
            
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
    
    def _prepare_analysis_data(self, player_stats: Dict[str, Any], teammates_stats: List[Dict[str, Any]], match_info: Dict[str, Any], weapon_stats: Optional[Dict[str, Any]] = None, match_weapon_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
            },
            "weapon_mastery": self._process_weapon_stats(weapon_stats) if weapon_stats else {},
            "match_weapons": match_weapon_data if match_weapon_data else {}
        }
    
    def _process_weapon_stats(self, weapon_stats: Dict[str, Any]) -> Dict[str, Any]:
        """무기 통계 데이터 처리"""
        try:
            if not weapon_stats or "data" not in weapon_stats:
                return {}
            
            processed_weapons = {}
            weapons_data = weapon_stats["data"]["attributes"]["weaponSummaries"]
            
            # 상위 5개 무기만 추출 (사용 빈도 기준)
            top_weapons = sorted(weapons_data, key=lambda x: x.get("TimesUsed", 0), reverse=True)[:5]
            
            for weapon in top_weapons:
                weapon_name = weapon.get("WeaponName", "Unknown")
                processed_weapons[weapon_name] = {
                    "times_used": weapon.get("TimesUsed", 0),
                    "kills": weapon.get("Kills", 0),
                    "damage": weapon.get("DamageDealt", 0),
                    "headshots": weapon.get("HeadshotKills", 0),
                    "longest_kill": weapon.get("LongestKill", 0),
                    "avg_damage_per_use": weapon.get("DamageDealt", 0) / max(weapon.get("TimesUsed", 1), 1)
                }
            
            return processed_weapons
            
        except Exception as e:
            print(f"무기 통계 처리 오류: {e}")
            return {}
    
    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """AI 분석을 위한 프롬프트 생성"""
        player = data["player"]
        teammates = data["teammates"]
        match = data["match"]
        weapon_mastery = data.get("weapon_mastery", {})
        match_weapons = data.get("match_weapons", {})
        
        # 게임 모드 분석
        game_mode = match["game_mode"].lower()
        is_solo = "solo" in game_mode
        is_duo = "duo" in game_mode
        is_squad = "squad" in game_mode
        is_fpp = "fpp" in game_mode
        
        # 성과 지표 계산
        kill_efficiency = player["kills"] / max(player["survival_time"] / 60, 1) if player["survival_time"] > 0 else 0
        damage_per_kill = player["damage"] / max(player["kills"], 1) if player["kills"] > 0 else player["damage"]
        headshot_rate = (player["headshots"] / max(player["kills"], 1)) * 100 if player["kills"] > 0 else 0
        team_total_kills = sum(t["kills"] for t in teammates) + player["kills"] if teammates else player["kills"]
        kill_contribution = (player["kills"] / max(team_total_kills, 1)) * 100 if team_total_kills > 0 else 100
        
        # 게임 모드별 특화 분석 컨텍스트
        mode_context = ""
        if is_solo:
            mode_context = """
🎯 **SOLO 모드 특화 분석**: 개인 실력과 독립적 판단력, 자원 관리 능력이 핵심입니다.
- 모든 교전이 1:1 상황이므로 개인 에임과 포지셔닝이 결정적
- 팀원 의존 없이 독립적 생존 전략과 판단력 필요
- 보급품과 장비 독점 사용 가능하지만 정보 수집의 한계
"""
        elif is_duo:
            mode_context = """
🎯 **DUO 모드 특화 분석**: 파트너와의 협력과 역할 분담, 의사소통이 핵심입니다.
- 2:2 교전 상황에서 파트너와의 시너지와 크로스파이어 중요
- 부활/치료 지원을 통한 생존률 향상 가능
- 정보 공유와 역할 분담 (공격수/서포터) 전략 필수
"""
        else:  # squad
            mode_context = """
🎯 **SQUAD 모드 특화 분석**: 팀워크, 리더십, 역할 분담이 승패를 좌우합니다.
- 4:4 대규모 교전에서 팀 협력과 전술적 포지셔닝 필수
- 부활/치료 지원이 팀 생존에 결정적 영향
- 리더십, 의사소통, 역할 분담 (IGL/어썰트/서포터/저격수) 중요
"""
        
        perspective_context = ""
        if is_fpp:
            perspective_context = "**FPP (1인칭)**: 제한된 시야로 인한 정보 수집 한계, 사운드 플레이와 맵 리딩 능력이 더욱 중요"
        else:
            perspective_context = "**TPP (3인칭)**: 넓은 시야 활용 가능, 엄폐물 뒤 정보 수집과 포지셔닝 우위 확보 중요"
        
        prompt = f"""
당신은 PUBG 전문 게임 코치이자 프로 선수 멘토입니다. 아래 데이터를 바탕으로 {match["game_mode"]} 모드에 특화된 매치 분석을 제공해주세요.

{mode_context}
{perspective_context}

## 📊 매치 기본 정보
- **게임 모드**: {match["game_mode"]} 
- **맵**: {match["map_name"]}
- **최종 순위**: {player["rank"]}위 / 100명
- **생존 시간**: {player["survival_time"]:.1f}분

## 🎯 플레이어 상세 성과 데이터
### 전투 통계
- **킬 수**: {player["kills"]}킬 {"" if is_solo else f"(팀 기여도: {kill_contribution:.1f}%)"}
- **총 데미지**: {player["damage"]:.0f} (킬당 평균: {damage_per_kill:.0f})
- **헤드샷**: {player["headshots"]}개 (정확도: {headshot_rate:.1f}%)
- **기절시킨 횟수**: {player["dbnos"]}명 (확정킬 전환율: {(player["kills"]/max(player["dbnos"], 1)*100):.1f}%)
- **어시스트**: {player["assists"]}회

### 생존 및 이동
- **킬 효율성**: {kill_efficiency:.2f}킬/분
- **이동 거리**: 차량 {player["ride_distance"]:.1f}km + 도보 {player["walk_distance"]:.1f}km (총 {player["ride_distance"] + player["walk_distance"]:.1f}km)
- **무기 획득**: {player["weapons_acquired"]}개

{"### 팀워크 및 지원" if not is_solo else "### 자원 관리 및 독립성"}
{"- **팀원 부활**: " + str(player["revives"]) + "회" if not is_solo else "- **독립적 생존**: 팀 지원 없이 개인 역량만으로 생존"}
{"- **팀킬**: " + str(player["team_kills"]) + "회 " + ("⚠️ 주의필요" if player["team_kills"] > 0 else "✅ 양호") if not is_solo else ""}

### 아이템 관리
- **부스터 사용**: {player["boosts"]}개
- **치료 아이템**: {player["heals"]}개

### 🔫 무기 활용 분석
{"**이번 매치 무기 성과**:" if match_weapons else "**무기 데이터 없음**"}
{f"- 무기 획득: {match_weapons.get('weapons_acquired', 0)}개" if match_weapons else ""}
{f"- 최장거리 킬: {match_weapons.get('longest_kill', 0):.0f}m" if match_weapons else ""}
{f"- 헤드샷 비율: {match_weapons.get('headshot_rate', 0):.1f}%" if match_weapons else ""}

{"**주요 무기 숙련도 (전체 통계)**:" if weapon_mastery else ""}"""

        if weapon_mastery:
            for weapon_name, stats in list(weapon_mastery.items())[:3]:  # 상위 3개 무기만
                prompt += f"""
- **{weapon_name}**: {stats['times_used']}회 사용, {stats['kills']}킬, 평균 {stats['avg_damage_per_use']:.0f} 데미지/사용
"""
        
        prompt += f"""
{"## 👥 팀원 성과 비교" if not is_solo else "## 🔍 SOLO 플레이 독립성 분석"}"""
        
        if teammates:
            for i, teammate in enumerate(teammates, 1):
                teammate_damage_per_kill = teammate["damage"] / max(teammate["kills"], 1) if teammate["kills"] > 0 else teammate["damage"]
                teammate_headshot_rate = (teammate["headshots"] / max(teammate["kills"], 1)) * 100 if teammate["kills"] > 0 else 0
                
                prompt += f"""
**팀원 {i}** ({teammate["name"]}):
- 킬/데미지: {teammate["kills"]}킬, {teammate["damage"]:.0f}데미지 (킬당: {teammate_damage_per_kill:.0f})
- 생존시간: {teammate["survival_time"]:.1f}분, 헤드샷: {teammate["headshots"]}개 ({teammate_headshot_rate:.1f}%)
- 기절/부활/어시스트: {teammate["dbnos"]}/{teammate["revives"]}/{teammate["assists"]}
"""
        else:
            prompt += "\n**솔로 플레이** - 팀원 데이터 없음"
        
        prompt += f"""

## 🎮 전문가 분석 요청

당신의 전문적인 게이밍 경험을 바탕으로 다음 영역을 **구체적인 수치와 예시**를 들어 분석해주세요:

### 1. 🔥 전투 퍼포먼스 심층 분석
- **킬 효율성 평가**: {kill_efficiency:.2f}킬/분은 이 게임모드/맵에서 어떤 수준인가?
- **데미지 효율성**: 킬당 {damage_per_kill:.0f} 데미지는 적절한가? (일반적으로 200-300이 이상적)
- **헤드샷 정확도**: {headshot_rate:.1f}%의 헤드샷 비율에 대한 평가와 개선 방안
- **확정킬 능력**: 기절 {player["dbnos"]}명 중 킬 {player["kills"]}개 전환 - 마무리 능력 분석
- **교전 스타일 추론**: 통계로 보는 플레이어의 교전 패턴 (적극적/수비적/저격형 등)

### 2. {"🤝 팀워크 & 협업 능력 분석" if not is_solo else "💪 개인 역량 & 독립적 플레이 분석"}
{"- **팀 기여도**: 전체 팀 킬 중 " + f"{kill_contribution:.1f}% 기여 - 캐리/서포트 역할 평가" if not is_solo else "- **개인 생존력**: 팀 지원 없이 " + f"{player['rank']}위까지 독립적 생존 - 자립적 플레이 능력"}
{"- **지원 능력**: " + f"{player['revives']}회 부활, {player['assists']}회 어시스트의 의미" if not is_solo else "- **독립적 판단**: 팀원 정보 공유 없이 개인 판단력과 맵 리딩 능력"}
{"- **팀 시너지**: 팀원들과의 성과 비교를 통한 협력 수준 평가" if not is_solo else "- **자원 독점 활용**: 팀과 공유할 필요 없는 아이템/장비의 효율적 활용"}
{"- **리더십 분석**: 통계로 보는 팀 내 역할과 책임감" if not is_solo else "- **전술적 유연성**: 상황 변화에 대한 즉각적 대응과 플랜 B 실행 능력"}

### 3. 🗺️ 전략적 플레이 & 맵 활용도
- **포지셔닝 능력**: {player["rank"]}위 달성까지의 생존 전략 분석
- **이동 패턴 분석**: 총 {player["ride_distance"] + player["walk_distance"]:.1f}km 이동의 효율성 (차량 {player["ride_distance"]:.1f}km vs 도보 {player["walk_distance"]:.1f}km 비율)
- **존 관리**: 생존 시간 {player["survival_time"]:.1f}분과 최종 순위의 상관관계
- **맵별 특성**: {match["map_name"]} 맵에서의 플레이 스타일 적합성

### 4. ⚡ 자원 관리 & 무기 활용 센스
- **아이템 활용도**: 부스터 {player["boosts"]}개, 치료템 {player["heals"]}개 사용의 적절성
- **무기 선택**: {player["weapons_acquired"]}개 무기 획득 - 장비 교체 빈도 및 선택 기준 분석
{"- **무기 숙련도 활용**: 주력 무기들의 효율성과 이번 매치에서의 활용도" if weapon_mastery else ""}
{"- **사거리별 대응**: 최장거리 킬 " + f"{match_weapons.get('longest_kill', 0):.0f}m" + "를 통한 교전 거리 선호도 분석" if match_weapons and match_weapons.get('longest_kill', 0) > 0 else ""}
- **타이밍 센스**: 킬 타이밍, 교전 선택, 회피 판단력 추론

### 🎯 무기 추천 & 에임 개선 전략
{self._generate_weapon_recommendations(weapon_mastery, match_weapons, player, match["game_mode"])}

### 5. 📈 {"팀플레이 개선점 & 액션 플랜" if not is_solo else "개인 실력 개선점 & 액션 플랜"}
**즉시 개선 가능한 항목 (다음 게임부터):**
{"- [ ] 팀원과의 커뮤니케이션 및 협력 개선사항" if not is_solo else "- [ ] 개인 생존 및 독립적 판단 개선사항"}
{"- [ ] 역할 분담 및 포지셔닝 개선" if not is_solo else "- [ ] 정보 수집 및 맵 리딩 능력 향상"}
{"- [ ] 팀 시너지 최적화 방안" if not is_solo else "- [ ] 자원 관리 및 효율성 증대"}

**단기 목표 (1-2주):**
{"- 팀워크 기반 수치적 목표 (예: 팀 기여도 향상, 부활 성공률 증가)" if not is_solo else "- 개인 역량 기반 수치적 목표 (예: 독립 생존률 향상, 킬/데스 비율 개선)"}

**중장기 발전 방향 (1개월+):**
{"- 팀 전술 및 협력 플레이 마스터" if not is_solo else "- 개인 기량 및 독립적 플레이 완성도 향상"}

### 6. 🏆 종합 평가 & 등급
**이번 매치 종합 점수**: S/A/B/C/D 등급 (근거와 함께)
**강점 TOP 3**: 
1. 
2. 
3. 

**우선 개선 영역 TOP 3**:
1. 
2. 
3. 

**다음 매치 목표**: 구체적이고 측정 가능한 목표 제시

---
💡 **{match["game_mode"]} 모드 특화 분석 가이드라인**:
- **모드별 핵심 요소 중심 분석**: {"개인 실력과 독립적 판단력" if is_solo else "팀워크와 협력, 역할 분담"}에 집중
- **관점별 특성 고려**: {"FPP 특성(제한된 시야, 사운드 플레이)" if is_fpp else "TPP 특성(넓은 시야, 정보 수집)"} 반영
- 모든 분석은 제공된 실제 수치를 근거로 작성
- {"개인 플레이에 특화된" if is_solo else "팀플레이에 최적화된"} 구체적 방법론 제시
- 격려와 동기부여가 되는 긍정적 톤 유지
- 각 섹션을 명확히 구분하고 이모지로 가독성 향상
"""
        
        return prompt
    
    def _generate_weapon_recommendations(self, weapon_mastery: Dict[str, Any], match_weapons: Dict[str, Any], player: Dict[str, Any], game_mode: str) -> str:
        """무기 추천 및 에임 개선 전략 생성"""
        if not weapon_mastery:
            return """
**무기 통계 데이터 부족으로 일반적인 추천만 제공합니다:**
- 현재 플레이 스타일과 게임 모드에 맞는 무기 조합을 분석하여 추천해주세요
- 에임 개선을 위한 구체적인 연습 방법을 제시해주세요
"""
        
        # 무기 효율성 분석
        best_weapons = []
        weak_weapons = []
        
        for weapon_name, stats in weapon_mastery.items():
            if stats['times_used'] < 10:  # 사용 횟수가 적으면 제외
                continue
                
            # 효율성 지표 계산
            kill_rate = stats['kills'] / max(stats['times_used'], 1)
            damage_efficiency = stats['avg_damage_per_use']
            headshot_rate = stats['headshots'] / max(stats['kills'], 1) if stats['kills'] > 0 else 0
            
            weapon_score = kill_rate * 100 + damage_efficiency * 0.1 + headshot_rate * 50
            
            if weapon_score > 30:  # 임계값은 조정 가능
                best_weapons.append((weapon_name, stats, weapon_score))
            elif weapon_score < 15:
                weak_weapons.append((weapon_name, stats, weapon_score))
        
        # 정렬
        best_weapons.sort(key=lambda x: x[2], reverse=True)
        weak_weapons.sort(key=lambda x: x[2])
        
        recommendations = """
**📊 개인 무기 효율성 분석 기반 추천:**

**🔥 주력 무기 (계속 사용 추천):**"""
        
        for weapon_name, stats, score in best_weapons[:3]:
            kill_rate = stats['kills'] / max(stats['times_used'], 1)
            headshot_rate = (stats['headshots'] / max(stats['kills'], 1)) * 100 if stats['kills'] > 0 else 0
            recommendations += f"""
- **{weapon_name}**: 효율성 {score:.1f}점
  - 킬 효율: {kill_rate:.2f}킬/사용, 헤드샷: {headshot_rate:.1f}%
  - 에임 개선: {self._get_weapon_aim_guide(weapon_name, headshot_rate, stats)}"""
        
        if weak_weapons:
            recommendations += """

**⚠️ 개선 필요 무기 (연습 또는 교체 고려):**"""
            for weapon_name, stats, score in weak_weapons[:2]:
                kill_rate = stats['kills'] / max(stats['times_used'], 1)
                recommendations += f"""
- **{weapon_name}**: 효율성 {score:.1f}점 (낮음)
  - 킬 효율: {kill_rate:.2f}킬/사용 - 개선 필요
  - 개선 방안: {self._get_weapon_improvement_guide(weapon_name, stats)}"""
        
        # 게임 모드별 추천
        mode_recommendations = self._get_mode_specific_weapon_recommendations(game_mode, best_weapons)
        recommendations += f"""

**🎮 {game_mode} 모드 특화 무기 조합:**
{mode_recommendations}

**🎯 종합 에임 트레이닝 플랜:**
{self._get_comprehensive_aim_training(best_weapons, match_weapons)}"""
        
        return recommendations
    
    def _get_weapon_aim_guide(self, weapon_name: str, headshot_rate: float, stats: Dict[str, Any]) -> str:
        """무기별 에임 개선 가이드"""
        weapon_lower = weapon_name.lower()
        
        if headshot_rate >= 40:
            return f"현재 헤드샷 비율이 우수합니다. 장거리 정확도 향상에 집중하세요"
        elif headshot_rate >= 20:
            return f"적정 수준입니다. 반동 제어 연습으로 연사 정확도를 높이세요"
        else:
            base_guide = f"헤드샷 비율이 낮습니다. 단발 사격 연습이 필요합니다"
            
        # 무기 타입별 구체적 가이드
        if any(ar in weapon_lower for ar in ['m416', 'm16a4', 'scar', 'ak']):
            return f"{base_guide}. 훈련장에서 100m 타겟 단발 연습 10분/일"
        elif any(sr in weapon_lower for sr in ['kar98k', 'awm', 'm24']):
            return f"{base_guide}. 다양한 거리에서 이동 타겟 연습 필요"
        elif any(smg in weapon_lower for smin ['ump', 'vector', 'uzi']):
            return f"{base_guide}. 근거리 추적 조준 연습 집중"
        else:
            return base_guide
    
    def _get_weapon_improvement_guide(self, weapon_name: str, stats: Dict[str, Any]) -> str:
        """효율성이 낮은 무기의 개선 방안"""
        kill_rate = stats['kills'] / max(stats['times_used'], 1)
        
        if kill_rate < 0.1:
            return f"다른 무기로 교체 고려. 현재 킬 효율이 매우 낮습니다"
        elif kill_rate < 0.2:
            return f"기초 조준 연습 필요. 정지 상태에서 조준점 맞추기부터 시작"
        else:
            return f"반동 패턴 숙지 및 연사 제어 연습 집중"
    
    def _get_mode_specific_weapon_recommendations(self, game_mode: str, best_weapons: list) -> str:
        """게임 모드별 무기 조합 추천"""
        mode_lower = game_mode.lower()
        
        if "solo" in mode_lower:
            return """
- **권장 조합**: AR(주무기) + SR/DMR(부무기)
- **이유**: 다양한 교전 거리 대응 + 즉석 치료 시간 확보
- **우선순위**: 안정성 > 화력 (생존이 최우선)
"""
        elif "duo" in mode_lower:
            return """
- **권장 조합**: AR + SMG/SR (역할 분담)
- **파트너 조합**: 한 명은 원거리(SR), 한 명은 근거리(AR/SMG)
- **우선순위**: 시너지 > 개인 화력
"""
        else:  # squad
            return """
- **권장 조합**: 팀 내 역할별 무기 특화
- **IGL**: AR(안정적 중거리), 서포터: LMG/AR, 저격수: SR, 어썰터: SMG/AR
- **우선순위**: 팀 밸런스 > 개인 선호도
"""
    
    def _get_comprehensive_aim_training(self, best_weapons: list, match_weapons: Dict[str, Any]) -> str:
        """종합 에임 트레이닝 계획"""
        if not best_weapons:
            return """
**기본 에임 트레이닝 플랜:**
1. 훈련장 15분: 정지 타겟 단발 연습
2. 아케이드 모드 10분: 빠른 반응속도 훈련
3. 실전 게임에서 단발 사격 의식적 연습
"""
        
        primary_weapon = best_weapons[0][0] if best_weapons else "AR"
        headshot_rate = match_weapons.get('headshot_rate', 0)
        
        training_plan = f"""
**맞춤형 에임 트레이닝 플랜 ({primary_weapon} 중심):**

**Week 1-2 (기초 정확도):**
- 훈련장 {primary_weapon} 단발: 50m/100m/200m 각 5분
- 목표: 정확도 80% 이상 달성

**Week 3-4 (반동 제어):**
- {primary_weapon} 연사 제어: 벽면 스프레이 패턴 연습
- 다양한 배율 스코프 적응 연습

**실전 적용:**
- 게임 내에서 단발→점사→연사 단계적 사격
- 헤드샷 의식적 조준 (현재 {headshot_rate:.1f}% → 목표 30%+)
"""
        
        if match_weapons.get('longest_kill', 0) > 300:
            training_plan += "\n- 장거리 특화: 바람 보정 및 리드샷 연습 추가"
        elif match_weapons.get('longest_kill', 0) < 100:
            training_plan += "\n- 근거리 특화: 빠른 조준 및 추적 사격 연습 강화"
        
        return training_plan
    
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
            # 먼저 Gemini 사용
            import asyncio
            
            def generate_content():
                print(f"[DEBUG] Gemini에게 보내는 프롬프트 길이: {len(prompt)}")
                print(f"[DEBUG] 프롬프트 시작 부분: {prompt[:200]}...")
                response = self.model.generate_content(prompt)
                print(f"[DEBUG] Gemini 응답 길이: {len(response.text)}")
                print(f"[DEBUG] Gemini 응답 시작: {response.text[:200]}...")
                return response.text
            
            response = await asyncio.get_event_loop().run_in_executor(None, generate_content)
            return response.strip()
            
        except Exception as e:
            error_msg = str(e)
            print(f"[DEBUG] Gemini 실패: {error_msg}")
            
            # Gemini 실패시 Ollama 시도
            try:
                import httpx
                async with httpx.AsyncClient(timeout=30.0) as client:
                    test_response = await client.get("http://localhost:11434/api/tags")
                    if test_response.status_code == 200:
                        print("[DEBUG] Gemini 실패, Ollama API 호출 중...")
                        return await self._call_ollama_api(prompt)
            except Exception as ollama_e:
                print(f"[DEBUG] Ollama도 실패: {str(ollama_e)}")
                pass
            
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