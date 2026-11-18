"""T21의 최종 캔버스와 확인 자료를 만든다."""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FORGE = ROOT.parent
REPO = ROOT.parents[3]
STAGE = ROOT / "n09_run_v2_take2_refined"
OUTPUT = FORGE / "n09_run_v2"
PIVOT = (55, 128)
SIZE = (105, 129)
TIMING = [80, 80, 70, 80] * 2
NEAR_LEG_FORWARD = [True, True, False, False, False, False, True, True]
NEAR_ARM_FORWARD = [False, False, True, True, True, True, False, False]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_check(tool, files, options):
    env = dict(os.environ, PYTHONUTF8="1")
    result = subprocess.run(
        [sys.executable, "-B", str(REPO / "tools" / tool), *map(str, files), *options],
        text=True, encoding="utf-8", capture_output=True, env=env,
    )
    return result.returncode, result.stdout + result.stderr


def measurements(frames):
    records = []
    expected_y = [62, 65, 62, 59] * 2
    for index, (frame, belt_y) in enumerate(zip(frames, expected_y), 1):
        pixels = np.array(frame, dtype=np.int16)
        red, green, blue, alpha = pixels.transpose(2, 0, 1)
        yy, xx = np.indices(alpha.shape)
        belt_mask = ((green > 82) & (green >= red*1.45) & (blue >= red*1.36) & (alpha==255) &
                     (abs(xx-PIVOT[0])<=7) & (abs(yy-belt_y)<=3))
        ys, xs = np.where(belt_mask)
        assert len(xs)
        box = frame.getbbox()
        records.append({
            "frame": index, "belt_x": float(np.median(xs)), "belt_y": float(np.median(ys)),
            "opaque_box": box, "bottom_y_exclusive": box[3], "air_clearance": PIVOT[1]-box[3],
            "front_leg": "near" if NEAR_LEG_FORWARD[index-1] else "far",
            "front_arm": "near" if NEAR_ARM_FORWARD[index-1] else "far",
        })
    return records


