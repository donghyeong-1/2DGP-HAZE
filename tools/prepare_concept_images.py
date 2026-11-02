from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

# 원본은 보존하고 발표 자료에 사용할 부분만 추출한다.
root = Path(__file__).resolve().parents[1] / 'assets' / 'concept'
hero = Image.open(root / 'source' / 'protagonist_illust.webp').convert('RGB')
patch = hero.crop((555, 887, 635, 957)).filter(ImageFilter.GaussianBlur(12))
mask = Image.new('L', patch.size)
ImageDraw.Draw(mask).rectangle((12, 8, 66, 60), fill=255)
hero.paste(patch, (625, 887), mask.filter(ImageFilter.GaussianBlur(8)))
hero.save(root / 'n09.png')

sheet = Image.open(root / 'source' / 'enemy_sheet.webp').convert('RGB')
boxes = {
    'boss_ark.png': (25, 22, 305, 615),
    'enemy_slum.png': (310, 38, 510, 420),
    'enemy_thrower.png': (510, 38, 751, 402),
    'enemy_hound.png': (310, 403, 749, 632),
    'enemy_guard.png': (55, 610, 351, 1018),
    'boss_crasher.png': (370, 630, 752, 1018),
}
for name, box in boxes.items():
    image = sheet.crop(box)
    if name == 'enemy_hound.png':
        ImageDraw.Draw(image).rectangle((0, 0, 44, 12), fill=(20, 28, 38))
    if name == 'boss_crasher.png':
        # 오른쪽 아래 표시는 인물 옆의 배경 부분에만 덮는다.
        ImageDraw.Draw(image).rectangle((287, 274, 315, 313), fill=(20, 28, 38))
    image.save(root / name)
