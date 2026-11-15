"""플레이어: 이동 상태 머신(transitions), 2단 점프, 대시 슬롯, 타일 충돌.

공격은 상태 머신 밖의 겹침(overlay)으로 처리한다 (2주차). pico2d는 그릴 때만 불러와서
이 모듈은 창 없이도 테스트할 수 있다.
"""
import math

from transitions import Machine

import assets
import config
import effects
import room as room_module
from body import EPS, TileBody
from haze_gauge import DEAD, HazeGauge
from weapon import Pipe

STATE_NAMES = ['IDLE', 'RUN', 'JUMP', 'FALL', 'DASH', 'HIT', 'DEAD']


class _State:
    """상태 객체. enter/exit는 전이 때, do는 매 프레임 속도·타이머 갱신, check는 물리 처리 뒤 전이 판단."""

    gravity = True

    def __init__(self, player):
        self.p = player

    def enter(self):
        pass

    def exit(self):
        pass

    def do(self, dt):
        pass

    def check(self):
        pass


class Idle(_State):
    def enter(self):
        self.p.jump_count = 0
        self.p.on_landing()

    def do(self, dt):
        self.p.vx = 0.0

    def check(self):
        p = self.p
        if not p.on_ground:
            p.jump_count = max(p.jump_count, 1)  # 걸어 떨어졌으면 공중 점프는 1회만 남는다
            p.fall()
        elif p.direction != 0:
            p.move()


class Run(_State):
    def enter(self):
        self.p.jump_count = 0
        self.p.on_landing()

    def do(self, dt):
        p = self.p
        p.vx = p.direction * config.RUN_SPEED * p.speed_mult()

    def check(self):
        p = self.p
        if not p.on_ground:
            p.jump_count = max(p.jump_count, 1)
            p.fall()
        elif p.direction == 0:
            p.stop()


class _Airborne(_State):
    """공중 상태 공통: 좌우 조작은 지상과 같은 속도로 받는다."""

    def do(self, dt):
        p = self.p
        p.air_time += dt
        p.vx = p.direction * config.RUN_SPEED * p.speed_mult()


class Jump(_Airborne):
    def enter(self):
        p = self.p
        p.vy = config.JUMP_SPEED
        p.jump_count += 1
        p.on_ground = False
        p.coyote_left = 0.0       # 뛰었으면 코요테 점프 기회는 쓴 것이다 (이중 점프 방지)
        p.jump_buffer_left = 0.0
        assets.play_sound('double_jump' if p.jump_count >= 2 else 'jump')

    def check(self):
        p = self.p
        if p.vy <= 0:
            p.fall()


class Fall(_Airborne):
    def check(self):
        p = self.p
        if p.on_ground:
            p.land()


class Dash(_State):
    gravity = False

    def enter(self):
        p = self.p
        p.dash_slots -= 1
        assets.play_sound('dash')
        p.dash_left = config.DASH_TIME
        p.invuln_left = config.DASH_INVULN
        ax, ay = p.aim_vector()
        p.dash_vec = (ax, ay)
        p.vy = 0.0
        p.afterimage_timer = 0.0  # 출발 지점에도 잔상을 남긴다

    def do(self, dt):
        p = self.p
        p.vx = p.dash_vec[0] * config.DASH_SPEED
        p.vy = p.dash_vec[1] * config.DASH_SPEED
        p.dash_left -= dt

    def check(self):
        p = self.p
        if p.dash_left <= 0:
            p.vx = 0.0
            p.vy = 0.0
            p.dash_end()


class Hit(_State):
    def enter(self):
        self.p.hit_left = config.HIT_STUN

    def do(self, dt):
        p = self.p
        p.vx = 0.0
        p.hit_left -= dt

    def check(self):
        if self.p.hit_left <= 0:
            self.p.hit_end()


class Dead(_State):
    def enter(self):
        assets.play_sound('death')

    def do(self, dt):
        self.p.vx = 0.0


