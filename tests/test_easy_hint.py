"""초보자 모드 안내 (2026-11-25, 밸런스 보고서 제안): 구역 1에서 연달아 쓰러진 사람에게 사망 화면에서 한 줄로 알린다.
창 없이: python tests/test_easy_hint.py

- 구역 1(슬럼)에서 두 판 연달아 쓰러졌고 초보자 모드가 꺼져 있을 때만 나온다.
- 한 번 쓰러진 것, 다른 구역, 탈출, 이미 켠 경우에는 나오지 않는다 (잘하는 사람에게 권하지 않는다).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import talk  # noqa: E402


def last(zone='stage1', streak=2, escaped=False):
    return {'escaped': escaped, 'zone': zone, 'cause': 'slum', 'weapon': 'pipe', 'streak': streak}


def test_hint_after_two_deaths_in_a_row_in_zone_one():
    text = talk.easy_hint(last(), easy_on=False)
    assert text and '초보자 모드' in text and '설정' in text
    assert talk.easy_hint(last(streak=3), easy_on=False)


def test_no_hint_otherwise():
    assert not talk.easy_hint(last(streak=1), easy_on=False)          # 한 번은 누구나 쓰러진다
    assert not talk.easy_hint(last(zone='stage2'), easy_on=False)
    assert not talk.easy_hint(last(escaped=True), easy_on=False)
    assert not talk.easy_hint(last(), easy_on=True)                    # 이미 켰다
    assert not talk.easy_hint(None, easy_on=False)                     # 기록이 없다


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
