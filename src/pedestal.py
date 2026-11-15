"""진열대: 황금방과 정비방에서 아이템을 보여 주고, 가까이 가서 F를 누르면 얻는다.

mode 'gold'  : 방에 놓인 여러 개 중 하나만 무료로 얻는다 (하나를 가지면 나머지는 사라진다).
mode 'shop'  : 헤이즈 조각을 내고 산다. 한 번 산 것은 품절이다.
"""
import assets
import config
import items

INTERACT_RANGE = 110   # 가로 거리 (px)
INTERACT_HEIGHT = 170  # 세로 거리 (px)


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
        faded = self.gone
        base = 'px_gray' if faded else 'px_black'
        assets.draw_rect_image(assets.image('placeholder/px_gray.png'), self.x - 46, self.y, 92, 16)          # 받침
        assets.draw_rect_image(assets.image('placeholder/px_black.png'), self.x - 34, self.y + 16, 68, 14)
        # 아이템 표지: 색 칸 위에 한 글자
        color_name = 'px_gray' if faded else 'px_yellow' if self.mode == 'gold' else 'px_cyan'
        assets.draw_rect_image(assets.image('placeholder/px_black.png'), self.x - 34, self.y + 44, 68, 68)
        assets.draw_rect_image(assets.image('placeholder/' + color_name + '.png'), self.x - 30, self.y + 48, 60, 60)
        glyph_color = (60, 70, 90) if faded else (10, 20, 40)
        assets.draw_text(self.x, self.y + 78, info['glyph'], glyph_color, center=True)
        if self.player is not None and not self.gone and self.near(self.player):
            assets.draw_text(self.x, self.y + 190, info['name'], info['color'], center=True)
            assets.draw_text(self.x, self.y + 156, info['desc'], (200, 210, 230), small=True, center=True)
            prompt = 'F 획득' if self.mode == 'gold' else f'F 구매 ({self.price}조각)'
            assets.draw_text(self.x, self.y + 128, prompt, (255, 240, 150), small=True, center=True)
        elif self.gone and self.mode == 'shop':
            assets.draw_text(self.x, self.y + 128, '품절', (130, 140, 160), small=True, center=True)