class Player(TileBody):
    def __init__(self, x, y, room):
        self.room = room
        self.x, self.y = x, y            # 발 아래 중앙 좌표
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.jump_count = 0
        self.air_time = 0.0              # 공중에 머문 시간(착지 소리용)
        self.coyote_left = 0.0           # 땅에서 막 떨어졌을 때 남은 점프 유예 시간
        self.jump_buffer_left = 0.0      # 점프를 미리 눌러 둔 채 남은 시간
        self.face_dir = 1
        self.hp = config.PLAYER_HP

        # 입력 상태
        self.left = self.right = self.down = False
        self.mouse_x, self.mouse_y = x + 150.0, y + config.PLAYER_HB_H / 2

        # 대시
        self.dash_slots = config.DASH_SLOTS_BASE
        self.dash_max = config.DASH_SLOTS_BASE
        self.dash_charge = 0.0
        self.dash_vec = (1.0, 0.0)
        self.dash_left = 0.0
        self.invuln_left = 0.0

        self.afterimages = []            # 대시 잔상: [x, y, face_dir, 남은 수명]
        self.afterimage_timer = 0.0

        self.drop_timer = 0.0
        self.hit_left = 0.0
        self.gauge = HazeGauge()
        self.gauge.listeners.append(self._on_gauge_event)
        self.weapon = Pipe(self)         # 장착 무기 (2주차는 철파이프 하나)
        self.attack_held = False         # 좌클릭을 누르고 있으면 쿨타임마다 이어서 친다
        self.shards = 0                  # 헤이즈 조각(재화). 죽으면 처음부터이므로 이번 플레이 동안만 유지

        # 상태 객체와 transitions 상태 머신 (Player 객체에 self.state 속성이 생긴다)
        self.states = {
            'IDLE': Idle(self), 'RUN': Run(self), 'JUMP': Jump(self), 'FALL': Fall(self),
            'DASH': Dash(self), 'HIT': Hit(self), 'DEAD': Dead(self),
        }
        air = ['IDLE', 'RUN', 'JUMP', 'FALL']
        self.machine = Machine(
            model=self,
            states=[{'name': n, 'on_enter': s.enter, 'on_exit': s.exit} for n, s in self.states.items()],
            transitions=[
                {'trigger': 'move', 'source': 'IDLE', 'dest': 'RUN'},
                {'trigger': 'stop', 'source': 'RUN', 'dest': 'IDLE'},
                {'trigger': 'jump', 'source': air, 'dest': 'JUMP'},
                {'trigger': 'fall', 'source': ['IDLE', 'RUN', 'JUMP'], 'dest': 'FALL'},
                {'trigger': 'land', 'source': ['FALL', 'JUMP'], 'dest': 'IDLE'},
                {'trigger': 'dash', 'source': air, 'dest': 'DASH'},
                {'trigger': 'dash_end', 'source': 'DASH', 'dest': 'FALL'},
                {'trigger': 'hit', 'source': air + ['DASH'], 'dest': 'HIT'},
                {'trigger': 'hit_end', 'source': 'HIT', 'dest': 'FALL'},
                {'trigger': 'die', 'source': '*', 'dest': 'DEAD'},
            ],
            initial='FALL',
            ignore_invalid_triggers=True,
        )
        # transitions는 초기 상태의 on_enter를 호출하지 않으므로 직접 호출한다 (FALL은 따로 할 일 없음)

    # ----- 입력 -----
    @property
    def direction(self):
        if self.stunned:
            return 0
        return int(self.right) - int(self.left)

    @property
    def stunned(self):
        """오버로드 기절 중에는 이동·점프·대시·공격을 할 수 없다."""
        return self.gauge.stun_timer > 0

    @property
    def stop_on_wall(self):
        return self.state != 'DASH'  # 대시 중에는 벽에 닿아도 속도를 유지한다

    @property
    def center(self):
        return (self.x, self.y + config.PLAYER_HB_H / 2)

    def rect(self):
        hw = config.PLAYER_HB_W / 2
        return (self.x - hw, self.y, self.x + hw, self.y + config.PLAYER_HB_H)

    def speed_mult(self):
        return self.gauge.zone_multipliers()['speed']

    def aim_vector(self):
        """몸 중심에서 마우스까지 단위 벡터. 거의 겹치면 보는 방향."""
        cx, cy = self.x, self.y + config.PLAYER_HB_H / 2
        dx, dy = self.mouse_x - cx, self.mouse_y - cy
        length = math.hypot(dx, dy)
        if length < 1.0:
            return (float(self.face_dir), 0.0)
        return (dx / length, dy / length)

    def handle_event(self, event):
        from pico2d import (SDL_BUTTON_LEFT, SDL_BUTTON_RIGHT, SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEBUTTONDOWN,
                            SDL_MOUSEBUTTONUP, SDL_MOUSEMOTION, SDLK_a, SDLK_d, SDLK_e, SDLK_LSHIFT, SDLK_s, SDLK_SPACE, SDLK_w,
                            get_canvas_height)
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_a:
                self.left = True
            elif event.key == SDLK_d:
                self.right = True
            elif event.key == SDLK_s:
                self.down = True
            elif event.key in (SDLK_SPACE, SDLK_w):
                self.request_jump()
            elif event.key == SDLK_LSHIFT:
                self.request_dash()
            elif event.key == SDLK_e:
                self.request_enhance()
        elif event.type == SDL_KEYUP:
            if event.key == SDLK_a:
                self.left = False
            elif event.key == SDLK_d:
                self.right = False
            elif event.key == SDLK_s:
                self.down = False
        elif event.type == SDL_MOUSEMOTION:
            self.mouse_x, self.mouse_y = event.x, get_canvas_height() - 1 - event.y
        elif event.type == SDL_MOUSEBUTTONDOWN:
            self.mouse_x, self.mouse_y = event.x, get_canvas_height() - 1 - event.y
            if event.button == SDL_BUTTON_RIGHT:
                self.request_dash()
            elif event.button == SDL_BUTTON_LEFT:
                self.attack_held = True
                self.request_attack()
        elif event.type == SDL_MOUSEBUTTONUP:
            if event.button == SDL_BUTTON_LEFT:
                self.attack_held = False

    def on_landing(self):
        """땅에 닿았을 때: 충분히 높은 곳에서 떨어졌으면 착지 소리를 낸다."""
        if self.air_time > 0.25:
            assets.play_sound('land')
        self.air_time = 0.0

    def request_enhance(self):
        """E: 게이지를 쓰고 무기를 잠시 강화한다. 게이지가 모자라거나 이미 강화 중이면 아무 일도 없다."""
        if self.state in ('HIT', 'DEAD') or self.stunned:
            return False
        if not self.gauge.use_enhance():
            return False
        assets.play_sound('enhance')
        effects.spawn('rage', self.x, self.y + config.PLAYER_HB_H + 10, duration=0.6)
        effects.add_trauma(0.25)
        return True

    def request_attack(self):
        if self.state in ('DASH', 'HIT', 'DEAD') or self.stunned:
            return False
        return self.weapon.try_attack()

    def request_jump(self):
        if self.state in ('DASH', 'HIT', 'DEAD') or self.stunned:
            return
        if self.down and self.state in ('IDLE', 'RUN'):
            # S + Space: 얇은 바닥 위에 서 있으면 아래로 내려간다
            if self.room.tile_at_world(self.x, self.y - EPS) == room_module.ONEWAY:
                self.drop_timer = config.DROP_TIME
                self.y -= 3.0
                self.on_ground = False
            return
        if self.state == 'FALL' and self.coyote_left > 0 and self.jump_count == 1:
            self.jump_count = 0  # 막 걸어 떨어진 직후라면 땅 위 첫 점프로 쳐 준다 (공중 점프는 그대로 한 번 남는다)
            self.jump()
            return
        if self.jump_count >= config.MAX_JUMPS:
            self.jump_buffer_left = config.JUMP_BUFFER  # 점프를 다 썼으면 눌러 둔 것을 기억했다가 착지하면 뛴다
            return
        self.jump()

    def request_dash(self):
        if self.state in ('DASH', 'HIT', 'DEAD') or self.stunned or self.dash_slots <= 0:
            return
        self.dash()

    def take_hit(self, damage=0, gauge_delta=0):
        """피격. 대시 무적과 피격 직후 무적 중에는 무시한다. 맞으면 게이지가 줄고(LOSS_DAMAGED),
        적 종류별 추가 변화(gauge_delta, 예: 간수 +15)도 받는다."""
        if self.invuln_left > 0 or self.state == 'DEAD':
            return
        self.hp = max(0, self.hp - damage)
        self.gauge.add(config.LOSS_DAMAGED + gauge_delta, 'damaged')
        if self.hp <= 0:
            self.die()
        elif self.state != 'DEAD':
            assets.play_sound('hit')
            self.invuln_left = config.HIT_INVULN
            self.hit()
        effects.add_trauma(config.SHAKE_DAMAGED)
        effects.request_hit_stop(config.HIT_STOP_DAMAGED)

    def _on_gauge_event(self, name, gauge):
        if name == 'overload':
            effects.add_trauma(config.SHAKE_OVERLOAD)
            # 오버로드: 최대 체력의 일부 피해 (기절은 게이지가 stun_timer로 건다)
            self.hp = max(0, self.hp - int(config.PLAYER_HP * config.OVERLOAD_DAMAGE_RATIO))
            if self.hp <= 0 and self.state != 'DEAD':
                self.die()

    # ----- 갱신 -----
    def update(self, dt):
        self._recharge_dash(dt)
        self.drop_timer = max(0.0, self.drop_timer - dt)
        self.weapon.update(dt)
        self.coyote_left = config.COYOTE_TIME if self.on_ground else max(0.0, self.coyote_left - dt)
        self.jump_buffer_left = max(0.0, self.jump_buffer_left - dt)
        if self.attack_held:
            self.request_attack()
        self.invuln_left = max(0.0, self.invuln_left - dt)
        if self.gauge.zone == DEAD and self.state != 'DEAD':
            self.die()

        state = self.states[self.state]
        state.do(dt)
        if state.gravity:
            self.vy = max(self.vy - config.GRAVITY * dt, -config.MAX_FALL_SPEED)
        self.move_with_tiles(dt)
        self.states[self.state].check()
        if self.jump_buffer_left > 0 and self.state in ('IDLE', 'RUN'):
            self.jump_buffer_left = 0.0  # 착지하자마자 눌러 둔 점프
            self.request_jump()
        self._update_afterimages(dt)

        # 조준 방향이 보는 방향 (조준이 거의 수직이면 이동 방향)
        if abs(self.mouse_x - self.x) > 4:
            self.face_dir = 1 if self.mouse_x > self.x else -1

    def _update_afterimages(self, dt):
        """대시 중에는 일정 간격으로 현재 모습을 남기고, 남은 잔상은 수명이 다할 때까지 옅어지다 사라진다."""
        for ghost in self.afterimages:
            ghost[3] -= dt
        self.afterimages = [g for g in self.afterimages if g[3] > 0]
        if self.state != 'DASH':
            return
        self.afterimage_timer -= dt
        if self.afterimage_timer <= 0:
            self.afterimage_timer += config.AFTERIMAGE_INTERVAL
            self.afterimages.append([self.x, self.y, self.face_dir, config.AFTERIMAGE_LIFE])

    def _recharge_dash(self, dt):
        if self.dash_slots >= self.dash_max:
            self.dash_charge = 0.0
            return
        self.dash_charge += dt
        if self.dash_charge >= config.DASH_RECHARGE:
            self.dash_charge -= config.DASH_RECHARGE
            self.dash_slots += 1

    # ----- 그리기 -----
    def draw(self):
        import assets
        img = assets.image('sprites/unified/n09_idle.png')
        steps = config.AFTERIMAGE_ALPHA_STEPS
        for gx, gy, gdir, left in self.afterimages:  # 오래된 것부터 그려 새 잔상이 위에 온다
            age = 1.0 - left / config.AFTERIMAGE_LIFE
            alpha = steps[min(int(age * len(steps)), len(steps) - 1)]
            assets.draw_image_tinted(img, gx, gy - config.SPRITE_FOOT_MARGIN, 'h' if gdir < 0 else '',
                                     config.AFTERIMAGE_COLOR, alpha)
        blink = self.invuln_left > 0 and self.state != 'DASH' and int(self.invuln_left * 20) % 2 == 0  # 피격 무적 중 깜빡임
        if not blink:
            assets.draw_image(img, self.x, self.y - config.SPRITE_FOOT_MARGIN, 'h' if self.face_dir < 0 else '')
        if config.DEBUG:
            self._draw_debug()

    def _draw_debug(self):
        import assets
        from pico2d import draw_rectangle
        hw = config.PLAYER_HB_W / 2
        draw_rectangle(self.x - hw, self.y, self.x + hw, self.y + config.PLAYER_HB_H)
        draw_rectangle(self.mouse_x - 4, self.mouse_y - 4, self.mouse_x + 4, self.mouse_y + 4)
        assets.draw_text(self.x, self.y + config.PLAYER_HB_H + 27, f'{self.state} j{self.jump_count}', (255, 240, 120), small=True, center=True)
