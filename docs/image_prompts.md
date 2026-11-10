# AI 이미지 프롬프트 (image_prompts)

과목 공지에 따라 캐릭터 이미지는 AI 이미지 생성 툴로 직접 만든다. 생성한 모델명, 날짜, 사용한 프롬프트를 아래 "생성 기록"에 남기고 `docs/ASSETS.md`에도 출처로 적는다.

## 공통 규칙
- 프롬프트에 기존 작품이나 특정 작가의 이름을 쓰지 않는다. (순수 창작 요건)
- **다른 작품의 캐릭터 이미지를 참조 이미지로 올리지 않는다.** 기존 캐릭터와 비슷한 결과가 나오면 순수 창작으로 볼 수 없다. 분위기만 말로 설명하고, 우리 게임만의 요소(청록 헤이즈 빛, N-09 번호표 등)를 넣는다.
- 기존 캐릭터를 알아볼 수 있는 고유 요소(번호표, 특정 로고, 소품, 얼굴의 점·붕대 같은 특징)는 넣지 않는다.
- 모든 캐릭터에 같은 **스타일 접두사**를 붙이고, 첫 결과물(우리가 만든 이미지)을 참조 이미지로 올려 같은 화풍을 유지한다.
- 구도는 **전신, 단색 어두운 배경**으로 고정한다. 배경 제거와 PPT 배치가 쉽다.

## 화풍 방향 (2026-10-31)
- **PPT용 콘셉트 일러스트**: 어둡고 거친 선의 반실사 만화풍. 먹선이 굵고, 남색·슬레이트 회색 위주에 청록(헤이즈) 빛만 포인트로 쓴다.
- **게임용 스프라이트**: 콘셉트 일러스트를 기준으로 나중에 픽셀 스케일로 정리한다. (캔버스 64×64 권장, 결정 전 제안) 일러스트를 그대로 애니메이션으로 쓰면 프레임 일관성이 깨지기 쉽다.

## 스타일 접두사 (콘셉트 일러스트용, 모든 프롬프트 앞에 붙임)
```
dark gritty semi-realistic manga ink illustration, heavy black line work, desaturated navy and slate gray palette with glowing cyan blue accents, dramatic low-key lighting, full body, plain dark background, no text, no logos
```

## 캐릭터별 프롬프트 (스타일 접두사 뒤에 이어서)
| 대상 | 프롬프트 |
|---|---|
| 주인공 N-09 | `a gaunt young man with messy short white hair, heavy-lidded tired eyes with a faint cyan glow, dark circles under the eyes, sharp jawline, torn gray-black prison uniform with cyan stitching, both arms visible, faintly glowing cyan veins on the neck and hands, deadpan expression, slouched relaxed stance` |
| 슬럼 폐인 | `a gaunt prisoner in ragged clothes, hunched posture, wild eyes, dull gray skin with faint cyan veins, charging forward with clenched fists` |
| 고철 투척병 | `a prisoner with a scrap metal shield on one arm, holding a piece of junk to throw, patched clothes, rusty color accents` |
| 안개 사냥개 | `a lean mutated hound made of dark smoke and bone, glowing cyan eyes, low crouched pose ready to pounce` |
| 중장갑 간수 | `a heavily armored prison guard with a large steel riot shield and a heavy baton, bulky silhouette, helmet with a cyan visor` |
| 제4구역장 크래셔 | `a huge factory boss prisoner with mechanical arms made of steel beams, oversized fists, rusty armor plates, cyan steam vents` |
| 총감시관 아크 | `a tall warden in a long dark coat with glowing cyan crystals embedded in the chest, calm cold expression, floating faint cyan mist` |

## 작업 순서
1. 주인공을 먼저 만들어 마음에 드는 한 장을 고르고, 이를 기준 이미지로 삼는다.
2. 나머지 캐릭터는 **우리가 만든 주인공 이미지**를 참조로 올리고 위 프롬프트를 넣는다.
3. 주인공과 기존 작품 캐릭터가 닮아 보이면 머리 모양, 옷, 얼굴 특징을 바꿔 다시 만든다.
4. 배경을 지워 PPT에 넣는다. 게임 스프라이트(픽셀)는 발표 후 별도로 만든다.
5. 동작별 프레임은 같은 캐릭터를 참조해 "same character, running pose"처럼 포즈만 바꿔 생성한다. 어긋나면 프레임 수를 줄이고 이동·기울임 같은 코드 연출로 보완한다.

