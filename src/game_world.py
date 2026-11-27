"""world 리스트. 객체를 레이어별로 보관하고 update/draw를 레이어 순서대로 호출한다."""

# 레이어 번호 = 그리기 순서
LAYER_BACKGROUND = 0
LAYER_TILES = 1
LAYER_ENEMY = 2
LAYER_PLAYER = 3
LAYER_EFFECT = 4
LAYER_UI = 5

world = [[] for _ in range(6)]
# R1(11/27): mist 메뉴 창(일시정지·NPC 창·연습 메뉴·효과음 듣기·설정)이 뒤에 멈춘 게임을 깔 때 True.
# 게임의 글자 덮개(처음 안내 카드·연습장 글자·NPC 이름표·머리 위 안내·진열대 이름판)는 그리지 않는다 (창의 글자 뒤로 비쳐 겹쳤다)
quiet = False


def add_object(obj, layer):
    world[layer].append(obj)


def remove_object(obj):
    for layer in world:
        if obj in layer:
            layer.remove(obj)
            return


def update(dt):
    for layer in world:
        for obj in list(layer):  # 순회 중 삭제를 허용하려고 복사본을 돈다
            obj.update(dt)


def render(before_layer=None):
    """before_layer(번호)가 있으면 각 레이어를 그리기 직전에 부른다 (화면 흔들림을 UI에는 걸지 않으려고)."""
    for number, layer in enumerate(world):
        if before_layer:
            before_layer(number)
        for obj in layer:
            obj.draw()


def clear():
    for layer in world:
        layer.clear()
