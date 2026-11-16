"""스테이지: 방 격자, 현재 방, 4방향 방 이동, 방 클리어(문 열림), 황금방·정비방·보스방, 미니맵 데이터.

방은 격자 좌표 (열, 행)에 놓이고 행은 위로 증가한다. 방마다 위·아래·좌·우 출입구가 있을 수 있고, 어느 문으로 나갈지는 플레이어가
고른다. 문 너머 방이 황금방·정비방·보스방이면 문 색과 이름으로 알려 준다. pico2d와 무관한 로직이라 창 없이 테스트한다.
배치 데이터는 data/stages/stage1.py (격자 좌표 -> 방 정의).

방 종류: start(안전), combat(적을 모두 처치해야 문이 열림), gold(아이템 중 하나를 무료로), shop(조각으로 구매), boss(보스).
"""
import importlib.util
import os
import random

import assets
import camera
import config
import game_world
import items
from boss import Boss
from enemy import Enemy
from pedestal import Pedestal
from room import Room

OPPOSITE = {'L': 'R', 'R': 'L', 'U': 'D', 'D': 'U'}
STEP = {'L': (-1, 0), 'R': (1, 0), 'U': (0, 1), 'D': (0, -1)}
SPECIAL_TYPES = ('gold', 'shop', 'boss')   # 문에 미리 알려 주는 방 종류

_exit_cache = {}


