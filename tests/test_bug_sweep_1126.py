"""2026-11-26 자동 플레이 버그 점검에서 찾은 것 (창 없이). 실행: python tests/test_bug_sweep_1126.py

docs/project/bug-sweep.md 2026-11-26 절.
- 테두리용 흰 판(assets.silhouette)과 검은 테두리 판(assets.outline_image)은 임시 폴더의 같은 파일에 쓴다.
  다른 실행(게임 두 개, 백신 검사)이 그 파일을 쥐고 있으면 Windows에서 PermissionError로 게임이 꺼졌다.
"""
import os
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import assets  # noqa: E402


class _Fake:
    def __init__(self, path):
        self.path = path


def _with_locked_cache(fn):
    """임시 폴더를 새로 잡고, 그 안의 캐시 파일 자리를 다른 실행이 쥐고 있는 것처럼(os.replace가 PermissionError) 한다."""
    fake = types.ModuleType('pico2d')
    fake.load_image = lambda path: _Fake(path)
    old_mod, old_tmp, old_replace = sys.modules.get('pico2d'), tempfile.tempdir, os.replace
    folder = tempfile.mkdtemp()
    sys.modules['pico2d'] = fake
    tempfile.tempdir = folder

    from PIL import Image
    old_save = Image.Image.save
    shared = lambda path: os.path.dirname(os.path.dirname(str(path))) == folder and '.tmp' not in str(path)   # noqa: E731

    def locked_save(self, fp, *a, **k):
        if shared(fp):                                                # 다른 실행이 쥐고 있는 공유 파일
            raise PermissionError(13, 'Permission denied', fp)
        return old_save(self, fp, *a, **k)

    def locked_replace(src, dst):
        if shared(dst):
            raise PermissionError(13, 'Permission denied', dst)
        return old_replace(src, dst)
    Image.Image.save = locked_save
    os.replace = locked_replace
    try:
        return fn()
    finally:
        Image.Image.save = old_save
        os.replace = old_replace
        tempfile.tempdir = old_tmp
        if old_mod is None:
            sys.modules.pop('pico2d', None)
        else:
            sys.modules['pico2d'] = old_mod


def test_silhouette_survives_a_locked_cache_file():
    assets._silhouettes.clear()
    img = _with_locked_cache(lambda: assets.silhouette('sprites/unified/n09_idle_1.png'))
    assert os.path.exists(img.path)                                   # 이 실행만의 파일을 대신 쓴다
    assets._silhouettes.clear()


def test_outline_survives_a_locked_cache_file():
    assets._outlines.clear()
    img = _with_locked_cache(lambda: assets.outline_image('sprites/unified/n09_idle_1.png', 2))
    assert os.path.exists(img.path)
    assets._outlines.clear()


# ----- 저주 조합 (자동 플레이로 밟은 길을 창 없이 한 번 더) -----
def _player(first='pipe', second='gauntlet'):
    sys.path.insert(0, HERE)
    import test_combat as tc
    p = tc.make_world()[1]
    if second:
        p.set_loadout(first, second)
    else:
        p.set_loadout(first)
    return p


def test_drifter_deal_never_offers_a_curse_card_even_when_curses_always_mix():
    import random
    import curse
    import events
    import mutations as mu
    old = curse.OFFER_CHANCE
    try:
        curse.OFFER_CHANCE = 1.0
        for seed in range(30):
            p = _player()
            mu.give(p, 'tide_cost')                                   # 증강이 있어야 방 보상에는 저주가 섞인다
            p.hp = p.max_hp
            text, _color, follow = events.take(p, events.CARD + 'deal:blood', random.Random(seed))
            assert follow and not any(c.startswith(curse.CARD) for c in follow), follow
    finally:
        curse.OFFER_CHANCE = old


def test_lowcap_with_a_cap_upgrade_and_a_spring_keeps_the_line_consistent():
    import random
    import config
    import curse
    import events
    import items
    p = _player()
    base = p.gauge.cap
    curse.take(p, curse.CARD + 'lowcap')
    items.apply(p, 'cap')                                             # 저주 중에 한계 강화
    assert p.gauge.cap == base + 20 - curse.LOWCAP
    events.take(p, events.CARD + 'spring:critical')                  # 헤이즈 샘 '들이붓기'는 낮아진 한계 기준
    assert p.gauge.value < p.gauge.cap and p.gauge.zone == 'CRITICAL'
    for _ in range(curse.CURSES['lowcap']['rooms']):
        curse.on_room_clear(p, random.Random(1))
    assert curse.active(p) is None and p.gauge.cap == base + 20
    assert config.ZONE_NORMAL_MAX < p.gauge.cap


def test_lock_curse_with_one_weapon_is_never_offered_and_a_new_weapon_mid_run_does_not_swap():
    import random
    import curse
    p = _player('pipe', None)
    assert not curse._usable(p, 'lock')                               # 무기 하나: 굳은 손은 나오지 않는다
    p = _player('pipe', 'gauntlet')
    held = p.weapon.weapon_id
    curse.take(p, curse.CARD + 'lock')
    assert not p.swap_weapon(strike=True)
    p.give_weapon('chain')                                            # 판 도중 무기를 얻으면 든 무기는 그대로, 빈 칸 쪽에 들어간다
    assert p.weapon.weapon_id == held and p.has_weapon('chain')
    for _ in range(curse.CURSES['lock']['rooms']):
        curse.on_room_clear(p, random.Random(2))
    assert p.swap_weapon(strike=True)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
