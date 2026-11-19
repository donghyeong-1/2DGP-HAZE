"""T22의 규격 검사, 1배 비교, 대기 GIF와 배치 미리보기를 만든다."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
FORGE = ROOT.parent
REPO = ROOT.parents[3]
HEIGHTS = {"mechanic":126,"keeper":117,"archivist":111}
BG = "#252d3b"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_gif(frames,path):
    previews=[]
    for frame in frames:
        base=Image.new("RGBA",frame.size,BG)
        base.alpha_composite(frame)
        previews.append(base.convert("RGB"))
    previews[0].save(path,save_all=True,append_images=previews[1:],duration=[600,600],loop=0,disposal=2)
    with Image.open(path) as sequence:
        assert sequence.n_frames==2
        for i,expected in enumerate(previews):
            sequence.seek(i)
            assert sequence.info["duration"]==600
            assert sequence.convert("RGB").tobytes()==expected.tobytes()


def check(files,options):
    result=subprocess.run(
        [sys.executable,"-B",str(REPO/"tools/check_sprites.py"),*map(str,files),*options],
        text=True,encoding="utf-8",capture_output=True,env=dict(os.environ,PYTHONUTF8="1"),
    )
    assert result.returncode==0,result.stdout+result.stderr
    return result.stdout+result.stderr


def main():
    manifest={"date_kst":"2026-11-19","route":"Codex host image_gen",
              "art_source":"host_image","model":None,"estimateUsd":None,
              "canvas":[128,132],"anchor":[64,130],"gif_frame_ms":600,"npcs":{}}
    logs=[]
    all_frames={}
    for role,height in HEIGHTS.items():
        name="npc_"+role
        master=ROOT/f"{name}_master"
        finish=ROOT/f"{name}_idle_finish"
        palette={v["hex"] for v in read_json(master/"palette.json")["colors"]}|{"#0b1020"}
        process=read_json(ROOT/role/"idle/processed/pipeline-meta.json")
        metadata=read_json(finish/"finish.json")
        assert process["qa"]["status"]=="pass"
        assert all(row["status"] in ("pass","skipped") for row in metadata["qa"]["checks"])
        assert sha256(ROOT/role/"idle/source.png")==process["provenance"]["input_sha256"]
        frames=[]
        files=[ROOT/f"{name}_idle_{i}.png" for i in (1,2)]
        records=[]
        all_colors=set()
        for path in files:
            frame=Image.open(path).convert("RGBA")
            assert frame.size==(128,132)
            pixels=np.array(frame)
            assert set(np.unique(pixels[:,:,3]))=={0,255}
            colors={"#%02x%02x%02x" % tuple(c) for c in np.unique(pixels[pixels[:,:,3]==255,:3],axis=0)}
            assert colors<=palette
            all_colors|=colors
            box=frame.getbbox()
            assert box[0]>0 and box[1]>0 and box[2]<128 and box[3]==130
            assert abs(box[3]-box[1]-height)<=2
            frames.append(frame)
            records.append({"file":path.name,"bbox":box,"height":box[3]-box[1],
                            "opaque_colors":len(colors),"semi_transparent":0,"sha256":sha256(path)})
            logs.append(f"## {path.name} --height {height}\n"+check([path],["--height",str(height)]))
        logs.append(f"## {role} 대기 2장\n"+check(files,["--height",str(height)]))
        assert records[0]["sha256"]!=records[1]["sha256"]
        verify_gif(frames,ROOT/f"{name}_idle_1x.gif")
        strip=Image.new("RGBA",(260,132))
        strip.paste(frames[0],(0,0))
        strip.paste(frames[1],(132,0))
        strip.save(ROOT/f"{name}_idle_strip_1x.png")
        manifest["npcs"][role]={
            "target_height":height,"palette_colors_used":len(all_colors),"frames":records,
            "master_source":f"{role}/source.png","master_prompt":f"{role}/actual_prompt.txt",
            "idle_source":f"{role}/idle/source.png","idle_prompt":f"{role}/idle/actual_prompt.txt",
            "master_sha256":sha256(ROOT/role/"source.png"),
            "idle_sha256":sha256(ROOT/role/"idle/source.png"),
            "finish":f"{name}_idle_finish/finish.json",
        }
        all_frames[role]=frames
    hero=Image.open(FORGE.parent/"unified/n09_idle_1.png").convert("RGBA")
    board=Image.new("RGBA",(560,316),BG)
    draw=ImageDraw.Draw(board)
    for row in (0,1):
        board.alpha_composite(hero,(64-21,24+row*158+130-124))
        draw.text((8,5+row*158),"N-09",fill="#e8eef7")
        for i,(role,frames) in enumerate(all_frames.items(),1):
            board.alpha_composite(frames[row],(140*i,24+row*158))
            draw.text((140*i+8,5+row*158),f"{role} idle {row+1}",fill="#e8eef7")
    board.save(ROOT/"compare_1x.png")
    background=Image.open(FORGE/"hideout_v1/far_hideout_v1.png").convert("RGBA")
    assert background.size==(1920,1080)
    pixels=np.array(background)
    assert (pixels[:,:,3]==255).all()
    color_count=len(np.unique(pixels[:,:,:3].reshape(-1,3),axis=0))
    assert color_count<=32
    lower=np.unique(pixels[810:,:,:3].reshape(-1,3),axis=0)
    assert (lower.max(axis=1)<50).all()
    preview=background.copy()
    floor=810
    preview.alpha_composite(hero,(600-21,floor-124))
    for x,role in zip((820,1120,1380),HEIGHTS):
        preview.alpha_composite(all_frames[role][0],(x-64,floor-130))
    preview.save(FORGE/"hideout_v1/preview_1x.png")
    write_json(ROOT/"provenance.json",manifest)
    (ROOT/"check_sprites.txt").write_text("\n".join(logs),encoding="utf-8")
    write_json(FORGE/"hideout_v1/provenance.json",{
        "date_kst":"2026-11-19","route":"Codex host image_gen","art_source":"host_image",
        "model":None,"estimateUsd":None,"prompt":"actual_prompt.txt","source":"source.png",
        "sha256":sha256(FORGE/"hideout_v1/source.png"),
        "source_size":Image.open(FORGE/"hideout_v1/source.png").size,
        "final_size":[1920,1080],"opaque_colors":color_count,"transparent_pixels":0,
        "lower_quarter_colors":lower.tolist(),"preview_actor_floor_y":floor,
    })
    print(json.dumps({role:{"heights":[v["height"] for v in data["frames"]],
                            "colors":data["palette_colors_used"]}
                      for role,data in manifest["npcs"].items()},ensure_ascii=False))
    print("background",background.size,color_count,"colors","lower quarter",lower.tolist())


if __name__=="__main__":
    main()
