"""영구 성장(로그라이트): 판이 끝나도 남는 것. pico2d와 무관한 순수 로직이다. (2026-11-19, docs/plan_v4.md 4절)

- 헤이즈 결정: 판이 끝날 때(죽든 이기든) 받는 영구 재화. 판 안의 헤이즈 조각과는 따로다.
  클리어한 방 META_PER_ROOM, 보스·관문 META_PER_END, 탈출 META_ESCAPE.
- 정비사: 결정으로 기본 스탯을 영구 강화한다 (최대 체력, 공격력, 시작 게이지, 대시 충전). 단계마다 값이 오른다.
- 보관인: 결정으로 보관 칸을 열면, 판이 끝날 때 들고 있던 것 하나를 맡겨 다음 판 시작 때 받는다
  (업그레이드는 1단계로만, 무기는 그대로). 한 번 받으면 사라진다.
- 무기 걸이(2026-11-23): 판을 시작할 두 번째 칸 무기를 고른다 (식칼·건틀릿·사슬 중 하나 또는 없음). 고른 것은 저장되어
  다음 판에도 그대로다. 맡겨 둔 무기가 있으면 그 판은 맡긴 무기가 이긴다.
저장은 사용자 홈 폴더의 ~/.haze_save.json (설정 파일과 같은 방식). 읽기·쓰기는 safe_io(임시 파일 후 바꿔 끼우기,
깨지면 .bak에서 되살리고 깨진 파일은 .broken으로 남김). 값의 종류가 이상하면 그 값만 기본값이다.
"""
import os

import config
import items
import safe_io

PATH = os.path.join(os.path.expanduser('~'), '.haze_save.json')

# key -> 이름, 설명, 최대 단계, 단계별 값(결정)
UPGRADES = {
    'hp':     dict(name='단련된 몸', desc=f'최대 체력 +{config.META_HP}', max=5, prices=(8, 12, 18, 26, 36)),
    'attack': dict(name='날 선 손', desc=f'공격력 +{int(config.META_ATTACK * 100)}%', max=5, prices=(10, 15, 22, 30, 40)),
    'gauge':  dict(name='헤이즈 적응', desc=f'시작 게이지 +{config.META_GAUGE}%', max=3, prices=(8, 14, 22)),
    'dash':   dict(name='발놀림', desc=f'대시 충전 -{config.META_DASH:g}초', max=3, prices=(10, 16, 24)),
}
ORDER = ('hp', 'attack', 'gauge', 'dash')
START_WEAPONS = ('pistol', 'gauntlet', 'chain')
ALL_WEAPONS = ('pipe', 'pistol', 'gauntlet', 'chain')      # v8 두 칸 자유: 두 칸 모두 이 넷 중에서 (서로 달라야 한다)
LEGACY_WEAPONS = {'knife': 'pistol'}             # v7 (2026-11-24): 식칼이 쌍권총으로 바뀌었다 (예전 저장을 그대로 읽는다)


def migrate_weapon(weapon_id):
    return LEGACY_WEAPONS.get(weapon_id, weapon_id)   # 무기 걸이에서 고를 수 있는 두 번째 칸 무기 (철파이프는 늘 첫 칸)

state = {}


def _default():
    return {'crystals': 0, 'levels': {k: 0 for k in UPGRADES}, 'keeper': False, 'keepsake': None, 'start_weapon': None,
            'start_first': 'pipe',
            'runs': 0, 'escapes': 0, 'best': '', 'hints': [], 'last': None, 'beaten': []}


def reset():
    """기본 상태로 (테스트·새 저장)."""
    state.clear()
    state.update(_default())


