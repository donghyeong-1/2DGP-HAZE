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

2026-11-11 [Codex] T01 v3b. v3 체형과 의상을 유지하고 올린 앞머리, 진청록 눈의 밝은 반사광, 살색 그림자, 짧은 옷 림라이트를 적용했다. Codex 내장 image_gen(모델명 미제공). 실제 프롬프트는 `assets/sprites/forge/hero_v3b/actual_prompt.txt` 및 `attempt_01/actual_prompt.txt`.

2026-11-11 [Codex] T02 적 3종 v3. 기존 캐릭터와 주인공 v3b를 참조해 폐인의 눈·로프·발 붕대, 투척병의 청록 고글·고철 방패, 간수의 바이저·강철 방패를 강조했다. Codex 내장 image_gen(모델명 미제공). 실제 프롬프트는 각 `assets/sprites/forge/enemy_*_v3/actual_prompt.txt`에 있다.

2026-11-11 [Codex] T01~T03 캐릭터 7종 재제작(총 9회). 우향 전신, 마젠타 배경, 선 없는 3단계 색면. 실제 프롬프트는 `assets/sprites/forge/remake_t01_t03/<캐릭터>/actual_prompt.txt`, 보고서는 `docs/codex/reports/T01_remake.md`~`T03_remake.md`.

2026-11-16 [Codex] T04 N-09 우향 걷기 4포즈, T06 감옥 복도·철골 공장·감시자의 탑. 원화별 실제 프롬프트는 forge 아래 hero_walk_v3/ 및 backgrounds_v1/의 actual_prompt.txt에 기록.

2026-11-16 [Codex] T05 N-09 v3b 기준 우향 대기·빈손 공격·피격·점프 시트. 실제 프롬프트는 assets/sprites/forge/hero_actions_v3/<동작>/actual_prompt.txt.

2026-11-16 [Codex] T07 N-09 v3b 기준 철파이프 우향 공격 5방향. 실제 프롬프트는 assets/sprites/forge/hero_pipe_v3/<방향>/actual_prompt.txt에 기록.

2026-11-16 [Codex] T08 N-09 v3b 기준 우향 대시·파이프 내려찍기·사망. 실제 프롬프트는 assets/sprites/forge/hero_special_v3/<동작>/actual_prompt.txt.

2026-11-16 [Codex] T09 폐인 걷기·공격·피격 및 투척병 던지기·피격 5종. 실제 프롬프트는 assets/sprites/forge/enemy_actions_v3/<동작>/actual_prompt.txt 등에 기록.

2026-11-16 [Codex] T10 크래셔 대기·찍기·돌진·도약·피격. 실제 프롬프트는 assets/sprites/forge/crasher_actions_v3/<동작>/actual_prompt.txt 등에 기록.

2026-11-16 [Codex] T11 사망은 누운 N-09와 헤이즈 안개, 엔딩은 새벽의 열린 문으로 걸어가는 N-09 후면. 실제 프롬프트는 assets/sprites/forge/screens_v1/{death,ending}/actual_prompt.txt.

2026-11-17 [Codex] T13 아이템 10종의 5×2 마젠타 시트. 금속 색면, 항목별 포인트색, 유리관·모래시계 및 강화·연마 실루엣 구분. 실제 프롬프트는 assets/sprites/forge/icons_v1/actual_prompt.txt.

2026-11-17 [Codex] T12 사냥개·간수 동작 9종. 기존 마스터를 참조해 달리기·걷기, 기술별 예고·타격·회수와 피격을 마젠타 격자로 제작하고 사냥개 몸통 높이를 재수정. Codex 내장 image_gen(모델명 미제공). 전문은 `assets/sprites/forge/guard_hound_actions_v3/*/actual_prompt.txt` 및 `hound_run/take_02/actual_prompt.txt`.

2026-11-17 [Codex] T17 N-09 걷기 8프레임. v3b와 기존 걷기를 참조해 좌우 지지발 교대 및 먼 팔다리 명암을 요청하고 6·7번 포즈를 수정했다. Codex 내장 image_gen(모델명 미제공). 전문은 `assets/sprites/forge/hero_walk_v4/take_01/actual_prompt.txt`와 `take_02/actual_prompt.txt`.

2026-11-17 [Codex] T17 v4b 걷기 각도 수정. 관절 가이드로 보폭·발목 각도를 조정하고 3·7번 통과 자세를 낮춘 뒤 지지발 명암을 교정. Codex 내장 image_gen(모델명 미제공). 전문은 `assets/sprites/forge/hero_walk_v4b/`의 `actual_prompt.txt` 및 `take_02/`, `take_03/`.

