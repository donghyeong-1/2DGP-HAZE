"""이벤트 방 (v8 계획 5-4, 2026-11-25): 전투 사이에 한 번 쉬어 가는 방. 구역 1·2의 본 경로에 하나씩 놓인다(mapgen).

- 헤이즈 샘(spring): 게이지를 원하는 구간으로 맞춘다. 한 번만.
- 떠돌이 죄수(drifter): 체력·조각·증강을 맞바꾸는 거래. 하나만.
같은 판의 구역 1과 2에는 서로 다른 이벤트가 나온다(시드가 구역마다 1씩 오른다).
도전방(시간 안에 처치하면 보상이 커진다)은 전투방에 붙는 규칙이라 stage.py에 있다.

카드 창은 증강 선택 창(mutation_mode)을 같이 쓴다: 카드 id가 'event:'로 시작한다.
pico2d를 쓰는 것은 Spot.draw뿐이라 규칙은 창 없이 테스트한다(tests/test_events.py).
"""
import random

import config

CARD = 'event:'
KINDS = ('spring', 'drifter')
NAMES = {'spring': '헤이즈 샘', 'drifter': '떠돌이 죄수'}
COLORS = {'spring': (110, 235, 215), 'drifter': (240, 190, 120)}
TITLES = {'spring': ('헤이즈 샘', '게이지를 원하는 구간으로 맞춥니다. 한 번만 쓸 수 있습니다'),
          'drifter': ('떠돌이 죄수', '거래는 하나만 할 수 있습니다')}
PROMPT = {'spring': 'F 사용', 'drifter': 'F 거래'}
SPRING_FRAMES, SPRING_FRAME = 4, 0.3        # 헤이즈 샘 물결: assets/ui/event_spring_1~4.png, 장당 0.3초
DONE = {'spring': '말라 버렸습니다', 'drifter': '거래를 마쳤습니다'}
INTERACT_RANGE = 130

# 헤이즈 샘: 카드 -> (이름, 구간 이름, 아이콘, 색)
SPRING = {
    'normal': ('가라앉히기', '노멀 구간', 'ui/mut_tide.png', (46, 230, 214)),
    'awake': ('끌어올리기', '각성 구간', 'ui/mut_bloom.png', (92, 220, 255)),
    'critical': ('들이붓기', '위험 구간', 'ui/mut_ember.png', (255, 120, 80)),
}
# 떠돌이 죄수: 카드 -> (이름, 아이콘, 색)
DEALS = {
    'blood': ('증강 거래', 'ui/reward_mutation.png', (150, 240, 225)),
    'heal': ('치료 거래', 'ui/reward_heal.png', (255, 150, 150)),
    'shards': ('조각 거래', 'ui/reward_shards.png', (130, 235, 225)),
    'skip': ('지나가기', None, (150, 165, 190)),
}

current = None          # 지금 카드 창을 연 이벤트 자리 (stage가 넣는다)


def greeting():
    """떠돌이 죄수 인사말 (v8 6일 차): 판마다 돌아가며 (data/dialogue.py DRIFTER). 가까이 가면 머리 위에 뜬다."""
    import meta
    import talk
    meta.ensure_loaded()
    return talk.drifter_line(meta.state.get('runs', 0))


def kind_of(stage):
    """이 구역의 이벤트 종류. 구역이 바뀔 때마다 시드가 1씩 올라 번갈아 나온다."""
    return KINDS[stage.seed % len(KINDS)]


def spring_target(player, key):
    """헤이즈 샘이 맞춰 주는 게이지 값. 위험은 한계 바로 아래(한계는 아이템으로 달라진다)."""
    if key == 'normal':
        return float(config.SPRING_NORMAL)
    if key == 'awake':
        return float(config.SPRING_AWAKE)
    return float(player.gauge.cap - config.SPRING_CRITICAL_BELOW)


def cards(kind):
    if kind == 'spring':
        return [f'{CARD}spring:{k}' for k in SPRING]
    return [f'{CARD}deal:{k}' for k in DEALS]


def card_info(player, card):
    """카드 그리기·고르기에 쓰는 정보: name, sub, desc, color, icon, ok(지금 고를 수 있는가)."""
    _e, group, key = card.split(':')
    if group == 'spring':
        name, zone, icon, color = SPRING[key]
        target = int(spring_target(player, key)) if player is not None else 0
        desc = {'normal': f'게이지를 {target}%로 맞춥니다. 오버로드에서 멀어집니다',
                'awake': f'게이지를 {target}%로 맞춥니다. 공격이 강해집니다',
                'critical': f'게이지를 {target}%로 맞춥니다. 가장 강하지만 오버로드가 가깝습니다'}[key]
        return dict(name=name, sub=zone, desc=desc, color=color, icon=icon, ok=True)
    name, icon, color = DEALS[key]
    hp = player.hp if player is not None else 0
    shards = player.shards if player is not None else 0
    if key == 'blood':
        return dict(name=name, sub=f'체력 -{config.DEAL_BLOOD_HP}', desc='체력을 내고 증강 하나를 선택합니다', color=color, icon=icon,
                    ok=hp > config.DEAL_BLOOD_HP, why='체력이 부족합니다')
    if key == 'heal':
        return dict(name=name, sub=f'조각 -{config.DEAL_HEAL_SHARDS}', desc=f'조각을 내고 체력 {config.DEAL_HEAL_HP} 회복합니다', color=color,
                    icon=icon, ok=shards >= config.DEAL_HEAL_SHARDS, why='조각이 부족합니다')
    if key == 'shards':
        return dict(name=name, sub=f'체력 -{config.DEAL_SHARDS_HP}', desc=f'체력을 내고 조각 {config.DEAL_SHARDS_GAIN}개를 받습니다', color=color,
                    icon=icon, ok=hp > config.DEAL_SHARDS_HP, why='체력이 부족합니다')
    return dict(name=name, sub='거래하지 않습니다', desc='나중에 다시 올 수 있습니다', color=color, icon=icon, ok=True)