## 생성 기록
| 날짜 | 대상 | 사용 도구 (모델명) | 비고 |
|---|---|---|---|
| 2026-10-31 | 주인공 N-09, 일반 적 4종, 보스 2종 | Gemini (모델명 확인 필요) | 제공된 두 원본을 발표용으로 정리. 실제 생성에 사용한 프롬프트는 확인 필요 |

## 2026-10-31 Codex 재제작 프롬프트

도구: OpenAI 내장 이미지 생성 도구 (모델명 미제공). PPT용 콘셉트 원화이며 게임용 스프라이트는 아니다.

- 화이트: `Use case: stylized-concept. Original character concept art for a dark 2D action game presentation. A gaunt young prisoner, short unruly white hair, tired heavy-lidded eyes, unmasked, both arms intact and visible, worn gray-black prison clothing, faint cyan haze glow, holding a broken iron pipe. Full body head to feet, centered with generous margin, 3/4 view. Gritty semi-realistic manga ink illustration, strong dark linework, muted navy and slate, restrained cyan lighting. Plain solid dark navy background #0f1623. No text, numbers, logos, watermark, borders, or other characters.`
- 사냥개·간수 공통 (화이트 이미지를 화풍 참고): `Use case stylized-concept. Original full-body enemy character concept for a dark 2D action game presentation. Match reference image 1 only for visual style and palette, do not copy its character. Subject: SUBJECT. Complete silhouette with generous margins, centered single figure, 3/4 view. Gritty semi-realistic manga ink, bold dark linework, navy and slate with restrained cyan haze glow. Plain solid dark navy backdrop #0f1623. No text, logos, letters, watermark, border or other characters.`
  - 사냥개 SUBJECT: `a lean mutated hound of dark smoke and bone, luminous cyan eyes, four legs, crouched`
  - 간수 SUBJECT: `a heavily armored prison guard with full helmet, cyan visor, heavy baton and large riot shield`
- 폐인·투척병·크래셔·아크 공통 (참고 이미지 없음): `Use case: stylized-concept. Original enemy character illustration for dark 2D action game. SUBJECT. Full body head to feet, generous margin, single character, 3/4 view. Gritty semi-realistic manga ink illustration, heavy black line work, muted navy and slate palette, restrained cyan haze glow. Plain dark navy background. No white hair, no white-haired character, no text, no logos, no letters, no watermark, no border.`
  - 폐인 SUBJECT: `a desperate middle-aged gaunt bald male prisoner with stubble and wild eyes, hunched forward, empty clenched fists, ragged prison clothes`
  - 투척병 SUBJECT: `a middle-aged dark-haired scavenger with goggles, patchwork prison clothes, holding a small scrap shield in one arm and a jagged piece of scrap metal in the other`
  - 크래셔 SUBJECT: `a huge bald factory boss prisoner, massive body, rusted steel-beam mechanical arms with enormous fists, rust armor plates and cyan steam vents`
  - 아크 SUBJECT: `a stern mature dark-haired prison warden, long tailored dark coat, cyan crystals embedded in chest, cold expression, no mask and no weapon`

## 2026-10-31 게임용 기본 자세 시안

OpenAI 내장 이미지 생성 도구(모델명 미제공). 각 캐릭터 1장씩 생성. 후처리: `tools/prepare_sprite_drafts.py`로 알파 정리, 최근접 축소 및 캔버스 정렬. 이미지들은 정적 시안으로 애니메이션 프레임이 아니다.

- 주인공: `Use case: stylized-concept. Create one actual in-game character sprite, not concept art: a single small standing playable character for a 2D side-scrolling platform action game, facing right in profile, full body. Original design: young gaunt prisoner with short white hair, tired eyes, both arms intact, no mask, worn charcoal prison outfit, subtle cyan details, empty hands so weapons are drawn separately. Clean hand-crafted chunky pixel art, 32-pixel-tall character appearance, readable silhouette, limited dark navy/gray/white/cyan palette, no anti-aliasing, no gradients, no outline glow. Show only one isolated idle frame with large empty margins, truly transparent background. No sheet, no UI, no words, no watermark.`
- 적 공통: `One actual in-game idle sprite for a 2D side-scrolling platform action game, facing right in profile, full body, one character only. SUBJECT. Clean chunky pixel art, 32-pixel-tall character appearance, readable silhouette, limited dark navy, slate gray, white and cyan palette, crisp hard pixel edges, no gradients or glow. Isolated on genuinely transparent background with margin; no scenery, no sprite sheet, no labels, no watermark.`
  - 슬럼 폐인 SUBJECT: `a gaunt bald middle-aged hostile prisoner in torn gray clothing, hunched, clenched fists`
  - 고철 투척병 SUBJECT: `a dark haired scavenger prisoner with goggles, holding a scrap shield and small piece of junk`
  - 안개 사냥개 SUBJECT: `a lean four-legged mutated dark smoke and bone hound with cyan eyes`
  - 중장갑 간수 SUBJECT: `a bulky armored prison guard with cyan visor, riot shield and baton`
  - 크래셔 SUBJECT: `a very large bald factory prisoner boss with oversized mechanical arms, rust armor and cyan vents`
  - 아크 SUBJECT: `a tall mature dark haired warden in a long dark coat, with cyan crystals in chest`

