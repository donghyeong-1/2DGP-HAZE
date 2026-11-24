"""플레이어: 이동 상태 머신(transitions), 2단 점프, 대시 슬롯, 타일 충돌.

공격은 상태 머신 밖의 겹침(overlay)으로 처리한다 (2주차). pico2d는 그릴 때만 불러와서
이 모듈은 창 없이도 테스트할 수 있다.
"""
import math

from transitions import Machine

import assets
import camera
import config
import effects
import game_world
import room as room_module
import sprites
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
        mult = p.speed_mult()
        if p.direction and p.direction != p.face_dir:            # 뒷걸음: 조준을 유지한 채 조금 느리게 물러난다
            mult *= config.BACKPEDAL_SPEED_MULT
        elif p.start_left > 0:                                    # 출발 자세 동안 최고 속도까지 오른다
            k = 1.0 - p.start_left / config.RUN_START_TIME
            mult *= config.RUN_START_SPEED + (1.0 - config.RUN_START_SPEED) * k
        p.vx = p.direction * config.RUN_SPEED * mult

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
        p.dash_count += 1
        assets.play_sound('dash')
        p.dash_left = config.DASH_TIME
        import mutations
        p.invuln_left = config.DASH_INVULN + mutations.dash_invuln_extra(p)   # v7 '미끄러짐'
        p.dash_age = 0.0                 # 저스트 대시 판정 (대시를 시작하고 지난 시간)
        p.just_used = False
        ax, ay = p.aim_vector()
        if p.on_ground and ay < -config.DASH_DOWN_AIM and p.room is not None:
            below = p.room.tile_at_world(p.x, p.y - EPS)
            if below == room_module.ONEWAY:                 # 얇은 발판 위에서 아래로 대시: 발판을 뚫고 내려간다
                p.drop_timer = config.DASH_TIME + 0.12
                p.y -= 3.0
                p.on_ground = False
            else:                                           # 단단한 바닥에서는 내려갈 수 없다: 보는 쪽 수평 대시로 바꾼다
                ax, ay = (math.copysign(1.0, ax) if abs(ax) > 0.05 else float(p.face_dir)), 0.0
        p.dash_vec = (ax, ay)
        p.vy = 0.0
        p.afterimage_timer = 0.0  # 출발 지점에도 잔상을 남긴다
        p.dash_window = config.DASH_ATTACK_WINDOW
        p.dash_origin = p.center
        p.dash_strike_queued = False
        if p.on_ground:
            effects.spawn('dust-land', p.x, p.y, duration=0.3)          # 땅에서 출발하면 먼지가 인다

    def do(self, dt):
        p = self.p
        p.dash_window = config.DASH_ATTACK_WINDOW      # 대시하는 동안은 계속 대시 평타를 칠 수 있다
        p.vx = p.dash_vec[0] * config.DASH_SPEED
        p.vy = p.dash_vec[1] * config.DASH_SPEED
        p.dash_left -= dt

    def check(self):
        p = self.p
        if p.dash_left <= 0:
            p.vx = 0.0
            p.vy = 0.0
            ox, oy = p.dash_origin
            cx, cy = p.center
            p.last_dash_path = (ox, oy, cx, cy)        # 지나온 직선
            if p.armed_dash == p.dash_count:           # 대시 중에 대시 공격을 걸었다: 지나온 자리에 붉은 궤적 (대시 v2)
                import weapon
                game_world.add_object(weapon.DashStreak(p.last_dash_path, color=effects.zone_glow(p)), game_world.LAYER_EFFECT)
            p.dash_end()
            import mutations
            mutations.on_dash_end(p)                   # 변이 '포자 폭발'
            if p.dash_strike_queued:                   # 대시 중에 눌러 둔 평타: 지나온 경로를 한 번에 벤다
                p.dash_strike_queued = False
                p.weapon.resolve_dash_strike(p.dash_strike_enhanced)