def _int(value, default=0):
    """정수로 읽는다. 이상한 값(글자, None, 목록)은 기본값."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load():
    reset()
    data = safe_io.read_json(PATH)
    if not isinstance(data, dict):
        return
    state['crystals'] = max(0, _int(data.get('crystals', 0)))
    levels = data.get('levels', {})
    if not isinstance(levels, dict):
        levels = {}
    for k, info in UPGRADES.items():
        state['levels'][k] = max(0, min(info['max'], _int(levels.get(k, 0))))
    state['keeper'] = bool(data.get('keeper', False))
    keep = data.get('keepsake')
    state['keepsake'] = keep if isinstance(keep, str) and keep in items.ITEMS else None
    first = migrate_weapon(data.get('start_first'))                 # v8 두 칸 자유: 첫 칸도 고른다 (기본 철파이프)
    state['start_first'] = first if isinstance(first, str) and first in ALL_WEAPONS else 'pipe'
    start = migrate_weapon(data.get('start_weapon'))
    state['start_weapon'] = start if isinstance(start, str) and start in ALL_WEAPONS and start != state['start_first'] else None
    state['runs'] = max(0, _int(data.get('runs', 0)))
    state['escapes'] = max(0, _int(data.get('escapes', 0)))
    state['best'] = str(data.get('best', '') or '')
    hints = data.get('hints', [])
    state['hints'] = [str(h) for h in hints] if isinstance(hints, list) else []   # 이미 본 처음 안내
    beaten = data.get('beaten', [])
    state['beaten'] = [b for b in BOSSES if isinstance(beaten, list) and b in beaten]   # 한 번이라도 쓰러뜨린 보스 (v8 NPC 대사)
    state['last'] = _read_last(data.get('last'))


def save():
    return safe_io.write_json(PATH, state)


def ensure_loaded():
    if not state:
        load()


# ----- 직전 판 기록 (v8 6일 차 NPC 대사, src/talk.py가 읽는다) -----
BOSSES = ('gate', 'crasher', 'ark', 'heart')                     # 구역 순서대로 쓰러뜨리는 것 (관문은 구역 1 끝의 정예 전투)
ZONE_ORDER = ('stage1', 'stage2', 'stage3')
PASSED = {'stage1': (), 'stage2': ('gate',), 'stage3': ('gate', 'crasher')}   # 그 구역에 있었다 = 앞 구역 끝을 넘었다


def _read_last(data):
    """저장된 직전 판 기록을 읽는다. 사전이 아니면 None, 값의 종류가 이상하면 그 값만 기본값."""
    if not isinstance(data, dict):
        return None
    zone = data.get('zone')
    weapon = migrate_weapon(data.get('weapon'))
    weapons = data.get('weapons')
    first = data.get('first')
    return {'escaped': bool(data.get('escaped', False)),
            'zone': zone if isinstance(zone, str) and zone in ZONE_ORDER else '',
            'cause': str(data.get('cause', '') or ''),
            'weapon': weapon if isinstance(weapon, str) and weapon in ALL_WEAPONS else None,
            'weapons': [w for w in (migrate_weapon(w) for w in weapons) if w in ALL_WEAPONS] if isinstance(weapons, list) else [],
            'first': [b for b in BOSSES if isinstance(first, list) and b in first],
            'rooms': max(0, _int(data.get('rooms', 0))), 'kills': max(0, _int(data.get('kills', 0))),
            'streak': max(0, _int(data.get('streak', 0))), 'escapes': max(0, _int(data.get('escapes', 0)))}


def beaten_in_run(zone, escaped, ark_down=False):
    """이 판에 쓰러뜨린 보스: 도달한 구역 앞의 것들 + 탑에서 아크를 눕혔으면 아크, 탈출했으면 전부."""
    if escaped:
        return list(BOSSES)
    out = list(PASSED.get(zone, ()))
    if zone == 'stage3' and ark_down:
        out.append('ark')
    return out


def record_run(player, escaped, zone, ark_down=False):
    """판이 끝날 때 직전 판 기록을 남긴다 (저장은 finish_run이 한다). 처음 쓰러뜨린 보스는 first에."""
    beaten = beaten_in_run(zone, escaped, ark_down)
    first = [b for b in beaten if b not in state['beaten']]
    state['beaten'] = [b for b in BOSSES if b in state['beaten'] or b in beaten]
    prev = state.get('last')
    if escaped:
        streak = 0
    elif isinstance(prev, dict) and not prev.get('escaped') and prev.get('zone') == zone:
        streak = prev.get('streak', 0) + 1
    else:
        streak = 1
    held = getattr(getattr(player, 'weapon', None), 'weapon_id', None)
    state['last'] = {'escaped': bool(escaped), 'zone': zone if zone in ZONE_ORDER else '',
                     'cause': '' if escaped else str(getattr(player, 'death_cause', '') or ''),
                     'weapon': held if held in ALL_WEAPONS else None,
                     'weapons': [w.weapon_id for w in getattr(player, 'weapons', []) if w is not None],
                     'first': first, 'rooms': int(getattr(player, 'run_rooms', 0)), 'kills': int(getattr(player, 'run_kills', 0)),
                     'streak': streak, 'escapes': state['escapes']}
    return state['last']


# ----- 재화 -----
def run_reward(rooms, ends, escaped):
    return rooms * config.META_PER_ROOM + ends * config.META_PER_END + (config.META_ESCAPE if escaped else 0)


def finish_run(player, escaped, zone=None, ark_down=False):
    """판이 끝났다: 결정을 주고 직전 판 기록을 남겨 저장한다. 같은 판에서 두 번 불러도 한 번만 준다. 받은 결정 수를 돌려준다.
    zone: 끝난 구역 이름(stage1~3), ark_down: 탑에서 아크를 쓰러뜨린 뒤였나 (NPC 대사가 쓴다)."""
    ensure_loaded()
    if getattr(player, 'run_rewarded', False):
        return 0
    player.run_rewarded = True
    got = run_reward(player.run_rooms, player.run_ends, escaped) + getattr(player, 'bonus_crystals', 0)
    state['crystals'] += got
    state['runs'] += 1
    if escaped:
        state['escapes'] += 1
    record_run(player, escaped, zone or ('stage3' if escaped else ''), ark_down)
    save()
    return got


# ----- 정비사 -----
def level(key):
    ensure_loaded()
    return state['levels'][key]


def price(key):
    lv = level(key)
    info = UPGRADES[key]
    return info['prices'][lv] if lv < info['max'] else None


def can_buy(key):
    p = price(key)
    return p is not None and state['crystals'] >= p


def buy(key):
    if not can_buy(key):
        return False
    state['crystals'] -= price(key)
    state['levels'][key] += 1
    save()
    return True


# ----- 보관인 -----
def keeper_open():
    ensure_loaded()
    return state['keeper']


def unlock_keeper():
    ensure_loaded()
    if state['keeper'] or state['crystals'] < config.META_KEEPER_PRICE:
        return False
    state['crystals'] -= config.META_KEEPER_PRICE
    state['keeper'] = True
    save()
    return True


def keepsake_options(player):
    """맡길 수 있는 것: 들고 있던 업그레이드·아이템(겹치지 않게) + 두 번째 칸 무기."""
    out = []
    for item_id in player.items:
        if item_id not in out:
            out.append(item_id)
    second = player.weapons[1]
    if second is not None:
        out.append('w_' + second.weapon_id)
    return out


def set_keepsake(item_id):
    if not keeper_open() or (item_id is not None and item_id not in items.ITEMS):
        return False
    state['keepsake'] = item_id
    save()
    return True


# ----- 무기 걸이 -----
def set_start_weapon(weapon_id):
    """판을 시작할 둘째 칸 무기 (None = 비움). 첫 칸과 같은 무기는 안 된다. 저장한다."""
    ensure_loaded()
    if weapon_id is not None and (weapon_id not in ALL_WEAPONS or weapon_id == state['start_first']):
        return False
    state['start_weapon'] = weapon_id
    save()
    return True


def set_start_first(weapon_id):
    """판을 시작할 첫 칸 무기 (v8 두 칸 자유). 둘째 칸의 무기를 고르면 둘이 자리를 바꾼다. 저장한다."""
    ensure_loaded()
    if weapon_id not in ALL_WEAPONS:
        return False
    if weapon_id == state['start_weapon']:
        state['start_weapon'] = state['start_first']
    state['start_first'] = weapon_id
    save()
    return True


def equip_loadout(player):
    """플레이어의 두 칸을 지금 저장된 시작 무기로 (은신처 무기 걸이에서 고른 즉시)."""
    player.set_loadout(state['start_first'], state['start_weapon'])


def equip_start_weapon(player, weapon_id=None):
    """예전 이름 (무기 걸이): 저장된 두 칸을 그대로 입힌다."""
    equip_loadout(player)


# ----- 새 판에 적용 -----
def apply_to_player(player):
    """새 판을 시작하는 플레이어에게 영구 강화와 맡긴 물건을 준다."""
    ensure_loaded()
    apply_levels(player, state['levels'])
    if (state['start_first'], state['start_weapon']) != ('pipe', None):
        player.set_loadout(state['start_first'], state['start_weapon'])   # 무기 걸이에서 고른 두 칸 (맡겨 둔 무기가 있으면 아래에서 바뀐다)
    keep = state['keepsake']
    if keep and 'weapon' in items.ITEMS[keep]:
        player.give_weapon(items.ITEMS[keep]['weapon'], slot=1)           # 맡겨 둔 무기는 둘째 칸에 (시작 무기를 이긴다)
    elif keep:
        items.apply(player, keep)                  # 업그레이드는 1단계(한 번 적용)
    if keep:
        state['keepsake'] = None                   # 한 번 받으면 사라진다
        save()
    return keep


def apply_levels(player, lv):
    """정비사 강화 단계(lv: key -> 단계)를 플레이어 능력치에 적용한다. 저장과 무관 (balance-sim도 쓴다)."""
    player.max_hp += lv['hp'] * config.META_HP
    player.hp = player.max_hp
    player.attack_bonus += lv['attack'] * config.META_ATTACK
    g = player.gauge
    g.value = float(config.GAUGE_START + lv['gauge'] * config.META_GAUGE)
    g.zone = g._zone_of(g.value)
    player.dash_recharge = config.DASH_RECHARGE - lv['dash'] * config.META_DASH
