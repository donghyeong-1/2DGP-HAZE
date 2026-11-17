"""스테이지 2 배치: 제4구역 철골 공장 (기획서 2.3). 격자 좌표 (열, 행) -> 방 정의. 행은 위로 증가한다.

중장비와 개조 죄수들이 배회하는 산업 구역. 스테이지 1보다 간수·사냥개가 많고 고농도 방(게이지가 오른다)이 섞인다.
보스는 제4구역장 크래셔. 보스로 가는 길이 위 줄로 나 있어서(스테이지 1은 아래 줄), 같은 방 모양이어도 동선이 다르다.

 (0,1) 우물(고농도) -- (1,1) 허브 -- (2,1) 구덩이 -- (3,1) 탑(고농도) -- (4,1) 골목 -- (5,1) 보스
   |                     |   \\
 (0,0) 시작 ------- (1,0) 교차로 -- (2,0) 아레나(고농도) -- (3,0) 홀
                         |          (1,2) 황금방 (허브 위)
                    (1,-1) 정비방

swap: 템플릿에 적힌 적 종류(s 슬럼, t 투척병)를 이 방에서만 바꾼다.
"""
START = (0, 0)
TITLE = '제4구역: 철골 공장'
THEME = 'foundry'

STAGE2 = {
    (0, 0): {"template": "start_hall", "type": "start"},
    (1, 0): {"template": "crossing", "type": "combat",
             "enemies": ["hound", "guard", "thrower", "hound", "slum", "guard"]},
    (1, 1): {"template": "hub_cavern", "type": "combat",
             "enemies": ["thrower", "guard", "hound", "hound", "guard", "thrower"]},
    (0, 1): {"template": "well_room", "type": "combat", "high_haze": True,
             "enemies": ["hound", "hound", "thrower", "guard", "slum", "thrower"]},
    (2, 1): {"template": "pit_02", "type": "combat", "swap": {"slum": "hound"}},
    (3, 1): {"template": "tower_03", "type": "combat", "high_haze": True, "swap": {"slum": "guard"}},
    (4, 1): {"template": "cover_04", "type": "combat", "swap": {"slum": "guard"}},
    (5, 1): {"template": "boss_arena", "type": "boss", "boss": "crasher"},
    (2, 0): {"template": "arena_05", "type": "combat", "high_haze": True, "swap": {"slum": "hound"}},
    (3, 0): {"template": "hall_01", "type": "combat", "swap": {"slum": "guard"}},
    (1, 2): {"template": "gold_room", "type": "gold"},
    (1, -1): {"template": "shop_room", "type": "shop"},
}
