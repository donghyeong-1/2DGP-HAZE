"""연습장 (v7, 2026-11-24, docs/plan_v7.md 5-F). 은신처의 '연습장' 표지판에서 들어가 콤보·증강 조합을 시험한다.

- 방 하나(data/stages/practice.py). 들어가면 쓰러지지 않는 허수아비 둘이 선다 (맞아도 체력이 다시 차고 공격하지 않는다).
- 허수아비가 받은 피해로 최근 DPS_WINDOW초의 초당 피해를 잰다 (PracticeHud가 머리 위에 띄운다).
- 연습 메뉴(practice_mode, 연습장에서 F): 아래 함수들로 적 불러내기·증강 넣고 빼기·게이지·무기·정리.
pico2d와 무관한 로직 (그리기는 PracticeHud.draw만).
"""
import assets
import config
import game_world

DUMMY_KIND = 'guard'          # 허수아비 모습 (간수 그림, 움직이지 않는다)
DUMMY_COLS = (21, 27)         # 허수아비가 서는 열 (data/rooms/practice_room.txt, 40열)
DPS_WINDOW = 5.0              # 초당 피해를 재는 시간(초)
ENEMY_KINDS = ('slum', 'thrower', 'hound', 'guard', 'rat', 'shaman', 'drone', 'cart', 'eye', 'knight', 'wraith')
WEAPONS = ('pistol', 'gauntlet', 'chain')
_log = []                     # (시각, 피해)
_time = 0.0


def dummies():
    return [e for e in game_world.world[game_world.LAYER_ENEMY] if getattr(e, 'dummy', False)]


def record(damage):
    _log.append((_time, damage))


def tick(dt):
    global _time
    _time += dt
    while _log and _log[0][0] < _time - DPS_WINDOW:
        _log.pop(0)


def dps():
    """최근 DPS_WINDOW초 동안의 초당 피해 (첫 타부터 지난 시간으로 나눈다)."""
    if not _log:
        return 0.0
    span = max(1.0, _time - _log[0][0])
    return sum(d for _t, d in _log) / span


def spawn_dummies(stage):
    import enemy_kinds
    for col in DUMMY_COLS:
        e = enemy_kinds.make(DUMMY_KIND, col * config.TILE, config.TILE * 2, stage.room, stage.player)
        e.dummy = e.immortal = True
        e.stats = dict(e.stats, speed=0.0, sight=0)          # 움직이지도 공격하지도 않는다
        e.face_dir = -1
        game_world.add_object(e, game_world.LAYER_ENEMY)


def spawn_enemy(stage, kind):
    """진짜 적 하나 (공격한다). 주인공 앞쪽에."""
    import enemy_kinds
    p = stage.player
    x = min(stage.room.width - config.TILE * 2, p.x + 360)
    e = enemy_kinds.make(kind, x, config.TILE * 2, stage.room, p)
    game_world.add_object(e, game_world.LAYER_ENEMY)
    return e


def reset(stage):
    """불러낸 적·허수아비를 치우고 허수아비를 다시 세운다. 피해 기록도 비운다."""
    for e in list(game_world.world[game_world.LAYER_ENEMY]):
        game_world.remove_object(e)
    _log.clear()
    spawn_dummies(stage)


def toggle_augment(player, mid):
    import mutations
    if mutations.has(player, mid):
        mutations.remove(player, mid)
    else:
        mutations.give(player, mid)


def clear_augments(player):
    import mutations
    for mid in list(mutations.owned(player)):
        mutations.remove(player, mid)


def set_gauge(player, value):
    g = player.gauge
    g.value = float(max(1, min(g.cap - 1, value)))
    g.zone = g._zone_of(g.value)


def set_weapon(player, weapon_id):
    player.give_weapon(weapon_id)


class PracticeHud:
    """연습장 위쪽 안내와 허수아비 머리 위 초당 피해. UI 레이어(화면 좌표)."""

    def __init__(self, stage):
        self.stage = stage

    def update(self, dt):
        tick(dt)

    def draw(self):
        if getattr(self.stage, 'name', '') != 'practice':
            return
        import game_world
        if game_world.quiet:                       # R1: 연습 메뉴 뒤에 깔린 멈춘 연습장에서는 '초당 피해'·안내 줄을 빼고
            return
        import hud_kit as kit
        kit.text(config.SCREEN_W // 2, config.SCREEN_H - 150, f'초당 피해 {dps():.0f}   (최근 {DPS_WINDOW:.0f}초)',
                 (255, 230, 150), center=True)
        kit.text(config.SCREEN_W // 2, config.SCREEN_H - 190, 'F 연습 메뉴: 적 불러내기 · 증강 · 게이지 · 무기 · 은신처로',
                 (170, 190, 220), small=True, center=True)
        assets.draw_offset = (0, 0)