2026-11-17~18 [Codex] T18 N-09 휘두르기 5방향. v3b 마스터와 T15 키프레임을 참조해 젖힘과 최대 신장 사이, 팔꿈치를 내리며 파이프 끝을 뒤·아래로 보내는 회수 자세를 2칸 마젠타 시트로 제작. Codex 내장 image_gen(모델명 미제공). 전문은 `assets/sprites/forge/hero_pipe_v5/<방향>/actual_prompt.txt`.

2026-11-18 [Codex] T19 N-09 달리기 8장과 전환 5장. v3b 마스터와 관절 가이드로 전방 기울기·지지발 교대·두 발 체공과 출발·제동·방향 전환을 요청했다. Codex 내장 image_gen(모델명 미제공), 프롬프트 전문은 `assets/sprites/forge/hero_run_v1/{run,trans}/actual_prompt.txt`.

2026-11-18 [Codex] T20 총감시관 아크 23프레임. 지정 마스터와 게임 대기 이미지를 참조해 5패턴의 예고·실행(특히 양팔 벌린 흡수와 X자로 웅크린 과충전), 이동·순간이동·피격·페이즈·사망을 선 없는 색면으로 제작. Codex 내장 image_gen(모델명 미제공). 실제 프롬프트는 assets/sprites/forge/ark_actions_v1/{A,B,C}/actual_prompt.txt.

2026-11-19 [Codex] T21 N-09 달리기 교대 재작업. 걸음 A·B를 별도 2×2 시트로 만들고 밝은 소매·찢어진 무릎이 가까운 팔다리에 붙어 앞뒤를 바꾸도록 요청했다. 각 시트 2차에서는 가까운 바지·부츠의 밝은 차콜과 먼 쪽의 검은 면을 강화했다. Codex 내장 image_gen(모델명 미제공). 실제 프롬프트는 assets/sprites/forge/hero_run_v2/{A,B}/actual_prompt.txt 및 take_02/actual_prompt.txt.

2026-11-19 [Codex] T22 은신처 원경과 NPC 3명 마스터·대기 6장. 원경은 따뜻한 등불·청록 결정·비어 있는 중앙과 아래 1/4을 요청했고, NPC는 주인공 v3b 화풍으로 렌치·결정 의수의 정비사, 자물쇠 상자·등불의 보관인, 안경·장부의 기록관을 제작했다. Codex 내장 image_gen(모델명 미제공). 실제 프롬프트는 assets/sprites/forge/hideout_v1/actual_prompt.txt 및 npc_v1/<역할>/{actual_prompt.txt,idle/actual_prompt.txt}.

2026-11-19 [Codex] T23 N-09 궁극기 컷인·시전 2장. v3b 마스터를 참조해 흰 머리·청록 눈빛·해진 상의의 오른쪽 클로즈업과 기술명 여백이 있는 사선 띠, 웅크려 모으기→앞으로 내지르기를 요청했다. 시전은 머리 비율과 해방 높이를 1회 편집. Codex 내장 image_gen(모델명 미제공). 전문은 assets/sprites/forge/cutin_v1/actual_prompt.txt와 n09_ult_v1/{take_01_prompt.txt,actual_prompt.txt}.