## 2026-10-31 최종 보스 기본 자세 재생성

OpenAI 내장 이미지 생성 도구(모델명 미제공), 투명 배경 요청. 기존 아크 원본은 `assets/sprites/source/boss_ark_idle_previous.png`에 보존했다. 생성 원본은 `boss_ark_idle_generated.png`, 게임용 정적 시안은 32×32 `boss_ark_idle.png`이다.

`Create one pixel-art game idle sprite, full body facing right in side view. Character: the final villain of a grim prison, an imposing older evil warden with slick black hair, a severe scarred angular face and an icy cyan glare. He wears a long black military warden coat with structured high collar, a deep cyan crystal in his chest, heavy dark gloves and boots. Rigid arrogant posture; cloak makes a sharp striking silhouette. No helmet, no mask, no shield. Clearly sinister and older, NOT a young hero. Single isolated character, plain transparent background. Crisp small-scale 32 pixel character look, limited palette of near-black navy, gray and cyan. Hard edges, no gradient, no shadows, no letters or logo.`

## 2026-10-31 주인공 원본 기준 세밀한 도트 시안

도구: OpenAI 내장 이미지 생성(정확한 모델명 미제공). 이미지 1은 `assets/sprites/source/n09_idle_generated.png`, 이미지 2는 각 적의 기존 `assets/sprites/source/*_idle_generated.png`이다. 생성 결과는 축소하지 않은 원본을 `assets/sprites/detailed/`에 별도로 보관한다.

`Use case style-transfer. Produce ONE original in-game idle sprite on transparent background, facing right in profile, full body with ample transparent margin. Image 1 is ONLY a style reference: match its pixel-art dot size, detail density, proportions, shading and palette. Image 2 is the character design: render only the character from image 2, preserving its species, distinctive silhouette, hair and costume; DO NOT draw the white-haired hero from image 1. Match image 1's fine pixel-art game-sprite style exactly, with sharp pixel clusters and detailed face and costume; do not reduce to 32x32 and do not render an illustration. The final image must have consistent pixel grid appearance, NOT smooth or vector artwork. No text, no logo, no UI, no extra characters.`

결과는 단일 기본 자세 시안이며 픽셀 격자 및 반투명 가장자리 정리, 프레임 정렬, 애니메이션 제작과 게임 테스트는 미완료다. 고철 투척병에서는 기존 시안의 방패가 생성되지 않았다.

## 게임 스프라이트용 프롬프트 (Morphic 등 외부 툴용, 2026-10-31 추가)

콘셉트 일러스트를 먼저 만든 뒤, 이 프롬프트로 게임에서 쓸 픽셀 스프라이트를 만든다. **우리가 만든 콘셉트 이미지(`assets/concept/*.png`)를 참조 이미지로 올린다.** 다른 작품의 이미지는 올리지 않는다.

### 공통 접두사 (스프라이트용)
```
2D side-view pixel art game sprite, facing right, limited palette of dark navy, slate gray and glowing cyan accents, clean 1px dark outline, no anti-aliasing, flat shading, plain solid background, no text, no logos, same character design as the reference image
```

### 필요한 동작과 프레임 수
| 대상 | 동작 (프레임 수) |
|---|---|
| 주인공 | idle 2, run 4, jump 1, fall 1, dash 1, attack(근접) 3, hurt 1 |
| 일반 적 (폐인, 투척병, 사냥개, 간수) | walk/run 4, attack 2, hurt 1 |
| 보스 (크래셔, 아크) | idle 2, 패턴별 공격 각 3, hurt 1 |