def load_layout(name='stage1'):
    """data/stages/<name>.py 에서 (START, 스테이지 딕셔너리)를 읽는다."""
    path = os.path.join(assets.DATA_DIR, 'stages', name + '.py')
    spec = importlib.util.spec_from_file_location('stage_data_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.START, getattr(module, name.upper())


def template_exits(template):
    """방 템플릿에 있는 출입구 방향 집합 (파일을 한 번만 읽는다)."""
    if template not in _exit_cache:
        _exit_cache[template] = set(Room.load(template).exits)
    return _exit_cache[template]


class Stage:
    def __init__(self, player, layout=None, start=None, seed=None):
        if layout is None:
            start, layout = load_layout()
        self.layout = layout
        self.player = player
        self.coord = start
        self.seed = random.randrange(1 << 30) if seed is None else seed
        self.visited = set()
        self.cleared = set()
        self.state = {}             # 방 좌표 -> 아이템 선택·품절 같은 진행 상태
        self.room = None
        self.pedestals = []
        self.boss = None
        self.finished = False       # 보스를 쓰러뜨려 탈출이 끝났는가
        self.finish_timer = 0.0
        self.on_clear = None        # 방을 클리어했을 때 부를 함수 (소리·글자용)
        self.on_message = None      # 화면에 띄울 짧은 글자: f(문구)

    # ----- 방 정의 -----
    def type_of(self, coord):
        return self.layout[coord].get('type', 'combat')

    def links_of(self, coord):
        """이 방에서 열 수 있는 출입구 방향: 이웃 방이 있고, 두 방의 템플릿 모두 그쪽에 문이 있는 곳."""
        links = set()
        here = template_exits(self.layout[coord]['template'])
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
        self.pedestals, self.boss = [], None
        self.room = Room.load(info['template'], self.links_of(coord), info.get('high_haze', False), self._theme_of(info))
        for d in self.room.links:      # 문 너머 방이 특별한 방이면 문에 표시한다
            kind = self.type_of(self.neighbour(coord, d))
            if kind in SPECIAL_TYPES:
                self.room.door_hints[d] = kind
        game_world.add_object(self.room, game_world.LAYER_BACKGROUND)
        self._place_player(from_dir)
        self.visited.add(coord)
        kind = self.type_of(coord)
        if kind == 'combat' and coord not in self.cleared:
            self._spawn_enemies(info)
        elif kind == 'boss' and coord not in self.cleared:
            x, y = self.room.boss_spawn or (self.room.width * 0.7, config.TILE * 2)
            self.boss = Boss(x, y, self.room, self.player)
            game_world.add_object(self.boss, game_world.LAYER_ENEMY)
        elif kind in ('gold', 'shop'):
            self._spawn_pedestals(coord, kind)
        self.room.locked = self.enemy_count() > 0

    @staticmethod
    def _theme_of(info):
        """방의 겉모습 테마: 스테이지 데이터의 theme, 없으면 종류로 (황금방 gold, 정비방 shop, 보스 boss, 고농도 haze, 나머지 cell)."""
        if info.get('theme'):
            return info['theme']
        kind = info.get('type')
        if kind in ('gold', 'shop', 'boss'):
            return kind
        return 'haze' if info.get('high_haze') else 'cell'

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
        # 칸에 종류가 적힌 스폰(s, t)은 그대로, 종류 없는 E 칸은 스테이지 데이터의 enemies를 순서대로 쓴다
        generic = list(info.get('enemies', []))
        for x, y, kind in self.room.enemy_spawns:
            if kind is None:
                if not generic:
                    continue
                kind = generic.pop(0)
            game_world.add_object(Enemy(kind, x, y, self.room, self.player), game_world.LAYER_ENEMY)

    def _spawn_pedestals(self, coord, kind):
        saved = self.state.setdefault(coord, {})
        if 'stock' not in saved:           # 처음 들어올 때 한 번만 뽑고, 다시 와도 같은 물건이다
            rng = random.Random(f'{self.seed}:{coord}')
            pool = items.GOLD_POOL if kind == 'gold' else items.SHOP_POOL
            count = min(len(self.room.pedestals), 3 if kind == 'gold' else 4)
            saved['stock'] = items.roll(rng, pool, count)
            saved['gone'] = set()
        for slot, (x, y) in enumerate(self.room.pedestals):
            if slot >= len(saved['stock']):
                break
            item_id = saved['stock'][slot]
            price = 0 if kind == 'gold' else items.ITEMS[item_id]['price']
            ped = Pedestal(x, y, item_id, kind, price)
            ped.player = self.player
            ped.gone = slot in saved['gone']
            ped.slot = slot
            self.pedestals.append(ped)
            game_world.add_object(ped, game_world.LAYER_TILES)

    def start(self):
        self.enter_room(self.coord)

    def enemy_count(self):
        return sum(1 for e in game_world.world[game_world.LAYER_ENEMY] if e.alive)

    # ----- 상호작용 (진열대) -----
    def interact(self):
        """F: 가까운 진열대의 아이템을 얻거나 산다."""
        p = self.player
        near = [ped for ped in self.pedestals if not ped.gone and ped.near(p)]
        if not near:
            return False
        ped = min(near, key=lambda d: abs(d.x - p.x))
        saved = self.state[self.coord]
        if not items.can_take(p, ped.item_id):
            self._say('이미 한계다')
            return False
        if ped.mode == 'shop':
            if p.shards < ped.price:
                self._say(f'조각이 모자라다 ({p.shards}/{ped.price})')
                return False
            p.shards -= ped.price
        items.apply(p, ped.item_id)
        info = items.ITEMS[ped.item_id]
        self._say(f'{info["name"]} 획득: {info["desc"]}')
        saved['gone'].add(ped.slot)
        ped.gone = True
        if ped.mode == 'gold':                 # 황금방은 하나만: 나머지는 사라진다
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
        if self.room.locked and self.enemy_count() == 0:
            self.room.locked = False
            self.cleared.add(self.coord)
            if self.on_clear:
                self.on_clear(self)
        if self.type_of(self.coord) == 'boss' and self.coord in self.cleared and not self.finished:
            self.finish_timer += 1 / 60
            if self.finish_timer >= 2.5:
                self.finished = True
            return
        if self.room.locked or p.state == 'DEAD':
            return
        direction = self._exit_direction()
        if direction:
            target = self.neighbour(self.coord, direction)
            if target in self.layout:
                self.enter_room(target, OPPOSITE[direction])

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
                shown.add(self.neighbour(c, d))
        cells = []
        for c in shown:
            if c == self.coord:
                state = 'current'
            elif c in self.cleared or (self.type_of(c) in ('gold', 'shop', 'start') and c in self.visited):
                state = 'cleared'
            elif c in self.visited:
                state = 'visited'
            else:
                state = 'unknown'
            kind = self.type_of(c)
            known = c in self.visited or kind in SPECIAL_TYPES   # 문에 표시된 특별한 방은 미리 보인다
            cells.append((c, state, kind if known else 'combat', bool(self.layout[c].get('high_haze')) and c in self.visited))
        return cells