class Hit(_State):
    def enter(self):
        self.p.hit_left = config.HIT_STUN

    def do(self, dt):
        p = self.p
        k = max(0.0, p.hit_left / config.HIT_STUN)        # 넉백: 경직이 끝날수록 줄어 멈춘다 (v7 무게감)
        p.vx = p.knock_vx * k
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
        self.max_hp = config.PLAYER_HP
        self.hp = self.max_hp
        # 이번 판 동안 아이템·업그레이드로 얻는 보너스 (죽으면 처음부터이므로 Player와 함께 사라진다)
        self.attack_bonus = 1.0        # 공격력 배율
        self.kill_bonus = 0            # 처치 시 게이지 추가 상승
        self.overload_mult = 1.0       # 오버로드 피해 배율
        self.dash_recharge = config.DASH_RECHARGE   # 대시 한 칸 충전 시간 (은신처 정비사 강화로 줄어든다)
        self.run_rooms = 0             # 이번 판에 클리어한 방 수 (판이 끝날 때 헤이즈 결정 보상)
        self.run_ends = 0              # 이번 판에 깬 보스·관문 수
        self.run_rewarded = False      # 이번 판 보상을 이미 받았는가
        self.death_cause = ''          # 쓰러진 원인 (사망 화면, killers)
        self.last_hit_by = ''
        self.attack_buffer_left = 0.0  # 미리 누른 공격·대시를 기억하는 남은 시간 (config.INPUT_BUFFER)
        self.dash_buffer_left = 0.0
        self.dash_age = 99.0           # 대시를 시작하고 지난 시간 (저스트 대시)
        self.just_used = False         # 이번 대시에서 저스트 대시를 이미 했는가
        self.just_dashes = 0           # 이번 판의 저스트 대시 수
        self.run_kills = 0             # 이번 판에 쓰러뜨린 적 수 (사망·탈출 화면의 판 기록, 계획 4-2)
        self.run_clock = 0.0           # 이번 판에 구역 안에서 보낸 시간(초, 은신처 제외)
        self.items = []                # 가진 아이템 id 목록
        self.mutations = []            # 이번 판의 헤이즈 변이 (mutations, 방을 깨고 셋 중 하나를 고른다)
        self.bonus_crystals = 0        # 방 보상으로 얻은 헤이즈 결정 (판이 끝날 때 meta에 더한다)
        self.aura_time = 0.0           # 오라 반복 재생 시간
        self.move_dist = 0.0           # 땅 위에서 달린 거리(px). 달리기·뒷걸음 프레임이 이 거리에 비례해 넘어간다 (멈추면 0)
        self.was_moving = False        # 지난 프레임에 땅 위에서 움직였는가 (출발·멈춤 판정)
        self.prev_face = 1
        self.run_time = 0.0            # 조준 쪽으로 계속 달린 시간 (멈춤 자세를 보일지)
        self.start_left = self.stop_left = self.turn_left = 0.0   # 출발·멈춤·방향 전환 자세가 남은 시간
        self.turn_face = 1             # 방향 전환 자세를 그릴 때 쓰는 원래 보던 쪽
        self.swing_left = 0.0          # 공격 자세 남은 시간 (철파이프를 든 3프레임)
        self.swing_total = config.SWING_TIME
        self.dead_time = 0.0           # 사망 후 지난 시간 (쓰러지는 프레임 재생용)
        self.swing_dir = 'side'        # 공격 자세 방향: side / up / down / upfwd / downfwd
        self.swing_style = 1           # 연타 몇 번째 모양인가 (1·2·3, config.SWING_STYLE_TIME)
        self.swing_anim = None         # v7 공격 v3: 이번 휘두르기 전용 그림 세트 (없으면 n09_swing_<방향>)
        self.air_combo = 0             # 이번 체공에서 친 공중 공격 수 (1타 가로 -> 2타 반원, 땅에 닿으면 0)
        self.lunge_vx = 0.0            # 휘두를 때 한 발 내딛는 속도 (빠르게 줄어든다)
        self.swap_cool = 0.0           # v8 교체기 쿨다운 (0이면 바꾸는 순간 기술이 나간다)
        self.forms = set()             # v8 무기 형태: 새 형태를 얻은 무기 이름들 (판 동안 유지, src/forms.py)
        self.swing_connected = False
        self._was_stunned = False      # 지난 프레임에 기절 중이었나 (회복하는 순간을 알아챈다)
        self.mouse_screen = None       # 마우스의 화면 좌표. 카메라가 움직여도 같은 곳을 겨누도록 월드 좌표를 매 프레임 다시 구한다

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
        self.knock_vx = 0.0          # 피격 넉백 속도 (Hit 상태가 쓴다)
        self.potions = config.POTION_START   # v7 물약 (Q)
        self.potion_cool = 0.0
        self.hang_left = 0.0         # v7 증강 '체공' 남은 시간
        self.no_death = False        # 연습장: 맞아도 체력 1에서 멈춘다
        self.absorb_glow = 0.0       # v7 흡수 입자가 닿은 뒤 몸이 빛나는 남은 시간 (effects.AbsorbOrb)
        self.steady_left = 0.0           # 이 시간 동안의 무적은 깜빡이지 않는다 (궁극기 시전: 몸이 보여야 한다)

        self.afterimages = []            # 대시 잔상: [x, y, face_dir, 남은 수명, (그림 세트, 번호)]
        self.afterimage_timer = 0.0

        self.drop_timer = 0.0
        self.hit_left = 0.0
        self.gauge = HazeGauge()
        self.gauge.listeners.append(self._on_gauge_event)
        self.weapon = Pipe(self)         # 지금 든 무기
        self.weapons = [self.weapon, None]   # 장착 2칸: 철파이프 + 황금방에서 얻는 무기 하나 (Q·1·2로 바꾼다)
        self.slot = 0
        self.punch_left = 0.0            # 맨손 자세(던지기·건틀릿 발사) 남은 시간
        self.ult_pose_left = 0.0         # 궁극기 시전 자세 남은 시간 (모으기 -> 해방)
        self.punch_total = 0.3
        self.punch_kind = 'throw'
        self.attack_held = False         # 좌클릭을 누르고 있으면 쿨타임마다 이어서 친다
        self.interact_pressed = False    # F를 눌렀다 (stage가 이번 프레임에 소비한다)
        self.dash_window = 0.0           # 대시 중이거나 막 끝난 뒤 남은 시간: 이 동안 공격하면 대시 평타
        self.dash_origin = (x, y)        # 이번 대시를 시작한 몸 중심
        self.last_dash_path = None       # 마지막 대시가 지나온 직선 (x0, y0, x1, y1). 대시 평타가 이 경로를 벤다
        self.dash_strike_queued = False  # 대시 중에 평타를 눌렀다: 대시가 끝나면 지나온 경로를 벤다
        self.dash_strike_enhanced = False
        self.motion_lock = 0.0           # 이 시간 동안 입력·중력으로 움직이지 않는다 (철파이프 궁극기 순간이동 베기)
        self.dash_count = 0              # 대시 v2: 지금까지 한 대시 수 (한 대시에 대시 공격 표식은 한 번)
        self.armed_dash = -1             # 대시 공격을 건 대시 번호
        self.dash_attack_left = 0.0      # 이 시간 동안의 적중이 대시 공격(표식·대시 회복)이다
        self.dash_marked = set()         # 이번 대시 공격으로 표식을 받은 적
        self.dash_refunded = False       # 이번 대시 공격으로 대시를 돌려받았나
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
        import mutations
        return mutations.speed_mult(self, self.gauge.zone_multipliers()['speed'])

    def kill_gain(self, enhanced=False):
        """적을 쓰러뜨렸을 때 오르는 게이지 (기본 + 아이템 + 변이)."""
        import mutations
        return config.GAIN_KILL + self.kill_bonus + mutations.kill_extra(self, enhanced)

    def aim_vector(self):
        """몸 중심에서 마우스까지 단위 벡터. 거의 겹치면 보는 방향."""
        cx, cy = self.x, self.y + config.PLAYER_HB_H / 2
        dx, dy = self.mouse_x - cx, self.mouse_y - cy
        length = math.hypot(dx, dy)
        if length < 1.0:
            return (float(self.face_dir), 0.0)
        return (dx / length, dy / length)

    def tick_run_clock(self, dt, stage_name):
        """판 기록의 시간: 은신처 밖에서만 센다."""
        if stage_name not in ('hideout', 'practice'):
            self.run_clock += dt

    def release_inputs(self):
        """누르고 있던 이동·아래·공격을 모두 뗀 것으로 한다. 다른 화면(증강 선택·NPC·일시정지)이 위에 뜨면 키를 떼는 신호가
        그 화면으로 가서 여기에 닿지 않는다: 그대로 두면 화면이 닫힌 뒤에도 그쪽으로 계속 걸어간다 (2026-11-25 사용자 보고)."""
        self.left = self.right = self.down = False
        self.attack_held = False

    def sync_inputs(self, pressed=None, mouse_left=None):
        """다른 화면이 닫혔다: 실제로 지금 눌려 있는 키만 다시 누른 것으로 한다 (누른 채 돌아오면 그대로 걷는다).
        pressed(키) -> 눌렸는가, mouse_left = 마우스 왼쪽이 눌렸는가. 주지 않으면 SDL에서 읽는다 (읽지 못하면 모두 뗀 것으로)."""
        import keybinds
        if pressed is None or mouse_left is None:
            try:
                import ctypes

                import sdl2
                state = sdl2.SDL_GetKeyboardState(None)
                if pressed is None:
                    def pressed(key):
                        return bool(state[sdl2.SDL_GetScancodeFromKey(int(key))])
                if mouse_left is None:
                    x, y = ctypes.c_int(0), ctypes.c_int(0)
                    mouse_left = bool(sdl2.SDL_GetMouseState(ctypes.byref(x), ctypes.byref(y)) & sdl2.SDL_BUTTON_LMASK)
            except Exception:
                self.release_inputs()
                return
        try:                                                 # 비어 있는 둘째 키 칸(None)은 건너뛴다 (2026-11-25: 여기서 튕겼다)
            held = {a: any(k is not None and pressed(k) for k in keybinds.keys(a)) for a in ('left', 'right', 'down')}
        except Exception:
            self.release_inputs()
            return
        for action, down in held.items():
            setattr(self, action, down)
        self.attack_held = bool(mouse_left)

    def handle_event(self, event):
        from pico2d import (SDL_BUTTON_LEFT, SDL_BUTTON_RIGHT, SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEBUTTONDOWN,
                            SDL_MOUSEBUTTONUP, SDL_MOUSEMOTION, get_canvas_height)
        import keybinds
        if event.type in (SDL_KEYDOWN, SDL_KEYUP):
            action = keybinds.action_for(event.key)          # 키 설정(설정 > 키 바꾸기)을 따른다
            down = event.type == SDL_KEYDOWN
            if action in ('left', 'right', 'down'):
                setattr(self, action, down)
            elif action == 'jump':
                self.request_jump() if down else self.release_jump()
            elif not down:
                pass
            elif action == 'dash':
                self.request_dash()
            elif action == 'enhance':
                self.request_enhance()
            elif action == 'interact':
                self.interact_pressed = True   # 진열대 앞에서 상호작용: stage가 처리한다
            elif action == 'swap':
                self.swap_weapon(strike=True)
            elif action == 'potion':
                self.drink_potion()
            elif action in ('weapon1', 'weapon2'):
                self.swap_weapon(0 if action == 'weapon1' else 1, strike=True)
        elif event.type == SDL_MOUSEMOTION:
            self.mouse_screen = (event.x, get_canvas_height() - 1 - event.y)
            self._sync_mouse()
        elif event.type == SDL_MOUSEBUTTONDOWN:
            self.mouse_screen = (event.x, get_canvas_height() - 1 - event.y)
            self._sync_mouse()
            if event.button == SDL_BUTTON_RIGHT:
                self.request_dash()
            elif event.button == SDL_BUTTON_LEFT:
                self.attack_held = True
                self.request_attack()
        elif event.type == SDL_MOUSEBUTTONUP:
            if event.button == SDL_BUTTON_LEFT:
                self.attack_held = False

    def _sync_mouse(self):
        """화면 좌표의 마우스를 월드 좌표로 바꾼다 (카메라가 방을 따라 움직이므로 매 프레임 다시 구한다)."""
        if self.mouse_screen is not None:
            self.mouse_x, self.mouse_y = camera.to_world(*self.mouse_screen)

    def on_landing(self):
        """땅에 닿았을 때: 충분히 높은 곳에서 떨어졌으면 착지 소리를 낸다."""
        if self.air_time > 0.25:
            assets.play_sound('land')
            effects.spawn('dust-land', self.x, self.y, duration=0.3)     # 착지 먼지
        self.air_time = 0.0
        if getattr(self, 'bolt_armed', False):                          # v7 진화 '낙뢰 내려찍기'
            self.bolt_armed = False
            import mutations
            mutations.on_plunge_land(self)

    def request_enhance(self):
        """E: 게이지를 쓰고 무기를 잠시 강화한다. 게이지가 모자라거나 이미 강화 중이면 아무 일도 없다."""
        if self.state in ('HIT', 'DEAD') or self.stunned:
            return False
        if not self.gauge.use_enhance():
            return False
        assets.play_sound(f'enhance_{max(1, min(3, self.gauge.enhance_level))}')   # v7: 단계마다 더 크고 무겁게
        effects.spawn('surge', self.x, self.y, duration=0.5)       # 발밑에서 기운이 솟는다
        effects.add_trauma(0.25)
        return True

    def request_attack(self):
        """공격. 지금 못 치면(재충전·경직) INPUT_BUFFER초 동안 기억했다가 칠 수 있게 되는 순간 친다."""
        if self._try_attack():
            self.attack_buffer_left = 0.0
            return True
        if self.state != 'DEAD':
            self.attack_buffer_left = config.INPUT_BUFFER
        return False

    def _try_attack(self):
        if self.state in ('HIT', 'DEAD') or self.stunned:   # 대시 중에는 대시 평타를 칠 수 있다
            return False
        dash = self.state == 'DASH' or self.dash_window > 0
        saved = (self.armed_dash, self.dash_attack_left, self.dash_marked, self.dash_refunded)
        if dash:
            self.arm_dash_attack()                       # 먼저 건다: 철파이프는 누르는 순간 벨 수 있다
        ok = self.weapon.try_attack()
        if dash and (not ok or self.ult_pose_left >= config.ULT_POSE_TIME - 1e-6):   # 못 쳤거나 궁극기: 되돌린다
            self.armed_dash, self.dash_attack_left, self.dash_marked, self.dash_refunded = saved
        return ok

    def arm_dash_attack(self):
        """대시 공격이 나갔다 (무기 4종 공통, 대시 v2): 잠깐 동안의 적중이 표식을 남기고 대시를 돌려준다. 한 대시에 한 번."""
        if self.armed_dash == self.dash_count:
            return
        self.armed_dash = self.dash_count
        self.dash_attack_left = config.DASH_MARK_WINDOW
        self.dash_marked = set()
        self.dash_refunded = False
        if self.state != 'DASH' and self.last_dash_path is not None:   # 대시 직후: 지나온 자리에 붉은 궤적
            import weapon
            game_world.add_object(weapon.DashStreak(self.last_dash_path, color=effects.zone_glow(self)), game_world.LAYER_EFFECT)

    # ----- 무기 -----
    def has_weapon(self, weapon_id):
        return any(w is not None and w.weapon_id == weapon_id for w in self.weapons)

    def give_weapon(self, weapon_id, slot=None):
        """무기를 얻어 바로 든다 (v8 두 칸 자유). 이미 가진 무기면 그것을 들 뿐이다. 빈 칸이 있으면 거기에 넣고,
        두 칸이 다 찼으면 **들고 있지 않은** 칸의 무기와 바꾼다 (남길 무기를 들고 주우면 된다). slot을 주면 그 칸에 넣는다."""
        from weapon import WEAPONS
        for i, w in enumerate(self.weapons):
            if w is not None and w.weapon_id == weapon_id:
                self.swap_weapon(i)
                return i
        if slot is None:
            slot = 1 if self.weapons[1] is None else 0 if self.weapons[0] is None else 1 - self.slot
        if slot == self.slot and hasattr(self.weapon, 'on_put_away'):
            self.weapon.on_put_away()                # 들고 있던 무기를 바꾼다: 충전·돌진을 끊는다
        self.weapons[slot] = WEAPONS[weapon_id](self)
        if slot == self.slot:
            self.weapon = self.weapons[slot]
            assets.play_sound('pickup')
        else:
            self.swap_weapon(slot)
        return slot

    def set_loadout(self, first, second=None):
        """두 칸을 통째로 정한다 (판 시작, 은신처 무기 걸이). 둘째 칸이 있으면 그것을, 없으면 첫 칸을 든다."""
        from weapon import WEAPONS
        if hasattr(self.weapon, 'on_put_away'):
            self.weapon.on_put_away()
        self.weapons = [WEAPONS[first](self), WEAPONS[second](self) if second and second != first else None]
        self.slot = 1 if self.weapons[1] is not None else 0
        self.weapon = self.weapons[self.slot]

    def drink_potion(self):
        """물약을 마신다 (Q). 체력 POTION_HEAL 회복. 마셨으면 True."""
        if (self.state == 'DEAD' or self.potions <= 0 or self.potion_cool > 0 or self.hp >= self.max_hp):
            if self.potions <= 0 and self.state != 'DEAD':
                assets.play_sound('ui_move')                  # 빈 병: 작은 소리만
            return False
        self.potions -= 1
        self.potion_cool = config.POTION_COOLDOWN
        healed = min(self.max_hp, self.hp + config.POTION_HEAL) - self.hp
        self.hp += healed
        assets.play_sound('enhance')
        cx, cy = self.center
        effects.spawn_bloom(cx, cy, (120, 255, 170), big=True, life=0.35, strength=0.6)
        effects.float_text(cx, cy + 90, f'+{int(healed)}', (130, 255, 170), big=True)
        return True

    def swap_weapon(self, index=None, strike=False):
        """Q: 다른 칸으로, 1·2: 그 칸으로. 빈 칸이면 바꾸지 않는다. 건틀릿 충전은 풀린다.
        strike=True(플레이어가 직접 바꿈)면 들어오는 무기의 교체기가 나간다 (v8, combo.swap_strike. 쿨 중이면 그냥 바뀐다)."""
        if index is None:
            index = 1 - self.slot
        if self.weapons[index] is None or index == self.slot and self.weapon is self.weapons[index]:
            return False
        if hasattr(self.weapon, 'on_put_away'):
            self.weapon.on_put_away()                    # 건틀릿: 충전·돌진을 끊는다
        self.slot = index
        self.weapon = self.weapons[index]
        assets.play_sound('pickup')
        if strike:
            import combo
            combo.swap_strike(self)
        return True

    def start_punch(self, kind):
        """맨손 자세: 던지기(throw)·건틀릿 발사(blast). 휘두르기 자세는 끝낸다."""
        self.punch_kind = kind
        self.punch_total = self.punch_left = config.PUNCH_TIME[kind]
        self.swing_left = 0.0

    def release_jump(self):
        """점프 키를 뗐다: 아직 올라가는 중이면 상승을 줄여 낮게 뛴다 (최고 높이는 끝까지 누를 때만)."""
        if self.state == 'JUMP' and self.vy > 0:
            self.vy *= config.JUMP_CUT

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
        """대시. 지금 못 하면(대시 중·경직·칸 없음) INPUT_BUFFER초 동안 기억했다가 할 수 있게 되는 순간 한다."""
        if self._try_dash():
            self.dash_buffer_left = 0.0
        elif self.state != 'DEAD':
            self.dash_buffer_left = config.INPUT_BUFFER

    def _try_dash(self):
        if self.state in ('DASH', 'HIT', 'DEAD') or self.stunned or self.dash_slots <= 0:
            return False
        self.dash()
        return True

    def take_hit(self, damage=0, gauge_delta=0, source=None):
        """피격. 대시 무적과 피격 직후 무적 중에는 무시한다. 맞으면 게이지가 줄고(LOSS_DAMAGED),
        적 종류별 추가 변화(gauge_delta, 예: 간수 +15)도 받는다."""
        if self.state == 'DEAD':
            return
        if self.invuln_left > 0:
            self.try_just_dash()
            return
        import options
        if options.test_mode:                                # v7 테스트 모드: 무적 (흔들림만)
            effects.add_trauma(config.SHAKE_DAMAGED * 0.5)
            return
        import mutations
        damage = round(damage * mutations.taken_mult(self))     # 변이 '그을린 피부'
        self.hp = max(0, self.hp - damage)
        if self.no_death and self.hp <= 0:                   # 연습장: 쓰러지지 않는다
            self.hp = 1
        import killers
        self.last_hit_by = killers.describe(source)          # 사망 화면의 '쓰러진 원인' (11/22)
        self.gauge.add(config.LOSS_DAMAGED + gauge_delta, 'damaged')
        if self.hp <= 0:
            self.death_cause = self.last_hit_by
            self.die()
        elif self.state != 'DEAD':
            assets.play_sound('hit')
            self.invuln_left = config.HIT_INVULN
            sx = getattr(source, 'x', None)                  # 때린 쪽 반대로 밀린다 (위치를 모르면 보는 쪽 뒤로)
            away = (1 if self.x >= sx else -1) if sx is not None else -self.face_dir
            self.knock_vx = away * config.PLAYER_KNOCK_VX
            if self.on_ground:
                self.vy = config.PLAYER_KNOCK_VY
            self.hit()
        effects.add_trauma(config.SHAKE_DAMAGED)
        effects.request_hit_stop(config.HIT_STOP_DAMAGED)

    def hit_test(self, box, source=None):
        """공격 판정 box가 몸에 닿아 맞는가. 무적이면 맞지 않지만, 막 대시한 참이면 저스트 대시가 된다."""
        if self.state == 'DEAD' or not _overlap(box, self.rect()):
            return False
        if self.invuln_left > 0:
            self.try_just_dash()
            return False
        return True

    def try_just_dash(self):
        """대시를 시작하고 JUST_WINDOW 안에 공격이 닿았다: 슬로 모션, 게이지, 대시 한 칸 (대시 한 번에 한 번)."""
        if self.just_used or self.dash_age > config.JUST_WINDOW:
            return False
        self.just_used = True
        self.just_dashes += 1
        self.gauge.add(config.JUST_GAIN, 'just')
        self.dash_slots = min(self.dash_max, self.dash_slots + 1)
        effects.request_slow_motion(*config.JUST_SLOW)
        effects.request_flash(0.12)
        cx, cy = self.center
        effects.spawn('surge', self.x, self.y, duration=0.4)
        effects.float_text(cx, cy + 90, '저스트!', (150, 245, 255), big=True, life=0.8)
        assets.play_sound('zone_awake')
        import mutations
        mutations.on_just_dash(self)                    # v7 쌍권총 '장전 회피'
        return True

    def _on_gauge_event(self, name, gauge):
        if name == 'overload':
            # 11/24 사용자: 기운이 모이며 어두워졌다가 팡 터지고, 빛·블러와 함께 공간이 일렁인다 (effects.OverloadPop)
            game_world.add_object(effects.OverloadPop(self), game_world.LAYER_EFFECT)
            # 오버로드: 최대 체력의 일부 피해 (기절은 게이지가 stun_timer로 건다)
            import mutations
            mutations.on_overload(self)                                   # 변이 '불씨 폭주'
            self.hp = max(0, self.hp - int(self.max_hp * config.OVERLOAD_DAMAGE_RATIO * self.overload_mult
                                           * mutations.overload_mult(self)))
            if self.hp <= 0 and self.state != 'DEAD':
                import killers
                self.death_cause = killers.OVERLOAD
                self.die()
        if name.startswith('zone:'):
            import drama
            drama.on_zone(name[5:])                                     # 구간 색으로 화면이 잠깐 번쩍 (각성은 zone_awake 소리)
        if name in ('zone:AWAKE', 'zone:CRITICAL'):
            effects.spawn('surge', self.x, self.y, duration=0.45)      # 높은 구간에 들어서는 순간 발밑에서 기운이 솟는다
            effects.add_trauma(0.15)
            if name == 'zone:CRITICAL':
                assets.play_sound('warn_high')                         # 곧 폭발한다는 경고음
        elif name == 'zone:FADE':
            assets.play_sound('warn_low')                              # 게이지가 바닥나 간다는 경고음 (0%면 사망)

    # ----- 갱신 -----
    def update(self, dt):
        self.dash_age += dt
        self._recharge_dash(dt)
        self._sync_mouse()
        self.aura_time += dt
        self.swing_left = max(0.0, self.swing_left - dt)
        self.absorb_glow = max(0.0, self.absorb_glow - dt)
        self.punch_left = max(0.0, self.punch_left - dt)
        self.ult_pose_left = max(0.0, self.ult_pose_left - dt)
        self.potion_cool = max(0.0, self.potion_cool - dt)
        self.swap_cool = max(0.0, self.swap_cool - dt)       # v8 교체기 쿨다운
        import options
        if (options.test_mode or self.no_death) and self.state != 'DEAD':   # 테스트 모드·연습장: 게이지가 사망·오버로드에 닿지 않게
            self.gauge.value = min(max(self.gauge.value, 5.0), self.gauge.cap - 1.0)
        self.dead_time = self.dead_time + dt if self.state == 'DEAD' else 0.0
        if self.state == 'RUN' and self.on_ground:
            self.move_dist += abs(self.vx) * dt
        else:
            self.move_dist = 0.0
        if self._was_stunned and not self.stunned and self.state != 'DEAD':   # 기절에서 깨어나는 순간
            effects.spawn('puff', self.x, self.y + 40, duration=0.45)
            effects.add_trauma(0.2)
            assets.play_sound('stun_end')
        self._was_stunned = self.stunned
        self.drop_timer = max(0.0, self.drop_timer - dt)
        self.weapon.update(dt)
        if self.state != 'DASH':
            self.dash_window = max(0.0, self.dash_window - dt)
        self.coyote_left = config.COYOTE_TIME if self.on_ground else max(0.0, self.coyote_left - dt)
        self.jump_buffer_left = max(0.0, self.jump_buffer_left - dt)
        if self.attack_held:
            self.request_attack()
        elif self.attack_buffer_left > 0:                   # 미리 누른 공격 (11/22)
            self.attack_buffer_left = 0.0 if self._try_attack() else self.attack_buffer_left - dt
        if self.dash_buffer_left > 0:                       # 미리 누른 대시
            self.dash_buffer_left = 0.0 if self._try_dash() else self.dash_buffer_left - dt
        self.invuln_left = max(0.0, self.invuln_left - dt)
        self.dash_attack_left = max(0.0, self.dash_attack_left - dt)
        self.motion_lock = max(0.0, self.motion_lock - dt)
        self.steady_left = max(0.0, self.steady_left - dt)
        if self.gauge.zone == DEAD and self.state != 'DEAD':
            import killers
            self.death_cause = killers.GAUGE_EMPTY               # 게이지가 바닥나 쓰러짐
            self.die()

        state = self.states[self.state]
        state.do(dt)
        self._apply_swing_motion(dt)
        self.hang_left = max(0.0, self.hang_left - dt)
        if state.gravity and self.hang_left <= 0:                    # v7 '체공': 공중에서 맞힌 직후 잠깐 떨어지지 않는다
            self.vy = max(self.vy - config.GRAVITY * dt, -config.MAX_FALL_SPEED)
        self.move_with_tiles(dt)
        self._check_spikes()
        self.states[self.state].check()
        if self.jump_buffer_left > 0 and self.state in ('IDLE', 'RUN'):
            self.jump_buffer_left = 0.0  # 착지하자마자 눌러 둔 점프
            self.request_jump()
        self._update_afterimages(dt)

        # 조준 방향이 보는 방향 (조준이 거의 수직이면 이동 방향)
        if abs(self.mouse_x - self.x) > 4:
            self.face_dir = 1 if self.mouse_x > self.x else -1
        self._update_move_anim(dt)

    def _update_move_anim(self, dt):
        """출발·멈춤·방향 전환 자세의 시간을 잰다. 그림만 바뀌고 속도는 그대로다 (가속·감속 없음)."""
        self.start_left = max(0.0, self.start_left - dt)
        self.stop_left = max(0.0, self.stop_left - dt)
        self.turn_left = max(0.0, self.turn_left - dt)
        moving = self.state == 'RUN' and self.on_ground         # 키를 누른 첫 프레임은 속도가 아직 0이라 상태로 본다
        forward = moving and self._move_sign() == self.face_dir
        if moving and self.was_moving and self.face_dir != self.prev_face:   # 달리다가 조준이 뒤로 넘어갔다
            self.turn_left, self.turn_face = config.RUN_TURN_TIME, self.prev_face
            self.start_left = 0.0
        elif moving and not self.was_moving and forward:           # 서 있다가 조준 쪽으로 달리기 시작
            self.start_left = config.RUN_START_TIME
        if moving:
            self.stop_left = 0.0
        else:
            self.start_left = 0.0
            if self.was_moving and self.state == 'IDLE' and self.on_ground and self.run_time >= config.RUN_STOP_MIN_RUN:
                self.stop_left = config.RUN_STOP_TIME                  # 충분히 달리다 멈췄다: 제동 자세
        self.run_time = self.run_time + dt if forward else 0.0
        self.prev_face = self.face_dir
        self.was_moving = moving

    def _move_sign(self):
        """움직이는 방향 (+1 오른쪽, -1 왼쪽): 누른 키, 없으면 속도."""
        return self.direction or (1 if self.vx >= 0 else -1)

    def draw_face(self):
        """그릴 때 쓰는 좌우 방향. 방향 전환 자세는 원래 보던 쪽 그대로 그린다(그림이 몸을 뒤로 트는 자세라서)."""
        return self.turn_face if self.turn_left > 0 else self.face_dir

    def _apply_swing_motion(self, dt):
        """땅 위에서 휘두르는 동안은 거의 멈추고, 조준 쪽으로 한 발 내딛는다 (선 자세로 미끄러지는 것을 막는다)."""
        if self.on_ground:
            self.air_combo = 0
        if self.motion_lock > 0:                                    # 궁극기 순간이동 베기: 제자리에 뜬 채
            self.vx = self.vy = 0.0
            self.hang_left = max(self.hang_left, dt * 1.5)
            return
        rush = self.weapon.rush_velocity() if hasattr(self.weapon, 'rush_velocity') else None
        if rush is not None:                                        # 건틀릿 돌진 강타: 곧게 날아간다 (땅 위 수평이면 바닥을 따라)
            self.vx = rush[0]
            if rush[1] is not None:
                self.vy = rush[1]
                self.hang_left = max(self.hang_left, dt * 1.5)          # 비스듬한·공중 돌진은 중력 없이 곧게
            return
        if self.lunge_vx:
            self.lunge_vx *= max(0.0, 1.0 - config.SWING_LUNGE_DECAY * dt)
            if abs(self.lunge_vx) < 5:
                self.lunge_vx = 0.0
        if (self.swing_left > 0 and self.on_ground and self.state in ('IDLE', 'RUN') and self.swing_dir != 'plunge'
                and self.swing_anim != 'n09_dashcut'):                 # 대시 평타는 흐름을 끊지 않는다
            self.vx = self.vx * config.SWING_MOVE_MULT + self.lunge_vx
        elif self.on_ground and self.state in ('IDLE', 'RUN'):
            if getattr(self.weapon, 'charging', False):           # 건틀릿 충전 중에는 천천히 걷는다
                self.vx *= config.GAUNTLET_CHARGE_MOVE
            self.vx += self.lunge_vx                                # 건틀릿 발사 반동

    def _check_spikes(self):
        """가시 타일에 닿으면 피해를 받고 위로 튕긴다. 대시 무적·피격 직후 무적 중에는 그냥 지나간다."""
        if self.state == 'DEAD' or self.invuln_left > 0 or self.room is None:
            return
        me = self.rect()
        for rect in self.room.spike_rects():
            if me[0] < rect[2] and rect[0] < me[2] and me[1] < rect[3] and rect[1] < me[3]:
                before = self.hp
                self.take_hit(config.SPIKE_DAMAGE, source='spike')
                if self.hp < before and self.state != 'DEAD':
                    self.vy = config.SPIKE_BOUNCE   # 가시에 찔려 튕겨 오른다
                    self.on_ground = False
                return

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
            self.afterimages.append([self.x, self.y, self.face_dir, config.AFTERIMAGE_LIFE, self._body_frame()])

    def _recharge_dash(self, dt):
        if self.dash_slots >= self.dash_max:
            self.dash_charge = 0.0
            return
        self.dash_charge += dt
        import mutations
        need = mutations.dash_recharge_time(self)        # v8: 페이드 '빈 몸'은 그 구간에서만 줄인다
        if self.dash_charge >= need:
            self.dash_charge -= need
            self.dash_slots += 1

    # ----- 그리기 -----
    def start_swing(self, ax, ay):
        """공격 자세를 시작한다. 조준 y 성분으로 위·앞 위·수평·앞 아래·아래 중 가까운 방향을 고른다 (좌우는 반전으로 처리)."""
        if ay > 0.85:
            self.swing_dir = 'up'
        elif ay > 0.35:
            self.swing_dir = 'upfwd'
        elif ay < -0.85:
            self.swing_dir = 'down'
        elif ay < -0.35:
            self.swing_dir = 'downfwd'
        else:
            self.swing_dir = 'side'
        self.swing_style = 1
        self.swing_anim = None
        self.swing_connected = False   # 이번 휘두르기가 적을 맞혔는가 (weapon._hit이 켠다)
        self.swing_total = config.SWING_TIME
        self.swing_left = config.SWING_TIME
        self.lunge_vx = 0.0

    def set_swing_style(self, style, ax):
        """연타 몇 번째인지에 따라 자세 시간과 내딛기를 바꾼다. 위·아래로 똑바로 휘두를 때는 내딛지 않는다."""
        self.swing_style = style
        self.swing_total = self.swing_left = config.SWING_STYLE_TIME[style]
        if self.swing_dir == 'side' and style in (2, 3):     # 공격 v3: 2타 사선 반원, 3타 올려베기
            self.swing_anim = f'n09_swing_side{style}'
        forward = self.swing_dir in ('side', 'upfwd', 'downfwd') and abs(ax) > 0.2
        self.lunge_vx = (1 if ax > 0 else -1) * config.SWING_LUNGE[style] if forward and self.on_ground else 0.0

    def start_air_swing(self, ax, ay):
        """공중 공격 자세 (공격 v3): 위로 겨누면 올려베기, 아니면 이번 체공의 1타 가로 베기 -> 2타 반원을 번갈아.
        고른 그림 세트 이름을 돌려준다 (이펙트 모양을 맞추는 데 쓴다)."""
        self.start_swing(ax, ay)
        if ay > 0.6:
            anim = 'n09_airup'
        else:
            self.air_combo += 1
            anim = 'n09_air1' if self.air_combo % 2 == 1 else 'n09_air2'
        self.swing_anim = anim
        self.swing_total = self.swing_left = config.AIR_SWING_TIME
        return anim

    def start_dash_cut(self):
        """대시 평타 자세 (공격 v3): 낮은 돌진 가로 베기. 몸 이동은 늦추지 않는다."""
        self.swing_dir = 'side'
        self.swing_style = 1
        self.swing_anim = 'n09_dashcut'
        self.swing_connected = False
        self.swing_total = self.swing_left = config.DASH_CUT_POSE_TIME

    def start_plunge_pose(self):
        """내려찍기 자세(파이프를 아래로 겨눈 두 프레임)를 보여 준다."""
        self.swing_dir = 'plunge'
        self.swing_total = config.PLUNGE_POSE_TIME
        self.swing_left = config.PLUNGE_POSE_TIME

    def _weapon_pose(self):
        """식칼·건틀릿·사슬의 전용 자세 (Codex T26). 해당 없으면 None.
        식칼: 당김 -> 뿌림 -> 흘림. 건틀릿: 충전 중 1, 발사 2 -> 회수 3, 공중에서 아래로 쏘면 4.
        사슬: 돌림 -> 던짐, 갈고리가 적을 끌어오는 동안은 두 손으로 당김(3)."""
        wid = getattr(self.weapon, 'weapon_id', '')
        if wid == 'gauntlet' and getattr(self.weapon, 'charging', False):
            return 'n09_gauntlet', 1
        hook = getattr(self.weapon, 'hook', None)
        if wid == 'chain' and hook is not None and hook.phase == 'pull':
            return 'n09_chain', 3
        if self.punch_left <= 0 or wid not in ('pistol', 'gauntlet', 'chain'):
            return None
        done = 1.0 - self.punch_left / self.punch_total
        if wid == 'pistol':                              # v7 쌍권총: 조준 방향·달리기·공중마다 다른 겨눔 자세
            return self._pistol_pose()
        if wid == 'gauntlet':
            if self.punch_kind == 'blast_down':
                return ('n09_gauntlet_airdown', 1) if 'n09_gauntlet_airdown' in sprites.SKIN else ('n09_gauntlet', 4)
            if done >= 0.45:
                return 'n09_gauntlet', 3                          # 회수
            return self._gauntlet_punch()
        if done < 0.25:
            return 'n09_chain', 1                                 # 돌리기
        return self._chain_throw() if done < 0.75 else ('n09_chain', 3)

    def _gauntlet_punch(self):
        """건틀릿 강타 자세 (2026-11-24 PixelLab): 조준 쪽으로 주먹을 뻗는다. 땅: 앞·앞 위·앞 아래, 공중: 앞·앞 위·아래."""
        ax, ay = self.aim_vector()
        up, down = ay > 0.35, ay < -0.35
        if not self.on_ground:
            if down:
                return ('n09_gauntlet_airdown', 1) if 'n09_gauntlet_airdown' in sprites.SKIN else ('n09_gauntlet', 4)
            if 'n09_gauntlet_air' in sprites.SKIN:
                return 'n09_gauntlet_air', 2 if up else 1
            return 'n09_gauntlet', 2
        name = 'n09_gauntlet_upfwd' if up else 'n09_gauntlet_downfwd' if down else None
        if name and name in sprites.SKIN:
            return name, 1
        return 'n09_gauntlet', 2

    def _chain_throw(self):
        """사슬 던지기 자세 (2026-11-24 PixelLab): 조준 쪽으로 팔을 뻗는다. 땅: 앞·앞 위·앞 아래, 공중: 앞·앞 위·아래."""
        ax, ay = self.aim_vector()
        up, down = ay > 0.35, ay < -0.35
        if not self.on_ground and 'n09_chain_air' in sprites.SKIN:
            return 'n09_chain_air', 2 if up else 3 if down else 1
        name = 'n09_chain_upfwd' if up else 'n09_chain_downfwd' if down else None
        if name and name in sprites.SKIN:
            return name, 1
        return 'n09_chain', 2

    def _pistol_pose(self):
        """쌍권총 겨눔 자세 (2026-11-24 PixelLab): 공중이면 앞·앞 위·앞 아래 3장, 앞으로 달리며 쏘면 달리며 쏘기 8장,
        서 있으면 위·앞 위·앞·앞 아래·아래 중 조준에 가까운 것. 새 그림이 없으면 앞 겨눔 한 장(없으면 맨손 뻗음)."""
        if 'n09_pistol' not in sprites.SKIN:
            return 'n09_punch', 3
        ax, ay = self.aim_vector()
        aim = 'up' if ay > 0.85 else 'upfwd' if ay > 0.35 else 'down' if ay < -0.85 else 'downfwd' if ay < -0.35 else 'side'
        if not self.on_ground and 'n09_pistol_air' in sprites.SKIN:
            return 'n09_pistol_air', {'up': 2, 'upfwd': 2, 'down': 3, 'downfwd': 3}.get(aim, 1)
        if self.state == 'RUN' and aim == 'side' and 'n09_pistol_run' in sprites.SKIN:
            count = sprites.count('n09_pistol_run')
            step = int(self.move_dist / config.RUN_FRAME_PX) % count
            return 'n09_pistol_run', (step + 1 if self._move_sign() == self.face_dir else count - step)   # 뒷걸음은 거꾸로
        name = 'n09_pistol' if aim == 'side' else 'n09_pistol_' + aim
        return (name, 1) if name in sprites.SKIN else ('n09_pistol', 1)

    def pistol_muzzle(self):
        """쌍권총 총알이 나가는 자리 (지금 겨눔 그림의 총구). 잰 값이 없으면 몸 가운데에서 조준 쪽으로."""
        name, n = self._pistol_pose()
        off = sprites.muzzle(name, n)
        if off is None:
            ax, ay = self.aim_vector()
            cx, cy = self.center
            return cx + ax * config.PISTOL_MUZZLE, cy + 8 + ay * config.PISTOL_MUZZLE
        face = 1 if self.aim_vector()[0] >= 0 else -1    # 몸은 다음 프레임에 조준 쪽을 본다 (막 돌아선 첫 발도 총구에서)
        return self.x + face * off[0], self.y + off[1]

    def _body_frame(self):
        """지금 상태에 맞는 몸 이미지 이름: 달리기 걷기 4장, 서 있기 숨쉬기 4장, 공중 점프 4장, 피격 2장. 없으면 대기 한 장."""
        if self.state == 'HIT':
            return 'n09_hurt', 1 if self.hit_left > config.HIT_STUN / 2 else 2
        if self.state == 'DEAD':
            t1, t2 = config.DEATH_FRAME_TIMES
            return 'n09_death', 1 if self.dead_time < t1 else 2 if self.dead_time < t2 else 3
        if self.state == 'DASH':
            return 'n09_dash', int(self.aura_time / config.DASH_FRAME_TIME) % 2 + 1
        if self.stunned:                                # 기절: 몸을 가누지 못하고 휘청인 자세
            return 'n09_hurt', 2
        if self.swing_left > 0 and self.swing_dir == 's2rise':     # 철파이프 2단계 올려베기 (T24): 3장을 고르게
            done = 1.0 - self.swing_left / self.swing_total
            k = sprites.count('n09_s2rise')
            return 'n09_s2rise', min(k, 1 + int(done * k))
        if self.swing_left > 0 and self.swing_dir == 's2slam':     # 내려찍기: 들고 뜸 -> 45도 -> 바닥 타격(머문다)
            t = self.swing_total - self.swing_left
            return 'n09_s2slam', 1 + sum(1 for edge in config.STAGE2_SLAM_FRAMES if t >= edge)
        if self.swing_left > 0 and self.swing_dir == 'plunge':
            return 'n09_plunge', 1 if self.swing_left > self.swing_total * 0.65 else 2
        if self.ult_pose_left > 0:                           # 궁극기 시전: 모으기 -> 해방 (T23)
            gathering = self.ult_pose_left > config.ULT_POSE_TIME - config.ULT_POSE_GATHER
            return 'n09_ult', 1 if gathering else 2
        pose = self._weapon_pose()
        if pose is not None:                                 # 무기 전용 자세 (Codex T26)
            return pose
        if getattr(self.weapon, 'charging', False):          # 건틀릿 충전: 주먹을 뒤로 당긴 채
            return 'n09_punch', 1
        if self.punch_left > 0:       # 맨손 자세: 던지기 = 당김 -> 뻗음 -> 회수, 발사 = 모음 -> 뻗음 -> 회수
            done = 1.0 - self.punch_left / self.punch_total
            first = 1 if self.punch_kind == 'throw' else 2
            return 'n09_punch', first if done < 0.2 else 3 if done < 0.7 else 4
        if self.swing_left > 0:       # 철파이프를 휘두르는 자세: 젖힘 -> 휘두르는 중 -> 타격 -> 마무리 -> 회수
            done = 1.0 - self.swing_left / self.swing_total
            phases = config.SWING_STYLE_PHASES.get(self.swing_style, config.SWING_PHASES)
            n = 1 + sum(1 for t in phases if done >= t)
            if self.swing_connected:        # 맞혔으면 타격 자세부터 (판정은 누르는 순간이라, 젖힌 채 멈추거나 멈춤 뒤 젖힘으로 되돌아가면 어색하다)
                n = max(n, 3)
            n = min(n, config.SWING_LAST_FRAME)   # 5번(회수)은 파이프를 몸 뒤로 되감는 그림이라 앞으로 친 뒤 뒤로 감기는 것처럼 보여 쓰지 않는다
            if self.swing_anim and self.swing_anim in sprites.SKIN:   # 공격 v3 전용 그림 (연타·공중·대시·강화)
                return self.swing_anim, n
            return 'n09_swing_' + self.swing_dir, n
        if not self.on_ground and self.state in ('JUMP', 'FALL'):
            if self.vy > config.JUMP_RISE_VY:
                return 'n09_jump', 2
            return ('n09_jump', 3) if self.vy > -config.JUMP_RISE_VY else ('n09_jump', 4)
        if self.state == 'RUN' and self.on_ground:
            if self.turn_left > 0:
                return 'n09_run_trans', 5                              # 방향 전환: 원래 보던 쪽으로 몸을 틀며 버팀
            if self.start_left > 0:                                    # 출발: 숙이며 디딤 -> 뒷발로 차고 나감
                return 'n09_run_trans', 1 if self.start_left > config.RUN_START_TIME / 2 else 2
            if self._move_sign() == self.face_dir:                     # 조준 쪽으로: 달리기
                return 'n09_run', int(self.move_dist / config.RUN_FRAME_PX) % sprites.count('n09_run') + 1
            count = sprites.count('n09_run')                           # 뒷걸음: 달리기를 거꾸로 (8 -> 7 -> ... -> 1)
            return 'n09_run', count - int(self.move_dist / config.RUN_FRAME_PX) % count
        if self.stop_left > 0 and self.state == 'IDLE' and self.on_ground:   # 멈춤: 몸을 젖혀 제동 -> 버티며 선다
            return 'n09_run_trans', 3 if self.stop_left > config.RUN_STOP_TIME / 2 else 4
        if self.state == 'IDLE':
            return 'n09_idle', int(self.aura_time / config.IDLE_FRAME_TIME) % sprites.count('n09_idle') + 1
        return 'n09_idle', 0

    def draw(self):
        steps = config.AFTERIMAGE_ALPHA_STEPS
        for gx, gy, gdir, left, (name, n) in self.afterimages:  # 오래된 것부터 그려 새 잔상이 위에 온다
            age = 1.0 - left / config.AFTERIMAGE_LIFE
            alpha = steps[min(int(age * len(steps)), len(steps) - 1)]
            sprites.draw_silhouette(name, n, gx, gy, gdir, config.AFTERIMAGE_COLOR, alpha)   # v7: 어두운 옷도 청록 잔상으로
        stunned = self.stunned and self.state != 'DEAD'
        if self.state != 'DEAD':   # 게이지 구간·강화·기절에 따른 몸 주위 오라 (캐릭터 뒤에 깔린다)
            for name in effects.aura_names(self.gauge.zone, self.gauge.enhanced, stunned, self.gauge.enhance_level):
                effects.draw_loop(name, self.x, self.y, self.aura_time, flip=self.draw_face() < 0)   # 몸 실루엣과 같은 쪽을 보게
        blink = (self.invuln_left > 0 and self.steady_left <= 0 and self.state not in ('DASH', 'DEAD')
                 and int(self.invuln_left * 20) % 2 == 0)
        if not blink:                                   # 피격 무적 중에는 깜빡인다
            name, n = self._body_frame()
            x, tint = self.x, None
            sprites.draw(name, n, x, self.y, self.draw_face(), tint)
            if stunned:                                 # 기절(과열, 2026-11-24 감전 연출을 대신): 몸이 붉게 달아올랐다 식기를 되풀이한다
                heat = 0.3 + 0.22 * math.sin(self.aura_time * 7.85)
                sprites.draw_silhouette(name, n, x, self.y, self.draw_face(), (255, 64, 78), heat)
            if self.absorb_glow > 0:                    # v7 흡수: 입자가 닿으면 몸이 청록·흰 빛으로 번쩍
                k = self.absorb_glow / effects.ABSORB_GLOW
                sprites.draw_silhouette(name, n, x, self.y, self.draw_face(), (190, 255, 245), 0.6 * k)
        if config.DEBUG:
            self._draw_debug()

    def _draw_debug(self):
        import assets
        from pico2d import draw_rectangle
        hw = config.PLAYER_HB_W / 2
        draw_rectangle(self.x - hw, self.y, self.x + hw, self.y + config.PLAYER_HB_H)
        draw_rectangle(self.mouse_x - 4, self.mouse_y - 4, self.mouse_x + 4, self.mouse_y + 4)
        assets.draw_text(self.x, self.y + config.PLAYER_HB_H + 27, f'{self.state} j{self.jump_count}', (255, 240, 120), small=True, center=True)


def _overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
