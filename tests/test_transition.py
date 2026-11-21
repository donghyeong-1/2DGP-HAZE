"""화면 전환 연출 테스트 (창 없이). 실행: python tests/test_transition.py

2026-11-21 퀄리티 계획 4-3: 방에 들어가거나 화면(타이틀·사망·탈출·크레딧)이 바뀌면 검은 화면이 점묘(베이어)로
걷히며 새 화면이 드러난다(DURATION초). 반투명 없이 켜짐·꺼짐 점으로만 (픽셀 규칙).
그림은 tools/make_atmosphere.py가 만드는 assets/ui/wipe_01~15.png (128x128 타일, 번호가 클수록 촘촘).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

from PIL import Image  # noqa: E402

import transition  # noqa: E402


def test_reveal_goes_from_black_to_clear():
    transition.reveal()
    assert transition.level() == transition.LEVELS                     # 처음엔 다 가린다
    seen = []
    for _ in range(40):
        transition.tick(1 / 60)
        seen.append(transition.level())
    assert seen == sorted(seen, reverse=True)                          # 점점 걷힌다
    assert seen[-1] == 0 and transition.level() == 0
    assert any(0 < s < transition.LEVELS for s in seen)                # 중간 단계(점묘)를 거친다


def test_wipe_tiles_get_denser():
    counts = []
    for n in range(1, transition.LEVELS):
        im = Image.open(os.path.join(HERE, '..', 'assets', 'ui', f'wipe_{n:02d}.png')).convert('RGBA')
        assert im.size == (transition.TILE, transition.TILE)
        alpha = im.getchannel('A').histogram()
        assert sum(alpha[1:255]) == 0                                  # 켜짐·꺼짐만
        counts.append(alpha[255])
    assert counts == sorted(counts) and counts[0] > 0 and counts[-1] < transition.TILE ** 2


def test_entering_a_room_starts_a_reveal():
    import game_world
    from player import Player
    from stage import Stage
    game_world.clear()
    p = Player(0, 0, None)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    st = Stage(p, seed=1)
    st.start()
    transition.tick(10.0)
    assert transition.level() == 0
    d = sorted(st.links_of(st.coord))[0]
    st.enter_room(st.neighbour(st.coord, d), {'L': 'R', 'R': 'L', 'U': 'D', 'D': 'U'}[d])
    assert transition.level() == transition.LEVELS                     # 새 방은 검은 화면에서 드러난다
    game_world.clear()


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
