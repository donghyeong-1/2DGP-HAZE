"""스테이지 3 배치: 코어 구역 감시자의 탑 (기획서 2.3). 격자 좌표 (열, 행) -> 방 정의. 행은 위로 증가한다.

교도소 정중앙의 통제 본부. 정비방 하나와 최종 보스로 곧게 이어지는 결전 구역이라 가지가 짧고 압박이 높다(황금방 없음).
간수·사냥개가 주력이고 고농도 방이 많다. 보스는 총감시관 아크(그림 Codex T20이 오기 전까지는 크래셔가 대신 선다).

 (0,1) 우물(고농도)          (2,1) 교차로
   |                           |
 (0,0) 시작 -- (1,0) 탑 -- (2,0) 허브 -- (3,0) 아레나(고농도) -- (4,0) 보스
                               |
                          (2,-1) 정비방
"""
START = (0, 0)
TITLE = '코어 구역: 감시자의 탑'
THEME = 'haze'

STAGE3 = {
    (0, 0): {"template": "start_hall", "type": "start"},
    (1, 0): {"template": "tower_03", "type": "combat", "swap": {"slum": "guard"}},
    (2, 0): {"template": "hub_cavern", "type": "combat",
             "enemies": ["guard", "hound", "thrower", "guard", "hound", "thrower"]},
    (3, 0): {"template": "arena_05", "type": "combat", "high_haze": True, "swap": {"slum": "hound", "thrower": "guard"}},
    (4, 0): {"template": "boss_arena", "type": "boss", "boss": "ark"},
    (2, -1): {"template": "shop_room", "type": "shop"},
    (3, 1): {"template": "rift_room", "type": "rift"},     # 교차로 오른쪽: 균열방 (11/19)
    (2, 1): {"template": "crossing", "type": "combat",
             "enemies": ["guard", "guard", "hound", "hound", "thrower", "thrower"]},
    (0, 1): {"template": "well_room", "type": "combat", "high_haze": True,
             "enemies": ["hound", "guard", "thrower", "hound", "guard", "thrower"]},
}
