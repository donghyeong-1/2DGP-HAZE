# T02 재제작 보고서

- 날짜: 2026-11-11 [Codex]
- 상태: review
- 생성 및 마감: agent-sprite-forge `generate2dsprite` (6b3da5c) 마스터 승인/키잉, Codex 내장 `image_gen` (모델명·비용 미제공), `tools/finish_character.py`에서 `video2dsprite`의 hibit 후처리 호출.
- 시도 횟수: 3회. 캐릭터당 1회.
- 1배 비교: `assets/sprites/forge/remake_t01_t03/t02_1x.png`. 전체 기존 적용본 대조는 `assets/sprites/forge/remake_t01_t03/compare_1x.png`(위 기존, 아래 재제작).
- `assets/sprites/forge/remake_t01_t03/finished/enemy_slum_remake_idle.png` / `assets/sprites/forge/remake_t01_t03/enemy_slum/master/master_rgba.png`
- `assets/sprites/forge/remake_t01_t03/finished/enemy_thrower_remake_idle.png` / `assets/sprites/forge/remake_t01_t03/enemy_thrower/master/master_rgba.png`
- `assets/sprites/forge/remake_t01_t03/finished/enemy_guard_remake_idle.png` / `assets/sprites/forge/remake_t01_t03/enemy_guard/master/master_rgba.png`

## 프롬프트

정체성은 기존 캐릭터, 화풍은 N-09 마스터를 따랐다. 마젠타 배경, 우향 전신, 선 없는 3단계 색면과 큰 얼굴 요소를 요구했다. 실제 프롬프트는 `assets/sprites/forge/remake_t01_t03/enemy_slum/actual_prompt.txt`, `assets/sprites/forge/remake_t01_t03/enemy_thrower/actual_prompt.txt`, `assets/sprites/forge/remake_t01_t03/enemy_guard/actual_prompt.txt`에 기록했다. T02·T03의 첫 생성에는 T01의 1차 재제작 마스터를 사용했고, 이후 T01은 몸 폭만 보정했다.

## 규격 검사

```
파일                                           캔버스        내용 WxH     반투명 색
enemy_slum_remake_idle.png                   (47, 119)  44x117        0 40
키 117px (목표 117px) OK
통과
```

```
파일                                           캔버스        내용 WxH     반투명 색
enemy_thrower_remake_idle.png                (52, 125)  50x123        0 39
키 123px (목표 123px) OK
통과
```

```
파일                                           캔버스        내용 WxH     반투명 색
enemy_guard_remake_idle.png                  (75, 137)  73x135        0 36
키 135px (목표 135px) OK
통과
```

`python tests/test_pixel_assets.py` 8개 통과. 새 후보 PNG는 위의 개별 검사로 확인했다.

## 1배 확인

폐인의 눈과 붕대, 투척병의 청록 고글과 녹슨 방패, 간수의 바이저·방패·경찰봉이 1배에서 구분된다. 기존 합격본과 비교하면 투척병의 고철 조각과 손이 가까워 외곽이 덜 뚜렷하다. 간수는 남색 비교판에서 밝은 갑옷 면과 바이저가 읽히고, 바이저 채도는 다른 인물보다 높다.

