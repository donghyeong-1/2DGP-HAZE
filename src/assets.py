"""이미지·글꼴 로드와 캐시. 같은 파일은 한 번만 읽는다. pico2d는 실제로 그릴 때 불러온다."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(ROOT, 'assets')
DATA_DIR = os.path.join(ROOT, 'data')

_images = {}
draw_offset = (0, 0)  # 화면 흔들림. 세계(타일·캐릭터·이펙트)를 그릴 때만 정수 픽셀로 켠다
_fonts = {}


def image(relative_path):
    """assets/ 아래 이미지를 반환한다. 예: image('sprites/unified/n09_idle.png')"""
    if relative_path not in _images:
        from pico2d import load_image
        _images[relative_path] = load_image(os.path.join(ASSET_DIR, relative_path))
    return _images[relative_path]


def draw_image(img, x, y, flip=''):
    """이미지를 원본 크기(1배)로 정수 좌표에 그린다. x는 가운데, y는 아래 가장자리.

    픽셀 아트 규칙: 확대·축소·회전 없이 그리고, 위치는 항상 정수 픽셀에 맞춘다.
    """
    left = int(round(x)) - img.w // 2 + draw_offset[0]
    bottom = int(round(y)) + draw_offset[1]
    if flip:
        img.composite_draw(0, flip, left + img.w / 2, bottom + img.h / 2, img.w, img.h)
    else:
        img.draw_to_origin(left, bottom)


def draw_image_tinted(img, x, y, flip, color, alpha):
    """색을 곱하고 투명도를 줘서 그린다(잔상용). 크기·위치 규칙은 draw_image와 같고, 끝나면 원래대로 되돌린다."""
    from sdl2 import SDL_SetTextureColorMod
    SDL_SetTextureColorMod(img.texture, *color)
    img.opacify(alpha)
    try:
        draw_image(img, x, y, flip)
    finally:
        SDL_SetTextureColorMod(img.texture, 255, 255, 255)
        img.opacify(1.0)


def draw_image_added(img, x, y, flip=''):
    """더하기 섞기(밝게 겹치기)로 그린다: 같은 그림을 한 번 더 더해 하얗게 번쩍이게 할 때. 끝나면 원래대로."""
    from sdl2 import SDL_BLENDMODE_ADD, SDL_BLENDMODE_BLEND, SDL_SetTextureBlendMode
    SDL_SetTextureBlendMode(img.texture, SDL_BLENDMODE_ADD)
    try:
        for _ in range(2):                         # 두 번 더하면 거의 흰색 (어두운 옷도 밝게 보인다)
            draw_image(img, x, y, flip)
    finally:
        SDL_SetTextureBlendMode(img.texture, SDL_BLENDMODE_BLEND)


def draw_clip(img, left, bottom, w, h, x, y, flip='', scale=1):
    """시트에서 (left, bottom, w, h) 칸을 잘라 화면의 왼쪽 아래 (x, y)에 그린다. 정수 좌표만 쓰고,
    scale은 정수(최근접 확대)만 허용한다. 이펙트에서만 2배를 쓴다 (docs/pixel_rules.md)."""
    assert isinstance(scale, int) and scale >= 1, '배율은 정수만'
    x, y = int(round(x)) + draw_offset[0], int(round(y)) + draw_offset[1]
    dw, dh = w * scale, h * scale
    if flip:
        img.clip_composite_draw(left, bottom, w, h, 0, flip, x + dw / 2, y + dh / 2, dw, dh)
    else:
        img.clip_draw_to_origin(left, bottom, w, h, x, y, dw, dh)


def draw_rect_color(left, bottom, w, h, color, alpha=1.0):
    """임의 색의 단색 사각형을 정수 좌표로 채운다 (직선 이펙트 같은 코드 그림용). 확대·회전 없이 사각형만 쓴다."""
    from sdl2 import SDL_SetTextureColorMod
    img = image('placeholder/px_white.png')
    SDL_SetTextureColorMod(img.texture, *color)
    img.opacify(alpha)
    try:
        draw_rect_image(img, left, bottom, w, h)
    finally:
        SDL_SetTextureColorMod(img.texture, 255, 255, 255)
        img.opacify(1.0)


def draw_rect_image(img, left, bottom, w, h):
    """단색 사각형(placeholder/px_*.png)을 정수 좌표로 채운다. 무늬 없는 색 칸 전용."""
    img.draw_to_origin(int(round(left)) + draw_offset[0], int(round(bottom)) + draw_offset[1], int(round(w)), int(round(h)))


# 갈무리(Galmuri, SIL OFL 1.1) 픽셀 폰트. 글자는 폰트의 원래 크기로만 그린다(docs/pixel_rules.md 규칙 6).
FONT_SIZES = {'normal': 14, 'small': 11}   # 원본(도트 하나가 1px) 크기. 실제로는 이 값의 정수 배로 불러온다
FONT_MULTIPLES = {'normal': 1, 'small': 1, 'big': 3}  # 종류별 추가 배수 (big은 14px의 3배 = 42px, 제목용)


_sounds = {}


def sfx_gain(name):
    """효과음 음량 균형 배율 (config.SFX_GAIN, 없으면 1.0)."""
    import config
    return config.SFX_GAIN.get(name, 1.0)


def sound(name):
    """assets/sfx/<name>.wav 를 불러와 캐시한다. 오디오를 쓸 수 없으면 None."""
    if name not in _sounds:
        try:
            from pico2d import load_wav
            wav = load_wav(os.path.join(ASSET_DIR, 'sfx', name + '.wav'))
            if wav is not None:
                import config
                import options
                wav.set_volume(options.volume(config.SFX_VOLUME * sfx_gain(name), options.sfx_level))
            _sounds[name] = wav
        except Exception:
            _sounds[name] = None
    return _sounds[name]


def play_sound(name):
    """효과음 재생. 소리가 꺼져 있거나 오디오가 없으면 조용히 넘어간다."""
    import config
    if not config.SOUND_ENABLED:
        return
    wav = sound(name)
    if wav is not None:
        import options
        wav.set_volume(options.volume(config.SFX_VOLUME * sfx_gain(name), options.sfx_level))   # 설정 크기 x 소리별 균형
        wav.play()


_music = {}
current_music = None   # 지금 틀고 있는 곡 이름 (없으면 None)


def play_music(name):
    """배경음악(assets/music/<name>.wav)을 반복 재생한다. 같은 곡이 이미 나오고 있으면 그대로 둔다.
    소리가 꺼져 있거나 오디오가 없으면 곡 이름만 기억하고 조용히 넘어간다."""
    global current_music
    if name == current_music:
        return
    current_music = name
    import config
    if not config.SOUND_ENABLED:
        return
    try:
        if name not in _music:
            from pico2d import load_music
            _music[name] = load_music(os.path.join(ASSET_DIR, 'music', name + '.wav'))
        import options
        _music[name].set_volume(options.volume(config.MUSIC_VOLUME, options.music_level))
        _music[name].repeat_play()
    except Exception:
        _music[name] = None


def apply_music_volume():
    """설정에서 음악 크기를 바꿨을 때 지금 나오는 곡에 바로 적용한다."""
    import config
    import options
    music = _music.get(current_music)
    if music is not None and config.SOUND_ENABLED:
        try:
            music.set_volume(options.volume(config.MUSIC_VOLUME, options.music_level))
        except Exception:
            pass


def stop_music():
    global current_music
    music = _music.get(current_music)
    current_music = None
    if music is not None:
        music.stop()


def _font_key(small=False, big=False):
    return 'big' if big else ('small' if small else 'normal')


def _font_px(key):
    import config
    if key == 'big':
        return FONT_SIZES['normal'] * FONT_MULTIPLES['big']  # 14px의 3배
    return FONT_SIZES[key] * config.FONT_SCALE


def font(small=False, big=False):
    """한글 픽셀 폰트를 반환한다. 갈무리는 도트 격자 폰트라 원본 크기의 정수 배(28/22/42px)로 불러오면
    도트가 정확히 정수 배로 커진다. 글꼴 파일이 없으면 None (글자는 그리지 않는다)."""
    key = _font_key(small, big)
    if key not in _fonts:
        base = FONT_SIZES['normal' if key == 'big' else key]
        path = os.path.join(ASSET_DIR, 'fonts', f'Galmuri{base}.ttf')
        if os.path.exists(path):
            from pico2d import load_font
            _fonts[key] = load_font(path, _font_px(key))
        else:
            _fonts[key] = None
    return _fonts[key]


def text_width(text, small=False, big=False):
    f = font(small, big)
    if f is None:
        return 0
    import ctypes
    from sdl2.sdlttf import TTF_SizeUTF8
    w, h = ctypes.c_int(0), ctypes.c_int(0)
    TTF_SizeUTF8(f.font, text.encode('utf-8'), ctypes.byref(w), ctypes.byref(h))
    return w.value


def draw_text(x, y, text, color=(255, 255, 255), small=False, center=False, big=False):
    """글자를 그린다. center=True면 x가 글자의 가운데. 위치는 정수로 맞춘다. big은 제목용 큰 글자."""
    f = font(small, big)
    if f is None:
        return
    left = int(round(x)) - (text_width(text, small, big) // 2 if center else 0)
    f.draw(left + draw_offset[0], int(round(y)) + draw_offset[1], text, color)