def take(player, card, rng=None):
    """카드를 고른다. (화면에 띄울 글, 색, 이어서 고를 카드 목록 또는 None)을 돌려준다. 고를 수 없으면 None."""
    info = card_info(player, card)
    if not info['ok']:
        return None
    _e, group, key = card.split(':')
    follow = None
    text = info['name']
    if group == 'spring':
        player.gauge.set_value(spring_target(player, key), 'spring')
        text = f'게이지 {int(player.gauge.value)}%'
    elif key == 'blood':
        import mutations
        player.hp -= config.DEAL_BLOOD_HP
        follow = mutations.offer(player, rng or random.Random()) or None
        if follow is None:                                  # 내놓을 증강이 없으면 조각으로
            player.shards += config.DEAL_SHARDS_GAIN
    elif key == 'heal':
        player.shards -= config.DEAL_HEAL_SHARDS
        player.hp = min(player.max_hp, player.hp + config.DEAL_HEAL_HP)
        text = f'체력 +{config.DEAL_HEAL_HP}'
    elif key == 'shards':
        player.hp -= config.DEAL_SHARDS_HP
        player.shards += config.DEAL_SHARDS_GAIN
        text = f'조각 +{config.DEAL_SHARDS_GAIN}'
    if key != 'skip' and current is not None:
        current.state['used'] = True
    return text, info['color'], follow


class Spot:
    """이벤트 방 가운데에 놓인 것: 헤이즈 샘(그릇) 또는 떠돌이 죄수(NPC 그림). 가까이 가서 F."""

    def __init__(self, kind, x, y, state):
        self.kind, self.x, self.y = kind, x, y
        self.state = state                # stage.state[방 좌표]: {'used': bool} (다시 들어와도 유지)
        self.player = None
        self.time = 0.0
        self.npc = None
        self.greeting = ''
        if kind == 'drifter':
            from npc import NPC
            self.npc = NPC('drifter', x, y)
            self.greeting = greeting()

    @property
    def used(self):
        return bool(self.state.get('used'))

    def near(self, player):
        return abs(player.x - self.x) <= INTERACT_RANGE and abs(player.y - self.y) <= 170

    def update(self, dt):
        before = int(self.time / 0.9)
        self.time += dt
        if self.npc is not None:
            self.npc.update(dt)
        elif not self.used and int(self.time / 0.9) != before:      # 샘에서 은은한 빛이 오른다
            import effects
            effects.spawn_bloom(self.x, self.y + 70, COLORS['spring'], big=True, life=0.9, strength=0.55)

    def draw(self):
        import assets
        import game_world
        p = self.player
        color = COLORS[self.kind]
        quiet = game_world.quiet                              # R1: mist 메뉴 창 뒤에 깔린 멈춘 화면에서는 글자를 빼고 (그림만)
        if self.npc is not None:
            self.npc.player = None if self.used else p       # 거래를 마치면 안내를 띄우지 않는다
            self.npc.draw()
            top = self.y + 132
            if quiet:
                return
            if p is not None and not self.used and self.npc.near(p) and self.greeting:   # 인사말: 안내('F 거래') 위에
                assets.draw_text(self.x, top + 106, self.greeting, (235, 220, 190), small=True, center=True)
        else:
            frame = 'dry' if self.used else str(int(self.time / SPRING_FRAME) % SPRING_FRAMES + 1)   # 물결 4장 (PixelLab)
            assets.draw_image(assets.image(f'ui/event_spring_{frame}.png'), self.x, self.y)
            top = self.y + 104
            if quiet:
                return
            assets.draw_text(self.x, top + 34, NAMES[self.kind], color if not self.used else (130, 140, 160), small=True, center=True)
            if p is not None and not self.used and self.near(p):
                import npc as npc_mod                                    # R1: 떠돌이 죄수(npc.NPC)의 안내와 같은 모양
                npc_mod.draw_prompt(self.x, top + 70, PROMPT[self.kind])
        if self.used:
            assets.draw_text(self.x, top + 70, DONE[self.kind], (130, 140, 160), small=True, center=True)
