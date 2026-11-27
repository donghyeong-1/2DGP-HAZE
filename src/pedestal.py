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
# 아이콘을 놓는 높이(발에서 px): 받침 가운데 윗면에서 아이콘 아래 빈 줄(2~6px)만큼 내린 자리 (Q1 2026-11-27, PixelLab 진열대.
# 그 전 Codex 진열대는 둘 다 66이었다)
ICON_Y = {'gold': 44, 'shop': 56}
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
        base = 'shop' if self.mode == 'shop' else 'gold'                # gold(제단: 황금방·균열방) / shop(선반)
        art = ('gone_shop' if base == 'shop' else 'gone') if self.gone else base   # 품절·가져감: 같은 그림을 어둡게 (Q1)
        assets.draw_image(assets.image(f'ui/pedestal_{art}.png'), self.x, self.y)
        if not self.gone:                                              # 받침 윗면에 아이템 아이콘 (1배)
            assets.draw_image(assets.image(f'ui/icon_{self.item_id}.png'), self.x, self.y + ICON_Y[base])
        import game_world
        if game_world.quiet:                                           # R1: mist 메뉴 창 뒤에 깔린 멈춘 화면에서는 이름판·안내를 빼고
            return
        if self.player is not None and not self.gone and self.near(self.player):
            desc = items.describe(self.player, self.item_id)
            if self.mode == 'rift' and self.item_id in items.UPGRADES:   # 두 단계를 한꺼번에: 'N단계' -> 'N~N+1단계'
                n = items.level(self.player, self.item_id) + 1
                desc = '두 단계 한꺼번에 · ' + desc.replace(f'{n}단계', f'{n}~{n + 1}단계', 1)
            import hud_kit as kit
            if kit.is_mist():
                self._draw_mist_info(info, desc)
                return
            x = self.x + text_shift(self.x, max(assets.text_width(info['name']), assets.text_width(desc, True)))
            assets.draw_text(x, self.y + 190, info['name'], info['color'], center=True)
            assets.draw_text(x, self.y + 156, desc, (200, 210, 230), small=True, center=True)
            prompt = f'F 구매 ({self.price}조각)' if self.mode == 'shop' else 'F 획득'
            assets.draw_text(self.x, self.y + 128, prompt, (255, 240, 150), small=True, center=True)
        elif self.gone and self.mode == 'shop':
            assets.draw_text(self.x, self.y + 128, '품절', (130, 140, 160), small=True, center=True)


    def _draw_mist_info(self, info, desc):
        """'mist' (11/27 S1): 이름·설명·안내를 H1 문 위 보상 판과 같은 가는 테두리 판 하나에 담는다.
        황금방(하나만 무료로 고르는 특별 보상)은 금 테두리, 나머지는 회백. 조각 값(헤이즈)은 청록, 경고 노랑은 쓰지 않는다.
        판 아래 진열대 아이콘과 겹치지 않게 글자 묶음을 철판 때보다 12~14px 올린다. 문구는 그대로."""
        import hud_kit as kit
        prompt = f'F 구매 ({self.price}조각)' if self.mode == 'shop' else 'F 획득'
        w = max(assets.text_width(info['name']), assets.text_width(desc, True), assets.text_width(prompt, True)) + 48
        w = w // 2 * 2
        x = int(self.x + text_shift(self.x, w))
        kit.hud_panel('plate', x - w // 2, self.y + MIST_INFO_Y, w, MIST_INFO_H, 'gold' if self.mode == 'gold' else 'line')
        kit.text(x, self.y + 204, info['name'], info['color'], center=True)
        kit.text(x, self.y + 172, desc, (205, 215, 235), small=True, center=True)
        kit.text(x, self.y + 142, prompt, (130, 235, 225) if self.mode == 'shop' else (236, 240, 248), small=True, center=True)


MIST_INFO_Y, MIST_INFO_H = 122, 106      # mist 이름판: 진열대 발 위 122px부터 (아이콘 위 끝 +114 위), 높이
