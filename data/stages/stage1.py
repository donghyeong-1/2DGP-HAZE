"""스테이지 1 배치: 격자 좌표 (열, 행) -> 방 정의. 손으로 짜는 고정 격자다 (기획서 5.6).

type: combat(적을 모두 처치해야 문이 열린다). goal이 True인 방은 오른쪽 문이 탈출구다.
high_haze: 고농도 방. 감소 대신 게이지가 오른다.
"""
START = (0, 0)

STAGE1 = {
    (0, 0): {"template": "combat_01", "type": "combat", "enemies": ["slum", "slum"]},
    (1, 0): {"template": "combat_02", "type": "combat", "enemies": ["slum", "thrower", "slum"]},
    (2, 0): {"template": "combat_03", "type": "combat", "enemies": ["thrower", "slum", "thrower", "slum"],
             "high_haze": True, "goal": True},
}
