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
SPECIAL_TYPES = ('gold', 'shop', 'boss', 'gate', 'rift')   # 문에 미리 알려 주는 방 종류
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
        self.state = {}             # 방 좌표 -> 아이템 선택·품절 같은 진행 상태
        self.paid_rifts = set()     # 체력을 내고 들어간 균열방 (다시 들어갈 때는 내지 않는다)
        self.block_left = 0.0       # 막힌 문 안내를 너무 자주 띄우지 않게
        self.room = None
        self.pedestals = []
        self.npcs = []              # 은신처 NPC (정비사·보관인·기록관)
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
        self.rewards = {c: self._roll_reward(c) for c in self.layout if self.type_of(c) == 'combat'}   # 방 보상 (11/22)

    def _roll_reward(self, coord):
        import mutations
        rng = random.Random(f'{self.seed}:{coord}:reward')
        kinds = list(mutations.REWARD_WEIGHTS)
        return rng.choices(kinds, [mutations.REWARD_WEIGHTS[k] for k in kinds])[0]

    def reward_of(self, coord):
        """이 방을 깨면 받을 보상 (전투방만, 아니면 None)."""
        return self.rewards.get(coord)

    def grant_reward(self, kind):
        """방 보상을 준다. 변이면 셋을 골라 on_mutation(카드 창)으로 넘긴다."""
        import mutations
        p = self.player
        rng = random.Random(f'{self.seed}:{self.coord}:grant')
        cx, cy = p.center
        if kind == 'shards':
            n = rng.randint(*mutations.REWARD_SHARDS)
            p.shards += n
            effects.float_text(cx, cy + 90, f'조각 +{n}', mutations.REWARDS[kind][2])
        elif kind == 'heal':
            p.hp = min(p.max_hp, p.hp + mutations.REWARD_HEAL)
            effects.float_text(cx, cy + 90, f'체력 +{mutations.REWARD_HEAL}', mutations.REWARDS[kind][2])
        elif kind == 'crystal':
            p.bonus_crystals += mutations.REWARD_CRYSTALS
            effects.float_text(cx, cy + 90, f'헤이즈 결정 +{mutations.REWARD_CRYSTALS}', mutations.REWARDS[kind][2])
        elif kind == 'mutation':
            choices = mutations.offer(p, rng)
            if not choices:
                return
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
            if n in self.layout and d in here and OPPOSITE[d] in template_exits(self.layout[n]['template']):
                links.add(d)
        return links

    def neighbour(self, coord, direction):
        dx, dy = STEP[direction]
        return (coord[0] + dx, coord[1] + dy)

    # ----- 방 입장 -----
    def enter_room(self, coord, from_dir=None):
        """방을 새로 읽고 적·진열대를 세운 뒤 플레이어를 입구에 놓는다. from_dir은 들어온 쪽 문(왼쪽 문으로 들어오면 'L')."""
        info = self.layout[coord]
        self.coord = coord
        if self.room is not None:
            game_world.remove_object(self.room)
        for layer in (game_world.LAYER_TILES, game_world.LAYER_ENEMY, game_world.LAYER_EFFECT):
            for obj in list(game_world.world[layer]):
                game_world.remove_object(obj)
        self.pedestals, self.boss, self.npcs = [], None, []
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
            if self.reward_of(target) and target not in self.cleared:      # 깨면 받을 보상을 문에 미리 보인다
                self.room.door_rewards[d] = self.reward_of(target)
        if self.type_of(coord) == 'hideout':
            self.room.door_hints['R'] = 'depart'
        self._update_door_texts()
        game_world.add_object(self.room, game_world.LAYER_BACKGROUND)
        self._place_player(from_dir)
        self.visited.add(coord)
        kind = self.type_of(coord)
        if kind in ('combat', 'gate') and coord not in self.cleared:
            self._spawn_enemies(info)
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
        return sum(1 for c in self.layout if self.type_of(c) == 'combat' and c not in self.cleared)

    def rift_cost(self):
        """균열방에 처음 들어갈 때 내는 체력: 최대 체력의 RIFT_HP_COST% (올림)."""
        return -(-self.player.max_hp * config.RIFT_HP_COST // 100)

    def _update_door_texts(self):
        """잠긴 황금방 문에는 남은 방 수, 아직 값을 치르지 않은 균열방 문에는 체력 대가를 적는다."""
        texts = {}
        left = self.gold_rooms_left()
        for d, kind in self.room.door_hints.items():
            target = self.neighbour(self.coord, d)
            if kind == 'gold' and left > 0:
                texts[d] = f'황금방 잠김 · 남은 방 {left}'
            elif kind == 'rift' and target not in self.paid_rifts:
                texts[d] = f'균열 · 체력 -{self.rift_cost()}'
        self.room.door_texts = texts

    def _blocked(self, target, direction):
        """그 문으로 지금 들어갈 수 없으면 이유(글자), 들어갈 수 있으면 None. 균열방은 여기서 체력을 낸다."""
        kind = self.type_of(target)
        if kind == 'gold' and self.gold_rooms_left() > 0:
            return f'이 구역의 전투방을 모두 클리어하면 황금방이 열립니다 (남은 방 {self.gold_rooms_left()})'
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
            spawns = [(x, y, kinds[i]) for i, (x, y, _k) in enumerate(self.room.enemy_spawns[:len(kinds)])]
            generic, swap = [], {}
        else:
            spawns = self.room.enemy_spawns
        for x, y, kind in spawns:
            if kind is None:
                if not generic:
                    continue
                kind = generic.pop(0)
            else:
                kind = swap.get(kind, kind)
            import enemy_kinds
            for i, enemy in enumerate(enemy_kinds.make_pack(kind, x, y, self.room, self.player)):   # 드론·수레·새 적은 자기 클래스, 쥐는 무리 (11/22)
                mod = roll_elite(rng, self.name) if i == 0 else None
                if mod:
                    enemy.make_elite(mod)
                game_world.add_object(enemy, game_world.LAYER_ENEMY)

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
        near = [ped for ped in self.pedestals if not ped.gone and ped.near(p)]
        if not near:
            return False
        ped = min(near, key=lambda d: abs(d.x - p.x))
        saved = self.state[self.coord]
        if not items.can_take(p, ped.item_id):
            self._say('이미 최대 단계입니다')
            return False
        if ped.mode == 'shop':
            if p.shards < ped.price:
                self._say(f'조각이 부족합니다 ({p.shards}/{ped.price})')
                return False
            p.shards -= ped.price
        text = items.describe(p, ped.item_id)
        items.apply(p, ped.item_id)
        if ped.mode == 'rift' and ped.item_id in items.UPGRADES and items.can_take(p, ped.item_id):
            items.apply(p, ped.item_id)            # 균열방 업그레이드는 두 단계를 한꺼번에
            text = '두 단계: ' + text
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
        if self.room.locked and self.enemy_count() == 0:
            self.room.locked = False
            before = self.gold_rooms_left()
            self.cleared.add(self.coord)
            if self.player is not None:            # 판이 끝날 때 헤이즈 결정 보상에 센다
                self.player.run_rooms += 1
                if self.type_of(self.coord) in END_TYPES:
                    self.player.run_ends += 1
            if self.on_clear:
                self.on_clear(self)
            if self.reward_of(self.coord) and p is not None:
                self.grant_reward(self.reward_of(self.coord))
            if before > 0 and self.gold_rooms_left() == 0 and any(self.type_of(c) == 'gold' for c in self.layout):
                self._say('모든 전투방을 클리어했습니다. 황금방이 열렸습니다')
            self._update_door_texts()
        if self.type_of(self.coord) in END_TYPES and self.coord in self.cleared and not self.finished:
            self.finish_timer += 1 / 60
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
        cells = []
        for c in shown:
            if c == self.coord:
                state = 'current'
            elif c in self.cleared or (self.type_of(c) in ('gold', 'shop', 'start', 'rift') and c in self.visited):
                state = 'cleared'
            elif c in self.visited:
                state = 'visited'
            else:
                state = 'unknown'
            kind = self.type_of(c)
            known = c in self.visited or kind in SPECIAL_TYPES   # 문에 표시된 특별한 방은 미리 보인다
            cells.append((c, state, kind if known else 'combat', bool(self.layout[c].get('high_haze')) and c in self.visited))
        return cells
