"""이미지·글꼴 로드와 캐시. 같은 파일은 한 번만 읽는다. pico2d는 실제로 그릴 때 불러온다."""
import os
import sys


def resource_root(frozen=None, bundle=None):
    """에셋·데이터가 있는 폴더. 실행 파일(PyInstaller)이면 풀어 둔 폴더(sys._MEIPASS), 아니면 저장소 폴더."""
    if frozen is None:
        frozen = getattr(sys, 'frozen', False)
    if frozen:
        return bundle or getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


ROOT = resource_root()
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


_silhouettes = {}


def silhouette(relative_path):
    """그림의 모양만 흰색으로 채운 판 (색 테두리용). 처음 한 번 Pillow로 만들어 임시 폴더에 두고 불러온다.
    알파는 원본 그대로(켜짐·꺼짐)라 픽셀 규칙을 지킨다."""
    if relative_path not in _silhouettes:
        import tempfile
        from PIL import Image
        from pico2d import load_image
        folder = os.path.join(tempfile.gettempdir(), 'haze_silhouettes')
        os.makedirs(folder, exist_ok=True)
        out = os.path.join(folder, relative_path.replace('/', '_'))
        src = Image.open(os.path.join(ASSET_DIR, relative_path)).convert('RGBA')
        white = Image.new('RGBA', src.size, (255, 255, 255, 255))
        white.putalpha(src.getchannel('A'))
        white.save(out)
        _silhouettes[relative_path] = load_image(out)
    return _silhouettes[relative_path]


_outlines = {}


def outline_image(relative_path, radius, color=(6, 8, 14), rim=0, rim_color=(110, 140, 185)):
    """그림의 모양을 radius px만큼 부풀려 한 색으로 채운 판 (검은 테두리용). rim px만큼은 그 바깥에 rim_color 선을 더 두른다
    (어두운 방에서 검은 선이 묻히지 않게). 사방 (radius+rim) px 여백이 붙은 (w+2R)x(h+2R) 판이다 (R=radius+rim).
    원본 위치에 맞추려면 x는 그대로, y는 R만큼 내려 그리면 된다 (너비 차가 짝수라 가운데가 같다). 알파는 켜짐·꺼짐뿐이라 픽셀 규칙을 지킨다."""
    key = (relative_path, radius, color, rim, rim_color)
    if key not in _outlines:
        import tempfile
        from PIL import Image, ImageChops
        from pico2d import load_image
        folder = os.path.join(tempfile.gettempdir(), 'haze_outlines')
        os.makedirs(folder, exist_ok=True)
        tag = f'{radius}_{"-".join(map(str, color))}_{rim}_{"-".join(map(str, rim_color))}_'
        out = os.path.join(folder, tag + relative_path.replace('/', '_'))
        src = Image.open(os.path.join(ASSET_DIR, relative_path)).convert('RGBA')
        w, h = src.size
        big = radius + rim
        alpha = src.getchannel('A').point(lambda v: 255 if v > 0 else 0)
        padded = Image.new('L', (w + 2 * big, h + 2 * big), 0)
        padded.paste(alpha, (big, big))

        def grow(r):                                   # 둥근 모양(원 안의 칸)으로 부풀린다. 게임 실행에 numpy가 없어도 되게 Pillow만
            g = Image.new('L', padded.size, 0)         # (여백이 r 이상이라 offset이 가장자리를 넘겨 감싸도 빈칸끼리다)
            for oy in range(-r, r + 1):
                for ox in range(-r, r + 1):
                    if ox * ox + oy * oy <= r * r + 1:
                        g = ImageChops.lighter(g, ImageChops.offset(padded, ox, oy))
            return g
        inner = grow(radius)
        outer = grow(big) if rim else inner
        img = Image.new('RGBA', padded.size, (0, 0, 0, 0))
        img.paste(rim_color + (255,), (0, 0) + padded.size, outer)
        img.paste(color + (255,), (0, 0) + padded.size, inner)
        img.save(out)
        _outlines[key] = load_image(out)
    return _outlines[key]


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


