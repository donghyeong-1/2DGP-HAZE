"""스테이지 1 배치: 격자 좌표 (열, 행) -> 방 정의. 손으로 짜는 고정 격자다 (기획서 5.6). 행은 위로 증가한다.

방 종류: start(안전), combat(적을 모두 처치해야 문이 열림), gold(황금방: 아이템 중 하나를 무료로), shop(정비방: 조각으로 구매),
boss(보스, 쓰러뜨리면 탈출). 문은 두 방의 템플릿 모두 그쪽에 출입구가 있고 이웃 방이 있을 때만 열린다.
종류 없는 E 스폰 칸은 enemies를 위에서 아래, 왼쪽에서 오른쪽 순서로 채운다. s·t 칸은 템플릿에 종류가 적혀 있다.

            (1,2) 황금방
               |
 (0,1) 우물 -- (1,1) 교차로 -- (2,1) 아레나(고농도) -- (3,1) 홀
   |              |
 (0,0) 시작 -- (1,0) 허브 -- (2,0) 구덩이 -- (3,0) 골목 -- (4,0) 탑 -- (5,0) 보스
                  |
               (1,-1) 정비방

보스로 가는 길(맨 아래 줄)은 곧게 이어지지만, 위·아래 가지를 돌면 황금방(아이템)과 정비방(조각 사용), 추가 전투(조각 획득)가 있다.
"""
START = (0, 0)

STAGE1 = {
    (0, 0): {"template": "start_hall", "type": "start"},
    (1, 0): {"template": "hub_cavern", "type": "combat",
             "enemies": ["thrower", "thrower", "slum", "slum", "slum", "slum"]},
    (2, 0): {"template": "pit_02", "type": "combat", "theme": "foundry"},
    (3, 0): {"template": "cover_04", "type": "combat", "theme": "foundry"},
    (4, 0): {"template": "tower_03", "type": "combat", "theme": "haze"},
    (5, 0): {"template": "boss_arena", "type": "boss"},
    (0, 1): {"template": "well_room", "type": "combat",
             "enemies": ["thrower", "slum", "thrower", "slum", "slum", "slum"]},
    (1, 1): {"template": "crossing", "type": "combat",
             "enemies": ["slum", "thrower", "thrower", "slum", "slum", "slum"]},
    (2, 1): {"template": "arena_05", "type": "combat", "high_haze": True},
    (3, 1): {"template": "hall_01", "type": "combat"},
    (1, 2): {"template": "gold_room", "type": "gold"},
    (1, -1): {"template": "shop_room", "type": "shop"},
}
