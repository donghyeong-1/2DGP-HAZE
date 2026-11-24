"""화면 밖 적 표시 (v8 남겨 둔 것, 2026-11-25). 창 없이: python tests/test_offscreen.py

- 큰 방(두 화면짜리)이거나 남은 적이 셋 이하일 때, 잠긴 방에서 화면 밖에 있는 적 쪽 화면 가장자리에 화살표를 띄운다.
- 화살표는 화면 안(가장자리에서 MARGIN 안쪽)에 머물고, 적이 있는 쪽 가장자리를 가리킨다(왼·오·위·아래 네 그림, 회전 없음).
- 화면 안에 있는 적, 쓰러진 적에는 띄우지 않는다. 한 번에 MAX개까지(가까운 적부터).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import config  # noqa: E402
import offscreen  # noqa: E402

W, H = config.SCREEN_W, config.SCREEN_H


class Foe:
    def __init__(self, x, y, alive=True):
        self.x, self.y, self.alive = x, y, alive

    @property
    def center(self):
        return self.x, self.y + 40


def at(foes, cam=(0, 0), player=(W / 2, H / 2)):
    return offscreen.markers(foes, cam, player)


def test_on_screen_and_dead_enemies_get_no_marker():
    assert at([Foe(500, 300), Foe(-400, 300, alive=False)]) == []


def test_marker_side_points_toward_the_enemy():
    sides = {m[2] for m in at([Foe(-500, 400)])}
    assert sides == {'l'}
    assert {m[2] for m in at([Foe(W + 500, 400)])} == {'r'}
    assert {m[2] for m in at([Foe(W / 2, H + 400)])} == {'u'}
    assert {m[2] for m in at([Foe(W / 2, -600)])} == {'d'}


def test_marker_stays_inside_the_screen_edge():
    for foe in (Foe(-3000, 4000), Foe(5000, -2000), Foe(W + 10, H / 2), Foe(W / 2, -5000)):
        for x, y, side, _d in at([foe]):
            assert offscreen.MARGIN <= x <= W - offscreen.MARGIN, (x, foe.x)
            assert offscreen.MARGIN <= y <= H - offscreen.MARGIN_TOP, (y, foe.y)     # 위쪽은 HUD 아래
            assert x == int(x) and y == int(y)                       # 정수 좌표 (픽셀 규칙)


def test_camera_offset_is_used():
    assert at([Foe(3000, 400)], cam=(0, 0)) != []
    assert at([Foe(3000, 400)], cam=(2400, 0)) == []                 # 카메라가 오른쪽으로 오면 화면 안


def test_crowded_enemies_share_one_marker():
    assert len(at([Foe(-400, 400), Foe(-420, 405), Foe(-450, 398)])) == 1


def test_at_most_max_markers_nearest_first():
    foes = [Foe(-200 - i * 300, 100 + i * 120) for i in range(offscreen.MAX + 4)]   # 화살표가 겹치지 않게 높이를 다르게
    got = at(foes)
    assert len(got) == offscreen.MAX
    assert [m[3] for m in got] == sorted(m[3] for m in got)          # 가까운 적부터


class Room:
    locked = True


class Stage:
    def __init__(self, big, n):
        self.room, self._big, self.n = Room(), big, n
        self.coord = (0, 0)

    def is_big(self, c):
        return self._big

    def enemy_count(self):
        return self.n


def test_shown_in_big_rooms_or_when_few_enemies_are_left():
    assert offscreen.active(Stage(True, 8))
    assert not offscreen.active(Stage(False, 8))
    assert offscreen.active(Stage(False, offscreen.FEW))
    st = Stage(True, 8)
    st.room.locked = False
    assert not offscreen.active(st)                                  # 다 깬 방에는 없다
    assert not offscreen.active(None)


def test_marker_images_exist():
    from PIL import Image
    for side in offscreen.SIDES:
        im = Image.open(os.path.join(HERE, '..', 'assets', 'ui', f'hud_offscreen_{side}.png')).convert('RGBA')
        alpha = im.getchannel('A').histogram()
        assert sum(alpha[1:255]) == 0 and im.size[0] % 2 == 0 and im.size[1] % 2 == 0


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
