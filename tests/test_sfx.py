"""효과음 파일 검사 (창·오디오 장치 없이 실행). 실행: python tests/test_sfx.py 또는 pytest"""
import os
import sys
import wave

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import config  # noqa: E402

NAMES = ["warn_low", "warn_high", "jump", "double_jump", "dash", "land", "hit", "pickup", "enhance", "overload", "death",
         "overload_zap", "stun_end", "swing", "swing_fade", "swing_awake", "swing_critical", "swing_enhanced", "enemy_hit", "enemy_die", "throw",
         # 2026-11-19 전용 효과음: 사슬, 궁극기, 아크
         "chain_throw", "chain_latch", "chain_clash", "ult_cast", "ult_hit",
         "ark_bullet", "ark_teleport", "ark_roar", "ark_absorb", "ark_burst", "ark_field",
         # 2026-11-21 퀄리티 계획 1-7: 무기별 명중, 적별 공격 예고
         "impact_pipe", "impact_knife", "impact_gauntlet",
         "windup_slum", "windup_thrower", "windup_hound", "windup_guard",
         # 2026-11-21 계획 2-3 환경음 (구역마다 가끔)
         "amb_drip", "amb_steam", "amb_wind", "amb_forge",
         # 2026-11-21 빠진 소리 채우기: 식칼·사슬 구간별·강화, 무기별 궁극기 마무리, 구간 진입·심장·마지막 처치
         "throw_fade", "throw_awake", "throw_critical", "throw_enhanced",
         "chain_throw_fade", "chain_throw_awake", "chain_throw_critical", "chain_throw_enhanced", "chain_latch_heavy",
         "ult_final_pipe", "ult_final_knife", "ult_final_gauntlet", "ult_final_chain",
         "zone_awake", "heartbeat", "kill_last",
         # 2026-11-22 메뉴 전용 소리
         "ui_move", "ui_select", "ui_back"]


def test_sfx_files_are_valid_short_wavs():
    for name in NAMES:
        path = os.path.join(ROOT, 'assets', 'sfx', name + '.wav')
        assert os.path.exists(path), name
        with wave.open(path, 'rb') as f:
            assert f.getnchannels() == 1 and f.getsampwidth() == 2
            seconds = f.getnframes() / f.getframerate()
            assert 0.05 < seconds < 1.0, f'{name}: {seconds:.2f}초'
            data = f.readframes(f.getnframes())
        peak = max(abs(int.from_bytes(data[i:i + 2], 'little', signed=True)) for i in range(0, len(data), 2))
        assert 3000 < peak < 32000, f'{name}: 피크 {peak} (무음이거나 클리핑)'


def test_sound_is_silent_when_disabled():
    import assets
    assert config.SOUND_ENABLED is False  # 테스트에서는 꺼져 있다
    assets.play_sound('jump')             # 예외 없이 아무 일도 하지 않아야 한다


def test_music_files_loop_cleanly():
    """배경음악: 곡마다 파일이 있다. 2026-11-24부터 OpenGameArt의 ogg·mp3 곡이라 길이·이음매 검사는
    tests/test_music_v2.py(파일 크기)로 옮겼다. 남은 합성 wav가 있으면 예전 규칙대로 검사한다."""
    import assets
    for name in ('title', 'explore', 'boss', 'ark', 'factory', 'tower', 'hideout'):
        path = assets.music_path(name)
        assert path, name
        if not path.endswith('.wav'):
            continue
        with wave.open(path, 'rb') as f:
            assert f.getnchannels() == 1 and f.getsampwidth() == 2
            n = f.getnframes()
            assert n / f.getframerate() > 20, name
            data = f.readframes(n)
        samples = [int.from_bytes(data[i:i + 2], 'little', signed=True) for i in range(0, len(data), 2)]
        peak = max(abs(s) for s in samples[::7])
        assert 8000 < peak < 32000, f'{name}: 피크 {peak}'
        assert abs(samples[0] - samples[-1]) < 3000, f'{name}: 반복 이음매가 튄다'


