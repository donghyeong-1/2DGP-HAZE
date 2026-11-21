"""구역 제목 카드 테스트 (창 없이). 실행: python tests/test_zone_card.py

2026-11-21 Codex T33 그림: 스테이지 1~3에 들어가는 순간 가로 띠 일러스트(1920x400)가 가운데에서 위아래로 열리고,
그 위에 구역 이름이 뜬 뒤 닫힌다. 은신처에서는 뜨지 않는다. 카드가 뜨는 구역은 예전 글자 알림(_say)을 하지 않는다.
열림·닫힘은 반투명 없이 띠의 높이(잘라 그리는 줄 수)로 한다 (픽셀 규칙).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

from PIL import Image  # noqa: E402

import zone_card  # noqa: E402


class FakeStage:
    def __init__(self, name, title=''):
        self.name, self.title = name, title


def test_card_images_exist():
    for name, theme in zone_card.CARDS.items():
        im = Image.open(os.path.join(HERE, '..', 'assets', 'backgrounds', f'zone_{theme}.png'))
        assert im.size == (1920, 400), name


def test_opens_holds_and_closes_when_entering_a_stage():
    st = FakeStage('hideout', '은신처')
    card = zone_card.ZoneCard(st)
    card.update(0.1)
    assert not card.visible()                                     # 은신처: 카드 없음
    card.stage = FakeStage('stage1', '제9구역: 폐기물 슬럼')         # 출발 문으로 스테이지 1에 들어갔다
    card.update(0.0)
    assert card.visible() and card.height() == 0                   # 막 열리기 시작
    card.update(zone_card.OPEN / 2)
    assert 0 < card.height() < zone_card.CARD_H
    assert card.height() % 2 == 0                                  # 위아래가 같은 정수 줄 수로 열린다
    card.update(zone_card.OPEN)
    assert card.height() == zone_card.CARD_H
    card.update(zone_card.HOLD)
    assert card.height() < zone_card.CARD_H                        # 닫히는 중
    card.update(zone_card.CLOSE + 0.1)
    assert not card.visible()
    card.update(1.0)
    assert not card.visible()                                      # 같은 구역에서는 다시 뜨지 않는다
    card.stage = FakeStage('stage2', '제4구역: 철골 공장')
    card.update(0.01)
    assert card.visible() and card.theme == 'foundry'


def test_card_replaces_old_title_message():
    assert zone_card.says_title('hideout') and not zone_card.says_title('stage3')
    import game_world
    import stage as stage_mod
    from player import Player
    game_world.clear()
    p = Player(0, 0, None)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    for name, want in (('hideout', ['은신처']), ('stage1', [])):
        said = []
        st = stage_mod.Stage(p, name=name, seed=1)
        st.on_message = said.append
        st.start()
        assert said == want, (name, said)                          # 카드가 뜨는 구역은 글자 알림을 하지 않는다
    game_world.clear()


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