### 대상별 프롬프트 (공통 접두사 뒤에 이어서)
| 대상 | 기본 프롬프트 | 동작 프롬프트 예시 (같은 캐릭터 참조 + 포즈만 변경) |
|---|---|---|
| 주인공 | `a gaunt young man with messy short white hair, tired heavy-lidded eyes with faint cyan glow, torn dark jacket with cyan stitching, bandaged forearms, glowing cyan veins on the hands, fists raised` | `running pose, mid-stride` / `jumping pose, knees bent` / `punching pose, cyan trail on the fist` / `hit reaction pose, leaning back` |
| 슬럼 폐인 | `a gaunt prisoner in ragged clothes, hunched posture, dull gray skin with faint cyan veins, holding a rusty pipe` | `walking pose` / `swinging the pipe` / `hit reaction` |
| 고철 투척병 | `a prisoner with a scrap metal shield on one arm, patched clothes, holding a piece of junk to throw` | `standing guard` / `throwing the junk overhand` / `hit reaction` |
| 안개 사냥개 | `a lean mutated hound made of dark smoke and bone, glowing cyan eyes, low crouched` | `running gallop` / `pouncing in the air` / `hit reaction` |
| 중장갑 간수 | `a heavily armored prison guard with a large steel riot shield and a heavy baton, helmet with a cyan visor` | `slow walking` / `heavy overhead swing` / `hit reaction` |
| 제4구역장 크래셔 | `a huge factory boss with mechanical arms made of steel beams, oversized fists, rusty armor plates, cyan steam vents` | `idle breathing` / `charging forward` / `slamming both fists on the ground` / `hit reaction` |
| 총감시관 아크 | `a tall warden in a long dark coat with glowing cyan crystals on the chest, military cap, calm cold expression` | `idle with floating mist` / `raising a hand firing a barrage` / `teleport slash` / `hit reaction` |

### 작업 요령
1. 콘셉트 이미지를 참조로 올리고 **기본 프롬프트로 정면 대기(idle) 한 장**을 먼저 만든다. 이것이 기준 스프라이트다.
2. 같은 도구에서 기준 스프라이트를 참조로 올려 동작 프롬프트만 바꿔 한 동작씩 생성한다. 한 번에 시트를 요청하면 프레임마다 모습이 달라지기 쉽다.
3. 프레임이 어긋나면 프레임 수를 줄이고, 이동·기울임·깜빡임 같은 코드 연출로 보완한다.
4. 생성 결과는 Aseprite 등으로 64×64 캔버스에 맞춰 정리하고 배경을 투명하게 만든다.
5. 도구별 이용 약관(상업·과제 사용, 워터마크)을 확인하고 `docs/ASSETS.md`에 기록한다.

## PixelLab Character Creator 입력값 (2026-10-31 추가)

설정 이름은 화면 버전에 따라 다를 수 있으므로 비슷한 항목을 고른다. 공통 설정: 시점은 side(옆모습)가 있으면 선택, 방향은 4방향 중 좌우만 사용, 외곽선 단색 1px, 음영 단순(flat), 배경 투명.

| 대상 | 캔버스 | 입력 프롬프트 | 애니메이션 |
|---|---|---|---|
| 주인공 | 64 | `gaunt young man, messy short white hair, tired eyes with faint cyan glow, torn dark jacket with cyan stitching, bandaged forearms, glowing cyan veins on hands, dark navy and gray palette` | idle, run, 그 외 `punching forward with cyan trail`, `jumping`, `hit reaction` |
| 슬럼 폐인 | 64 | `gaunt prisoner in ragged clothes, hunched posture, dull gray skin with faint cyan veins, holding a rusty pipe` | walk, `swinging the pipe` |
| 고철 투척병 | 64 | `prisoner with a scrap metal shield on one arm, patched clothes, holding a piece of junk to throw` | walk, `throwing junk overhand` |
| 안개 사냥개 | 64 | `lean mutated hound made of dark smoke and bone, glowing cyan eyes, low crouched` | run, `pouncing` |
| 중장갑 간수 | 64 | `heavily armored prison guard, large steel riot shield, heavy baton, helmet with cyan visor` | walk, `heavy overhead swing` |
| 제4구역장 크래셔 | 128 | `huge factory boss with mechanical arms made of steel beams, oversized fists, rusty armor plates, cyan steam vents` | idle, `charging forward`, `slamming both fists on the ground` |
| 총감시관 아크 | 96 | `tall warden in a long dark coat, glowing cyan crystals on chest, military cap, calm cold expression` | idle, `raising a hand firing a barrage`, `teleport slash` |

## 2026-10-31 투척병·간수 악역 외형 수정

