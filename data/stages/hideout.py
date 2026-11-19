"""은신처(로비): 판을 시작하기 전과 죽은 뒤에 머무는 안전한 방 (2026-11-19, docs/plan_v4.md 4절).

방 하나. 적이 없고 게이지가 줄지 않는다. NPC 셋(정비사·보관인·기록관) 앞에서 F로 이야기하고,
오른쪽 '출발' 문으로 나가면 스테이지 1(슬럼)이 시작된다.
NPCS: (종류, 서는 열). 그림은 Codex T22(npc_<종류>_idle_1~2.png)가 오기 전까지 코드로 그린 임시 모습.
"""
START = (0, 0)
TITLE = '은신처'
THEME = 'shop'

HIDEOUT = {
    (0, 0): {"template": "hideout_room", "type": "hideout", "theme": "shop"},
}

NPCS = [('mechanic', 9), ('keeper', 17), ('archivist', 25)]
