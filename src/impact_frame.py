"""임팩트 프레임 (v8 4-2, docs/plan_v8.md 대기열 4 '남겨 둔 것'): 강화 일격과 보스 막타에 1~2프레임 끼워 넣는 장면.

배경은 검정, 주인공과 맞은 적은 흰 실루엣, 맞은 자리를 가로지르는 흰 베기 선. 처형·궁극기 마무리는 이미 FinisherCut이 한다.
- 강화 일격이 여러 적을 맞혀도 한 장면이다(같은 장면에 맞은 적이 늘어난다).
- 보스(BOSS_KINDS)를 쓰러뜨린 타격이면 강화가 아니어도 나온다.
- FinisherCut이 돌고 있으면 겹치지 않는다. 설정 '번쩍임 줄이기'면 나오지 않는다.
- 시간이 아니라 그려진 프레임 수(FRAMES)로 끝난다: 타격 멈춤 중에는 갱신이 멈춰도 그리기는 돌므로 바로 그 순간에 보인다.
- UI 층의 구간 색(Atmosphere) 바로 뒤에 둔다: 세계의 모든 이펙트·안개 위, HUD 아래. 세계 좌표는 카메라·흔들림을 직접 더해 그린다.
"""
import assets
import config
import game_world
import options
import sprites

FRAMES = 2
BOSS_KINDS = ('gatekeeper', 'crasher', 'ark', 'heart')
MAX_VICTIMS = 6
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def is_boss(e):
    return getattr(e, 'kind', None) in BOSS_KINDS


def _finisher_running():
    import weapon
    return any(isinstance(o, weapon.FinisherCut) for o in game_world.world[game_world.LAYER_EFFECT])


def _current():
    for o in game_world.world[game_world.LAYER_UI]:
        if isinstance(o, ImpactFrame) and o.visible():
            return o
    return None


def trigger(player, enemy, from_x=None, snap=None):
    """임팩트 프레임을 띄우거나, 이미 떠 있으면 맞은 적을 더한다. 띄우지 않았으면 None."""
    if options.reduce_flash or _finisher_running():
        return None
    import weapon
    snap = snap or weapon._enemy_snap(enemy)
    f = _current()
    if f is None:
        f = ImpactFrame(player, from_x if from_x is not None else player.x)
        ui = game_world.world[game_world.LAYER_UI]
        at = max([i + 1 for i, o in enumerate(ui) if type(o).__name__ == 'Atmosphere'] + [0])
        ui.insert(at, f)                                            # 세계 이펙트·구간 색(안개·비네트) 위, HUD 아래
    f.add(enemy, snap)
    return f


class ImpactFrame:
    def __init__(self, player, from_x):
        self.player = player
        self.from_x = from_x
        self.victims = []          # (그림, 발 x, 발 y, 보는 쪽)
        self.centers = []          # 맞은 적의 가운데 (베기 선이 지나는 자리)
        self.ids = set()
        self.drawn = 0

    def add(self, enemy, snap):
        if id(enemy) in self.ids or len(self.victims) >= MAX_VICTIMS:
            return
        self.ids.add(id(enemy))
        if snap:
            self.victims.append(snap)
        self.centers.append(enemy.center)

    def visible(self):
        return self.drawn < FRAMES

    def update(self, dt):
        if not self.visible():
            game_world.remove_object(self)

    def draw(self):
        if not self.visible():
            return
        import camera
        import effects
        self.drawn += 1
        offset = assets.draw_offset
        assets.draw_offset = (0, 0)
        assets.draw_rect_color(-16, -16, config.SCREEN_W + 32, config.SCREEN_H + 32, BLACK)
        (cx, cy), (sx, sy) = camera.offset(), effects.shake_offset()
        assets.draw_offset = (cx + sx, cy + sy)                      # 세계 좌표 (play_mode._apply_shake와 같다)
        self._world()
        assets.draw_offset = offset

    def _world(self):
        for frame, x, y, face in self.victims:
            sprites.draw_silhouette(*frame, x, y, face, WHITE, 1.0)
        p = self.player
        if p is not None:
            sprites.draw_silhouette(*p._body_frame(), p.x, p.y, p.draw_face(), WHITE, 1.0)
        self._slash()

    def _slash(self):
        """맞은 자리를 가로지르는 흰 베기 선: 가운데가 두껍고 양끝이 가늘다 (높이가 비슷한 적끼리는 한 줄)."""
        rows = []
        for cx, cy in sorted(self.centers, key=lambda c: c[1]):
            if rows and cy - rows[-1][1] <= 60:
                rows[-1][0].append(cx)
            else:
                rows.append(([cx], cy))
        for xs, cy in rows[:3]:
            left, right = min(xs) - 260, max(xs) + 260
            w = right - left
            y = int(cy) // 2 * 2
            for i, h in enumerate((2, 6, 12)):                     # 바깥에서 안으로 좁아지며 두꺼워진다
                inset = int(w * 0.16 * i)
                assets.draw_rect_color(int(left) + inset, y - h // 2, w - 2 * inset, h, WHITE)
