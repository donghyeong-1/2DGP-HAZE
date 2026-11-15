"""world 리스트. 객체를 레이어별로 보관하고 update/draw를 레이어 순서대로 호출한다."""

# 레이어 번호 = 그리기 순서
LAYER_BACKGROUND = 0
LAYER_TILES = 1
LAYER_ENEMY = 2
LAYER_PLAYER = 3
LAYER_EFFECT = 4
LAYER_UI = 5

world = [[] for _ in range(6)]


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
