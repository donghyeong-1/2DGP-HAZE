"""비어 있는 칸을 제외하고 원화 픽셀을 손실 없이 재배치한다."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent


def main():
    name, count, cols, rows = sys.argv[1], *map(int, sys.argv[2:])
    folder = ROOT / name
    source = Image.open(folder / "source.png").convert("RGB")
    if name == "C":
        # 쓰러진 자세가 넓게 그려져 세 인물 사이의 빈 구간으로 소유 영역을 나눈다.
        bounds = [(0, 0, 400, source.height), (400, 0, 840, source.height),
                  (840, 0, source.width, source.height)]
        width = max(box[2] - box[0] for box in bounds)
        sheet = Image.new("RGB", (width * count, source.height), "#ff00ff")
        for index, box in enumerate(bounds):
            sheet.paste(source.crop(box), (index * width, 0))
        sheet.save(folder / "input.png")
        (folder / "cells.json").write_text(json.dumps(bounds, indent=2) + "\n", encoding="utf-8")
        return
    width = (source.width + cols - 1) // cols
    height = (source.height + rows - 1) // rows
    sheet = Image.new("RGB", (width * count, height), "#ff00ff")
    cells = []
    for index in range(cols * rows):
        y, x = divmod(index, cols)
        bounds = (round(source.width * x / cols), round(source.height * y / rows),
                  round(source.width * (x + 1) / cols), round(source.height * (y + 1) / rows))
        cell = source.crop(bounds)
        if index < count:
            sheet.paste(cell, (index * width, 0))
            cells.append(bounds)
        else:
            pixels = np.asarray(cell, dtype=np.int16)
            key = (pixels[:, :, 0] - pixels[:, :, 1] > 170) & (pixels[:, :, 2] - pixels[:, :, 1] > 170)
            assert key.all(), ("사용하지 않는 칸에 키 색 외 픽셀이 있음", index)
    sheet.save(folder / "input.png")
    (folder / "cells.json").write_text(json.dumps(cells, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
