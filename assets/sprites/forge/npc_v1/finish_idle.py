"""대기 원화 2장을 기준 마스터 크기로 등록하고 픽셀 마감한다."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    role = sys.argv[1]
    name = "npc_" + role
    working = ROOT / role
    source = Image.open(working / "idle/processed/raw-sheet-clean.png").convert("RGBA")
    count = 2
    cell_width = source.width // count
    ref = read_json(ROOT / f"{name}_master/finish.json")
    first = source.crop((0, 0, cell_width, source.height))
    first_box = first.getchannel("A").point(lambda a: 255 if a>=128 else 0).getbbox()
    factor = ref["rest"]["heightPx"] / (first_box[3]-first_box[1]-1)
    raw = working / "idle/registered"
    raw.mkdir(exist_ok=False)
    origin = (650, 1000)
    canvas_size = (1400, 1200)
    records = []
    for index in range(count):
        cell = source.crop((index*cell_width, 0, (index+1)*cell_width, source.height))
        pixels = np.array(cell)
        alpha = pixels[:, :, 3]
        ys, xs = np.where(alpha>=128)
        top, floor = int(ys.min()), int(ys.max())
        sole_x = xs[ys>=floor-3]
        x_root = float(np.median(sole_x))
        uniform = cell.transform(canvas_size, Image.Transform.AFFINE,
                                 (1/factor, 0, x_root-origin[0]/factor,
                                  0, 1/factor, floor-origin[1]/factor),
                                 Image.Resampling.BICUBIC)
        # 흡기 프레임은 허리 아래를 고정한 채 상체를 약 1px만 높인다.
        if index:
            waist = round(origin[1] - ref["rest"]["heightPx"]*0.47)
            extra = max(0, 1/ref["scale"] - (first_box[1]-top)*factor)
            source_top = extra * waist / max(1, ref["rest"]["heightPx"]*0.53)
            uniform = uniform.transform(canvas_size, Image.Transform.MESH, [
                ((0,0,canvas_size[0],waist),
                 (0,source_top,0,waist,canvas_size[0],waist,canvas_size[0],source_top)),
                ((0,waist,*canvas_size),
                 (0,waist,0,canvas_size[1],canvas_size[0],canvas_size[1],canvas_size[0],waist)),
            ], Image.Resampling.BICUBIC)
        box = uniform.getbbox()
        assert box[0]>8 and box[1]>8 and box[2]<canvas_size[0]-8 and box[3]<canvas_size[1]-8
        uniform.save(raw / f"idle-{index+1}.png")
        records.append({"frame":index+1,"source_root":[x_root,floor],"source_top":top,
                        "factor_to_master":factor})
    (raw / "registration.json").write_text(json.dumps({
        "source_anchor":origin,"frames":records,
    }, indent=2)+"\n", encoding="utf-8")
    temp = ROOT / "temp"
    temp.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONUTF8="1", TEMP=str(temp), TMP=str(temp))
    command = [sys.executable, "-B", str(REPO/"tools/finish_character.py"),
               str(raw), f"{name}_idle_finish", "--root", str(ROOT), "--like", f"{name}_master"]
    run = subprocess.run(command, text=True, encoding="utf-8", capture_output=True, env=env)
    (working / "idle/finish_stdout.txt").write_text(run.stdout+run.stderr, encoding="utf-8")
    if run.returncode:
        sys.exit(run.stdout+run.stderr)
    print(run.stdout.strip())
    output = ROOT / f"{name}_idle_finish"
    metadata = read_json(output / "finish.json")
    pivot = [round(a+(b-c)*metadata["scale"]) for a,b,c in
             zip(metadata["anchor"], origin, metadata["anchorSource"])]
    shift = (64-pivot[0], 130-pivot[1])
    for index,path in enumerate(sorted((output/"frames").glob("*.png")),1):
        frame=Image.open(path).convert("RGBA")
        box=frame.getbbox()
        bounds=[box[0]+shift[0],box[1]+shift[1],box[2]+shift[0],box[3]+shift[1]]
        assert bounds[0]>0 and bounds[1]>0 and bounds[2]<128 and bounds[3]<132
        packaged=Image.new("RGBA",(128,132))
        packaged.paste(frame,shift)
        assert packaged.crop((shift[0],shift[1],shift[0]+frame.width,shift[1]+frame.height)).tobytes()==frame.tobytes()
        packaged.save(ROOT / f"{name}_idle_{index}.png")
    (working/"idle/packaging.json").write_text(json.dumps({
        "size":[128,132],"anchor":[64,130],"translation":shift,
        "source_finish":f"{name}_idle_finish/finish.json",
    },indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
