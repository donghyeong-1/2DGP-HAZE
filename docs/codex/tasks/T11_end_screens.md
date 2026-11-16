# T11 사망·엔딩 화면 일러스트

먼저 `docs/codex/COMMON.md`를 읽고 따른다. 배경판(T06)과 같은 방식으로 **화면 한 장짜리 그림**을 만든다 (`$generate2dmap` 배경 방식, `hibit_plate.py --size 1920x1080 --colors 32`, 확대 금지).

## 입력
정체성·화풍: 주인공 `assets/sprites/forge/hero_v3b/master/master_rgba.png`, 배경 분위기는 `assets/sprites/forge/backgrounds_v1/`, 게임의 세계관은 `docs/기획서.md` 1.2절(헤이즈 결정이 뒤덮은 격리 도시 '네뷸라 교도소').

## 그림
| 이름 | 장면 |
|---|---|
| `screen_death_v3` | 쓰러진 주인공(옆모습)이 어두운 복도 바닥에 누워 있고, 푸른 헤이즈 안개가 서서히 걷힌다. 화면 아래쪽에 글자를 얹을 빈 공간 |
| `screen_ending_v3` | 보스를 쓰러뜨린 뒤 탈출구로 걸어 나가는 주인공의 뒷모습(작게), 열린 문 너머로 새벽빛과 도시 윤곽. 화면 가운데 위쪽에 제목을 얹을 빈 공간 |

## 규칙
- 1920×1080, 32색 이하, 투명 픽셀 0개. 글자는 그림에 넣지 않는다(게임이 얹는다).
- 주인공은 마스터의 얼굴·옷(흰 머리, 청록 밴드·허리끈)을 지킨다.
- 저장: `assets/sprites/forge/screens_v1/`. 같은 이미지는 최대 3번까지 시도한다.

## 합격 기준
- [ ] 두 장 모두 규격 통과 (Pillow로 크기·색 수 확인, `reduction` 경고는 보고서에 설명)
- [ ] 글자를 얹을 빈 공간이 있다
- [ ] 보고서에 솔직하게

보고서 `docs/codex/reports/T11.md`, 상태 `review`.
