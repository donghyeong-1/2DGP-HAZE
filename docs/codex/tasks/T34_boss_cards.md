# T34 보스 등장 카드 (크래셔·아크, 2장)

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. T33(구역 제목 카드)과 같은 방식(`$generate2dmap` plate 원화 → `conform_background.py` → `hibit_plate.py` 32색, 1배)을 쓴다.

## 배경 (퀄리티 계획 4단계)
구역에 들어갈 때는 T33 제목 카드가 열린다. 보스방에 들어갈 때는 아직 아무 연출이 없어, 보스가 그냥 서 있다. 보스방에 들어서는 순간 **보스의 모습이 크게 담긴 가로 띠**가 열리고 이름이 뜨면 "결전"의 느낌이 산다(띠를 여닫는 코드는 Claude Code, T33과 같다).

## 입력 (같은 인물·색을 지킨다)
- 크래셔: `assets/sprites/forge/remake_t01_t03/boss_crasher/master/master_rgba.png`, 게임 그림 `assets/sprites/unified/boss_crasher_idle_1.png`
- 아크: `assets/sprites/forge/remake_t01_t03/boss_ark/master/master_rgba.png`, 게임 그림 `assets/sprites/unified/boss_ark_idle_1.png`, 상점 그림 `assets/store/capsule_main.png`(아크 모습)
- 배경 색: 크래셔는 공장 원경 `assets/backgrounds/far_foundry.png`, 아크는 탑 원경 `far_haze.png`, 보스방 `far_boss.png`

## 그림 (2장)
| 이름 | 장면 |
|---|---|
| `boss_card_crasher` | 오른쪽 1/3에 크래셔 상반신(크고 위협적으로, 왼쪽을 노려봄), 뒤로 용광로 불빛과 불똥. 왼쪽 2/3은 어둡고 단순하게 |
| `boss_card_ark` | 오른쪽 1/3에 아크 상반신(모자·긴 코트·가슴 결정, 왼쪽을 내려다봄), 뒤로 청록 헤이즈가 소용돌이. 왼쪽 2/3은 어둡고 단순하게 |

- 크기 **1920x400**(1배), 32색 이하, 불투명. **왼쪽 2/3에는 글자가 올라간다**(보스 이름·별칭) — 그 자리는 어둡고 차분하게. 글자는 넣지 않는다.
- 새 폴더 `assets/sprites/forge/boss_cards_v1/<이름>.png` + 두 장 비교 시트, 가짜 글자를 왼쪽에 얹은 미리보기 1장.

## 절차
크래셔 → 아크. 같은 이미지는 최대 3번. 보고서 `docs/codex/reports/T34.md`, 상태 `review`.

## 합격 기준
- [ ] 게임 속 보스와 같은 인물로 알아볼 수 있다
- [ ] 왼쪽 글자 자리가 읽기 좋게 차분하다
- [ ] 보고서에 솔직하게
