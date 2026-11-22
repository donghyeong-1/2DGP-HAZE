"""스테이지 1 배치: 격자 좌표 (열, 행) -> 방 정의. 손으로 짜는 고정 격자다 (기획서 5.6). 행은 위로 증가한다.

방 종류: start(안전), combat(적을 모두 처치해야 문이 열림), gold(황금방: 아이템 중 하나를 무료로), shop(정비방: 조각으로 구매),
gate(관문: 정예 전투, 이기면 다음 구역). 보스는 스테이지 2(크래셔)·3(아크)에 있다(기획서 3.2). 문은 두 방의 템플릿 모두 그쪽에 출입구가 있고 이웃 방이 있을 때만 열린다.
종류 없는 E 스폰 칸은 enemies를 위에서 아래, 왼쪽에서 오른쪽 순서로 채운다. s·t 칸은 템플릿에 종류가 적혀 있다.

            (1,2) 황금방
               |
 (0,1) 우물 -- (1,1) 교차로 -- (2,1) 아레나(고농도) -- (3,1) 홀
   |              |
 (0,0) 시작 -- (1,0) 허브 -- (2,0) 구덩이 -- (3,0) 골목 -- (4,0) 탑 -- (5,0) 관문
                  |
               (1,-1) 정비방

관문으로 가는 길(맨 아래 줄)은 곧게 이어지지만, 위·아래 가지를 돌면 황금방(아이템)과 정비방(조각 사용), 추가 전투(조각 획득)가 있다.
"""
START = (0, 0)
TITLE = '제9구역: 폐기물 슬럼'
THEME = 'cell'

STAGE1 = {
    (0, 0): {"template": "start_hall", "type": "start"},
    (1, 0): {"template": "hub_cavern", "type": "combat",
             "enemies": ["thrower", "thrower", "slum", "hound", "slum", "rat"]},
    (2, 0): {"template": "pit_02", "type": "combat", "theme": "foundry"},
    (3, 0): {"template": "cover_04", "type": "combat", "theme": "foundry"},
    (4, 0): {"template": "tower_03", "type": "combat", "theme": "haze"},
    # 관문: 아레나 모양에 간수·사냥개 정예 (템플릿의 슬럼·투척병 자리를 바꾼다)
    (5, 0): {"template": "arena_05", "type": "gate", "theme": "foundry", "swap": {"slum": "guard", "thrower": "hound"}},
    (0, 1): {"template": "well_room", "type": "combat",
             "enemies": ["thrower", "slum", "shaman", "guard", "slum", "rat"]},
    (1, 1): {"template": "crossing", "type": "combat",
             "enemies": ["rat", "thrower", "shaman", "guard", "slum", "slum"]},
    (2, 1): {"template": "arena_05", "type": "combat", "high_haze": True},
    (3, 1): {"template": "hall_01", "type": "combat"},
    (1, 2): {"template": "gold_room", "type": "gold"},
    (1, -1): {"template": "shop_room", "type": "shop"},
    (4, 1): {"template": "rift_room", "type": "rift"},     # 홀 오른쪽: 체력을 내고 들어가는 균열방 (11/19)
}
