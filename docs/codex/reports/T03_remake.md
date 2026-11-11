# T03 재제작 보고서

- 날짜: 2026-11-11 [Codex]
- 상태: review
- 생성 및 마감: agent-sprite-forge `generate2dsprite` (6b3da5c) 마스터 승인/키잉, Codex 내장 `image_gen` (모델명·비용 미제공), `tools/finish_character.py`에서 `video2dsprite`의 hibit 후처리 호출.
- 시도 횟수: 4회. 1차 시안과 보정 결과를 함께 보관.
- 1배 비교: `assets/sprites/forge/remake_t01_t03/t03_1x.png`. 전체 기존 적용본 대조는 `assets/sprites/forge/remake_t01_t03/compare_1x.png`(위 기존, 아래 재제작).
- `assets/sprites/forge/remake_t01_t03/finished/enemy_hound_fit_remake_idle.png` / `assets/sprites/forge/remake_t01_t03/enemy_hound_fit/master/master_rgba.png`
- `assets/sprites/forge/remake_t01_t03/finished/boss_crasher_remake_idle.png` / `assets/sprites/forge/remake_t01_t03/boss_crasher/master/master_rgba.png`
- `assets/sprites/forge/remake_t01_t03/finished/boss_ark_remake_idle.png` / `assets/sprites/forge/remake_t01_t03/boss_ark/master/master_rgba.png`

## 프롬프트

정체성은 기존 캐릭터, 화풍은 N-09 마스터를 따랐다. 마젠타 배경, 우향 전신, 선 없는 3단계 색면과 큰 얼굴 요소를 요구했다. 실제 프롬프트는 `assets/sprites/forge/remake_t01_t03/enemy_hound/actual_prompt.txt`, `assets/sprites/forge/remake_t01_t03/enemy_hound_fit/actual_prompt.txt`, `assets/sprites/forge/remake_t01_t03/boss_crasher/actual_prompt.txt`, `assets/sprites/forge/remake_t01_t03/boss_ark/actual_prompt.txt`에 기록했다. T02·T03의 첫 생성에는 T01의 1차 재제작 마스터를 사용했고, 이후 T01은 몸 폭만 보정했다.

## 규격 검사

```
파일                                           캔버스        내용 WxH     반투명 색
enemy_hound_remake_idle.png                  (151, 83)  148x81         0 34
키 81px (목표 81px) OK
통과
```

```
파일                                           캔버스        내용 WxH     반투명 색
enemy_hound_fit_remake_idle.png              (114, 83)  112x81         0 36
키 81px (목표 81px) OK
통과
```

```
파일                                           캔버스        내용 WxH     반투명 색
boss_crasher_remake_idle.png                 (190, 197) 188x195        0 41
키 195px (목표 195px) OK
통과
```

```
파일                                           캔버스        내용 WxH     반투명 색
boss_ark_remake_idle.png                     (77, 161)  75x159        0 39
키 159px (목표 159px) OK
통과
```

`python tests/test_pixel_assets.py` 8개 통과. 새 후보 PNG는 위의 개별 검사로 확인했다.

## 1배 확인

사냥개는 꼬리 수정으로 148×81px에서 112×81px(1.38:1)로 줄였다. 1배에서도 눈과 갈비뼈가 읽힌다. 크래셔의 눈·녹슨 장갑·증기 배출구와 아크의 눈·가슴 수정·코트 안감이 구분된다. 크래셔의 주먹 폭과 아크의 코트 장식은 기존보다 강조됐다. 크래셔의 볼 흉터는 갈색보다 붉게 보인다.

