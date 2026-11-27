"""스테이지: 방 격자, 현재 방, 4방향 방 이동, 방 클리어(문 열림), 황금방·정비방·보스방, 미니맵 데이터.

방은 격자 좌표 (열, 행)에 놓이고 행은 위로 증가한다. 방마다 위·아래·좌·우 출입구가 있을 수 있고, 어느 문으로 나갈지는 플레이어가
고른다. 문 너머 방이 황금방·정비방·보스방이면 문 색과 이름으로 알려 준다. pico2d와 무관한 로직이라 창 없이 테스트한다.
배치 데이터는 data/stages/stage1~3.py (격자 좌표 -> 방 정의, 구역 이름 TITLE, 기본 테마 THEME).

방 종류: start(안전), combat(적을 모두 처치해야 문이 열림), gold(아이템 중 하나를 무료로), shop(조각으로 구매),
boss(보스, 쓰러뜨리면 다음 구역), gate(관문: 정예 전투, 이기면 다음 구역. 보스가 없는 스테이지 1의 끝).
구역 순서는 STAGE_ORDER. 한 구역을 끝내면 next_stage()가 같은 플레이어(체력·게이지·아이템·무기·조각 그대로)로 다음 구역을 연다.
"""
import importlib.util
import os
import random

import assets
import camera
import config
import effects
import game_world
import items
from boss import Boss
from enemy import Enemy
from pedestal import Pedestal
from room import Room

OPPOSITE = {'L': 'R', 'R': 'L', 'U': 'D', 'D': 'U'}
STEP = {'L': (-1, 0), 'R': (1, 0), 'U': (0, 1), 'D': (0, -1)}
SPECIAL_TYPES = ('gold', 'shop', 'boss', 'gate', 'rift', 'event')   # 문에 미리 알려 주는 방 종류
END_TYPES = ('boss', 'gate')                        # 클리어하면 구역이 끝나는 방
STAGE_ORDER = ('stage1', 'stage2', 'stage3')        # 기획서 2.3: 슬럼 -> 공장 -> 코어(탑)

_exit_cache = {}