def test_music_choice_and_silence_when_disabled():
    import assets
    import play_mode

    class FakeBoss:
        alive = True

    class FakeStage:
        boss = None

    stage = FakeStage()
    assert play_mode.music_for(stage) == 'explore'
    stage.boss = FakeBoss()
    assert play_mode.music_for(stage) == 'boss'           # 살아 있는 보스가 있으면 보스 곡
    stage.boss.alive = False
    assert play_mode.music_for(stage) == 'explore'
    assets.play_music('explore')                          # 소리가 꺼져 있어도 예외 없이 곡 이름만 기억한다
    assert assets.current_music == 'explore'
    assets.stop_music()
    assert assets.current_music is None



# ----- 전용 효과음이 제자리에서 나는지 (2026-11-19) -----
class Recorder:
    """assets.play_sound를 잠시 바꿔 어떤 소리가 났는지 적는다."""
    def __enter__(self):
        import assets
        self.names, self._old = [], assets.play_sound
        assets.play_sound = self.names.append
        return self

    def __exit__(self, *exc):
        import assets
        assets.play_sound = self._old


def test_final_boss_has_its_own_music():
    import play_mode
    from ark import Ark

    class FakeStage:
        name = 'stage3'

    stage = FakeStage()
    stage.boss = Ark.__new__(Ark)
    stage.boss.alive = True
    assert play_mode.music_for(stage) == 'ark'            # 최종 보스는 크래셔와 다른 곡


def test_chain_throw_and_latch_have_their_own_sounds():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import test_chain as tch
    room, p, (e,) = tch.setup(35, [300])
    with Recorder() as rec:
        tch.fire_and_wait(p)
    assert 'chain_throw' in rec.names and 'chain_latch' in rec.names, rec.names


def test_chain_clash_has_its_own_sound():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import test_chain as tch
    room, p, foes = tch.setup(90, [250, 320])             # 위험 구간: 끌려온 적끼리 부딪친다
    with Recorder() as rec:
        tch.fire_and_wait(p)
    assert 'chain_clash' in rec.names, rec.names


def test_ultimate_cast_hits_and_finish_have_their_own_sounds():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import test_ultimate as tu
    room, p, foes = tu.stacked(90, 3, [150])
    with Recorder() as rec:
        assert p.request_attack()
        tu.run_out_ultimate()
    assert rec.names.count('ult_cast') == 1, rec.names
    assert 'ult_hit' in rec.names and rec.names.count('ult_final_pipe') == 1, rec.names   # 마무리는 무기마다 (11/21)


def test_ark_patterns_have_their_own_sounds():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import test_ark as ta
    room, p, a = ta.make_fight()
    with Recorder() as rec:
        a._fire_barrage()
        a._teleport_beside_player()
        a._absorb_waves()
        a._overcharge_ring()
        a._lay_fields()
        a._enter_phase(2, '각성')
    for name in ('ark_bullet', 'ark_teleport', 'ark_absorb', 'ark_burst', 'ark_field', 'ark_roar'):
        assert name in rec.names, (name, rec.names)


# ----- 무기별 명중·적별 예고·음량 균형 (2026-11-21) -----
def test_each_weapon_adds_its_own_impact_sound():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import test_combat as tc
    heard = {}
    for wid in ('pipe', 'pistol', 'gauntlet'):
        room, p = tc.make_world()
        if wid != 'pipe':
            p.give_weapon(wid)
        e = tc.freeze(tc.add_enemy('slum', p.x + 100, room, p))
        e.hp = e.max_hp = 1000
        with Recorder() as rec:
            p.weapon._hit(e, 1, 0, config.ZONE_FX['NORMAL'], extra=False)
        heard[wid] = rec.names
    for wid, names in heard.items():
        assert 'impact_' + wid in names, (wid, names)


def test_enemies_warn_with_their_own_windup_sound():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import test_combat as tc
    for kind in ('slum', 'thrower', 'hound', 'guard'):
        room, p = tc.make_world()
        e = tc.add_enemy(kind, p.x + 150, room, p)
        with Recorder() as rec:
            e.on_attack_start()
        assert 'windup_' + kind in rec.names, (kind, rec.names)


