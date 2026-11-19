"""캐릭터 원화를 같은 해부학적 배율로 등록한다."""
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
SOURCE_ROOTS_X = [270,440]
ORIGIN=(550,1000)
RAW_SCALE=1.1


def main():
    source=Image.open(ROOT/"processed/raw-sheet-clean.png").convert("RGBA")
    raw=ROOT/"registered"
    raw.mkdir(exist_ok=False)
    records=[]
    for index,root_x in enumerate(SOURCE_ROOTS_X):
        cell=source.crop((index*896,0,(index+1)*896,1024))
        bounds=cell.getchannel("A").point(lambda a:255 if a>=128 else 0).getbbox()
        floor=bounds[3]-1
        dx=root_x-ORIGIN[0]/RAW_SCALE
        dy=floor-ORIGIN[1]/RAW_SCALE
        frame=cell.transform((1400,1200),Image.Transform.AFFINE,
                             (1/RAW_SCALE,0,dx,0,1/RAW_SCALE,dy),Image.Resampling.BICUBIC)
        bb=frame.getbbox()
        assert bb[0]>8 and bb[1]>8 and bb[2]<1392 and bb[3]<1192
        frame.save(raw/f"ult-{index+1}.png")
        records.append({"frame":index+1,"source_root":[root_x,floor],
                        "source_box":bounds,"uniform_source_scale":RAW_SCALE})
    (raw/"registration.json").write_text(json.dumps({
        "sourceRoot":ORIGIN,"frames":records,
    },indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