def _load_module(name):
    path = os.path.join(assets.DATA_DIR, 'stages', name + '.py')
    spec = importlib.util.spec_from_file_location('stage_data_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def roll_elite(rng, stage_name):
    """적 하나가 정예인가: 수식어 이름 또는 None (구역마다 확률이 다르다, config.ELITE_CHANCE)."""
    if rng.random() >= config.ELITE_CHANCE.get(stage_name, 0.0):
        return None
    return rng.choice(sorted(config.ELITE_MODS))


def load_layout(name='stage1'):
    """data/stages/<name>.py 에서 (START, 스테이지 딕셔너리)를 읽는다."""
    module = _load_module(name)
    return module.START, getattr(module, name.upper())


def jump_to(stage, name):
    """테스트 모드 바로가기 (F6~F8): 같은 플레이어로 name 구역의 시작 방을 연다. 지금 구역의 방·적·이펙트는 치운다."""
    if stage.room is not None:
        game_world.remove_object(stage.room)
    for layer in (game_world.LAYER_TILES, game_world.LAYER_ENEMY, game_world.LAYER_EFFECT):
        for obj in list(game_world.world[layer]):
            game_world.remove_object(obj)
    nxt = Stage(stage.player, seed=stage.seed + 1, name=name)
    _copy_callbacks(stage, nxt)
    nxt.start()
    return nxt


def _copy_callbacks(old, new):
    new.on_clear, new.on_message, new.on_pickup = old.on_clear, old.on_message, old.on_pickup
    new.on_mutation, new.on_npc, new.on_practice = old.on_mutation, old.on_npc, old.on_practice


def boss_room(stage):
    """그 구역의 보스·관문 방 좌표 (없으면 None). 테스트 모드 F9."""
    return next((c for c in stage.layout if stage.type_of(c) in END_TYPES), None)


def next_stage(stage):
    """끝난 구역 다음 구역을 같은 플레이어로 연다. 마지막 구역이면 None(탈출 = 엔딩)."""
    if stage.next_name is None:
        return None
    if stage.room is not None:                       # 지난 구역의 방·적·이펙트·진열대를 치운다
        game_world.remove_object(stage.room)
    for layer in (game_world.LAYER_TILES, game_world.LAYER_ENEMY, game_world.LAYER_EFFECT):
        for obj in list(game_world.world[layer]):
            game_world.remove_object(obj)
    nxt = Stage(stage.player, seed=stage.seed + 1, name=stage.next_name)
    _copy_callbacks(stage, nxt)
    nxt.start()
    return nxt


# 판마다 전투 방이 될 수 있는 새 모양 (2026-11-21 계획 2-4). 칸에 필요한 문을 모두 가진 것만 고른다.
# 앞 셋은 좌우 문만(33x18), 뒤 셋은 사방 문(48x22). 스폰은 모두 종류 없는 E 6칸 이상이다.
COMBAT_VARIANTS = ('bridge_06', 'stairs_07', 'pillars_08', 'shaft_09', 'terrace_10', 'twin_11')
# v8 큰 방 (2026-11-25, 계획 5-3): 두 화면짜리 전투방. 무작위 새 모양(COMBAT_VARIANTS)과 따로, 구역마다 정해진 수만 넣는다.
BIG_ROOMS = ('causeway_12', 'plaza_13', 'foundry_14', 'ascent_15', 'descent_16', 'atrium_17')
_spawn_cache = {}


def template_spawn_kinds(template):
    """템플릿의 스폰 종류 목록 (위에서 아래·왼쪽에서 오른쪽, 종류 없는 E는 None)."""
    if template not in _spawn_cache:
        _spawn_cache[template] = [k for _x, _y, k in Room.load(template).enemy_spawns]
    return _spawn_cache[template]


def template_exits(template):
    """방 템플릿에 있는 출입구 방향 집합 (파일을 한 번만 읽는다)."""
    if template not in _exit_cache:
        _exit_cache[template] = set(Room.load(template).exits)
    return _exit_cache[template]


class Stage:
    def __init__(self, player, layout=None, start=None, seed=None, name='stage1'):
        self.name = name
        self.title, self.default_theme = '', 'cell'
        self.npc_spots = []
        self.seed = random.randrange(1 << 30) if seed is None else seed
        if layout is None:
            module = _load_module(name)
            start, layout = module.START, getattr(module, name.upper())
            self.title = getattr(module, 'TITLE', '')
            self.default_theme = getattr(module, 'THEME', 'cell')
            self.npc_spots = getattr(module, 'NPCS', [])
            import mapgen
            if config.PROCEDURAL_MAPS and name in mapgen.SPECS:     # v7: 매판 시드로 배치를 새로 만든다
                start, layout = mapgen.generate(name, self.seed)
        self.layout = layout
        self.player = player
        self.start_coord = start
        self.coord = start
        self.visited = set()
        self.cleared = set()
        self.sealed = set()         # v8 갈림길: 고르지 않아 닫힌 길의 방들 (문이 사라지고 황금방 조건에서도 빠진다)
        self.state = {}             # 방 좌표 -> 아이템 선택·품절 같은 진행 상태
        self.paid_rifts = set()     # 체력을 내고 들어간 균열방 (다시 들어갈 때는 내지 않는다)
        self.block_left = 0.0       # 막힌 문 안내를 너무 자주 띄우지 않게
        # v8 물결 전투: 아직 나오지 않은 물결들, 다음 물결 예고의 남은 시간(없으면 None), 이 방의 물결 수·지금 물결·무리 수·적 수
        self.waves, self.wave_timer = [], None
        self.wave_total, self.wave_index, self.wave_packs, self.wave_enemies = 1, 1, 0, 0
        self.room = None
        self.pedestals = []
        self.npcs = []              # 은신처 NPC (정비사·보관인·기록관)
        self.event = None           # v8 이벤트 방에 놓인 것 (events.Spot: 헤이즈 샘·떠돌이 죄수)
        self.devices = []           # v8 구역별 장치 (devices.py: 상자·증기 분출구·감시 레이저)
        self.challenges = set()     # v8 도전방 좌표 (구역마다 하나)
        self.challenge = None       # 지금 방의 도전: {'limit': 초, 'left': 남은 초} (도전방이 아니면 None)
        self.on_npc = None          # NPC 앞에서 F: f(npc) (play_mode가 창을 연다)
        self.on_practice = None     # 연습장에서 F: 연습 메뉴 (play_mode가 연다)
        self.boss = None
        self.finished = False       # 끝 방(보스·관문)을 클리어해 이 구역이 끝났는가
        self.finish_timer = 0.0
        self.on_clear = None        # 방을 클리어했을 때 부를 함수 (소리·글자용)
        self.on_message = None      # 화면에 띄울 짧은 글자: f(문구)
        self.on_pickup = None       # 아이템을 얻었을 때: f(아이템 id, 효과 글) (play_mode가 화면 아래 띠로 보여 준다)
        self.on_mutation = None     # 변이 보상: f([변이 id 셋]) (play_mode가 카드 창을 연다). 없으면 첫 번째를 준다
        self.templates = {c: self._pick_template(c) for c in self.layout}   # 이번 판의 방 모양
        self._place_big_rooms()
        self.rewards = {c: self._roll_reward(c) for c in self.layout if self.type_of(c) == 'combat'}   # 방 보상 (11/22)
        for c in self.rewards:                       # 11/25 증강 속도: 큰 방을 깨면 늘 증강 (오래 싸운 방의 보상)
            if self.is_big(c):
                self.rewards[c] = 'mutation'
        self._split_lane_rewards()
        self._place_challenge()
        if self.rewards:                             # v8 무기 형태: 출발 방에서 가장 가까운 전투방의 보상은 늘 형태 카드
            first = min(sorted(self.rewards), key=lambda c: abs(c[0] - start[0]) + abs(c[1] - start[1]))
            self.rewards[first] = 'form'
        # 11/25 증강 속도: 다음 구역이 있는 구역의 끝(문지기·크래셔)을 쓰러뜨리면 증강을 고른다. 마지막 구역은 탈출이라 없다
        self.end_reward = None                       # 끝 방을 깬 뒤 연출이 지나면 줄 보상 (BOSS_REWARD_DELAY)
        end = next((c for c in self.layout if self.type_of(c) in END_TYPES), None)
        if end is not None and self.name in STAGE_ORDER and self.next_name is not None:
            self.rewards[end] = 'mutation'

    def _roll_reward(self, coord):
        import mutations
        rng = random.Random(f'{self.seed}:{coord}:reward')
        kinds = list(mutations.REWARD_WEIGHTS)
        return rng.choices(kinds, [mutations.REWARD_WEIGHTS[k] for k in kinds])[0]

    def _split_lane_rewards(self):
        """v8 갈림길: 갈림 방의 두 문에 보이는 보상(두 길의 첫 방)이 같으면 긴 길 쪽을 다른 것으로 바꾼다 (보상을 보고 고르게)."""
        import mutations
        fork = next((c for c, i in self.layout.items() if i.get('fork')), None)
        if fork is None:
            return
        firsts = sorted(c for c in (self.neighbour(fork, d) for d in STEP) if c in self.rewards and self.layout[c].get('lane'))
        if len(firsts) == 2 and self.rewards[firsts[0]] == self.rewards[firsts[1]]:
            long_ = next(c for c in firsts if self.layout[c]['lane'] == 'long')
            other = [k for k in mutations.REWARD_WEIGHTS if k != self.rewards[long_]]
            self.rewards[long_] = other[random.Random(f'{self.seed}:lane').randrange(len(other))]

    def choose_lane(self, coord):
        """v8 갈림길: 한쪽 길의 방에 들어섰다 -> 다른 길은 닫힌다. 길을 닫았으면 True."""
        lane = self.layout[coord].get('lane')
        if not lane or self.sealed:
            return False
        self.sealed = {c for c, i in self.layout.items() if i.get('lane') and i['lane'] != lane}
        return bool(self.sealed)

    def _place_challenge(self):
        """v8 도전방: 구역마다 전투방 하나를 고른다 (판의 시드로). 큰 방과 출발 방 옆(형태 카드 방)은 빼고,
        되도록 갈림길 밖에서(어느 길을 골라도 만나게)."""
        if self.name not in config.CHALLENGE_ZONES:
            return
        sx, sy = self.start_coord
        spots = sorted(c for c in self.rewards if not self.is_big(c) and abs(c[0] - sx) + abs(c[1] - sy) > 1)
        free = [c for c in spots if not self.layout[c].get('lane')]
        if free or spots:
            self.challenges = {random.Random(f'{self.seed}:challenge').choice(free or spots)}

    def challenge_limit(self):
        """이 방의 도전 제한 시간(초): 적이 많을수록 길다."""
        return config.CHALLENGE_BASE + config.CHALLENGE_PER_ENEMY * self.wave_enemies

    def reward_of(self, coord):
        """이 방을 깨면 받을 보상 (전투방만, 아니면 None)."""
        return self.rewards.get(coord)

    def grant_reward(self, kind, boost=False):
        """방 보상을 준다. 변이면 셋을 골라 on_mutation(카드 창)으로 넘긴다.
        boost(v8 도전 성공): 조각·회복·결정은 CHALLENGE_MULT배, 증강·형태는 조각을 더 준다."""
        import mutations
        p = self.player
        rng = random.Random(f'{self.seed}:{self.coord}:grant')
        cx, cy = p.center
        mult = config.CHALLENGE_MULT if boost else 1
        if kind == 'shards':
            n = rng.randint(*mutations.REWARD_SHARDS) * mult
            p.shards += n
            effects.float_text(cx, cy + 90, f'조각 +{n}', mutations.REWARDS[kind][2])
        elif kind == 'heal':
            n = mutations.REWARD_HEAL * mult
            p.hp = min(p.max_hp, p.hp + n)
            effects.float_text(cx, cy + 90, f'체력 +{n}', mutations.REWARDS[kind][2])
        elif kind == 'crystal':
            n = mutations.REWARD_CRYSTALS * mult
            p.bonus_crystals += n
            effects.float_text(cx, cy + 90, f'헤이즈 결정 +{n}', mutations.REWARDS[kind][2])
        elif kind in ('mutation', 'form'):
            import forms
            if boost:
                p.shards += config.CHALLENGE_BONUS_SHARDS
                effects.float_text(cx, cy + 90, f'조각 +{config.CHALLENGE_BONUS_SHARDS}', mutations.REWARDS['shards'][2])
            choices = forms.cards(p) if kind == 'form' else []          # 형태 카드: 들고 있는 무기의 새 형태 + 넘기기
            if choices:
                if self.on_mutation:
                    self.on_mutation(choices)
                else:
                    forms.take_card(p, choices[0])
                return
            choices = mutations.offer(p, rng)                           # 내놓을 형태가 없으면 증강 셋으로 대신한다
            if not choices:
                return
            import curse
            choices = curse.mix_in(p, choices, rng)                     # 가끔 한 장이 저주 카드 (src/curse.py)
            if self.on_mutation:
                self.on_mutation(choices)
            else:
                mutations.give(p, choices[0])

    def _pick_template(self, coord):
        """전투 방은 원래 모양 또는 새 모양 중 하나 (판의 시드로 정한다). 그 밖의 방은 원래 모양."""
        original = self.layout[coord]['template']
        if self.type_of(coord) != 'combat':
            return original
        need = self.links_of(coord)
        options = [original] + [v for v in COMBAT_VARIANTS if need <= template_exits(v)]
        return random.Random(f'{self.seed}:{coord}:shape').choice(options)

    def _place_big_rooms(self):
        """v8 큰 방: 좌우 문만 쓰는 전투방 가운데 구역마다 BIG_ROOMS_PER_ZONE개를 두 화면짜리 방으로 바꾼다 (판의 시드로).
        출발 방 바로 옆 방은 뺀다(첫 전투는 짧게). 첫 번째는 갈림길 밖에서, 없으면 두 길에 하나씩 고른다(어느 길을 골라도 하나는 만난다).
        한 구역에 같은 모양이 두 번 나오지 않는다."""
        n = config.BIG_ROOMS_PER_ZONE.get(self.name, 0)
        sx, sy = self.start_coord
        spots = sorted(c for c in self.layout if self.type_of(c) == 'combat' and self.links_of(c) <= {'L', 'R'}
                       and abs(c[0] - sx) + abs(c[1] - sy) > 1)
        if not n or not spots:
            return
        rng = random.Random(f'{self.seed}:big')
        rng.shuffle(spots)
        lane = {k: [c for c in spots if self.layout[c].get('lane') == k] for k in (None, 'short', 'long')}
        if lane[None]:                                   # 갈림길 밖의 방 하나를 먼저
            order = lane[None][:1] + [c for c in spots if c != lane[None][0]]
        else:                                            # 없으면 두 길에 하나씩
            order = lane['short'][:1] + lane['long'][:1]
            order += [c for c in spots if c not in order]
        for c, shape in zip(order, rng.sample(BIG_ROOMS, min(n, len(order)))):
            self.templates[c] = shape

    def is_big(self, coord):
        return self.template_of(coord) in BIG_ROOMS

    def _big_room_extras(self, have):
        """큰 방은 적 무리가 BIG_ROOM_PACKS가 되게 구역의 적 목록에서 더 뽑는다 (판의 시드로)."""
        import mapgen
        pool = mapgen.SPECS.get(self.name, {}).get('pool')
        if not pool:
            return []
        rng = random.Random(f'{self.seed}:{self.coord}:big')
        return [mapgen._weighted(rng, pool) for _ in range(max(0, config.BIG_ROOM_PACKS - have))]

    def template_of(self, coord):
        return self.templates.get(coord, self.layout[coord]['template'])

    def original_kinds(self, info):
        """원래 방에서 나올 적 종류 목록 (종류가 적힌 스폰은 swap을 따르고, E 칸은 enemies를 차례로)."""
        generic = list(info.get('enemies', []))
        swap = info.get('swap', {})
        out = []
        for kind in template_spawn_kinds(info['template']):
            if kind is None:
                if generic:
                    out.append(generic.pop(0))
            else:
                out.append(swap.get(kind, kind))
        return out

    @property
    def next_name(self):
        if self.name == 'hideout':                 # 은신처의 출발 문 -> 스테이지 1
            return STAGE_ORDER[0]
        if self.name == 'practice':                # 연습장은 다음 구역이 없다 (메뉴에서 은신처로)
            return None
        i = STAGE_ORDER.index(self.name) if self.name in STAGE_ORDER else len(STAGE_ORDER)
        return STAGE_ORDER[i + 1] if i + 1 < len(STAGE_ORDER) else None

    # ----- 방 정의 -----
    def type_of(self, coord):
        return self.layout[coord].get('type', 'combat')

    def links_of(self, coord):
        """이 방에서 열 수 있는 출입구 방향: 이웃 방이 있고, 두 방의 템플릿 모두 그쪽에 문이 있는 곳."""
        links = set()
        here = template_exits(self.layout[coord]['template'])
        if self.type_of(coord) == 'hideout':       # 은신처: 오른쪽 문은 이웃 방이 없어도 '출발' 문이다
            links |= {'R'} & here
        for d, (dx, dy) in STEP.items():
            n = (coord[0] + dx, coord[1] + dy)
            if (n in self.layout and n not in self.sealed and d in here      # 닫힌 길(v8 갈림길)로 가는 문은 없다
                    and OPPOSITE[d] in template_exits(self.layout[n]['template'])):
                links.add(d)
        return links

    def neighbour(self, coord, direction):
        dx, dy = STEP[direction]
        return (coord[0] + dx, coord[1] + dy)

    # ----- 방 입장 -----
    def enter_room(self, coord, from_dir=None):
        """방을 새로 읽고 적·진열대를 세운 뒤 플레이어를 입구에 놓는다. from_dir은 들어온 쪽 문(왼쪽 문으로 들어오면 'L')."""
        import postfx
        postfx.clear()                                   # U1-3: 방을 옮기면 앞 방의 화면 연출(색 번짐·렌즈·줌)을 끈다
        info = self.layout[coord]
        self.coord = coord
        if self.choose_lane(coord):                      # v8 갈림길: 이 길을 골랐다
            self._say('다른 길은 닫혔습니다')
        if self.room is not None:
            game_world.remove_object(self.room)
        for layer in (game_world.LAYER_TILES, game_world.LAYER_ENEMY, game_world.LAYER_EFFECT):
            for obj in list(game_world.world[layer]):
                game_world.remove_object(obj)
        self.pedestals, self.boss, self.npcs = [], None, []
        self.event, self.challenge = None, None
        self.devices = []
        self.waves, self.wave_timer = [], None
        self.wave_total, self.wave_index, self.wave_packs, self.wave_enemies = 1, 1, 0, 0
        import transition
        transition.reveal()                              # 새 방은 검은 화면에서 점묘로 드러난다 (계획 4-3)
        self.room = Room.load(self.template_of(coord), self.links_of(coord), info.get('high_haze', False), self.theme_of(info))
        for d in self.room.links:      # 문 너머 방이 특별한 방이면 문에 표시한다
            if self.neighbour(coord, d) not in self.layout:      # 은신처 출발 문처럼 너머에 방이 없는 문
                continue
            kind = self.type_of(self.neighbour(coord, d))
            if kind in SPECIAL_TYPES:
                self.room.door_hints[d] = kind
            target = self.neighbour(coord, d)
            if target in self.challenges and target not in self.cleared:      # v8 도전방: 문에 알린다
                self.room.door_hints[d] = 'challenge'
            if self.reward_of(target) and target not in self.cleared:      # 깨면 받을 보상을 문에 미리 보인다
                self.room.door_rewards[d] = self.reward_of(target)
        if self.type_of(coord) == 'hideout':
            self.room.door_hints['R'] = 'depart'
        self._update_door_texts()
        game_world.add_object(self.room, game_world.LAYER_BACKGROUND)
        self._place_player(from_dir)
        self.visited.add(coord)
        kind = self.type_of(coord)
        if kind == 'gate' and coord not in self.cleared and config.GATEKEEPER:   # v8 구역 1 중간 보스 문지기
            self._spawn_gatekeeper()
        elif kind in ('combat', 'gate') and coord not in self.cleared:
            self._spawn_enemies(info)
            if coord in self.challenges:                 # v8 도전방: 제한 시간 시작
                limit = self.challenge_limit()
                self.challenge = {'limit': limit, 'left': limit}
                self._say(f'도전방 · {int(limit)}초 안에 모두 처치하면 추가 보상을 받습니다')
        elif kind == 'event':
            self._spawn_event(coord)
        if kind == 'combat':                             # v8 구역별 장치 (깬 방에도 그대로 있다)
            import devices
            self.devices = devices.place(self)
        elif kind == 'boss' and coord not in self.cleared:
            x, y = self.room.boss_spawn or (self.room.width * 0.7, config.TILE * 2)
            self.boss = self._make_boss(info.get('boss', 'crasher'), x, y)
            game_world.add_object(self.boss, game_world.LAYER_ENEMY)
        elif kind in ('gold', 'shop', 'rift'):
            self._spawn_pedestals(coord, kind)
        elif kind == 'hideout':
            self._spawn_npcs()
        elif kind == 'practice':                   # v7 연습장: 쓰러지지 않는 허수아비
            import practice
            practice.spawn_dummies(self)
        self.room.locked = self.enemy_count() > 0 and kind != 'practice'   # 연습장은 잠그지 않는다 (남은 적 칩도 안 뜬다)

    def _spawn_gatekeeper(self):
        """관문 방: 정예 전투 대신 문지기가 보스로 선다 (B 칸, 없으면 방 오른쪽)."""
        from gatekeeper import Gatekeeper
        x, y = self.room.boss_spawn or (self.room.width * 0.75, config.TILE * 2)
        self.boss = Gatekeeper(x, y, self.room, self.player)
        game_world.add_object(self.boss, game_world.LAYER_ENEMY)

    def _make_boss(self, kind, x, y):
        """보스 종류별 객체: 크래셔(스테이지 2), 아크(스테이지 3)."""
        if kind == 'ark':
            from ark import Ark
            return Ark(x, y, self.room, self.player)
        return Boss(x, y, self.room, self.player)

    def theme_of(self, info):
        """방의 겉모습 테마: 방의 theme, 없으면 종류로 (황금방 gold, 정비방 shop, 보스 boss, 고농도 haze),
        나머지는 구역의 기본 테마(슬럼 cell, 공장 foundry, 탑 haze)."""
        if info.get('theme'):
            return info['theme']
        kind = info.get('type')
        if kind in ('gold', 'shop', 'boss'):
            return kind
        if kind == 'rift':
            return 'haze'
        return 'haze' if info.get('high_haze') else self.default_theme

    def _spawn_event(self, coord):
        """v8 이벤트 방: 가운데 단 위(I 칸)에 헤이즈 샘 또는 떠돌이 죄수를 놓는다. 쓴 것은 다시 들어와도 그대로다."""
        import events
        saved = self.state.setdefault(coord, {})
        x, y = self.room.pedestals[0] if self.room.pedestals else (self.room.width / 2, config.TILE * 2)
        self.event = events.Spot(events.kind_of(self), x, y, saved)
        self.event.player = self.player
        game_world.add_object(self.event, game_world.LAYER_TILES)

    def _spawn_npcs(self):
        from npc import NPC
        for kind, col in self.npc_spots:
            n = NPC(kind, col * config.TILE + config.TILE / 2, config.TILE * 2)
            n.player = self.player
            self.npcs.append(n)
            game_world.add_object(n, game_world.LAYER_TILES)

    # ----- 황금방 잠금·균열방 (11/19) -----
    def gold_rooms_left(self):
        """황금방이 열리기까지 남은 전투방 수: 이 구역의 보스·관문을 뺀 전투방 중 아직 클리어하지 않은 것."""
        return sum(1 for c in self.layout if self.type_of(c) == 'combat' and c not in self.cleared and c not in self.sealed)

    def rift_cost(self):
        """균열방에 처음 들어갈 때 내는 체력: 최대 체력의 RIFT_HP_COST% (올림)."""
        return -(-self.player.max_hp * config.RIFT_HP_COST // 100)

    def _update_door_texts(self):
        """잠긴 황금방 문에는 남은 방 수, 아직 값을 치르지 않은 균열방 문에는 체력 대가를 적는다."""
        texts = {}
        left = self.gold_rooms_left()
        for d, kind in self.room.door_hints.items():
            target = self.neighbour(self.coord, d)
            if kind == 'event':                          # v8 이벤트 방: 무엇이 있는지 이름으로
                import events
                texts[d] = events.NAMES[events.kind_of(self)]
            elif kind == 'gold' and left > 0:
                texts[d] = f'황금방 잠김 · 남은 방 {left}'
            elif kind == 'rift' and target not in self.paid_rifts:
                texts[d] = f'균열 · 체력 -{self.rift_cost()}'
        self.room.door_texts = texts

    def _blocked(self, target, direction):
        """그 문으로 지금 들어갈 수 없으면 이유(글자), 들어갈 수 있으면 None. 균열방은 여기서 체력을 낸다."""
        kind = self.type_of(target)
        if kind == 'gold' and self.gold_rooms_left() > 0:
            return f'전투방을 모두 클리어해야 황금방이 열립니다 (남은 방 {self.gold_rooms_left()})'
        if kind == 'rift' and target not in self.paid_rifts:
            cost = self.rift_cost()
            if self.player.hp <= cost:
                return f'균열에 들어가려면 체력이 {cost}보다 많아야 합니다'
            self.player.hp -= cost
            self.paid_rifts.add(target)
            self._say(f'균열의 대가: 체력 -{cost}')
        return None

    def _push_back(self, direction):
        """막힌 문에서 플레이어를 방 안쪽으로 조금 되돌린다."""
        p, room, t = self.player, self.room, config.TILE
        half = config.PLAYER_HB_W / 2
        if direction == 'R':
            p.x = room.width - half - t
        elif direction == 'L':
            p.x = half + t
        elif direction == 'U':
            p.y = room.height - config.PLAYER_HB_H - t * 1.5
            p.vy = min(p.vy, 0.0)
        else:
            p.y, p.vy = t * 2.5, 500.0
        p.vx = 0.0

    def _place_player(self, from_dir):
        p, room = self.player, self.room
        p.room = room
        p.vx = p.vy = 0.0
        t = config.TILE
        door = room.door_center(from_dir) if from_dir else None
        if door is None:                     # 그쪽 문이 없는 방 모양: 방의 시작 자리로
            from_dir = None
        if from_dir == 'L':
            p.x, p.y = config.PLAYER_HB_W / 2 + t * 1.6, door[1]
        elif from_dir == 'R':
            p.x, p.y = room.width - config.PLAYER_HB_W / 2 - t * 1.6, door[1]
        elif from_dir == 'U':                # 위 문으로 떨어져 들어온다
            p.x, p.y, p.vy = door[0], room.height - t * 2.7, -200.0
        elif from_dir == 'D':                # 아래 문(바닥 구멍)에서 올라와 구멍 옆 바닥에 선다 (바로 다시 빠지지 않게)
            cols = [c for c, _ in room.exits['D']]
            for c in (max(cols) + 2, min(cols) - 2):
                if room.tile_at(c, room.nrows - 2) == '#' and room.tile_at(c, room.nrows - 3) in ('.', 'E', 's', 't', 'P'):
                    p.x, p.y, p.vy = c * t + t / 2, 2 * t, 650.0
                    break
            else:
                p.x, p.y, p.vy = door[0], 2 * t + 4, 900.0
        else:
            p.x, p.y = room.spawn
        p.invuln_left = max(p.invuln_left, 0.6)  # 입장 직후 잠깐 무적
        p.on_ground = False
        camera.snap(p, room)                     # 카메라는 날아오지 않고 바로 맞춘다

    def _spawn_enemies(self, info):
        rng = random.Random(f'{self.seed}:{self.coord}:elite')                 # 같은 판·같은 방이면 늘 같은 정예
        # 칸에 종류가 적힌 스폰(s, t)은 그대로, 종류 없는 E 칸은 스테이지 데이터의 enemies를 순서대로 쓴다
        # swap: 템플릿에 적힌 종류를 이 방에서만 바꾼다 (같은 방 모양을 다른 구역에서 다른 적으로, 예: {'slum': 'guard'})
        generic = list(info.get('enemies', []))
        swap = info.get('swap', {})
        if self.template_of(self.coord) != info['template']:      # 새 모양: 원래 방의 적 구성을 새 스폰 칸에 차례로
            kinds = self.original_kinds(info)
            if self.is_big(self.coord):                           # v8 큰 방: 적 무리를 늘린다 (세 물결)
                kinds = kinds + self._big_room_extras(len(kinds))
            spawns = [(x, y, kinds[i]) for i, (x, y, _k) in enumerate(self.room.enemy_spawns[:len(kinds)])]
            generic, swap = [], {}
        else:
            spawns = self.room.enemy_spawns
        packs = []
        for x, y, kind in spawns:
            if kind is None:
                if not generic:
                    continue
                kind = generic.pop(0)
            else:
                kind = swap.get(kind, kind)
            import enemy_kinds
            pack = list(enemy_kinds.make_pack(kind, x, y, self.room, self.player))   # 드론·수레·새 적은 자기 클래스, 쥐는 무리
            mod = roll_elite(rng, self.name) if pack else None
            if mod:
                pack[0].make_elite(mod)
            if pack:
                packs.append(pack)
        self._release_waves(packs, info)

    def _release_waves(self, packs, info):
        """v8 물결 전투: 무리가 많은 전투방은 2~3물결로 나눈다. 첫 물결은 바로 세우고 나머지는 앞 물결을 다 쓰러뜨리면 예고 뒤에 나온다.
        정예가 있는 무리는 뒤로 돌려 마지막 물결에 나오게 한다. 관문(정예 전투)과 무리가 적은 방은 한 번에."""
        self.wave_packs = len(packs)
        self.wave_enemies = sum(len(pk) for pk in packs)
        n = 1
        if info.get('type') == 'combat' and len(packs) >= config.WAVE_MIN_PACKS:
            n = 3 if len(packs) >= config.WAVE_THREE_PACKS else 2
        elites = [pk for pk in packs if getattr(pk[0], 'elite', None)]
        normals = [pk for pk in packs if not getattr(pk[0], 'elite', None)]
        size = -(-len(packs) // n) if packs else 0
        chunks = []
        for _ in range(n - 1):                             # 앞 물결들은 보통 무리만
            if normals[:size]:
                chunks.append(normals[:size])
            normals = normals[size:]
        if normals or elites:
            chunks.append(normals + elites)                # 마지막 물결: 남은 무리 + 정예 전부
        self.wave_total, self.wave_index = max(1, len(chunks)), 1
        for k, chunk in enumerate(chunks):
            wave = [e for pk in chunk for e in pk]
            if k == 0:
                for e in wave:
                    game_world.add_object(e, game_world.LAYER_ENEMY)
            else:
                self.waves.append(wave)

    def _advance_wave(self):
        """지금 물결을 다 쓰러뜨렸다: 다음 물결의 자리에 예고를 띄우고, WAVE_WARN 뒤에 내보낸다."""
        if self.wave_timer is None:
            self.wave_timer = config.WAVE_WARN
            assets.play_sound('warn_low')
            for e in self.waves[0]:
                effects.spawn('surge', e.x, e.y, duration=0.36)
                effects.spawn_bloom(e.x, e.y + 40, (255, 96, 96), big=True, life=config.WAVE_WARN, strength=0.8)
            return
        self.wave_timer -= 1 / 60
        if self.wave_timer > 0:
            return
        self.wave_timer = None
        self.wave_index += 1
        for e in self.waves.pop(0):
            effects.spawn('puff', e.x, e.y + 40, duration=0.3)
            game_world.add_object(e, game_world.LAYER_ENEMY)

    def _spawn_pedestals(self, coord, kind):
        saved = self.state.setdefault(coord, {})
        if 'stock' not in saved:           # 처음 들어올 때 한 번만 뽑고, 다시 와도 같은 물건이다
            rng = random.Random(f'{self.seed}:{coord}')
            count = min(len(self.room.pedestals), 3 if kind == 'gold' else 4)
            if kind == 'rift':
                saved['stock'] = items.roll_rift(rng, self.player)
            elif kind == 'gold':
                saved['stock'] = items.roll_gold(rng, count, self.player)
            else:
                saved['stock'] = items.roll_shop(rng, count, self.player)
            saved['gone'] = set()
        for slot, (x, y) in enumerate(self.room.pedestals):
            if slot >= len(saved['stock']):
                break
            item_id = saved['stock'][slot]
            price = items.price(self.player, item_id) if kind == 'shop' else 0
            ped = Pedestal(x, y, item_id, kind, price)
            ped.player = self.player
            ped.gone = slot in saved['gone'] or (kind == 'shop' and item_id in items.UPGRADES
                                                 and items.level(self.player, item_id) >= items.MAX_LEVEL)
            ped.slot = slot
            self.pedestals.append(ped)
            game_world.add_object(ped, game_world.LAYER_TILES)

    def start(self):
        self.enter_room(self.coord)
        import zone_card
        if self.title and zone_card.says_title(self.name):
            self._say(self.title)                        # 구역 이름을 띄운다 (스테이지 1~3은 구역 제목 카드가 대신한다)

    def enemy_count(self):
        return sum(1 for e in game_world.world[game_world.LAYER_ENEMY] if e.alive)

    # ----- 상호작용 (진열대) -----
    def interact(self):
        """F: 가까운 진열대의 아이템을 얻거나 사고, 은신처에서는 가까운 NPC와 이야기한다."""
        p = self.player
        if self.type_of(self.coord) == 'practice':  # 연습장 어디서나 F: 연습 메뉴
            if self.on_practice:
                self.on_practice()
            return True
        talk = [n for n in self.npcs if n.near(p)]
        if talk:
            if self.on_npc:
                self.on_npc(min(talk, key=lambda n: abs(n.x - p.x)))
            return True
        ev = self.event
        if ev is not None and not ev.used and ev.near(p):          # v8 이벤트 방: 카드 창을 연다
            import events
            events.current = ev
            cards = events.cards(ev.kind)
            if self.on_mutation:
                self.on_mutation(cards)
            else:
                events.take(p, cards[0])
            return True
        near = [ped for ped in self.pedestals if not ped.gone and ped.near(p)]
        if not near:
            return False
        ped = min(near, key=lambda d: abs(d.x - p.x))
        saved = self.state[self.coord]
        if not items.can_take(p, ped.item_id):
            info = items.ITEMS[ped.item_id]
            self._say('이미 얻은 형태입니다' if 'form' in info else '물약이 가득 찼습니다' if ped.item_id == 'heal'
                      else '이미 최대 단계입니다')
            return False
        if ped.mode == 'shop':
            if p.shards < ped.price:
                self._say(f'조각이 부족합니다 ({p.shards}/{ped.price})')
                return False
            p.shards -= ped.price
        rift = ped.mode == 'rift' and ped.item_id in items.UPGRADES
        text = items.describe(p, ped.item_id, steps=2 if rift else 1)   # 균열방: 두 단계 뒤의 수치 (U1)
        items.apply(p, ped.item_id)
        if rift and items.can_take(p, ped.item_id):
            items.apply(p, ped.item_id)            # 균열방 업그레이드는 두 단계를 한꺼번에
        info = items.ITEMS[ped.item_id]
        if self.on_pickup:                                # 화면 아래 이름·효과 띠 (11/22)
            self.on_pickup(ped.item_id, text)
        else:
            self._say(f'{info["name"]} 획득: {text}')
        upgrade_left = (ped.mode == 'shop' and ped.item_id in items.UPGRADES
                        and items.level(p, ped.item_id) < items.MAX_LEVEL)
        if upgrade_left:                       # 정비방 업그레이드: 품절 대신 다음 단계가 올라온다 (값이 오른다)
            ped.price = items.price(p, ped.item_id)
            for other in self.pedestals:       # 기본 성장처럼 단계를 함께 쓰는 진열대도 값을 맞춘다
                if other.mode == 'shop' and other.item_id in items.UPGRADES:
                    other.price = items.price(p, other.item_id)
                    other.gone = other.gone or items.level(p, other.item_id) >= items.MAX_LEVEL
            return True
        saved['gone'].add(ped.slot)
        ped.gone = True
        if ped.mode == 'shop':                 # 3단계를 다 샀다: 단계를 함께 쓰는 진열대도 품절
            for other in self.pedestals:
                if other.mode == 'shop' and other.item_id in items.UPGRADES and not items.can_take(p, other.item_id):
                    other.gone = True
        if ped.mode in ('gold', 'rift'):       # 황금방·균열방은 하나만: 나머지는 사라진다
            for other in self.pedestals:
                other.gone = True
                saved['gone'].add(other.slot)
        return True

    def _say(self, text):
        if self.on_message:
            self.on_message(text)

    # ----- 매 프레임 -----
    def update(self):
        """클리어 판정, 출입구 이동, 진열대 상호작용. play_mode가 world 갱신 뒤에 부른다."""
        p = self.player
        if p.interact_pressed:
            p.interact_pressed = False
            self.interact()
        self.block_left = max(0.0, self.block_left - 1 / 60)
        self._summon_heart()
        ch = self.challenge
        if ch is not None and self.room.locked and ch['left'] > 0:      # v8 도전방: 시간이 간다
            ch['left'] -= 1 / 60
            if ch['left'] <= 0:
                ch['left'] = 0.0
                self._say('도전 실패 · 보상은 그대로입니다')
        if self.room.locked and self.enemy_count() == 0 and (self.waves or self.wave_timer is not None):
            self._advance_wave()                   # v8 물결 전투: 아직 나올 물결이 있다 (방은 잠긴 채)
        elif self.room.locked and self.enemy_count() == 0:
            self.room.locked = False
            before = self.gold_rooms_left()
            self.cleared.add(self.coord)
            if self.player is not None:            # 판이 끝날 때 헤이즈 결정 보상에 센다
                self.player.run_rooms += 1
                if self.type_of(self.coord) in END_TYPES:
                    self.player.run_ends += 1
            if self.on_clear:
                self.on_clear(self)
            if p is not None:                      # 저주 증강: 전투방을 하나 깼다. 풀렸으면 보상을 알린다 (src/curse.py)
                import curse
                got = curse.on_room_clear(p, random.Random(f'{self.seed}:{self.coord}:curse'))
                if got is not None:
                    self._say(curse.reward_text(got))
                    assets.play_sound('enhance')
                    effects.float_text(p.center[0], p.center[1] + 150, curse.reward_text(got), curse.REWARD_COLOR, big=True, life=1.6)
            won = ch is not None and ch['left'] > 0                 # v8 도전 성공: 보상이 커진다
            if won:
                self._say('도전 성공 · 추가 보상을 받습니다')
            if self.reward_of(self.coord) and p is not None:
                if self.type_of(self.coord) in END_TYPES:
                    self.end_reward = self.reward_of(self.coord)      # 보스가 쓰러지는 연출 뒤에 준다 (아래)
                else:
                    self.grant_reward(self.reward_of(self.coord), boost=won)
            self.challenge = None
            if before > 0 and self.gold_rooms_left() == 0 and any(self.type_of(c) == 'gold' for c in self.layout):
                self._say('모든 전투방을 클리어했습니다. 황금방이 열렸습니다')
            self._update_door_texts()
        if self.type_of(self.coord) in END_TYPES and self.coord in self.cleared and not self.finished:
            self.finish_timer += 1 / 60
            if self.end_reward and self.finish_timer >= config.BOSS_REWARD_DELAY and p is not None:
                kind, self.end_reward = self.end_reward, None
                self.grant_reward(kind)                # 구역 보스 보상: 증강 선택
            if self.finish_timer >= 2.5:
                self.finished = True
            return
        if self.room.locked or p.state == 'DEAD':
            return
        direction = self._exit_direction()
        if direction == 'R' and self.type_of(self.coord) == 'hideout':
            self.finished = True                   # 출발 문: 스테이지 1로 (play_mode가 next_stage를 연다)
            return
        if direction:
            target = self.neighbour(self.coord, direction)
            if target in self.layout:
                reason = self._blocked(target, direction)
                if reason:
                    self._push_back(direction)
                    if self.block_left <= 0:
                        self._say(reason)
                        self.block_left = 1.5
                    return
                self.enter_room(target, OPPOSITE[direction])

    def _summon_heart(self):
        """탑 꼭대기(final: heart): 아크가 쓰러지면 같은 방에 헤이즈 심장이 내려온다 (방은 잠긴 채, 11/22 v5)."""
        b = self.boss
        if (b is None or b.alive or getattr(b, 'kind', '') != 'ark'
                or self.layout[self.coord].get('final') != 'heart' or self.coord in self.cleared):
            return
        import heart
        self.boss = heart.spawn(self.room, self.player)

    def _exit_direction(self):
        """플레이어가 지금 열린 출입구를 지나고 있다면 그 방향."""
        p, room = self.player, self.room
        half = config.PLAYER_HB_W / 2
        if 'R' in room.links and p.x >= room.width - half - 2 and self._at_side_exit('R'):
            return 'R'
        if 'L' in room.links and p.x <= half + 2 and self._at_side_exit('L'):
            return 'L'
        if 'U' in room.links and p.y + config.PLAYER_HB_H >= room.height - 6 and self._in_door_cols('U'):
            return 'U'
        if 'D' in room.links and p.y <= 14 and self._in_door_cols('D'):
            return 'D'
        return None

    def _at_side_exit(self, direction):
        """플레이어 몸 중심 높이가 좌우 출입구 줄 중 하나에 있는가."""
        row = self.room.row_of(self.player.y + config.PLAYER_HB_H / 2)
        return any(abs(r - row) <= 1 for _, r in self.room.exits.get(direction, []))

    def _in_door_cols(self, direction):
        cols = [c for c, _ in self.room.exits.get(direction, [])]
        return bool(cols) and min(cols) * config.TILE <= self.player.x <= (max(cols) + 1) * config.TILE

    # ----- 미니맵 -----
    def minimap_cells(self):
        """[(좌표, 상태, 종류, 고농도)] 상태: 'current' / 'cleared' / 'visited' / 'unknown'. 방문한 방과 그 이웃만 보여 준다."""
        shown = set(self.visited)
        for c in list(self.visited):
            for d in self.links_of(c):
                if self.neighbour(c, d) in self.layout:       # 은신처 출발 문처럼 너머에 방이 없는 문은 빼고
                    shown.add(self.neighbour(c, d))
        shown -= self.sealed                                  # v8 갈림길: 닫힌 길은 지도에서 뺀다
        cells = []
        for c in shown:
            if c == self.coord:
                state = 'current'
            elif c in self.cleared or (self.type_of(c) in ('gold', 'shop', 'start', 'rift', 'event') and c in self.visited):
                state = 'cleared'
            elif c in self.visited:
                state = 'visited'
            else:
                state = 'unknown'
            kind = self.type_of(c)
            known = c in self.visited or kind in SPECIAL_TYPES   # 문에 표시된 특별한 방은 미리 보인다
            cells.append((c, state, kind if known else 'combat', bool(self.layout[c].get('high_haze')) and c in self.visited))
        return cells