OpenAI 내장 이미지 생성 도구(모델명 미제공). 이미지 1은 수정 전 해당 적, 이미지 2는 주인공 도트 화풍 참고. 수정 전 상세 원본은 `assets/sprites/detailed/previous/`에 보존했다.

공통: `Use case: game-sprite edit. Image 1 is the target enemy design; image 2 is the style reference only. Restyle the target into a clearly dangerous antagonist, preserving the character's gameplay role. Match image 2's fine pixel-art style, dot scale, character proportions, dark slate/cyan palette, shading and output framing. One complete full-body figure facing right, isolated on transparent background, idle pose. No text, labels, logos or extra figures.`

- 투척병: `Enemy role: scrap thrower, a hostile adult prisoner with a sinister scowling weathered face, messy dark hair, ragged dark prison clothing and a jagged scrap piece ready to throw; a small makeshift scrap shield on the other arm. Make the design visibly threatening, not a youthful heroic adventurer. No gore.`
- 간수: `Enemy role: heavily armored oppressive prison guard with a threatening angular dark helmet and narrow cold cyan visor, menacing silhouette, scarred dark steel armor, large dark steel riot shield and heavy baton. Read as a brutal prison enforcer, not a friendly clean robot. No gore.`

새 상세 원본은 `assets/sprites/detailed/`, 게임용 시안은 `assets/sprites/unified/`의 동일 이름에 반영했다. 기존 통일 세트의 색상을 팔레트로 사용해 대상 두 장만 가공했다.


## 주인공 마스터 스틸컷 시험 (2026-11-07)

- 기준: `assets/sprites/unified/n09_idle.png` (이미지 직접 첨부)
- 생성 경로: Codex 내장 `image_gen` (host_image; 정확한 모델명 미제공), 원화 1장. 이용 조건 확인 필요.
- 후처리: generate2dsprite의 hibit 방식, 다수결 축소, 이진 알파, 남색 1px 외곽선. 승인 전 시험 시안이며 애니메이션은 만들지 않음.
- 결과: `assets/sprites/forge/n09_idle_trial.png`, 비교: `assets/sprites/forge/comparison_1x.png`.
- 실제 생성 프롬프트:

```text
Create exactly ONE square image. Use the attached reference as the exact identity and costume: same slim young man, short tousled spiky white hair and long front fringe, pale face, black fitted short-sleeve shirt and black dark trousers, dark shoes, teal forearm and belt accents, same body and head proportions. Adapt to a clear RIGHT-facing side profile, standing relaxed idle, both intact arms visibly separated, empty hands, feet grounded. Full figure centered, generous margins. Clean flat cel-shaded lineless 2D art for later pixel conversion: no outlines or line art, at most 3 flat tones per material, crisp angular solid shapes; no gradients, no texture, no dithering, no pixel grid. No weapon, no text, no logo. Entire background flat pure magenta #FF00FF without shadow or ground.
```


## 주인공 마스터 v2 (2026-11-07)

- 기준: `assets/sprites/unified/n09_idle.png`, 화풍: `assets/sprites/forge/master/master_rgba.png` (순서대로 직접 첨부).
- 경로: Codex 내장 image_gen (host_image, 세부 모델명 미제공), 원화 1장; 비용 정보 미제공.
- 후처리: `tools/finish_character.py`의 hibit, 키 82px(외곽선 포함), 팔레트 24색 및 외곽선. 사용자 승인 대기, 게임 미적용.
- 실사용 프롬프트 (`hero_v2/prompt/prompt.txt`는 생성기 템플릿이며 실제 전달문과 다름):

```text
Edit the SECOND image: it is the previous master still, preserve its clean flat lineless cel-shaded visual style, same white-haired male and dark clothes with teal accents, same right-facing profile and relaxed standing pose. The FIRST image is the original game sprite and controls identity, white hair and worn black clothes; do not invent a new character. Change the second image as follows: visibly widen shoulders and torso: body depth in profile is at least 35 percent of total character height, with somewhat larger head around one sixth the full height. Make the visible profile eye strongly exaggerated, dark teal to near-black, at least 3 percent of full figure height, distinct dark eyebrow, clear nose and mouth, readable after downsampling. Indicate worn torn sleeves and ragged trouser hems using large simple shapes, no tiny details. Both arms must be visible, naturally separated, both feet on same ground line; no weapons. Full body centered with generous margins. Flat opaque colors without outlines, no gradients or texture. Solid pure magenta #FF00FF background; no shadow, no ground, no letters, no symbols or text.
```


