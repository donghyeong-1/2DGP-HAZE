"""진열대: 황금방과 정비방에서 아이템을 보여 주고, 가까이 가서 F를 누르면 얻는다.

mode 'gold'  : 방에 놓인 여러 개 중 하나만 무료로 얻는다 (하나를 가지면 나머지는 사라진다).
mode 'shop'  : 헤이즈 조각을 내고 산다. 업그레이드는 사면 다음 단계가 올라오고(값이 오른다) 3단계면 품절,
               응급 치료는 한 번 사면 품절이다.
"""
import assets
import config
import items

INTERACT_RANGE = 110   # 가로 거리 (px)
INTERACT_HEIGHT = 170  # 세로 거리 (px)
EDGE = 24              # 이름·설명 글자가 화면 가장자리에서 떨어지는 거리 (px)


def text_shift(world_x, width):
    """가운데 정렬 글자(폭 width)가 화면 밖으로 나가지 않게 옮길 가로 거리. 방 끝 진열대의 긴 설명(형태·무기)용."""
    import camera
    sx = camera.to_screen(world_x, 0)[0]
    half = width // 2
    return min(config.SCREEN_W - EDGE - half, max(EDGE + half, sx)) - sx


class Pedestal:
    def __init__(self, x, y, item_id, mode, price=0):
        self.x, self.y = x, y            # 발 위치(바닥 윗면)
        self.item_id = item_id
        self.mode = mode
        self.price = price
        self.gone = False                # 이미 가져갔거나(황금방) 품절(정비방)
        self.player = None               # 가까이 있는지 보려고 stage가 넣어 준다

    @property
    def info(self):
        return items.ITEMS[self.item_id]

    def near(self, player):
        return abs(player.x - self.x) <= INTERACT_RANGE and abs((player.y) - self.y) <= INTERACT_HEIGHT

    def update(self, dt):
        pass

    def draw(self):
        info = self.info
        kind = 'gone' if self.gone else 'gold' if self.mode == 'rift' else self.mode   # gold(제단) / shop(선반) / gone(품절), 균열방은 제단
        assets.draw_image(assets.image(f'ui/pedestal_{kind}.png'), self.x, self.y)
        if not self.gone:                                              # 받침 위 보관함에 아이템 아이콘 (1배)
            assets.draw_image(assets.image(f'ui/icon_{self.item_id}.png'), self.x, self.y + 66)
        if self.player is not None and not self.gone and self.near(self.player):
            desc = items.describe(self.player, self.item_id)
            if self.mode == 'rift' and self.item_id in items.UPGRADES:   # 두 단계를 한꺼번에: 'N단계' -> 'N~N+1단계'
                n = items.level(self.player, self.item_id) + 1
                desc = '두 단계 한꺼번에 · ' + desc.replace(f'{n}단계', f'{n}~{n + 1}단계', 1)
            x = self.x + text_shift(self.x, max(assets.text_width(info['name']), assets.text_width(desc, True)))
            assets.draw_text(x, self.y + 190, info['name'], info['color'], center=True)
            assets.draw_text(x, self.y + 156, desc, (200, 210, 230), small=True, center=True)
            prompt = f'F 구매 ({self.price}조각)' if self.mode == 'shop' else 'F 획득'
            assets.draw_text(self.x, self.y + 128, prompt, (255, 240, 150), small=True, center=True)
        elif self.gone and self.mode == 'shop':
            assets.draw_text(self.x, self.y + 128, '품절', (130, 140, 160), small=True, center=True)
