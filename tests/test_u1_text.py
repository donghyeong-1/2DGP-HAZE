"""U1-1 (2026-11-27) 글 검토 A의 동작 버그 테스트 (창 없이). 실행: python tests/test_u1_text.py

글 검토 문서 docs/project/text_review_1127.md의 A 가운데 글이 아니라 동작이 틀린 것:
- 사망 원인: 충격파(projectile.Shockwave)는 크래셔·간수·문지기·헤이즈 심장이 모두 쓴다. 쏜 주체를 기록에 실어
  '간수의 충격파'처럼 맞는 이름이 나오고, 은신처 대사 조건(talk.cause_kind)도 크래셔로 잘못 잡지 않는다.
- 정비방 물약이 가득 찼을 때 '이미 최대 단계입니다'가 아니라 물약이 가득 찼다고 알린다.
- 균열방 업그레이드(두 단계를 한꺼번에)의 획득 알림·진열대 설명이 두 단계 뒤의 실제 수치를 보인다.
- 키 설정: Esc·F1~F5를 넣으려 하면 '도움말'이 아니라 일시정지·개발용이라고 알린다.
- 키 안내: 진열대·이벤트·NPC·밸브·연습장 안내의 'F'가 키 설정을 따른다.
- 증강 시너지 알림이 카드와 같은 말('계열 효과', '진화 열림')을 쓴다.
- 처음 안내의 키 자리 뒤에 받침에 따라 바뀌는 조사가 붙지 않는다.
"""
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import log  # noqa: E402

log.PATH = os.path.join(tempfile.mkdtemp(), 'haze_log.txt')

import options  # noqa: E402

options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')     # 사용자 설정 파일을 건드리지 않는다
import meta  # noqa: E402

meta.PATH = os.path.join(tempfile.mkdtemp(), 'meta.json')       # 사용자 저장 파일을 건드리지 않는다

import sdl2  # noqa: E402

import config  # noqa: E402
import game_world  # noqa: E402
import items  # noqa: E402
import keybinds  # noqa: E402
import killers  # noqa: E402
import projectile  # noqa: E402
import talk  # noqa: E402
import test_stage as ts  # noqa: E402   (손으로 짠 배치의 좌표로 방을 오간다)


# ----- 사망 원인: 충격파는 쏜 주체의 이름 -----
class _Catch:
    """projectile.Shockwave를 잠깐 바꿔 끼워 만들어진 충격파를 모은다."""

    def __enter__(self):
        self.made, self.real = [], projectile.Shockwave
        catch = self

        class Rec(self.real):
            def __init__(self, *a, **kw):
                super().__init__(*a, **kw)
                catch.made.append(self)
        Rec.__name__ = 'Shockwave'                  # 이름표는 클래스 이름으로 찾는다
        projectile.Shockwave = Rec
        return self

    def __exit__(self, *exc):
        projectile.Shockwave = self.real


def _room_player():
    from player import Player
    from room import Room
    game_world.clear()
    room = Room.load('test_01')
    p = Player(300, 120, room)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    return room, p


def test_shockwave_death_names_who_made_it():
    from boss import Boss
    from enemy import Enemy
    from gatekeeper import Gatekeeper
    import heart
    room, p = _room_player()
    with _Catch() as c:
        Boss(600, 120, room, p)._shockwaves()
    assert c.made and killers.describe(c.made[0]) == '크래셔의 충격파'
    with _Catch() as c:
        Gatekeeper(600, 120, room, p)._shockwaves()
    assert c.made and killers.describe(c.made[0]) == '문지기의 충격파'
    with _Catch() as c:
        g = Enemy('guard', 600, 120, room, p)
        g.struck = False
        g._move_heavy(0.0)
    assert c.made and killers.describe(c.made[0]) == '간수의 충격파'
    with _Catch() as c:
        g = Enemy('guard', 600, 120, room, p)
        g.make_elite('swift')
        g.struck = False
        g._move_heavy(0.0)
    assert c.made and killers.describe(c.made[0]) == g.elite_label() + ' 간수의 충격파'
    with _Catch() as c:
        core = heart.HeartCore(room, p)
        hand = core.hands[0]
        hand.y = heart.floor_under(room, hand.x, hand.y + 1)            # 손이 바닥에 닿은 순간
        hand._fall(1 / 60)
    assert c.made and killers.describe(c.made[0]) == '헤이즈 심장의 충격파'
    bare = projectile.Shockwave.__new__(projectile.Shockwave)
    assert killers.describe(bare) == '충격파'                          # 누가 쐈는지 모르면 이름만


def test_shockwave_death_reaches_the_right_hideout_line():
    """은신처 대사 조건: 간수·문지기의 충격파로 쓰러져도 '크래셔 앞에서 끊긴 기록'이 나오지 않는다."""
    assert talk.cause_kind('간수의 충격파') == 'enemy'
    assert talk.cause_kind('문지기의 충격파') == 'enemy'
    assert talk.cause_kind('크래셔의 충격파') == 'boss:crasher'
    assert talk.cause_kind('헤이즈 심장의 충격파') == 'boss:heart'
    assert 'died_at:crasher' not in talk.tags({'zone': 'stage1', 'cause': '간수의 충격파'})
    room, p = _room_player()
    from enemy import Enemy
    g = Enemy('guard', 300, 120, room, p)
    with _Catch() as c:
        g.struck = False
        g._move_heavy(0.0)
    p.hp = 1
    p.take_hit(99, source=c.made[0])
    assert p.death_cause == '간수의 충격파'