def draw_image_added(img, x, y, flip='', color=None, times=2):
    """더하기 섞기(밝게 겹치기)로 그린다: 같은 그림을 더해 하얗게 번쩍이게(기본 두 번) 하거나, color를 곱해 색 테두리를
    만들 때. 끝나면 원래대로."""
    from sdl2 import SDL_BLENDMODE_ADD, SDL_BLENDMODE_BLEND, SDL_SetTextureBlendMode, SDL_SetTextureColorMod
    SDL_SetTextureBlendMode(img.texture, SDL_BLENDMODE_ADD)
    if color is not None:
        SDL_SetTextureColorMod(img.texture, *color)
    try:
        for _ in range(times):                     # 두 번 더하면 거의 흰색 (어두운 옷도 밝게 보인다)
            draw_image(img, x, y, flip)
    finally:
        SDL_SetTextureBlendMode(img.texture, SDL_BLENDMODE_BLEND)
        if color is not None:
            SDL_SetTextureColorMod(img.texture, 255, 255, 255)


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


def draw_clip_added(img, left, bottom, w, h, x, y, flip='', scale=1, alpha=1.0, color=None):
    """draw_clip을 더하기 섞기로 (빛 층 assets/light 전용: 시트 칸 둘레로 번지는 빛). color를 주면 그 색을 곱한다. 끝나면 원래대로."""
    from sdl2 import SDL_BLENDMODE_ADD, SDL_BLENDMODE_BLEND, SDL_SetTextureBlendMode, SDL_SetTextureColorMod
    SDL_SetTextureBlendMode(img.texture, SDL_BLENDMODE_ADD)
    if color is not None:
        SDL_SetTextureColorMod(img.texture, *color)
    img.opacify(alpha)
    try:
        draw_clip(img, left, bottom, w, h, x, y, flip, scale)
    finally:
        SDL_SetTextureBlendMode(img.texture, SDL_BLENDMODE_BLEND)
        SDL_SetTextureColorMod(img.texture, 255, 255, 255)
        img.opacify(1.0)


def draw_clip_tinted(img, left, bottom, w, h, x, y, color, scale=1):
    """draw_clip에 색을 곱해서 (회색조로 구운 이펙트 색 층에 공격 색을 입힌다, tools/fxkit.export_tint). 끝나면 원래대로."""
    from sdl2 import SDL_SetTextureColorMod
    SDL_SetTextureColorMod(img.texture, *color)
    try:
        draw_clip(img, left, bottom, w, h, x, y, '', scale)
    finally:
        SDL_SetTextureColorMod(img.texture, 255, 255, 255)


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


_channels_ready = [False]


def sound(name):
    """assets/sfx/<name>.wav 를 불러와 캐시한다. 오디오를 쓸 수 없으면 None."""
    if name not in _sounds:
        try:
            if not _channels_ready[0]:                 # v7 효과음 v3: 휘두르기·무기·재질·처치 소리가 겹친다 (기본 8 -> 32)
                _channels_ready[0] = True
                from sdl2.sdlmixer import Mix_AllocateChannels
                Mix_AllocateChannels(32)
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


PRELOAD_FOLDERS = ('sprites/unified', 'effects', 'props', 'props/boss', 'decor', 'tiles', 'ui', 'backgrounds', 'portraits', 'placeholder')


def preload(sounds=True):
    """게임이 쓰는 그림(과 효과음)을 시작할 때 한 번에 읽는다 (2026-11-21). 처음 쓰는 순간 읽으면 그 프레임이
    끊긴다(점검 도구 smoke_run: 첫 방 입장 약 45ms). 모두 읽는 데 약 0.7초. 읽은 그림 수를 돌려준다."""
    import glob
    count = 0
    for folder in PRELOAD_FOLDERS:
        for path in sorted(glob.glob(os.path.join(ASSET_DIR, folder, '*.png'))):
            image(folder + '/' + os.path.basename(path))
            count += 1
    for path in sorted(glob.glob(os.path.join(ASSET_DIR, 'sprites', 'unified', '*.png'))):
        name = os.path.basename(path)
        if name.startswith(('enemy_', 'boss_')):           # 적 테두리(얇은 테두리·정예) 판도 미리 만든다 (싸우는 중 끊기지 않게)
            silhouette('sprites/unified/' + name)
    if sounds:
        for path in sorted(glob.glob(os.path.join(ASSET_DIR, 'sfx', '*.wav'))):
            sound(os.path.basename(path)[:-4])
    return count


