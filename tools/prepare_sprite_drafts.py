"""생성 원본을 정적 게임 스프라이트 시안으로 정리한다."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1] / "assets" / "sprites"
sizes = {"n09": (32, 32), "enemy_slum": (32, 32),
         "enemy_thrower": (32, 32), "enemy_hound": (32, 32),
         "enemy_guard": (32, 32), "boss_crasher": (32, 32),
         "boss_ark": (32, 32)}
for name, canvas_size in sizes.items():
    source = Image.open(root / "source" / f"{name}_idle_generated.png").convert("RGBA")
    # 생성된 미세한 배경 반투명을 제거하고 불투명한 인물 영역을 찾는다.
    alpha = source.getchannel("A").point(lambda a: 255 if a >= 160 else 0)
    bounds = alpha.getbbox()
    if bounds is None:
        raise ValueError(f"불투명한 픽셀이 없음: {name}")
    source.putalpha(alpha)
    character = source.crop(bounds)
    limit = (canvas_size[0] - 4, canvas_size[1] - 2)
    character.thumbnail(limit, Image.Resampling.NEAREST)
    frame = Image.new("RGBA", canvas_size)
    frame.alpha_composite(character, ((canvas_size[0] - character.width) // 2,
                                      canvas_size[1] - character.height - 1))
    frame.save(root / f"{name}_idle.png")