def test_overload_cause_is_named_by_the_limit_and_old_records_still_count():
    """오버로드는 게이지 한계(100%~160%)에서 일어난다. 옛 저장의 '(게이지 100%)' 기록도 오버로드로 읽는다."""
    assert '100%' not in killers.OVERLOAD
    assert talk.cause_kind(killers.OVERLOAD) == 'overload'
    assert talk.cause_kind('오버로드 폭발 (게이지 100%)') == 'overload'


# ----- 진열대 알림 -----
def test_full_potions_say_so_in_the_maintenance_room():
    stage, p = ts.make_stage()
    ts.to_shop(stage, p)
    msgs = []
    stage.on_message = msgs.append
    ped = next(d for d in stage.pedestals if d.item_id == 'heal')
    p.potions = config.POTION_MAX
    p.shards = 99
    p.x, p.y = ped.x, ped.y
    assert not stage.interact()
    assert msgs and msgs[-1] == '물약이 가득 찼습니다', msgs
    assert p.shards == 99


def test_rift_upgrade_notice_shows_both_steps_with_the_final_value():
    stage, p = ts.make_stage()
    ts.to_rift_door(stage, p)
    ts.at_door(stage, p, 'R')
    up = next(d for d in stage.pedestals if d.item_id != 'fury')
    up.item_id = 'cap'                                                   # 수치가 분명한 게이지 용량으로
    got = []
    stage.on_pickup = lambda iid, text: got.append(text)
    want = f'1~2단계: 게이지 한계 {config.GAUGE_CAP}% → {config.GAUGE_CAP + 40}%'
    assert items.describe(p, 'cap', steps=2) == want
    p.x, p.y = up.x, up.y
    assert stage.interact() and items.level(p, 'cap') == 2
    assert got == [want], got
    assert items.describe(p, 'cap', steps=2) == f'3단계: 게이지 한계 {config.GAUGE_CAP + 40}% → {config.GAUGE_CAP + 60}%'   # 한 단계만 남았다


# ----- 키 설정 -----
def test_reserved_keys_explain_pause_and_developer_use():
    import keys_mode
    keybinds.reset()
    keys_mode.listening = ('enhance', 0)
    keys_mode.press_key(sdl2.SDLK_F1)
    assert '도움말' not in keys_mode.message and '개발' in keys_mode.message, keys_mode.message
    assert '바꿨' not in keys_mode.message and '바꿀' not in keys_mode.message


def test_key_swap_message_uses_the_change_wording():
    import keys_mode
    keybinds.reset()
    keys_mode.listening = ('enhance', 0)
    keys_mode.press_key(sdl2.SDLK_f)
    m = keys_mode.message
    assert '바꿨' not in m and 'F' in m and 'E' in m and keybinds.NAMES['interact'] in m, m
    keybinds.reset()


def test_interact_prompts_follow_the_key_setting():
    import events
    import npc
    import pedestal
    import practice
    import boss_terrain
    keybinds.reset()
    keys = dict(keybinds.to_json())
    keys['interact'] = [sdl2.SDLK_g, None]
    keys['enhance'] = [sdl2.SDLK_f, None]
    keybinds.load_json(keys)
    try:
        shop = pedestal.Pedestal(0, 0, 'cap', 'shop', price=6)
        gold = pedestal.Pedestal(0, 0, 'cap', 'gold')
        assert shop.prompt() == 'G 구매 (6 조각)' and gold.prompt() == 'G 획득'
        assert events.prompt('spring') == 'G 사용' and events.prompt('drifter') == 'G 거래'
        assert npc.prompt_text('mechanic').startswith('G ')
        assert boss_terrain.VALVE_PROMPT() == 'G 밸브 잠그기'
        assert practice.menu_prompt().startswith('G 연습 메뉴')
    finally:
        keybinds.reset()


# ----- 증강 시너지 알림 -----
def test_synergy_float_uses_the_card_wording():
    import effects
    import mutation_mode
    import mutations as mu
    room, p = _room_player()
    effects.reset()
    mu.give(p, 'bloom_crit')
    mutation_mode.setup(p, ['bloom_gain'])
    mutation_mode.choose()
    texts = [getattr(o, 'text', '') for o in game_world.world[game_world.LAYER_EFFECT]]
    assert '각성 계열 효과 켜짐' in texts and not any('시너지' in t for t in texts), texts
    room, p = _room_player()
    effects.reset()
    mu.give(p, 'combo_speed')
    mutation_mode.setup(p, ['combo_third'])
    mutation_mode.choose()
    texts = [getattr(o, 'text', '') for o in game_world.world[game_world.LAYER_EFFECT]]
    assert f'진화 열림: {mu.MUTATIONS["combo_evo"]["name"]}' in texts and not any('시너지' in t for t in texts), texts


# ----- 처음 안내: 키 이름 뒤에 바뀌는 조사 없음 -----
def test_hints_put_no_changing_particle_after_a_key_name():
    import tutorial
    bad = re.compile(r'\{\w+\}(을|를|이|가|은|는|와|과|으로|로)(?![가-힣])')
    for hid, (title, lines) in tutorial.HINTS.items():
        for line in [title] + lines:
            assert not bad.search(line), (hid, line)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
