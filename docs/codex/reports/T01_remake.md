# T01 재제작 보고서

- 날짜: 2026-11-11 [Codex]
- 상태: review
- 생성 및 마감: agent-sprite-forge `generate2dsprite` (6b3da5c) 마스터 승인/키잉, Codex 내장 `image_gen` (모델명·비용 미제공), `tools/finish_character.py`에서 `video2dsprite`의 hibit 후처리 호출.
- 시도 횟수: 2회. 1차 시안과 보정 결과를 함께 보관.
- 1배 비교: `assets/sprites/forge/remake_t01_t03/t01_1x.png`. 전체 기존 적용본 대조는 `assets/sprites/forge/remake_t01_t03/compare_1x.png`(위 기존, 아래 재제작).
- `assets/sprites/forge/remake_t01_t03/finished/n09_fit_remake_idle.png` / `assets/sprites/forge/remake_t01_t03/n09_fit/master/master_rgba.png`

## 프롬프트

정체성은 기존 캐릭터, 화풍은 N-09 마스터를 따랐다. 마젠타 배경, 우향 전신, 선 없는 3단계 색면과 큰 얼굴 요소를 요구했다. 실제 프롬프트는 `assets/sprites/forge/remake_t01_t03/n09/actual_prompt.txt`, `assets/sprites/forge/remake_t01_t03/n09_fit/actual_prompt.txt`에 기록했다. T02·T03의 첫 생성에는 T01의 1차 재제작 마스터를 사용했고, 이후 T01은 몸 폭만 보정했다.

## 규격 검사

```
파일                                           캔버스        내용 WxH     반투명 색
n09_remake_idle.png                          (38, 125)  36x123        0 36
키 123px (목표 123px) OK
통과
```

```
파일                                           캔버스        내용 WxH     반투명 색
n09_fit_remake_idle.png                      (54, 125)  52x123        0 32
키 123px (목표 123px) OK
통과
```

`python tests/test_pixel_assets.py` 8개 통과. 새 후보 PNG는 위의 개별 검사로 확인했다.

## 1배 확인

N-09은 머리카락과 검은 옷, 청록 밴드와 허리끈을 유지했다. 1차 시안의 내용 폭이 36px라 어깨와 자세를 넓혔고, 재검토 후보의 내용 폭은 52px다(기존 합격본 40px). 10배 얼굴에서 눈의 흰 하이라이트와 눈썹, 정리된 앞머리가 보이며 청록 림라이트나 분홍·보라 피부는 육안으로 확인되지 않았다. 입과 장화 끈은 1배에서 희미하다. 비교용 `n09_face_10x.png` 참조.

