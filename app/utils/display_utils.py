"""
UI 표시용 유틸리티 함수들
"""

def get_korean_game_mode(game_mode: str) -> str:
    """게임모드를 한글로 변환"""
    mode_map = {
        'solo': '솔로',
        'solo-fpp': '솔로 (1인칭)',
        'duo': '듀오',
        'duo-fpp': '듀오 (1인칭)',
        'squad': '스쿼드',
        'squad-fpp': '스쿼드 (1인칭)',
        'normal-solo': '솔로',
        'normal-duo': '듀오',
        'normal-squad': '스쿼드',
        'ranked-solo': '랭크드 솔로',
        'ranked-duo': '랭크드 듀오',
        'ranked-squad': '랭크드 스쿼드'
    }
    return mode_map.get(game_mode.lower(), game_mode)

def get_korean_map_name(map_name: str) -> str:
    """맵 이름을 한글로 변환"""
    map_dict = {
        'Erangel_Main': '에란겔',
        'Desert_Main': '미라마',
        'Savage_Main': '사녹',
        'DihorOtok_Main': '비켄디',
        'Summerland_Main': '카라킨',
        'Baltic_Main': '에란겔 (리마스터)',
        'Range_Main': '훈련장',
        'Chimera_Main': '파라모',
        'Tiger_Main': '태이고',
        'Heaven_Main': '헤이븐',
        'Kiki_Main': '데스톤',
        'Neon_Main': '네온'
    }
    return map_dict.get(map_name, map_name)

def get_rank_color(rank: int) -> str:
    """순위에 따른 색상 반환"""
    if rank == 1:
        return "#FFD700"  # 금색
    elif rank <= 3:
        return "#C0C0C0"  # 은색
    elif rank <= 10:
        return "#CD7F32"  # 동색
    else:
        return "#666666"  # 회색