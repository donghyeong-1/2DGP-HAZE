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
    ('line', '은신처 배경 · NPC 3명 · 궁극기 컷인과 시전 자세 · 아이콘 · 진열대'),
    ('small', '이미지 모델명은 도구가 제공하지 않았다. 생성 기록: docs/image_prompts.md'),
    ('line', 'agent-sprite-forge (0x0funky, MIT) - 원화 다듬기·픽셀 마무리 도구'),
    ('gap', ''),
    ('head', '그래픽'),
    ('line', '캐릭터·적·보스·NPC 동작 - AI 생성 원화를 직접 픽셀로 마무리'),
    ('line', '타일·이펙트·HUD·무기 아이콘·로고 - 코드로 직접 그림 (code-drawn)'),
    ('gap', ''),
    ('head', '소리'),
    ('line', '효과음 109종 · 배경음악 8곡'),
    ('line', '효과음 - 코드로 합성 (numpy) + 녹음 원본'),
    ('line', '효과음 녹음 원본 - Kenney (kenney.nl) Impact · Interface · Sci-fi · RPG · Digital Audio, CC0'),
    ('line', '배경음악 - OpenGameArt.org'),
    ('small', 'Rise of Spirit · Alexandr Zhelanov (CC-BY 3.0) - 타이틀'),
    ('small', 'Galactic Temple · yd (CC0) - 은신처'),
    ('small', 'EmptyCity · yd (CC0) - 슬럼'),
    ('small', 'Gi-i Dark Ambient Techno · SouljahdeShiva (CC-BY 3.0) - 공장'),
    ('small', 'Ancient Apparitions · marcelofg55 (CC-BY 3.0) - 탑'),
    ('small', 'Dark Horse · Centurion_of_war (CC0) - 전투'),
    ('small', 'Battle Theme A · cynicmusic (CC0) - 크래셔'),
    ('small', 'The 9th Circle · Joth (CC0) - 최종 보스 아크'),
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


SCENES = ('credits_1', 'credits_2', 'credits_3')     # Codex T35: 탈출 뒤 장면 (언덕 -> 은신처 -> 도시)
_scene = SCENES[0]


def scene_for(scroll_px):
    """크레딧이 흐른 정도에 따라 보여 줄 장면 (전체 길이를 셋으로 나눈다)."""
    total = total_height() + config.SCREEN_H * 0.5 + 180
    i = min(len(SCENES) - 1, int(len(SCENES) * max(0.0, scroll_px) / total))
    return SCENES[i]


def enter():
    global scroll, _fast, _ignore_input, _scene
    _scene = SCENES[0]
    scroll, _fast, _ignore_input = 0.0, False, 0.5
    import transition
    transition.reveal()
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
    global _scene
    nxt = scene_for(scroll)
    if nxt != _scene:                              # 장면이 바뀔 때 점묘로 넘긴다
        import transition
        _scene = nxt
        transition.reveal()
    if finished():
        _to_title()


def draw():
    clear_canvas()
    W, H = config.SCREEN_W, config.SCREEN_H
    assets.draw_image(assets.image(f'backgrounds/{_scene}.png'), W // 2, 0)   # 탈출 뒤 장면 (Codex T35)
    assets.draw_rect_color(0, 0, W, H, (6, 9, 18), 0.5)           # 그림 위에서도 글자가 읽히게 어둡게 덮는다
    y = int(scroll) - 40                                          # 첫 줄은 화면 아래에서 시작한다
    for kind, text in CREDITS:
        step, color, big, small = STYLE[kind]
        if color is not None and -60 < y < H + 60:
            assets.draw_text(W // 2, y, text, color, center=True, big=big, small=small)
        y -= step
    assets.draw_rect_color(0, 0, W, 70, (6, 9, 18), 1.0)                     # 안내 줄 뒤는 막아 올라오는 글자와 겹치지 않게
    assets.draw_text(W // 2, 34, '키를 누르고 있으면 빨리 감기   Esc 타이틀로', (110, 125, 150), small=True, center=True)
    import transition
    transition.draw()                              # 화면 전환 점묘 (계획 4-3, 가장 위)
    update_canvas()