2026-11-21 [Codex] T24 N-09 철파이프 2단계 강화 6장. v3b 마스터를 참조해 웅크림→수평→머리 위 올려베기, 두 손을 머리 위로 든 체공→45° 하강→깊게 내딛는 바닥 타격을 요청했다. 마지막 컷은 손 높이와 파이프 접촉을 강조해 1회 재생성했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/n09_stage2_v1/raw/*_prompt.txt.

2026-11-21 [Codex] T25 일반 적 4종의 피격 반동 및 쓰러짐 16장. 각 종의 대기 원화와 기존 피격 ①을 참조해 앞발 들기, 무릎 꺾임, 무릎 또는 어깨가 닿고 바닥에 누움을 요청했다. 사냥개는 옆구리와 주둥이를 바닥에 댄 컷을 별도 생성했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/enemy_death_v1/<종류>/actual_prompt.txt 및 hound/flat_prompt.txt.

2026-11-21 [Codex] T26 N-09의 식칼 준비·던지기·마무리, 건틀릿 충전·발사·회수·공중 하향 사격, 사슬 머리 뒤 준비·던지기·당기기 10장. v3b와 기존 무기 그래픽을 참조했고 식칼 준비의 칼날 분리를 1회 다시 생성했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/n09_weapon_poses_v1/provenance.json에서 연결.

2026-11-21 [Codex] T27 크래셔 걷기 4장·사망 2장. 승인 마스터와 관절 가이드로 밝은 가까운 장화와 먼 장화의 교대, 접지 후 하강을 지정하고 한 손으로 무릎 자세를 지탱한 뒤 앞으로 엎어지도록 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/crasher_walk_death_v1/provenance.json에서 연결.

2026-11-21 [Codex] T28 슬럼·공장·탑·은신처의 원경과 타일을 참조해 배경 소품 12종의 반복 4컷을 3×4 시트로 생성했다. 브래킷·받침은 고정하고 낙하와 파문, 좌우 흔들림, 점멸, 상하 왕복, 회전을 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트는 assets/sprites/forge/props_anim_v1/provenance.json에서 연결.

2026-11-21 [Codex] T29 기존 제목 화면·컷인·N-09·아크를 참조해 청록 투명 HAZE/헤이즈 로고, 감옥 헤더와 작은 상반신 배너, 두 인물의 대치, 아래에서 보는 탑, 감옥→공장→탑 파노라마를 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/store_art_v1/provenance.json에 연결.

2026-11-21 [Codex] T30 투척병 승인 마스터와 걷기 가이드를 참조해 방패와 고철을 든 전진 4컷, 오른쪽을 보며 뒷발을 뻗고 앞발을 당기는 물러서기 2컷을 요청했다. 걷기 후반 두 컷은 장화와 무릎의 차이를 키워 재생성했다. Codex 내장 image_gen(모델명 미제공), 프롬프트 전문은 assets/sprites/forge/thrower_walk_v1/provenance.json에서 연결.

2026-11-21 [Codex] T31 슬럼·공장·탑의 실제 원경·중경·타일과 T28 소품을 참조해 바닥 3종·벽 3종의 마젠타 시트를 테마별 한 장씩 생성했다. 왼쪽 위의 약한 빛, 글자 없는 얼굴 실루엣·톱니·마름모, 분리된 색면을 지정했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/room_decor_v1/provenance.json.

2026-11-21 [Codex] T32 N-09·정비사·보관인·기록관의 마스터와 게임 스프라이트를 참조해 마젠타 상반신 두 컷으로 무표정·결의, 무뚝뚝·웃음, 차분·걱정, 생각·놀람을 만들었다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/portraits_v1/provenance.json.

2026-11-21 [Codex] T33 제목 화면과 각 원경을 참조해 비 내리는 감옥 골목과 청록 웅덩이, 용광로·컨베이어·증기, 결정이 자란 탑 계단을 가로 띠로 만들었다. 중앙은 어둡게 남기고 슬럼은 탑과 웅덩이가 함께 보이도록 구도를 보정했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/zone_cards_v1/provenance.json.

2026-11-21 [Codex] T34 크래셔·아크의 마스터와 인게임 그림, 공장·탑·보스방 원경, 아크 상점 그림을 참조했다. 왼쪽을 보는 오른쪽 상반신, 용광로 불똥과 청록 소용돌이, 어두운 왼쪽을 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/boss_cards_v1/provenance.json.

2026-11-21 [Codex] T35 탈출·제목 화면, 은신처 원경, N-09와 NPC 마스터를 참조했다. 새벽 언덕, 화로 곁의 세 NPC와 빈자리, 헤이즈가 걷힌 도시를 만들고 도시에서 성벽을 줄여 주거지를 드러냈다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/credits_scenes_v1/provenance.json.

2026-11-22 [Codex] T36 공장 원경·타일과 기존 적을 참조해 주황 철판, 두 로터, 청록 렌즈, 아래 토치를 가진 용접 드론을 만들었다. 마스터를 고정해 로터 회전·아래쪽 공격 예고와 분사·엇갈린 피격 각도·사망 2컷을 만들었다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/drone_v1/provenance.json.

2026-11-22 [Codex] T37 공장 타일·원경·장식 수레·간수·크래셔를 참조해 고철, 바퀴 넷, 찌그러진 범퍼, 청록 통, 빨간 경고등을 가진 수레를 만들었다. 굴러감·통 팽창과 경고등 점멸·앞바퀴 들림·그을린 잔해를 각각 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/cart_v1/provenance.json.

2026-11-22 [Codex] T43 공장·헤이즈 원경과 타일, 기존 소품을 참조해 수평 발판이 있는 고철 기둥의 낙하·박힘·붕괴, 증기 밸브의 열림·피격·닫힘, 배기구의 꺼짐·빨간 예고·황주황 분출 직전, 결정 기둥의 솟음·직립·파괴를 각각 마젠타 3칸 시트로 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/boss_terrain_v1/provenance.json.

2026-11-22 [Codex] T38 탑 감시 카메라·청록 패널·아크·탑 원경과 타일을 참조해 둥근 청회색 철 몸통과 마름모·케이블·우향 청록 렌즈·왼쪽 벽 고정판을 가진 감시 눈을 만들었다. 마스터를 기준으로 동공 좌우 이동, 렌즈 점등 3단계, 발사 직전보다 밝은 발사, 균열과 반동, 파편과 소등을 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/eye_v1/provenance.json.

2026-11-22 [Codex] T39 중장갑 간수·아크와 탑 원경·타일을 참조해 얼굴을 가린 투구, 날렵한 갑옷, 어깨 청록 결정, 한 손의 결정 장검을 그렸다. 대기, 가까운 다리와 먼 다리가 교대하는 걷기, 결정 분해와 재조립, 칼을 뒤로 빼는 예고부터 타격과 회수, 반동과 파편을 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/knight_v1/provenance.json.

2026-11-22 [Codex] T40 각성 오라·아크·탑 원경과 타일을 참조해 어두운 청록색 연기 상반신, 밝은 민트 눈 두 개, 연기 꼬리 하나를 가진 망령을 만들었다. 꼬리의 네 단계 변화, 양손을 모으는 예고부터 앞으로 뻗고 거두는 흡수, 피격으로 갈라진 몸, 눈이 사라지고 옅은 연기점만 남는 소멸을 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/wraith_v1/provenance.json.

2026-11-22 [Codex] T41 사냥개·폐인·슬럼 원경과 타일을 참조해 짙은 남색 털, 뾰족한 주둥이, 둥근 귀, 붉은 눈, 등에 솟은 청록 결정과 긴 꼬리를 가진 헤이즈 쥐를 만들었다. 달리기 발 접지와 도약, 웅크린 뒤 턱을 벌리는 물기, 피격 반동, 뒤집혀 눈이 닫히는 쓰러짐을 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/rat_v1/provenance.json.

2026-11-22 [Codex] T42 폐인·투척병·보관인과 슬럼 원경·타일을 참조해 황토색 누더기 후드, 큰 부적, 청록 결정을 낀 고철 지팡이로 누더기 무당을 만들었다. 지팡이를 짚는 대기, 발을 교대하는 뒷걸음, 손을 올린 뒤 민트색 결정 지팡이를 들어 올리는 보호막 시전, 피격 뒤 균형을 잡는 동작을 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/shaman_v1/provenance.json.

2026-11-22 [Codex] T44 기존 UI 아이콘을 참조해 각성 꽃결정·위험 불씨·페이드 고리·강화 소용돌이, 리벳 쇠·청록 결정·금과 진홍 결정의 빈 카드 테두리, 조각·심장·결정 꽃·보라 결정·망치·해골 보상을 각각 시트로 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/mutation_ui_v1/provenance.json.

2026-11-22 [Codex] T45 아크의 날개 문장과 가슴 청록 결정을 탑 기계 강철 껍질에 옮겼다. 고정된 외곽 안에서 셔터 닫힘·반개방·완전 개방, 열린 마름모 약점의 피격 균열, 균열이 퍼지고 하단 판 두 조각이 떨어지는 두 붕괴 단계를 순서대로 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/heart_core_v1/provenance.json.

2026-11-22 [Codex] T48 각 구역의 중경을 참고해 중앙이 빈 마젠타 바탕에 좌우로 이어지는 어두운 실루엣을 요청했다. 슬럼은 전선·빨래·철창, 공장은 배관·사슬·크레인 갈고리, 탑은 가로 철골과 결정 가지를 지정했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/foreground_v1/provenance.json.

2026-11-22 [Codex] T46 본체의 강철·날개 문장·청록 결정과 아크 장갑을 참조해 손목에 짧은 케이블 두 가닥을 단 기계 오른손을 요청했다. 대기, 주먹 내려치기, 펼친 손바닥 레이저 예고와 발사, 결정이 꺼진 기절을 순서대로 각각 두 자세로 지정했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/heart_hands_v1/provenance.json.

2026-11-22 [Codex] T47 탑과 보스방 원경을 참조해 중앙 상단을 비우고 하단 1/4을 어둡게 둔 기계 공동을 요청했다. T34 아크 카드, T45 본체 및 T46 손을 참조해 오른쪽 1/3에 열린 본체와 양손을, 왼쪽 2/3에는 글자 자리를 둔 카드를 요청했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 assets/sprites/forge/heart_arena_v1/provenance.json.

2026-11-23 [Gemini] G01 새 주인공 디자인 시안 3안(A: 짧은 작업 재킷+청록 연기 머플러, B: 찢어진 롱코트+헤이즈 흡입 마스크·관, C: 각진 후드+등 헤이즈 탱크·팔 호스). 어두운 무채색 몸체·청록(#00F0E0) 단일 포인트·3단계 평면 음영·마젠타 배경 옆모습(`hero_<A|B|C>_side.png`)과 정면·달리기 실루엣·8색 색표 시트(`hero_<A|B|C>_sheet.png`) 요청. Antigravity 내장 image-generator(모델명 미제공). 상세는 docs/gemini/reports/G01.md.

2026-11-23 [Gemini] G04 주인공 대화 초상화(`hero_portrait.png`, 1024×1024). `hero_A_side.png` 기준에 G01 결정 흰 머리·청록 눈(#00F0E0)·어두운 작업 재킷·청록 연기 머플러, 가슴 위 3/4 구도, 애니풍 선화·3단계 셀 음영, 마젠타 배경 요청. Antigravity 내장 image-generator(`gemini-3.1-flash-image`). 나머지 NPC 3장 및 G02·G03은 429 할당량 소진으로 중단. 상세는 docs/gemini/reports/G04.md.

2026-11-24 [Gemini] G05 UI 전면 개편 시안 3안(A 최소형·B 공업형·C 결정형) 중 전투 HUD 3장(`ui_{A,B,C}_hud.png`) 및 일시정지 3장(`ui_{A,B,C}_pause.png`, 1920×1080). `docs/gemini/refs/G05_ui/{01_battle_hud,02_pause}.png`의 게임 세계는 보존하고 UI만 960×540 2배 픽셀 격자·흰색+헤이즈 청록(#2ee6d6)+불투명 어두운 남색(#0d121f, 경고만 주황·빨강)으로 재디자인 요청(A: 1점 흰 선·ㄱ자 꺾쇠·판 바탕 제거 / B: 리벳 철판·청록 액체 압력 유리관 게이지 / C: 비대칭 사선 다각형·양끝 수정 첨탑·모서리 결정 클러스터). Antigravity 내장 image-generator(`gemini-3.1-flash-image`). 증강 카드 3장은 429 할당량 소진으로 대기. 상세는 docs/gemini/reports/G05.md.

2026-11-25 [Gemini] G05 2차(C안 결정형 + A안 크기) `ui_C2_hud.png` 및 `ui_C_cards.png`(1920×1080, NEAREST 전용). `01_battle_hud.png`·`ui_A_hud.png`·`ui_C_hud.png` 참조로 결정 장식을 게이지 양끝·2번 무기 모서리·온전한 하트 옆 3곳만 남긴 축소 결정형 HUD 요청, 이어 `03_augment_cards.png`·`ui_C2_hud.png` 참조로 왼쪽 전설(금색 `#ffd36e` 선·결정)·가운데 희귀(청록 선·결정·상승 선택 강조)·오른쪽 보통(흰 1점 선·결정 없음)+진행 칸 2개 카드 3장 요청(새 영어 문구 금지). Antigravity 내장 image-generator(`gemini-3.1-flash-image`). 상세는 docs/gemini/reports/G05.md 6절.
2026-11-23 [Codex] T49 슬럼의 남색 비·판자촌·감시탑, 공장의 녹슨 주황 굴뚝·용광로·크레인, 탑의 어두운 청록 공동·결정 기둥·난간·감시 장치를 요청했다. 원경은 아래 전투 영역을 어둡게, 중경은 마젠타 바탕 위 구조물이 좌우에서 이어지게 지정했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 `assets/sprites/forge/backdrops_v6/provenance.json`.

2026-11-25 [Gemini] G02 보스 3종 새 디자인(`crasher_side.png`, `ark_side.png`, `heart_core.png`, `heart_hand.png`, `bosses_sheet.png`). `hero_A_side.png` 화풍(선 없는 평면 색면·3단계 음영·왼쪽 위 광원·마젠타 배경)과 기존 보스 그림을 참조해 크래셔(공장 주황·녹슨 갈색·거대 유압 건틀릿·등 배기관·왼쪽 향함), 아크(감시탑 검은 금속·청록 안감 분할 코트·챙모자·지휘봉·왼쪽 향함), 헤이즈 심장 본체(정면 대칭·방폭문 틈 청록 핵) 및 기계 오른손(손바닥 청록 마름모 핵) 요청. Antigravity 내장 image-generator(`gemini-3.1-flash-image`), `bosses_sheet.png`는 Pillow 합성. 상세는 docs/gemini/reports/G02.md.

2026-11-25 [Codex] T50 간수와 크래셔를 참조해 오른쪽을 보는 녹슨 중갑, 투구의 청록 눈구멍, 큰 철창 방패와 짧은 몽둥이, 황동 열쇠와 호루라기를 요청했다. 대기·걷기·방패 돌진·내려찍기·증원 호출·피격·처치 17컷을 마젠타 원화 시트로 생성했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 `assets/sprites/forge/gatekeeper_v1/provenance.json`.

2026-11-25 [Gemini] G06 UI 부품 4장(`c_frames.png`, `c_bars.png`, `c_icons.png`, `c_cards.png`, 8× 정합·G06 13색 팔레트·순수 `#FF00FF` 마젠타). G05 `ui_C2_hud.png`·`ui_C_hud.png`·`ui_C_pause.png`·`ui_C_cards.png`를 참조해 판·틀 8종, 막대·첨탑 9종, 아이콘 11묶음을 Antigravity 내장 image-generator(`gemini-3.1-flash-image`)로 생성(`c_cards` 신규 호출은 429 소진으로 G05 `ui_C_cards.png` 모서리 결정 추출) 후 Pillow/numpy로 1× 목표 논리 크기 정합·13색 양자화·8배 NEAREST 마감. 상세는 docs/gemini/reports/G06.md.

2026-11-25 [Codex] T51 은신처 NPC들을 참고해 오른쪽 옆모습의 두건과 목 천, 여러 겹 해진 적갈색 망토, 가슴·허리의 병과 주머니, 내민 손 위 청록 결정 하나를 요청했다. 같은 인물의 대기 호흡과 결정 부유 2컷, 결정을 쥐고 끄덕이는 거래 2컷을 마젠타 시트로 생성했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 `assets/sprites/forge/drifter_v1/provenance.json`.

2026-11-25 [Codex] T52 기존 샘 폭과 두 구역 타일을 참고해 끊긴 철 배수관, 고철·벽돌 테두리, 청록 웅덩이와 결정을 마젠타 원화로 요청했다. 같은 구조에서 물결과 결정의 밝은 면만 변하는 두 컷, 물이 빠져 균열과 회색 결정만 남은 한 컷을 추가로 생성했다. Codex 내장 image_gen(모델명 미제공). 프롬프트 전문은 `assets/sprites/forge/spring_v1/provenance.json`.

2026-11-25 [Claude Code] PixelLab(v6 방식, 화풍 기준 = 간수 base)으로 이벤트 방의 떠돌이 죄수와 헤이즈 샘을 만듦. 떠돌이: 오른쪽 옆모습, 해진 죄수복 위 누빈 적갈색 망토, 두건과 목 천, 허리·가슴의 주머니와 병, 내민 손바닥 위 청록 결정 하나(결정만 밝게). 샘: 깨진 배수관 아래 고철·벽돌 그릇에 고인 청록 헤이즈와 결정(표면과 결정만 밝게), 마른 그림은 같은 그림을 글로 편집(물과 빛을 없애고 결정을 회색 그루터기로). 영문 프롬프트 전문·seed·시안 비교는 `assets/sprites/pixellab/drifter_v6/GENERATION_LOG.md`, `assets/sprites/pixellab/spring_v6/GENERATION_LOG.md`.

2026-11-25 [Claude Code] PixelLab(v6 방식, 화풍 기준 = 간수 base)으로 은신처 NPC 셋을 다시 만듦. 정비사: 올린 머리·이마의 주황 고글·올리브색 작업복·회색 의수(청록 불빛)·어깨에 멘 큰 렌치. 보관인: 구부정한 노인·갈색 두건 망토(청록 안감)·등에 진 자물쇠 궤짝·손에 든 등불. 기록관: 헝클어진 갈색 머리·둥근 안경·귀에 꽂은 연필·회청색 셔츠·가슴에 안은 두꺼운 적갈색 장부. 글로 적은 키를 지키지 않아 캔버스를 줄여 키를 맞췄다. 영문 프롬프트 전문·seed·시안 비교는 `assets/sprites/pixellab/(mechanic|keeper|archivist)_v6/GENERATION_LOG.md`.

2026-11-25 [Claude Code] PixelLab(v6 방식)으로 남은 일반 적 5종을 다시 만듦: 누더기 무당(올리브색 누더기·두건·청록 결정 지팡이), 헤이즈 쥐(보랏빛 회색 털·등의 청록 결정), 감시 눈(회청색 강철 몸통·받침대·큰 청록 렌즈), 헤이즈 망령(어두운 청록 안개·긴 팔·빛나는 눈), 자폭 수레(녹슨 광차·고철 돌·청록 통과 붉은 경고등). 캔버스 크기로 몸 크기를 맞췄고 동작은 전부 글로 지시(pixminimax). 영문 프롬프트 전문·seed·고른 프레임은 `assets/sprites/pixellab/(shaman|rat|eye|wraith|cart)_v6/GENERATION_LOG.md`.

2026-11-25 [Claude Code] PixelLab(v6 방식)으로 최종 보스 아크를 다시 만듦. Gemini G02 원화를 글로 옮김: 키 크고 마른 감시탑 총감시관, 발목까지 오는 검은 군용 코트와 청록 안감, 높은 깃, 청록 마름모 배지의 검은 챙모자, 창백한 얼굴과 빛나는 청록 눈, 어깨·팔뚝 장갑의 청록 결정, 가슴·허리의 청록 약병, 앞손의 가는 검은 지휘봉. 동작은 패턴마다 "예고 자세를 잠깐 유지 -> 실행 자세를 유지"로 지시. 영문 프롬프트 전문·seed·고른 프레임은 `assets/sprites/pixellab/ark_v6/GENERATION_LOG.md`.

2026-11-25 [Claude Code] PixelLab(v6 방식)으로 헤이즈 심장을 다시 만듦. 본체: 정면에서 본 좌우 대칭 요새형 기계의 **왼쪽 절반만**(가운데 절단선이 캔버스 오른쪽 끝) 그리게 해 뒤집어 붙임. 가운데 장갑 문과 청록 이음매, 날개 문장, 볼트 기둥, 청록 띠가 있는 날개 블록, 위쪽 굵은 관, 계단형 받침. 문이 열려 결정이 드러나는 동작과 결정이 깨지며 꺼지는 동작. 손: 손바닥이 보이는 거대한 기계 오른손, 통통한 손가락 넷과 엄지, 손바닥의 큰 청록 결정, 손목 고리. 영문 프롬프트 전문·seed·고른 프레임은 `assets/sprites/pixellab/heart_core_v6/GENERATION_LOG.md`, `heart_hand_v6/GENERATION_LOG.md`.

2026-11-25 [Claude Code] PixelLab으로 은신처 대화 초상화를 새 몸 그림에 맞춰 다시 만듦(화풍 기준 = 주인공 초상화). 왼쪽을 보는 3/4 흉상: 정비사(올린 머리·이마의 주황 고글·올리브 작업복·회색 의수·어깨 뒤 렌치), 보관인(갈색 두건·회색 수염·등의 자물쇠 궤짝), 기록관(헝클어진 갈색 머리·둥근 안경·귀의 연필·회청색 셔츠·장부). 표정 2는 "표정만 바꾸고 나머지는 그대로"로 글 편집(씩 웃음·걱정·놀람·결의). 전문은 `assets/sprites/pixellab/portraits_v6/GENERATION_LOG.md`.

2026-11-25 [Gemini] G04 대화 초상화 남은 5장 완료(`mechanic_portrait.png`, `keeper_portrait.png`, `archivist_portrait.png`, 추가 표정 `hero_portrait_angry.png`, `hero_portrait_hurt.png`, 각 1024×1024). `hero_portrait.png` 화풍·가슴 위 3/4 구도와 `npc_{mechanic,keeper,archivist}_idle_1.png` 외형을 참조해 애니풍 선화·3단계 셀 음영·마젠타 배경 요청. Antigravity 내장 image-generator(`gemini-3.1-flash-image`). 상세는 docs/gemini/reports/G04.md.

2026-11-26 [Claude Code] PixelLab으로 주인공 대화 초상화를 다시 만듦(사용자 요청: NPC처럼 PixelLab으로). 가슴 위 3/4 오른쪽, 창백한 회청색 피부, 뒤로 솟은 흰 머리, 빛나는 청록 눈, 차분하고 지친 표정, 목을 감싼 짙은 머플러와 검은 작업 재킷, 머플러에서 오르는 청록 기운. 예전 주인공 초상화를 기준 그림으로 넣고 "같은 인물을 다시 그려라". 결의 표정은 얼굴만 글로 편집. 영문 프롬프트·seed·시안 평가는 `assets/sprites/pixellab/portraits_v6/GENERATION_LOG.md`.

2026-11-26 [Claude Code] PixelLab으로 보스 이름 카드 상반신(크래셔·아크·문지기)을 새로 만듦(O4). create_image_pro_flash 208x200, 화풍 기준 = 주인공 대화 초상화(color_palette false), 보스마다 seed 3·11 두 장. 설명은 각 보스의 v6 디자인 그대로, 3/4 시점 왼쪽을 봄, 허리에서 자른 상반신. 영문 프롬프트 전문과 시안 평가는 `assets/sprites/pixellab/boss_cards_v6/GENERATION_LOG.md`.

## 2026-11-26 UI 3차 증강 갈래 아이콘 (PixelLab create_image_pro_flash 32x32)
프롬프트·시안·고른 이유는 `assets/sprites/pixellab/ui_plate_v1/GENERATION_LOG.md` 표. 공통: "pixel art game icon symbol: <갈래 기호>, bold chunky shapes, readable at small size, dark outline, flat shading, no background, centered", 팔레트 #0c0e13 #5a6272 #a7afbd #eef1f6, 첫 장(연결)을 style_image로.

## 2026-11-27 UI 'mist' 증강 카드 테두리 (PixelLab create_image_pro_flash 128x176)
"Minimalist card border frame for a dark game UI: one single thin 1-pixel pale grey-white line forming a tall rectangle, with a small white diamond ornament centered on the top edge and on the bottom edge, and tiny short accent ticks at each of the four corners. The inside of the rectangle and the outside are fully transparent. Flat clean lines, elegant and quiet. No fill, no metal, no rivets, no thick border, no bevel." 팔레트 #eef1f5 #b8c0cc #6e7888 #343c4a, 화풍 기준 = A 흰 장식선, seed 21·22 중 22. 기록 `assets/sprites/pixellab/ui_mist_v1/GENERATION_LOG.md`.

## 2026-11-27 타이틀 번갯줄기 (PixelLab create_image_pro_flash 64x160)
"A single thin jagged lightning bolt striking downward from the top edge, pixel art. One main crooked channel one to two pixels wide with a few thinner forking side branches that split off and fade. Bright white core with a pale blue edge. Transparent background, no clouds, no glow blob, no ground." 팔레트 #ffffff #dce8ff #9fb6ee #5d74b8, seed 31·32·33 모두 씀. 기록 `assets/sprites/pixellab/ui_mist_v1/GENERATION_LOG.md`.

## 2026-11-27 무기·E 패널 그림 시험 P1 (PixelLab create_image_pro_flash, 화풍 기준 = 갈래 아이콘 up_mut_bloom. 기록 `assets/sprites/pixellab/ui_wp_v1/GENERATION_LOG.md`)
- 소켓(씀, 48x48 seed 61, 팔레트 고정): "Pixel art HUD gem socket, 1-pixel scale: a large diamond (rhombus, square rotated 45 degrees) touching all four canvas edges. Bright pale white 1-pixel outer outline clearly visible, a second thinner grey outline two pixels inside it, small bright plus-shaped notches sitting on each of the four points. Inside is plain flat dark navy, empty. High contrast between the pale outline and the dark inside. Transparent outside the diamond. No metal, no rivets, no stripes, no text."
- 결정(씀, 32x32 seed 52): "Pixel art game item at 1-pixel scale: a single tall pointed hexagonal crystal shard standing vertically, about 12 pixels wide and 26 pixels tall, centred. Sharp points at top and bottom, glowing teal-cyan, light left facet, darker right facet, a bright thin highlight down the middle edge, dark outline. Clean, no base, no sparkles. Transparent background."
- 무기 칸 틀(씀, 48x36 seed 64, 팔레트 + 열쇠색 #ff00ff, 배경 지우기 끔): "Pixel art HUD item slot frame, 1-pixel scale, a wide rectangle filling the canvas edge to edge. Bright pale white 1-pixel outline clearly visible, the top-left and bottom-right corners cut off diagonally by 4 pixels, a short bright tick mark beside each cut corner, a faint grey inner line two pixels inside the outline. Inside the frame is plain flat dark navy, empty. Outside the frame (the cut corner triangles) is solid magenta #ff00ff. No metal, no rivets, no bolts, no stripes, no text."
- 버린 것(소켓 96x96 s41·48x48 s51, 결정 64x64 s42, 칸 틀 96x72 s43·48x36 s53, 키 배지 16x16 s65)의 프롬프트는 위와 같은 말투이고 기록 파일에 까닭을 적었다.
- (W6, 11/27) 게임 기본 모습('mix')에 쓰는 것은 위 P1의 결정(32x32 seed 52)과 무기 칸 틀(48x36 seed 64) 두 장이다. 새로 생성하지 않았다.
