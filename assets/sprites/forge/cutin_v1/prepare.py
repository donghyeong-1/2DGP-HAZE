"""원화의 사선 띠를 화면 크기에 맞추고 바깥 알파를 정리한다."""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


ROOT = Path(__file__).resolve().parent


def main():
    source=Image.open(ROOT/"source.png").convert("RGBA")
    width,height=source.size
    alpha=np.array(source.getchannel("A"))>=128
    labels,count=ndimage.label(alpha)
    areas=np.bincount(labels.ravel())
    areas[0]=0
    alpha=ndimage.binary_fill_holes(labels==areas.argmax())
    opaque=np.array(source)
    opaque[:,:,3]=alpha.astype(np.uint8)*255
    source=Image.fromarray(opaque)
    # 원화의 기울기를 조금 완만하게 하고 공통 배율로 얼굴 비율을 유지한다.
    shear=0.065
    extra=round(width*shear)+8
    expanded=source.transform((width,height+extra),Image.Transform.AFFINE,
                               (1,0,0,-shear,1,0),Image.Resampling.BICUBIC)
    mask=np.array(expanded.getchannel("A"))>=128
    ys,xs=np.where(mask)
    crop=(int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)
    cropped=expanded.crop(crop)
    factor=1920/cropped.width
    assert factor<=1
    native_height=round(cropped.height*factor)
    assert native_height<=420,(crop,native_height)
    scaled=cropped.resize((1920,native_height),Image.Resampling.LANCZOS)
    offset=(420-native_height)//2
    native=Image.new("RGBA",(1920,420))
    native.paste(scaled,(0,offset))
    binary=np.array(native.getchannel("A"))>=128
    # 열마다 원래 절단면을 따라 띠 내부를 불투명하게 만든다.
    for x in range(binary.shape[1]):
        visible=np.flatnonzero(binary[:,x])
        if len(visible):
            binary[visible.min():visible.max()+1,x]=True
    alpha_image=Image.fromarray(binary.astype(np.uint8)*255)
    alpha_image.save(ROOT/"alpha_mask.png")
    background=Image.new("RGBA",native.size,"#0f1623")
    background.alpha_composite(native)
    background.convert("RGB").save(ROOT/"registered.png")
    (ROOT/"registration.json").write_text(json.dumps({
        "source_size":source.size,"raw_shear_y_per_x":shear,"crop":crop,
        "uniform_scale":factor,"native_height":native_height,
        "placement_y":offset,"size":[1920,420],
    },indent=2)+"\n",encoding="utf-8")
    print("crop",crop,"scale",factor,"height",native_height)


if __name__=="__main__":
    main()
