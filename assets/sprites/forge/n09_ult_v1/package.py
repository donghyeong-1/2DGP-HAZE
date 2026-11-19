"""시전 두 장을 최종 캔버스로 묶고 컷인과 함께 검사한다."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


ROOT=Path(__file__).resolve().parent
FORGE=ROOT.parent
REPO=ROOT.parents[3]
STAGE=ROOT/"finish_stage/n09_ult_v1"
SIZE=(140,132)
ANCHOR=(64,130)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    metadata=read_json(STAGE/"finish.json")
    origin=[round(a+(b-c)*metadata["scale"]) for a,b,c in
            zip(metadata["anchor"],(550,1000),metadata["anchorSource"])]
    shift=(ANCHOR[0]-origin[0],ANCHOR[1]-origin[1])
    target=ROOT/"frames"
    target.mkdir(exist_ok=True)
    frames=[]
    records=[]
    colors_used=set()
    palette={x["hex"] for x in read_json(FORGE/"n09_v3b/palette.json")["colors"]}|{"#0b1020"}
    for index,path in enumerate(sorted((STAGE/"frames").glob("*.png")),1):
        original=Image.open(path).convert("RGBA")
        frame=Image.new("RGBA",SIZE)
        frame.paste(original,shift)
        assert frame.crop((shift[0],shift[1],shift[0]+original.width,shift[1]+original.height)).tobytes()==original.tobytes()
        pixels=np.array(frame)
        alpha=pixels[:,:,3]
        assert set(np.unique(alpha))=={0,255}
        box=frame.getbbox()
        assert box[0]>0 and box[1]>0 and box[2]<SIZE[0] and box[3]==130
        colors={"#%02x%02x%02x"%tuple(c) for c in np.unique(pixels[alpha==255,:3],axis=0)}
        assert colors<=palette
        colors_used|=colors
        frame.save(target/f"ult-{index}.png")
        frames.append(frame)
        records.append({"frame":index,"box":box,"opaque_height":box[3]-box[1],
                        "colors":len(colors),"semi_transparent":0,"anchor":ANCHOR})
    assert len(frames)==2
    def rebase(doc):
        if isinstance(doc,list):
            return [rebase(value) for value in doc]
        if isinstance(doc,dict):
            result={key:rebase(value) for key,value in doc.items()}
            if "path" in result:
                result["path"]=os.path.relpath((STAGE/result["path"]).resolve(),ROOT).replace(chr(92),"/")
            return result
        return doc
    final_meta=rebase(metadata)
    final_meta["source"]["frames"]="registered"
    final_meta["size"]=list(SIZE)
    final_meta["anchor"]=list(ANCHOR)
    final_meta["engine"]["sourceSize"]=list(SIZE)
    final_meta["engine"]["sourceAnchor"]=list(ANCHOR)
    for size in final_meta["displaySizes"]:
        if size["label"]=="1x":
            size["size"]=list(SIZE)
            size["anchor"]=list(ANCHOR)
    final_meta["packaging"]={"sourceFinish":"finish_stage/n09_ult_v1/finish.json",
                             "translation":shift,"resampling":"none"}
    write_json(ROOT/"finish.json",final_meta)
    strip=Image.new("RGBA",(SIZE[0]*2+4,SIZE[1]))
    for i,frame in enumerate(frames):
        strip.paste(frame,(i*(SIZE[0]+4),0))
    strip.save(ROOT/"strip_1x.png")
    hero=Image.open(FORGE.parent/"unified/n09_idle_1.png").convert("RGBA")
    compare=Image.new("RGBA",(SIZE[0]*3+8,SIZE[1]),"#252d3b")
    compare.alpha_composite(hero,(64-21,130-124))
    for i,frame in enumerate(frames,1):
        compare.alpha_composite(frame,(i*(SIZE[0]+4),0))
    compare.save(ROOT/"compare_1x.png")
    cutin=FORGE/"cutin_v1"
    banner=Image.open(cutin/"cutin_hero_v1.png").convert("RGBA")
    a=np.array(banner)
    assert banner.size==(1920,420) and set(np.unique(a[:,:,3]))=={0,255}
    assert not (ndimage.binary_fill_holes(a[:,:,3]>0)&(a[:,:,3]==0)).any()
    assert (a[100:315,1320:1840,3]==255).all()
    banner_colors=len(np.unique(a[a[:,:,3]==255,:3],axis=0))
    assert banner_colors<=32
    logs=[]
    env=dict(os.environ,PYTHONUTF8="1")
    commands=[([cutin/"cutin_hero_v1.png"],["--height","420"]),
              (sorted(target.glob("*.png")),[]),
              (sorted(target.glob("*.png")),["--air"])]
    for files,options in commands:
        run=subprocess.run([sys.executable,"-B",str(REPO/"tools/check_sprites.py"),
                            *map(str,files),*options],text=True,encoding="utf-8",capture_output=True,env=env)
        logs.append(f"{files[0].name} {' '.join(options)} (exit {run.returncode})\n"+run.stdout+run.stderr)
        if options:
            assert run.returncode==0,run.stdout+run.stderr
    (ROOT/"checks.txt").write_text("\n".join(logs),encoding="utf-8")
    write_json(ROOT/"provenance.json",{
        "date_kst":"2026-11-19","art_source":"host_image","route":"Codex image_gen",
        "model":None,"estimateUsd":None,"source":"source.png","source_sha256":sha256(ROOT/"source.png"),
        "prompt":"actual_prompt.txt","first_source":"take_01_source.png",
        "first_prompt":"take_01_prompt.txt","size":SIZE,"anchor":ANCHOR,"frames":records,
        "shared_colors":len(colors_used),
    })
    write_json(cutin/"provenance.json",{
        "date_kst":"2026-11-19","art_source":"host_image","route":"Codex image_gen",
        "model":None,"estimateUsd":None,"source":"source.png",
        "source_sha256":sha256(cutin/"source.png"),"prompt":"actual_prompt.txt",
        "size":[1920,420],"colors":banner_colors,
        "transparent":int((a[:,:,3]==0).sum()),"semitransparent":0,"internal_holes":0,
        "text_safe_rectangle":[1320,100,1840,315],"registration":"registration.json",
    })
    print("cast",records,"colors",len(colors_used),"shift",shift)
    print("cutin",banner.size,"colors",banner_colors,"transparent",int((a[:,:,3]==0).sum()))


if __name__=="__main__":
    main()
