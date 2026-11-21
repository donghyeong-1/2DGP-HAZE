"""전체 판 자동 점검 (2026-11-21, 퀄리티 계획 3-5 보조): 봇이 한 판을 처음부터 끝까지 돌며 오류와 프레임 시간을 잰다.

은신처 -> 스테이지 1·2·3의 모든 방(시작 방에서 문으로 이어진 순서) -> 탈출 화면 -> 크레딧. 방마다 실제 창에
그리면서(그리기 코드도 점검) 몇 초 동안 싸운다: 가까운 적을 조준해 공격·대시·점프·E 강화를 섞어 쓰고,
조금 지나면 남은 적을 쓰러뜨려 방을 연다. 플레이어는 죽지 않게(체력·게이지를 유지) 한다.
사용자 저장·설정·기록은 임시 경로를 쓴다. 소리는 끈다.

사용: python tools/smoke_run.py [--seeds 3] [--seconds 3] [--display 2]
결과: 오류가 나면 추적 내용과 그때의 구역·방을 찍고 끝 코드 1. 끝나면 방별 프레임 시간(갱신+그리기) 표,
      16.7ms(60fps)를 넘는 방은 표시한다.
"""
import argparse
import os
import random
import sys
import tempfile
import time
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))

FRAME = 1 / 60
BUDGET_MS = 1000 / 60


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=3)
    ap.add_argument('--seconds', type=float, default=3.0, help='방마다 싸우는 시간(게임 시간)')
    ap.add_argument('--display', type=int, default=None)
    a = ap.parse_args()
    if a.display:
        os.environ['HAZE_DISPLAY'] = str(a.display)

    import config
    import log
    import meta
    import options
    tmp = tempfile.mkdtemp()
    meta.PATH, options.PATH, log.PATH = (os.path.join(tmp, n) for n in ('save.json', 'opt.json', 'log.txt'))
    config.SOUND_ENABLED = False
    from pico2d import SDL_HINT_RENDER_SCALE_QUALITY, SDL_SetHint, close_canvas, open_canvas
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b'0')
    open_canvas(config.SCREEN_W, config.SCREEN_H)
    from window_place import place_window
    place_window()
    import assets
    assets.preload(sounds=False)                         # 게임처럼 시작할 때 그림을 미리 읽는다
    import credits_mode
    import ending_mode
    import game_framework
    import game_world
    import play_mode
    import stage as stage_mod
    import title_mode
    for m in (play_mode, ending_mode, credits_mode, title_mode):
        m.update_canvas = lambda: None
    game_framework.frame_time = FRAME

    timings = []          # (구역, 방 좌표, 템플릿, 평균 ms, 최대 ms)
    where = ['-', '-']

    def frames(n, fight=True):
        """n프레임 갱신+그리기. 걸린 시간(ms) 목록."""
        out = []
        p = play_mode.player
        for i in range(n):
            t0 = time.perf_counter()
            if fight and p is not None:
                bot(p, i)
            play_mode.update()
            play_mode.draw()
            out.append((time.perf_counter() - t0) * 1000)
        return out

    def bot(p, i):
        p.hp = p.max_hp
        if p.gauge.value < 30 or p.gauge.value > 80:      # 죽지도 터지지도 않게
            p.gauge.value = 55.0
            p.gauge.zone = p.gauge._zone_of(55.0)
        foes = [e for e in game_world.world[game_world.LAYER_ENEMY] if getattr(e, 'alive', False)]
        if not foes:
            return
        e = min(foes, key=lambda f: abs(f.x - p.x) + abs(f.y - p.y))
        p.mouse_x, p.mouse_y = e.x, e.y + 50
        p.mouse_screen = None
        p.left, p.right = e.x < p.x - 80, e.x > p.x + 80
        if i % 6 == 0:
            p.request_attack()
        if i % 45 == 10:
            p.request_dash()
        if i % 50 == 20:
            p.request_jump()
        if i % 120 == 60 and p.gauge.can_enhance():
            p.request_enhance()

    def kill_all():
        for e in list(game_world.world[game_world.LAYER_ENEMY]):
            if getattr(e, 'alive', False):
                e.take_damage(10 ** 6)

    def visit_stage(st, rng):
        play_mode.stage, play_mode.room = st, st.room
        for o in game_world.world[game_world.LAYER_UI]:
            if hasattr(o, 'stage'):
                o.stage = st
        p = play_mode.player
        if rng.random() < 0.75:                          # 판마다 두 번째 무기를 바꿔 들어 무기별 코드를 돈다
            p.give_weapon(rng.choice(('knife', 'gauntlet', 'chain')))
        order, seen = [(st.start_coord, None)], {st.start_coord}
        k = 0
        while k < len(order):                            # 시작 방에서 문으로 이어진 순서 (너비 우선)
            c, _ = order[k]
            k += 1
            for d in sorted(st.links_of(c)):
                n = st.neighbour(c, d)
                if n in st.layout and n not in seen:
                    seen.add(n)
                    order.append((n, stage_mod.OPPOSITE[d]))
        for coord, side in order:
            where[1] = f'{coord} {st.template_of(coord)}'
            if coord != st.coord:
                if st.type_of(coord) == 'rift':
                    st.paid_rifts.add(coord)            # 균열방 입장료는 건너뛴다
                st.enter_room(coord, side)
            ms = frames(int(a.seconds * 60))
            kill_all()
            ms += frames(40, fight=False)
            timings.append((st.name, coord, st.template_of(coord), sum(ms) / len(ms), max(ms)))

    try:
        for seed in range(a.seeds):
            rng = random.Random(seed)
            random.seed(seed)
            where[:] = ['hideout', '-']
            game_framework.stack[:] = [play_mode]
            play_mode.enter()
            frames(60, fight=False)
            st = play_mode.stage
            for name in ('stage1', 'stage2', 'stage3'):
                st = stage_mod.next_stage(st)
                where[0] = f'seed {seed} {name}'
                visit_stage(st, rng)
            where[:] = [f'seed {seed} ending', '-']
            ending_mode.result = 'clear'
            game_framework.stack[:] = [ending_mode]
            ending_mode.enter()
            for _ in range(60):
                ending_mode.update()
                ending_mode.draw()
            game_framework.stack[:] = [credits_mode]
            credits_mode.enter()
            credits_mode._fast = True
            for _ in range(240):
                credits_mode.update()
                if game_framework.stack[-1] is not credits_mode:
                    break
                credits_mode.draw()
            play_mode.exit()
            print(f'seed {seed}: 끝까지 오류 없음')
    except Exception:
        print(f'오류: {where[0]} / {where[1]}')
        traceback.print_exc()
        close_canvas()
        return 1
    close_canvas()
    print()
    print(f'{"구역":8} {"방":10} {"모양":12} {"평균ms":>7} {"최대ms":>7}')
    worst = sorted(timings, key=lambda r: -r[3])
    for name, coord, tpl, avg, peak in worst[:12]:
        mark = '  <- 60fps 넘음' if avg > BUDGET_MS else ''
        print(f'{name:8} {str(coord):10} {tpl:12} {avg:7.2f} {peak:7.2f}{mark}')
    over = sum(1 for r in timings if r[3] > BUDGET_MS)
    print(f'방 {len(timings)}개, 평균이 {BUDGET_MS:.1f}ms를 넘는 방 {over}개')
    return 0


if __name__ == '__main__':
    sys.exit(main())
