"""엔딩 크레딧. 탈출 화면 뒤에 이어지고, 타이틀에서 C로도 볼 수 있다.

글자가 아래에서 위로 천천히 올라간다. 아무 키나 누르고 있으면 빨리 감고, Esc를 누르면 바로 타이틀로 간다.
내용은 docs/ASSETS.md 맨 위 표(지금 게임이 쓰는 에셋)를 따른다. 에셋 출처가 바뀌면 CREDITS도 함께 고친다.
"""
from pico2d import SDL_KEYDOWN, SDL_KEYUP, SDL_QUIT, SDLK_ESCAPE, clear_canvas, get_events, update_canvas

import assets
import config
import game_framework

# (종류, 글자): title 큰 제목 / head 절 제목 / line 본문 / small 작은 설명 / gap 빈 줄
CREDITS = [
    ('title', '헤이즈 (HAZE)'),
    ('small', '안개를 삼키고 탈출하라'),
    ('gap', ''),
    ('head', '기획 · 개발'),
    ('line', '김동형'),
    ('small', '2026년 2학기 2D 게임 프로그래밍 개인 프로젝트'),
    ('gap', ''),
    ('head', '개발 환경'),
    ('line', 'Python 3.12 · pico2d (PySDL2)'),
    ('line', 'transitions (MIT) · numpy · Pillow'),
    ('gap', ''),
    ('head', 'AI 도구'),
    ('line', 'Claude Code (Anthropic) - 게임 코드, 코드로 그린 그림, 합성한 소리'),
    ('line', 'Codex (OpenAI) 내장 이미지 생성 - 캐릭터·적·보스 원화와 동작, 배경판, 화면 일러스트'),
    ('small', '이미지 모델명은 도구가 제공하지 않았다. 생성 기록: docs/image_prompts.md'),
    ('line', 'agent-sprite-forge (0x0funky, MIT) - 원화 다듬기·픽셀 마무리 도구'),
    ('gap', ''),
    ('head', '그래픽'),
    ('line', '캐릭터·적·보스 동작 - AI 생성 원화를 직접 픽셀로 마무리'),
    ('line', '타일·배경·이펙트·HUD·아이콘·로고 - 코드로 직접 그림 (code-drawn)'),
    ('gap', ''),
    ('head', '소리'),
    ('line', '효과음 · 배경음악 - 코드로 직접 합성'),
    ('gap', ''),
    ('head', '글꼴'),
    ('line', 'Galmuri - Lee Minseo (SIL Open Font License 1.1)'),
    ('gap', ''),
    ('gap', ''),
    ('head', '플레이해 주셔서 감사합니다'),
]
STYLE = {'title': (74, (235, 240, 250), True, False), 'head': (80, (130, 235, 225), False, False),
         'line': (54, (210, 220, 235), False, False), 'small': (44, (130, 145, 170), False, True), 'gap': (60, None, False, False)}
SPEED = 70.0             # 올라가는 속도(px/s)
FAST = 5.0               # 키를 누르고 있으면 이만큼 빠르게
scroll = 0.0
_fast = False
_ignore_input = 0.0


def total_height():
    return sum(STYLE[kind][0] for kind, _ in CREDITS)


def finished():
    """마지막 줄이 화면 가운데를 지나 잠시 머문 뒤 끝난다."""
    return scroll >= total_height() + config.SCREEN_H * 0.5 + 180


def enter():
    global scroll, _fast, _ignore_input
    scroll, _fast, _ignore_input = 0.0, False, 0.5
    assets.play_music('title')


def exit():
    pass


def pause():
    pass


def resume():
    pass


def _to_title():
    import title_mode
    game_framework.change_mode(title_mode)


def handle_events():
    global _fast
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and _ignore_input <= 0:
            if event.key == SDLK_ESCAPE:
                _to_title()
                return
            _fast = True
        elif event.type == SDL_KEYUP:
            _fast = False


def update():
    global scroll, _ignore_input
    dt = game_framework.frame_time
    _ignore_input = max(0.0, _ignore_input - dt)
    scroll += SPEED * (FAST if _fast else 1.0) * dt
    if finished():
        _to_title()


def draw():
    clear_canvas()
    W, H = config.SCREEN_W, config.SCREEN_H
    assets.draw_image(assets.image('backgrounds/screen_ending.png'), W // 2, 0)
    assets.draw_rect_color(0, 0, W, H, (6, 9, 18), 0.72)          # 그림 위에서도 글자가 읽히게 어둡게 덮는다
    y = int(scroll) - 40                                          # 첫 줄은 화면 아래에서 시작한다
    for kind, text in CREDITS:
        step, color, big, small = STYLE[kind]
        if color is not None and -60 < y < H + 60:
            assets.draw_text(W // 2, y, text, color, center=True, big=big, small=small)
        y -= step
    assets.draw_rect_color(0, 0, W, 70, (6, 9, 18), 1.0)                     # 안내 줄 뒤는 막아 올라오는 글자와 겹치지 않게
    assets.draw_text(W // 2, 34, '키를 누르고 있으면 빨리 감기   Esc 타이틀로', (110, 125, 150), small=True, center=True)
    update_canvas()
