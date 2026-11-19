"""시전 원화의 소유 영역을 분리하고 공통 몸 크기와 발 기준점에 등록한다."""
import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent


def main():
    image=Image.open(ROOT/"source.png").convert("RGB")
    assert image.size==(1536,1024)
    # 원화의 뒷발을 보존하도록 두 인물 사이 빈 구간 x=640으로 분리한다.
    crops=[(0,0,640,1024),(640,0,1536,1024)]
    sheet=Image.new("RGB",(1792,1024),"#ff00ff")
    for index,box in enumerate(crops):
        sheet.paste(image.crop(box),(896*index,0))
    sheet.save(ROOT/"sheet_input.png")
    (ROOT/"cells.json").write_text(json.dumps(crops)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
