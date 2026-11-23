"""연습장 (2026-11-24, v7 docs/plan_v7.md 5-F): 은신처 '연습장' 표지판에서 들어온다. 방 하나, 허수아비 둘.
F로 연습 메뉴(적 불러내기·증강·게이지·무기·은신처로). 다음 구역이 없다(은신처로는 메뉴에서).
"""
START = (0, 0)
TITLE = '연습장'
THEME = 'shop'

PRACTICE = {
    (0, 0): {"template": "practice_room", "type": "practice", "theme": "shop"},
}
