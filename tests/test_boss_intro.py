"""보스 등장씬·대사 테스트 (창 없이). 실행: python tests/test_boss_intro.py

v8 6일 차 (docs/plan_v8.md 6절, 스레드 v8/day6-boss):
- 보스방에 들어서면 카메라가 보스 쪽으로 이동 -> 대사 2~3줄 -> 이름 띠(zone_card 보스 카드). 크래셔·아크·헤이즈 심장.
- 등장씬 동안 게임이 멈춘다(입력과 피해가 막힌다). Enter·Space로 넘긴다.
- 같은 보스를 두 번째 만나면 짧게(다시 만난 대사 한 줄, 카메라 이동·이름 띠도 짧게).
- 헤이즈 심장은 다 내려온 뒤에 등장씬을 시작한다.
- 페이즈가 바뀔 때와 쓰러질 때 보스가 한 줄씩 말한다(게임은 멈추지 않는다). 플레이어가 쓰러지면 한 줄.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))

import boss_intro as bi  # noqa: E402
import camera  # noqa: E402
import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import zone_card  # noqa: E402
from player import Player  # noqa: E402

DT = 1 / 60
KINDS = ('crasher', 'ark', 'heart')


def fresh():
    game_world.clear()
    effects.reset()
    bi.reset_all()
    zone_card.freezing = zone_card.showing = False


class FakeRoom:
    def __init__(self, width=3840, height=1080):
        self.width, self.height = width, height


class FakeBoss:
    def __init__(self, kind='crasher', x=3000.0, y=128.0, title='크래셔'):
        self.kind, self.x, self.y, self.title = kind, x, y, title
        self.alive, self.hb_h, self.anim_time = True, 200, 0.0


class FakePlayer:
    def __init__(self, x=400.0, y=128.0):
        self.x, self.y, self.state = x, y, 'IDLE'
        self.mouse_x, self.mouse_y = x, y
        self.released = self.synced = 0

    @property
    def center(self):
        return self.x, self.y + 60

    def release_inputs(self):
        self.released += 1

    def sync_inputs(self):
        self.synced += 1


class FakeStage:
    def __init__(self, name='stage2'):
        self.name, self.boss, self.room = name, None, FakeRoom()


def make(name='stage2', with_card=True):
    fresh()
    st = FakeStage(name)
    p = FakePlayer()
    card = zone_card.ZoneCard(st) if with_card else None
    intro = bi.BossIntro(st, p, card)
    camera.snap(p, st.room)
    return st, p, card, intro


def tick(intro, card, seconds):
    for _ in range(int(round(seconds / DT))):
        if card is not None:
            card.update(DT)
        intro.update(DT)


def run_until_free(intro, card, limit=30.0):
    """등장씬이 게임을 풀어 줄 때까지 돌리고 걸린 시간을 돌려준다."""
    t = 0.0
    while (bi.freezing or zone_card.freezing) and t < limit:
        if card is not None:
            card.update(DT)
        intro.update(DT)
        t += DT
    return t


# ----- 대사 -----
def test_every_boss_has_intro_again_phase_and_death_lines():
    import ui
    for kind in KINDS:
        lines = bi.LINES[kind]
        assert 2 <= len(lines['intro']) <= 3, kind                  # 등장 대사 2~3줄
        assert len(lines['again']) >= 1, kind                       # 다시 만나면 짧게
        assert lines['death'] and lines['win'], kind
        assert lines['speaker'], kind
        for text in lines['intro'] + lines['again']:
            assert 0 < len(text) <= bi.MAX_CHARS, (kind, text)      # 한 줄에 들어간다
    assert bi.LINES['crasher']['phase2']
    assert bi.LINES['ark']['phase2'] and bi.LINES['ark']['phase3']
    assert bi.LINES['heart']['phase2'] and bi.LINES['heart']['phase3']
    assert set(KINDS) <= set(ui.BOSS_EPITHET)


def test_lines_use_world_terms_and_screen_rules():
    """대사는 세계관 용어(헤이즈·N-09·교도소 구역)를 쓰고, '결정'(재화 이름)·'변이'를 쓰지 않는다."""
    words = ' '.join(t for kind in KINDS for k, v in bi.LINES[kind].items() if k != 'color'
                     for t in (v if isinstance(v, list) else [v]))
    assert '헤이즈' in words and 'N-09' in words
    assert '결정' not in words and '변이' not in words


# ----- 등장씬 순서 -----
def test_full_intro_pans_to_boss_then_lines_then_name_card():
    st, p, card, intro = make()
    start = camera.x
    tick(intro, card, 0.2)
    assert intro.step is None and not bi.freezing                 # 보스가 없으면 아무 일도 없다
    st.boss = FakeBoss()
    intro.update(DT)
    assert intro.step == 'wait' and bi.freezing
    assert p.released == 1                                         # 누르고 있던 키를 뗀다 (멈춘 동안 걷지 않게)
    tick(intro, card, bi.FULL['wait'] + bi.FULL['pan'] + 0.05)
    assert intro.step == 'lines'
    want_x, _ = camera.look_at(st.room, st.boss.x, st.boss.y + st.boss.hb_h / 2)
    assert abs(camera.x - want_x) < 2 and camera.x > start + 500   # 카메라가 보스를 비춘다
    shown = []
    while intro.step == 'lines':
        shown.append(intro.line_index)
        intro.update(DT)
        card.update(DT)
    assert sorted(set(shown)) == list(range(len(bi.LINES['crasher']['intro'])))   # 대사를 차례로 모두
    assert intro.step == 'card' and card.visible() and card.boss and card.title == '크래셔'
    assert bi.freezing
    run_until_free(intro, card)
    assert not bi.freezing and not zone_card.freezing
    px, _ = camera.target_for(p, st.room)
    assert abs(camera.x - px) < 4                                  # 이름 띠가 닫힐 때 카메라는 플레이어로 돌아와 있다
    assert p.synced == 1                                           # 풀릴 때 실제로 눌린 키만 다시 누른다
    tick(intro, card, 1.0)
    assert intro.step is None and not intro.bars()
    st.boss = st.boss                                              # 같은 보스에게 다시 뜨지 않는다
    tick(intro, card, 0.5)
    assert intro.step is None


def test_typing_and_advance_with_enter_or_space():
    st, p, card, intro = make()
    st.boss = FakeBoss()
    intro.update(DT)
    intro.advance()
    assert intro.step == 'wait'                                    # 들어서자마자 누른 것은 무시 (점프하며 들어오던 Space)
    tick(intro, card, bi.ADVANCE_GUARD)
    intro.advance()                                                # 카메라 이동 중 누르면 바로 대사로
    assert intro.step == 'lines' and intro.line_index == 0
    tick(intro, card, 0.1)
    assert 0 < intro.typed() < len(intro.line())                    # 글자가 차례로 찍힌다
    intro.advance()
    assert intro.typed() == len(intro.line()) and intro.line_index == 0   # 첫 번째 누름: 줄을 다 보여 준다
    intro.advance()
    assert intro.line_index == 1                                   # 두 번째 누름: 다음 줄
    presses = 0
    while (bi.freezing or zone_card.freezing) and presses < 12:
        intro.advance()
        card.update(DT)
        intro.update(DT)
        presses += 1
    assert presses <= 8 and not bi.freezing and not zone_card.freezing   # 계속 누르면 금방 끝난다 (이름 띠도 넘긴다)


def test_second_meeting_is_shorter():
    st, p, card, intro = make()
    st.boss = FakeBoss()
    intro.update(DT)
    first = run_until_free(intro, card)
    assert intro.short is False
    tick(intro, card, 1.0)
    st.boss = FakeBoss()                                           # 같은 종류의 보스를 다시 만났다 (새 판)
    intro.update(DT)
    assert intro.short is True and intro.lines == bi.LINES['crasher']['again']
    second = run_until_free(intro, card)
    assert second < first * 0.6, (first, second)
    assert first < 14.0                                            # 처음에도 너무 길지 않다


def test_seen_survives_new_run_but_reset_all_clears_it():
    st, p, card, intro = make()
    st.boss = FakeBoss()
    intro.update(DT)
    run_until_free(intro, card)
    intro2 = bi.BossIntro(FakeStage(), FakePlayer(), None)          # 새 판: play_mode가 새로 만든다
    intro2.stage.boss = FakeBoss()
    intro2.update(DT)
    assert intro2.short
    bi.reset_all()
    assert 'crasher' not in bi.seen


def test_no_card_image_still_returns_camera():
    st, p, card, intro = make(with_card=False)
    st.boss = FakeBoss()
    intro.update(DT)
    t = run_until_free(intro, None)
    assert t < 12 and not bi.freezing
    px, _ = camera.target_for(p, st.room)
    assert abs(camera.x - px) < 4


def test_heart_waits_until_it_has_descended():
    st, p, card, intro = make(name='stage3')
    heart = FakeBoss('heart', 1920, 600, '헤이즈 심장')
    heart.intro_left = 1.0
    st.boss = heart
    tick(intro, card, 0.5)
    assert intro.step is None and not bi.freezing                  # 내려오는 동안은 기다린다
    heart.intro_left = 0.0
    intro.update(DT)
    assert intro.step == 'wait' and intro.lines == bi.LINES['heart']['intro']


def test_switch_off_keeps_old_card_only():
    old = config.BOSS_INTRO
    try:
        config.BOSS_INTRO = False
        st, p, card, intro = make()
        st.boss = FakeBoss()
        card.update(DT)
        intro.update(DT)
        assert intro.step is None and card.visible() and card.boss  # 예전처럼 이름 띠가 바로 뜬다
    finally:
        config.BOSS_INTRO = old


def test_camera_look_at_stays_inside_room():
    room = FakeRoom(3840, 1080)
    x, y = camera.look_at(room, 3800, 100)
    assert x == 3840 - config.SCREEN_W and y == 0
    x, _ = camera.look_at(room, 10, 100)
    assert x == 0
    x, y = camera.look_at(FakeRoom(1920, 1080), 1500, 900)
    assert (x, y) == (0, 0)


# ----- 입력 -----
class Ev:
    def __init__(self, type_, key=None):
        self.type, self.key = type_, key


def test_input_filter_while_frozen():
    from pico2d import (SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEBUTTONDOWN, SDL_MOUSEMOTION, SDLK_ESCAPE, SDLK_RETURN, SDLK_SPACE,
                        SDLK_a)
    assert bi.filter_event(Ev(SDL_KEYDOWN, SDLK_RETURN)) == 'advance'
    assert bi.filter_event(Ev(SDL_KEYDOWN, SDLK_SPACE)) == 'advance'
    assert bi.filter_event(Ev(SDL_KEYDOWN, SDLK_a)) == 'block'        # 이동·공격 키는 먹지 않는다
    assert bi.filter_event(Ev(SDL_MOUSEBUTTONDOWN)) == 'block'        # 공격하며 들어오던 클릭으로 넘어가지 않는다
    assert bi.filter_event(Ev(SDL_KEYDOWN, SDLK_ESCAPE)) == 'pass'    # 일시정지는 연다
    assert bi.filter_event(Ev(SDL_KEYUP, SDLK_a)) == 'pass'           # 뗀 신호는 플레이어에게 (키가 눌린 채 남지 않게)
    assert bi.filter_event(Ev(SDL_MOUSEMOTION)) == 'pass'             # 조준은 따라간다


# ----- 한 줄 대사 (페이즈·처치) -----
def test_bark_shows_and_fades():
    fresh()
    assert bi.current_bark() is None
    assert bi.bark(FakeBoss(), 'phase2')
    speaker, text, color = bi.current_bark()
    assert speaker == bi.LINES['crasher']['speaker'] and text == bi.LINES['crasher']['phase2']
    bi.tick_bark(bi.bark_time(text) + 0.1)
    assert bi.current_bark() is None
    assert not bi.bark(FakeBoss('nobody'), 'phase2')                 # 대사가 없는 보스는 조용히
    assert not bi.bark(FakeBoss('ark'), 'phase9')


def arena_fight(make_boss):
    import balance_sim
    fresh()
    room = balance_sim.arena()
    floor = float(2 * config.TILE)
    p = Player(6 * config.TILE, floor, room)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    boss = make_boss(room, p, floor)
    game_world.add_object(boss, game_world.LAYER_ENEMY)
    p.hp = p.max_hp = 10 ** 6
    return room, p, boss


def step(n=1):
    for _ in range(n):
        effects.hit_stop_left = 0.0
        effects.slow_left = 0.0
        game_world.update(DT)


def test_crasher_barks_on_phase2_and_death():
    from boss import Boss
    room, p, b = arena_fight(lambda room, p, floor: Boss(p.x + 600, floor, room, p))
    b.cooldown = 99.0
    b.hp = b.max_hp / 2 - 1
    step()
    assert b.phase == 2 and bi.current_bark()[1] == bi.LINES['crasher']['phase2']
    b.take_damage(10 ** 6)
    assert bi.current_bark()[1] == bi.LINES['crasher']['death']


def test_ark_barks_on_each_phase_and_death():
    from ark import Ark
    room, p, a = arena_fight(lambda room, p, floor: Ark(p.x + 600, floor, room, p))
    a.cooldown = 99.0
    a.hp = a.max_hp * config.ARK_PHASES[0] - 1
    step()
    assert a.phase == 2 and bi.current_bark()[1] == bi.LINES['ark']['phase2']
    a.hp = a.max_hp * config.ARK_PHASES[1] - 1
    step()
    assert a.phase == 3 and bi.current_bark()[1] == bi.LINES['ark']['phase3']
    a.take_damage(10 ** 6)
    assert bi.current_bark()[1] == bi.LINES['ark']['death']


def test_heart_barks_on_each_phase_and_death_and_no_float_name_at_landing():
    import heart as hm
    from room import Room
    fresh()
    room = Room.load('boss_arena', ('L',))
    p = Player(12 * config.TILE, 2 * config.TILE + 5, room)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    step(20)
    p.hp = p.max_hp = 10 ** 6
    core = hm.spawn(room, p)
    core.cooldown = 99.0
    before = len(game_world.world[game_world.LAYER_EFFECT])
    step(int(config.HEART['intro'] * 60) + 3)
    names = [o for o in game_world.world[game_world.LAYER_EFFECT] if getattr(o, 'text', None) == '헤이즈 심장']
    assert not names, before                                       # 이름은 등장씬의 이름 띠가 보여 준다
    a, b = config.HEART['phases']
    core.hp = core.max_hp * a - 1
    step()
    assert core.phase == 2 and bi.current_bark()[1] == bi.LINES['heart']['phase2']
    core.hp = core.max_hp * b - 1
    step()
    assert core.phase == 3 and bi.current_bark()[1] == bi.LINES['heart']['phase3']
    core.open_left = 5.0
    core.take_damage(10 ** 7)
    assert not core.alive and bi.current_bark()[1] == bi.LINES['heart']['death']


def test_boss_taunts_once_when_player_falls():
    st, p, card, intro = make()
    st.boss = FakeBoss()
    intro.update(DT)
    run_until_free(intro, card)
    tick(intro, card, 1.0)
    p.state = 'DEAD'
    intro.update(DT)
    assert bi.current_bark()[1] == bi.LINES['crasher']['win']
    bi.tick_bark(10.0)
    intro.update(DT)
    assert bi.current_bark() is None                               # 한 번만


# ----- 실제 판: 보스방에 들어서면 멈추고, 끝나면 싸움이 시작된다 -----
def test_real_boss_room_freezes_play_until_intro_ends():
    import game_framework
    import play_mode
    import stage as stage_mod
    fresh()
    p = Player(0, 0, None)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    st = stage_mod.Stage(p, name='stage2', seed=1)
    st.start()
    card = zone_card.ZoneCard(st)
    intro = bi.BossIntro(st, p, card)
    game_world.add_object(card, game_world.LAYER_UI)
    game_world.add_object(intro, game_world.LAYER_UI)
    st.enter_room(stage_mod.boss_room(st), 'L')
    boss = st.boss
    assert boss is not None and boss.kind == 'crasher'
    play_mode.stage, play_mode.player, play_mode.room = st, p, st.room
    game_framework.frame_time = DT
    hp, bx, cd = p.hp, boss.x, boss.cooldown
    for _ in range(3):
        play_mode.update()
    assert bi.freezing and intro.step == 'wait'
    p.right = True                                                 # 멈춘 동안에는 눌러도 움직이지 않는다
    px = p.x
    for _ in range(60):
        play_mode.update()
    assert p.x == px and boss.x == bx and boss.cooldown == cd and p.hp == hp
    p.right = False
    for _ in range(int(20 / DT)):
        if not (bi.freezing or zone_card.freezing):
            break
        play_mode.update()
    assert not bi.freezing and not zone_card.freezing
    cd = boss.cooldown
    for _ in range(10):
        play_mode.update()
    assert boss.cooldown != cd or boss.state != 'IDLE'             # 끝나면 보스가 움직인다
    game_world.clear()


def test_play_mode_and_gamepad_use_the_intro():
    src = open(os.path.join(HERE, '..', 'src', 'play_mode.py'), encoding='utf-8').read()
    assert 'boss_intro.freezing' in src and 'boss_intro.filter_event' in src and 'BossIntro(' in src
    pad = open(os.path.join(HERE, '..', 'src', 'gamepad.py'), encoding='utf-8').read()
    assert 'boss_intro.freezing' in pad


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