## 적·보스 마스터 6종 (2026-11-07)

- 생성: Codex 내장 image_gen, host_image; 정확한 모델명과 비용 미제공. 각 1장.
- 참조 순서: 각 `assets/sprites/unified/<이름>_idle.png`, `assets/sprites/forge/hero_v2/master/master_rgba.png`.
- `prompt/prompt.txt`는 준비 단계 템플릿이며 아래와 `actual_prompt.txt`가 실제 전달한 프롬프트다. hibit 마감 후 사용자 검토 대기, 게임 미적용.

### enemy_slum

```text
One full body character, FIRST reference is exact identity and outfit: gaunt bald hostile prisoner in ragged gray clothing, hunched, clenched fists, faint cyan veins, big dark wild visible eye. SECOND reference is the exact shared rendering style, saturation and light-shadow levels, not the identity: clean flat lineless cel-shaded angular shapes, no outlines, no texture. Side profile facing RIGHT, both feet on ground, large distinct eye, worn details as large shapes, no small decoration. Center whole figure with ample margin on solid pure magenta #FF00FF background, no ground shadow, no text or logo. Artwork for subsequent pixel conversion.
```

### enemy_thrower

```text
One full body character; FIRST reference is this exact enemy's identity: hostile dark-haired scavenger prisoner with goggles, scrap-metal shield on left arm, junk held in right hand, patched black gray clothing and restrained rust accents. SECOND reference supplies the exact shared style, palette saturation, angular cel shading and value steps only. Side view facing RIGHT, standing naturally, large high contrast visible eye or goggle lens, cyan details, oversized simple battered shapes, no fine details. Clean flat lineless art, no outline, no texture, full figure and equipment visible with ample margins. Solid pure magenta #FF00FF background, no floor shadow, no text, no logos.
```

### enemy_guard

```text
One full-body bulky armored prison guard, FIRST reference provides exact character identity: heavy dark steel helmet, large cyan visor, wide armored silhouette, big riot shield in front and a heavy baton clearly held in the other hand. SECOND reference dictates same flat lineless cel-shaded angular forms, saturation and lighting. Facing RIGHT, clear side view, feet grounded; armor worn with large simple shapes, high contrast cyan visor large enough to read at small size. Entire shield, baton and figure inside frame with ample margin. No outlines, no fine detail, no text, no logos, pure solid magenta #FF00FF background with no shadow.
```

### enemy_hound

```text
One lean four-legged hostile mutated hound, FIRST reference supplies exact identity: dark smoke and exposed bone hound, oversized single visible glowing cyan eye, low crouched body; strict right-facing SIDE PROFILE, full body length about 1.4 times height, all paws grounded, silhouette and paws fully inside margins. SECOND reference supplies only its rendering style: flat opaque lineless angular cel-shaded solid shapes, matching dark saturation and light-shadow contrast; large shapes, no fine detail. No atmospheric glow or loose smoke outside silhouette. Solid pure magenta #FF00FF background, no ground shadow, text, logo or outlines.
```

### boss_crasher

```text
One extremely large bald factory boss, FIRST reference supplies identity: massive muscular body, steel-beam mechanical arms with enormous fists, rust armor plates, cyan steam vents, hostile and big dark clear visible eye. SECOND reference supplies the flat lineless cel shaded art style and matched saturation/value steps. Full body in strict side view facing RIGHT with feet on ground, arms clearly visible, no weapon, worn details as big simple shapes. Fully opaque color shapes without black outlines, no texture; entire figure fully visible with generous margin. Solid pure magenta #FF00FF background, no shadow, text or logos.
```

### boss_ark

```text
One tall mature sinister male prison warden final boss. FIRST reference is exact character identity: long dark structured military coat, dark hair, military cap, bright cyan crystals on chest; cold mature stern expression, large clear dark eye, no mask and no weapon, both arms visible. SECOND reference controls ONLY style: matching flat lineless cel-shaded angular color shapes, same dark saturation and light-shadow steps. Full body idle, strict side profile facing RIGHT, feet on ground, generous empty margins. Large simple worn shapes with no small details. No outlines, no texture, no text, no logo; solid pure magenta #FF00FF background and no ground shadow.
```

2026-11-11 [Codex] T01 주인공 v3: legacy·v2 참조, 눈·실루엣·3단 음영·청록 림라이트 강화. Codex image_gen(모델명 미제공); 실제 프롬프트 `assets/sprites/forge/hero_v3/actual_prompt.txt`.