def main():
    metadata = read_json(STAGE / "finish.json")
    source_root = (600, 900)
    root = [round(a+(b-c)*metadata["scale"]) for a,b,c in
            zip(metadata["anchor"], source_root, metadata["anchorSource"])]
    shift = (PIVOT[0]-root[0], PIVOT[1]-root[1])
    frames_out = OUTPUT / "frames"
    frames_out.mkdir(parents=True, exist_ok=True)
    frames = []
    source_files = sorted((STAGE / "frames").glob("*.png"))
    assert len(source_files)==8
    palette = {color["hex"] for color in read_json(FORGE / "n09_v3b/palette.json")["colors"]} | {"#0b1020"}
    for source in source_files:
        image = Image.open(source).convert("RGBA")
        box = image.getbbox()
        bounds = [box[0]+shift[0],box[1]+shift[1],box[2]+shift[0],box[3]+shift[1]]
        assert bounds[0]>0 and bounds[1]>0 and bounds[2]<SIZE[0] and bounds[3]<SIZE[1], bounds
        canvas = Image.new("RGBA", SIZE)
        canvas.paste(image, shift)
        assert canvas.crop((shift[0], shift[1], shift[0]+image.width, shift[1]+image.height)).tobytes()==image.tobytes()
        array = np.array(canvas)
        assert set(np.unique(array[:,:,3]))=={0,255}
        colors = {"#%02x%02x%02x" % tuple(c) for c in np.unique(array[array[:,:,3]==255,:3],axis=0)}
        assert colors <= palette
        canvas.save(frames_out / source.name)
        frames.append(canvas)

    def rebase(document):
        if isinstance(document,list):
            return [rebase(v) for v in document]
        if isinstance(document,dict):
            adjusted = {key: rebase(value) for key,value in document.items()}
            if "path" in adjusted:
                absolute = (STAGE / adjusted["path"]).resolve()
                adjusted["path"] = os.path.relpath(absolute, OUTPUT).replace(chr(92),"/")
            return adjusted
        return document

    metadata = rebase(metadata)
    metadata["source"]["frames"] = os.path.relpath((ROOT / "registered_take_02_refined").resolve(), OUTPUT).replace(chr(92),"/")
    metadata["size"] = list(SIZE)
    metadata["anchor"] = list(PIVOT)
    metadata["engine"]["sourceSize"] = list(SIZE)
    metadata["engine"]["sourceAnchor"] = list(PIVOT)
    metadata["packaging"] = {
        "sourceFinish": "../hero_run_v2/n09_run_v2_take2_refined/finish.json",
        "translation": shift, "sampling": "none", "gameOrigin": PIVOT,
    }
    for display in metadata["displaySizes"]:
        if display["label"]=="1x":
            display["size"] = list(SIZE)
            display["anchor"] = list(PIVOT)
    # 기존 마감 QA는 원래 마감 결과의 해시를 보존한다. 최종 PNG 해시는 별도로 기록한다.
    metadata["packaging"]["outputs"] = [
        {"path": "frames/"+source.name, "sha256": sha256(frames_out/source.name)}
        for source in source_files
    ]
    write_json(OUTPUT / "finish.json", metadata)
    records = measurements(frames)
    write_json(OUTPUT / "registration.json", {"size":SIZE,"anchor":PIVOT,"frames":records})

    spec = importlib.util.spec_from_file_location("prior_package", FORGE / "hero_run_v1/package.py")
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    prior.strip_png(frames, OUTPUT / "strip_1x.png")
    prior.save_gif(frames, TIMING, OUTPUT / "run_1x.gif")
    prior.strip_png(frames, FORGE / "n09_run_v2_strip_1x.png")
    unified = FORGE.parent / "unified"
    idle = (Image.open(unified/"n09_idle_1.png").convert("RGBA"), (21,124))
    transitions = [
        (Image.open(unified/f"n09_run_trans_{i}.png").convert("RGBA"),(55,124))
        for i in range(1,5)
    ]
    run = [(frame,PIVOT) for frame in frames]
    sequence = [idle,*transitions[:2],*run,*run,*transitions[2:],idle]
    prior.save_gif(prior.align_for_preview(sequence),
                   [300,60,60,*TIMING,*TIMING,80,80,300],
                   OUTPUT / "start_run_stop_1x.gif")
    # 확인판에만 한국어로 실제 앞에 나온 팔다리를 표시한다.
    gap = 5
    labelled = Image.new("RGBA",(8*(SIZE[0]+gap)-gap,SIZE[1]+46),"#252d3b")
    draw = ImageDraw.Draw(labelled)
    font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",11)
    for index,(frame,record) in enumerate(zip(frames,records)):
        x=index*(SIZE[0]+gap)
        labelled.alpha_composite(frame,(x,0))
        leg="가까운" if record["front_leg"]=="near" else "먼"
        arm="가까운" if record["front_arm"]=="near" else "먼"
        draw.text((x+3,SIZE[1]+2),f"{index+1} 앞 다리 {leg}",font=font,fill="#e8eef7")
        draw.text((x+3,SIZE[1]+18),f"앞 팔 {arm}",font=font,fill="#e8eef7")
        if index in (2,6):
            draw.text((x+3,SIZE[1]+32),"통과 중",font=font,fill="#e8eef7")
    labelled.save(ROOT / "limb_labels_1x.png")
    before = Image.open(FORGE / "n09_run_v1/strip_1x.png").convert("RGBA")
    after = Image.open(OUTPUT / "strip_1x.png").convert("RGBA")
    board = Image.new("RGBA",(max(before.width,after.width),before.height+after.height+24),"#252d3b")
    board.alpha_composite(before,(0,0))
    board.alpha_composite(after,(0,before.height+24))
    board.save(ROOT / "compare_1x.png")
    files=sorted(frames_out.glob("*.png"))
    logs=[]
    for tool,options in [("check_gait.py",[]),("check_sprites.py",[]),("check_sprites.py",["--air"])]:
        code,text=run_check(tool,files,options)
        logs.append(f"{tool} {' '.join(options)} (exit {code})\n{text}")
        if tool=="check_gait.py" or options:
            assert code==0
    (ROOT / "checks.txt").write_text("\n".join(logs),encoding="utf-8")
    write_json(ROOT / "provenance.json",{
        "date_kst":"2026-11-19","art_source":"host_image","route":"Codex image_gen",
        "model":None,"estimateUsd":None,"finish":"n09_v3b scale and palette, hibit",
        "source_steps": {
            step: {"source":f"{step}/take_02/source.png","sha256":sha256(ROOT/step/"take_02/source.png"),
                   "prompt":f"{step}/take_02/actual_prompt.txt"}
            for step in ("A","B")
        },
        "source_take1":[f"{step}/source.png" for step in ("A","B")],
        "registration": "../n09_run_v2/registration.json",
        "gif_timing_ms":TIMING,"game_frame_time_ms":78.125,
    })
    print("translation",shift)
    print(*records,sep="\n")


if __name__ == "__main__":
    main()
