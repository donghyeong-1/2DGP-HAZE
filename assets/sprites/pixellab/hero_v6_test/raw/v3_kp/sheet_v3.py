# v3 확인 시트: 첫 칸 base96, 3배, 어두운 배경.
# 아래 줄에는 같은 프레임 위에 계획한 파이프 끝 궤적(빨간 선, 그 프레임 = 노란 점)을 겹쳐 그린다.
# 사용: python sheet_v3.py <동작> <job_id>   (job_id가 있으면 먼저 내려받음)
import sys, os, json, glob, urllib.request
import numpy as np
from PIL import Image, ImageDraw

D = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.dirname(D)
OUT = "C:/code/2-2/2DGP-project/shots/pixellab_test/"
name = sys.argv[1]
folder = os.path.join(RAW, "v3_" + name)
if len(sys.argv) > 2:
    os.makedirs(folder, exist_ok=True)
    for i in range(8):
        url = f"https://api.pixellab.ai/mcp/images/{sys.argv[2]}/download?index={i}"
        try:
            urllib.request.urlretrieve(url, os.path.join(folder, f"frame_{i}.png"))
        except Exception as e:
            print("fail", i, e)
tips = json.load(open(os.path.join(D, "tips.json")))[name]
base = Image.open(os.path.join(RAW, "base96.png")).convert("RGBA")
pal = np.unique(np.array(base)[np.array(base)[..., 3] > 0][:, :3], axis=0).astype(int)
fs = [Image.open(f).convert("RGBA") for f in sorted(glob.glob(folder + "/frame_*.png"), key=lambda p: int(p.split("_")[-1][:-4]))]
W, S = 96, 3
cells = [base] + fs
cv = Image.new("RGB", (W * S * len(cells), W * S * 2), (18, 24, 40))
for k, f in enumerate(cells):
    t = Image.new("RGBA", (W, W), (18, 24, 40, 255))
    t.alpha_composite(f)
    big = t.resize((W * S, W * S), Image.NEAREST)
    cv.paste(big.convert("RGB"), (k * W * S, 0))
    ov = big.copy()
    d = ImageDraw.Draw(ov)
    if k > 0:
        pts = [(x * W * S, y * W * S) for x, y in tips]
        d.line(pts, fill=(255, 80, 80), width=2)
        p = pts[k - 1]
        d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill=(255, 220, 60))
    cv.paste(ov.convert("RGB"), (k * W * S, W * S))
cv.save(OUT + f"v3_{name}.png")
px = np.concatenate([np.array(f)[np.array(f)[..., 3] > 0][:, :3].astype(int) for f in fs])
off = (np.sqrt(((px[:, None] - pal[None]) ** 2).sum(2)).min(1) > 0).mean()
edge = sum(1 for f in fs if f.getbbox() and (f.getbbox()[0] == 0 or f.getbbox()[1] == 0 or f.getbbox()[2] == W))
print(name, len(fs), "off %.0f%%" % (off * 100), "edge", edge)