def test_mix_keeps_frequent_sounds_quieter_than_big_moves():
    import assets
    base = assets.sfx_gain('pickup')
    assert base == 1.0                                      # 표에 없는 소리는 그대로
    for quiet in ('land', 'jump', 'swing', 'enemy_hit'):
        assert assets.sfx_gain(quiet) < 1.0, quiet          # 자주 나는 소리는 작게
    for loud in ('ult_cast', 'ult_final_pipe', 'overload', 'ark_roar'):
        assert assets.sfx_gain(loud) >= 1.0, loud           # 큰 기술은 줄이지 않는다


def test_each_stage_and_the_hideout_have_their_own_music():
    """2026-11-21 퀄리티 계획 2-3: 슬럼(탐험)·공장·탑·은신처가 다른 곡. 보스가 살아 있으면 보스 곡이 먼저."""
    import play_mode

    class FakeStage:
        boss = None

    for name, song in (('stage1', 'explore'), ('stage2', 'factory'), ('stage3', 'tower'), ('hideout', 'hideout')):
        s = FakeStage()
        s.name = name
        assert play_mode.music_for(s) == song, (name, play_mode.music_for(s))


def test_ambience_plays_the_stage_sound_now_and_then():
    """환경음: 구역마다 다른 짧은 소리가 몇 초마다 (슬럼 물방울, 공장 증기, 탑 바람, 은신처 화로)."""
    import ambience
    for name, sound in (('stage1', 'amb_drip'), ('stage2', 'amb_steam'), ('stage3', 'amb_wind'), ('hideout', 'amb_forge')):
        class FakeStage:
            pass
        s = FakeStage()
        s.name = name
        a = ambience.Ambience(s, seed=3)
        with Recorder() as rec:
            for _ in range(60 * 20):                       # 20초
                a.update(1 / 60)
        assert rec.names and set(rec.names) == {sound}, (name, rec.names)
        assert 20 / 8 <= len(rec.names) <= 20 / 3 + 1, (name, len(rec.names))

# ----- 같은 소리 반복 줄이기·메뉴 전용 소리 (2026-11-22 v5 빠른 개선 1) -----
def test_frequent_sounds_rotate_three_versions():
    """자주 나는 소리는 음 높이·잡음이 조금씩 다른 3버전을 돌려 쓴다 (같은 소리가 기관총처럼 반복되지 않게)."""
    import assets
    for name in config.SFX_VARIANTS:
        for suffix in ('', '_v2', '_v3'):
            assert os.path.exists(os.path.join(ROOT, 'assets', 'sfx', name + suffix + '.wav')), name + suffix
        picked = [assets.variant_of(name) for _ in range(6)]
        assert set(picked) == {name, name + '_v2', name + '_v3'}, picked
        assert all(a != b for a, b in zip(picked, picked[1:]))          # 같은 버전이 연달아 나오지 않는다
    assert assets.variant_of('ult_cast') == 'ult_cast'                  # 큰 소리는 한 버전


def test_menus_have_their_own_sounds():
    import hud_kit
    from pico2d import SDL_KEYDOWN, SDLK_DOWN, SDLK_RETURN

    class Ev:
        def __init__(self, key):
            self.type, self.key = SDL_KEYDOWN, key

    buttons = [hud_kit.Button('a', 'A', 0, 0), hud_kit.Button('b', 'B', 0, 100)]
    with Recorder() as rec:
        hud_kit.menu_pick(buttons, 0, Ev(SDLK_DOWN), 1080)
        hud_kit.menu_pick(buttons, 1, Ev(SDLK_RETURN), 1080)
    assert rec.names == ['ui_move', 'ui_select']
    for name in ('ui_move', 'ui_select', 'ui_back'):
        assert os.path.exists(os.path.join(ROOT, 'assets', 'sfx', name + '.wav')), name


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