_variant_turn = {}


def variant_of(name):
    """자주 나는 소리는 3버전을 차례로 돌린다 (같은 소리가 기관총처럼 반복되지 않게). 그 밖의 소리는 그대로."""
    import config
    if name not in config.SFX_VARIANTS:
        return name
    k = _variant_turn.get(name, 0)
    _variant_turn[name] = (k + 1) % 3
    return name if k == 0 else f'{name}_v{k + 1}'


def play_sound(name):
    """효과음 재생. 소리가 꺼져 있거나 오디오가 없으면 조용히 넘어간다."""
    import config
    if not config.SOUND_ENABLED:
        return
    base, name = name, variant_of(name)
    wav = sound(name)
    if wav is not None:
        import options
        wav.set_volume(options.volume(config.SFX_VOLUME * sfx_gain(base), options.sfx_level))   # 설정 크기 x 소리별 균형
        wav.play()


_music = {}
current_music = None   # 지금 틀고 있는 곡 이름 (없으면 None)


MUSIC_EXTS = ('.ogg', '.mp3', '.wav')      # v7 (2026-11-24): OpenGameArt 곡은 ogg·mp3 그대로 쓴다 (SDL_mixer가 읽는다)
MUSIC_FADE_MS = 700                        # 곡이 바뀔 때 새 곡이 서서히 커지는 시간
_music_pos = {}                            # 곡 이름 -> 마지막으로 멈춘 위치(초). 전투곡 <-> 탐험곡을 오가도 처음부터 다시 틀지 않는다


def music_path(name):
    """assets/music/<name>.(ogg|mp3|wav) 중 있는 파일. 없으면 None."""
    for ext in MUSIC_EXTS:
        p = os.path.join(ASSET_DIR, 'music', name + ext)
        if os.path.exists(p):
            return p
    return None


def play_music(name):
    """배경음악을 반복 재생한다. 같은 곡이 이미 나오고 있으면 그대로 둔다.
    v7: 곡이 바뀌면 지금 곡의 위치를 기억하고, 새 곡은 기억한 위치에서 서서히 커지며 시작한다.
    소리가 꺼져 있거나 오디오가 없으면 곡 이름만 기억하고 조용히 넘어간다."""
    global current_music
    if name == current_music:
        return
    old = current_music
    current_music = name
    import config
    if not config.SOUND_ENABLED:
        return
    try:
        import sdl2.sdlmixer as mix
        if old is not None and _music.get(old) is not None:
            try:
                _music_pos[old] = float(mix.Mix_GetMusicPosition(_music[old].music))
            except Exception:
                pass
        if name not in _music:
            from pico2d import load_music
            _music[name] = load_music(music_path(name))
        import options
        _music[name].set_volume(int(options.volume(config.MUSIC_VOLUME, options.music_level) * music_duck))
        try:
            mix.Mix_FadeInMusicPos(_music[name].music, -1, MUSIC_FADE_MS, _music_pos.get(name, 0.0))
        except Exception:
            _music[name].repeat_play()
    except Exception:
        _music[name] = None


music_duck = 1.0      # 음악 크기 배율 (페이드 구간에서 먹먹하게, drama.music_duck)


def set_music_duck(k):
    """음악 크기 배율을 바꾼다 (바뀔 때만 적용)."""
    global music_duck
    if abs(k - music_duck) > 1e-6:
        music_duck = k
        apply_music_volume()


def apply_music_volume():
    """설정에서 음악 크기를 바꿨을 때 지금 나오는 곡에 바로 적용한다."""
    import config
    import options
    music = _music.get(current_music)
    if music is not None and config.SOUND_ENABLED:
        try:
            music.set_volume(int(options.volume(config.MUSIC_VOLUME, options.music_level) * music_duck))
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
