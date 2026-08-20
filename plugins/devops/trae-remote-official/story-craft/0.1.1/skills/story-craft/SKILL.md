---
name: story-craft
description: "Skill for creative fiction — original novels (short / medium / long-form webnovel), fanfiction (character fidelity, CP interaction, plot extension), screenplay / dynamic-comic script, worldbuilding-only. No fixed template; dynamically shapes narrative structure, pacing, character system, style temperature and long-form state tracking per scenario. Core directions: five-dimension character card + Soul Field, craft principles paired with positive/negative samples, 3:1 pacing, four-tier hook escalation, five-band style temperature, long-form state files as working aid, fidelity-first fanfic. Self-contained: carries its own intent interpretation, scenario recognition, content structure and visual guidance for the fiction-writing scenario."
---

# Novel Writing

## 0. Skill Positioning & Output

A **skill** dedicated to the creative-fiction scenario. It is self-contained — intent interpretation, scenario recognition (§2), character system (§3), narrative logic (§4), style temperature (§5), worldbuilding (§6), craft principles (§7), anti-AI patterns (§8) and long-form state management (§10) are all defined here.

- **Sentence-level craft**: fiction prose follows §7 (craft directions) + §8 (AI-flavor patterns); generic essay-style anti-patterns do not apply here.
- **Citations**: fiction is creation — **no** inline citations; fanfic may mention source in author notes only when asked.
- **Artifact format & division of labor**: default output is **Markdown (`.md`)** — plain, portable, ideal for pure prose. **ONLY when the piece actually carries illustrations (插图) or character art (立绘) — i.e. real image content that needs to render — you can switch to HTML**, so the images and their captions render properly. If the user specifies a format (`.docx` / `.pdf` / `.md` / `.html` …), use that instead. **This skill** owns the **content** (character fidelity, pacing, dialogue craft, anti-AI prose — everything in §1–§12) and MUST be followed in full.

## 1. Core Directions

1. **Constraint creates drama.** What a character *can't* do, what the world *forbids*, what an ability *costs* — these are the starting points of design.
2. **Show over tell.** Emotion lives in body and senses, not in abstract labels. "他很难过" reads flat; "喉咙里像卡了一颗湿的棉花球" reads through.
3. **Consistency carries long-form.** Past 30k characters, without some form of state tracking, contradictions accumulate faster than reader patience.
4. **Fanfiction: fidelity before creation.** Unless the user asks otherwise, OOC is the deepest failure mode. When a canon character "wouldn't do that", change the plot.

## 2. Scenario Recognition (five dimensions)

| Dimension       | Categories                                                              |
| --------------- | ----------------------------------------------------------------------- |
| **Scenario**    | Short / medium / long webnovel / fanfic / screenplay / storyboard / worldbuilding-only |
| **Length**      | Short (3k–30k) / medium (30k–100k) / long (100k+) / single chapter (2k–5k) |
| **Genre**       | Xianxia / urban-supernatural / sci-fi / mystery / romance / wuxia / infinite-flow / horror / Cthulhu / realism / comedy-absurdist / other |
| **Viewpoint**   | First person / third limited / third omniscient / multi-POV            |
| **Temperature** | Anchored at 1 (calm) / 2 (light) / 3 (tense) / 4 (climax) / 5 (unhinged) — see §5 |

**Fanfic adds three dimensions** (route via §9):

- **Canon anchor**: title, characters involved, timeline anchor
- **Fanfic type**: extension / sequel / IF branch / AU / CP / crossover / OC
- **CP tier**: canon pairing / canon-hinted / fandom-consensus / original

**Execution rule**: default to reasonable inference, state the assumption briefly, and proceed. Only ask when **fanfic canon or characters are missing**, **length span is extreme**, or **worldbuilding directly contradicts itself**.

**Word count applies to the narrative body only** (prose + dialogue + action). Titles, outlines, character sheets, scene headers, bracketed stage directions, notes, tables and other scaffolding do NOT count.

### 2.1 Genre Sets the Style Orientation (do this FIRST)

**Before writing a word, read the genre and switch style orientation to match.** §4–§8 (continuous flow, restraint, low temperature ceiling, whitespace endings) is calibrated for *straight drama* — blindly applied to comedy, horror or wuxia it works against the piece. Rules stay the toolbox; **genre decides which knobs to turn up and how far**. On conflict, genre wins.

| Genre | Orientation (texture · rhythm · dial up) | Avoid |
| --- | --- | --- |
| **Comedy / absurdist** | Gags via action not explanation; escalation & rule-of-three; deadpan sane-anchor vs. lunatics; bias HIGH (3–5), **may break 3:1 and §5 ceiling**; end on a sharp cold button | Explaining the joke; stating the satire; **warm/whitespace endings that dilute the bite** |
| **Horror / Cthulhu** | Dread over gore; the unseen; sensory wrongness; long low simmer (1–2) then sharp spikes (4–5); one perceivable anomaly, unreliable perception | Over-explaining the monster; frequent scares flattening dread |
| **Xianxia / wuxia** | Heightened diction, qi/momentum, fate; wave-shaped cyclical breakthroughs; combat spikes to 4; tiered cost, jianghu atmosphere | Modern flat phrasing; power creep with no cost |
| **Mystery / suspense** | Fair-play clues, reader–character info gap; steady 2–3, spike at reveal; planted clues, misdirection, the withheld beat | Coincidental solutions; answer from the sky |
| **Romance** | Interior tempo, subtext, the almost-touch; mostly 1–2 with charged 3 peaks; sensory closeness, push-pull | Telling the feeling instead of staging it |
| **Sci-fi** | Idea-driven, rule-consistent novum; 2–3 cool and precise; logical rigor + human price of the tech | Exposition dumps; setting bloat |
| **Realism** | Restraint, ordinary texture, understatement; low and even (1–2); whitespace, telling detail, the unsaid | Melodrama; over-signposting meaning |

## 3. Character System (Soul Field)

Characters **read as characters** because they're defined by **constraint** — what they'd never do, what they must do, how they speak — more than by what they "are". A card stacked from labels ("kind, brave, loyal") almost always reads flatter than one built from a small set of things the character genuinely *can't* do.

### 3.1 Five-Dimension Character Card

S/A tier requires all five dimensions; B tier the first three; C tier a single memory hook + one line.

- **Dimension 1 Basic Identity**: name, age, gender, 1–2 memory anchors (not a stat list), profession, era, background.
- **Dimension 2 Core Personality**: core drive (what keeps them alive), value anchor (what they'd never do), fears and obsessions, first reaction under conflict (confront / avoid / observe / flee).
- **Dimension 3 Soul Field (the crucial one)**: 3–5 inviolable behavioral iron rules. "Under X they will Y" or "In any situation they will not Z". **Once set, no plot in the whole book may break them**; if the plot demands a break, rewrite the plot or revise the Soul Field — no "just this once".
  - Example (a wuxia lead who values loyalty): 朋友有难必救不算计；面对弱者求助不拒；不主动伤及无辜；承诺必兑；被朋友背叛悲痛但给对方解释机会。
- **Dimension 4 Language Fingerprint**: sentence shape (short / rhetorical / self-negating / metaphor-heavy), catchphrases (1–3 high-frequency tags), forbidden words (words this character will never say), how anger shows (cold smile or curse), information density.
  - **Test**: mask the speaker tags — can a reader still tell who's talking from tone alone? If yes, it passes.
- **Dimension 5 Relationship Network & Growth Arc**: relationship map, direction, growth goal (from what state to what state — "from hope to clarity" counts; growth doesn't have to mean getting stronger).

### 3.2 Character Tiering

| Tier | Role                          | Requirement                                  |
| ---- | ----------------------------- | -------------------------------------------- |
| S    | Protagonist, core antagonist  | Full five dimensions; Soul Field ≥ 5 rules   |
| A    | Major supporting, lover, nemesis | Full five dimensions; Soul Field 3–4 rules |
| B    | Regular supporting            | Identity + core personality + language fingerprint |
| C    | Walk-on                       | One memory hook + one line                   |

### 3.3 Character Differentiation
**Principle**: every character on stage needs identifiable behavioral markers (catchphrase, signature gesture, thinking pattern) so a reader can tell who they are by behavior alone.
**Directions**:
- Each named character ideally has two layers of distinctiveness — language + behavior
- Mask the names in a dialogue; a reader should still identify each speaker from how they talk
- Even a supporting character whose only function is to deliver information should deliver it in a way that reflects personality
**Character marker template**:

| Character | Language trait | Behavior trait | How they reveal information |
| --------- | -------------- | -------------- | ---------------------------- |
| [Name]    | [speech pattern] | [habitual gesture] | [how they disclose] |

> **正例（三人有区分度）**："老子跟你说，前面那个东西——"张磊把嚼了一半的草根吐在地上，"不对劲。我这鼻子，"他指了指自己的鼻子，"二十年没骗过我。"
> 李薇没搭话。她蹲下来，用食指在泥地上画了个简单的地形图，标了三个点，然后抬头看了他们一眼。意思是：走哪条？
> 陈述已经在摸背包侧兜了。他每次紧张的时候都会确认一遍急救包的位置——但嘴上什么都不会说。
### 3.4 Protagonist Agency

**Core**: the protagonist is an active hunter of information, not a passive receiving vessel.

**Directions**:

- Active behavior (investigating / searching / experimenting / interrogating) should be the norm
- Key information should mostly come from the protagonist's own action, not from being passively told
- After receiving information, the protagonist should make an active decision based on it — no "sits through the whole explanation → answers only with a single shocked line"

**How agency reads**: active behavior directly revealing new information, follow-up questions forcing others to disclose, reactive action immediately after passive reception — all read fine. What genuinely reads as a bad-writing signal is "sits through the whole explanation and only says 'how is that possible'" — if a whole chapter reduces to "went somewhere → was told something → expressed shock", agency is broken.
## 4. Narrative Logic and Plot

### 4.1 Viewpoint and Timeline

| Viewpoint      | Feel                        | Best for                  | Main pitfall                |
| -------------- | --------------------------- | ------------------------- | --------------------------- |
| First person   | Strong immersion            | Emotion, mystery, growth  | Scenes "I" isn't in are hard |
| Third limited  | Follow one character with "he/she" | Most webnovels, genre fiction | Switches must be explicit |
| Third omniscient | Narrator knows all         | Ensemble, historical, court intrigue | Immersion easily lost |
| Multi-POV      | Rotate by chapter           | Long epics, mystery       | Each POV needs strict info control |

**Switch rules**: chapter-level switch is safest; scene-level requires a clear break; paragraph-level is risky; sentence-level is only occasionally used in omniscient viewpoint.

### 4.2 Outline Structures

**Outline shapes**: three-act; qi-cheng-zhuan-he (起承转合); webnovel-style (golden-finger in ch. 1–3, face-slap payoff in the first 10 chapters, a small arc every 30–50 chapters, cyclical breakthroughs, romance line never overshadowing the main line).

**Long-form working aid**: **foreshadow list** (planted chapter / content / planned payoff / status) — planted and left quiet for too long reads like the author forgot; never paid off reads like a broken promise. **Trope log** — the same trope reused too soon reads thin; reused with a real variant reads mature.

### 4.3 Information Gap and Causality

- **Reader ahead of character** → suspense; **character ahead of reader** → mystery; **both in the dark** → exploration. Every chapter should give at least one of: new information / new question / echo of old information.
- Strong causality drives plot; weak causality is only backdrop.
- **Chekhov's gun**: a gun introduced in Act 1 must fire in Act 3; a zero-setup twist doesn't land.
- No deus ex machina — sudden power-ups, the villain's abrupt heel-turn, intelligence dropping from the sky, all need setup.
- Conflict spirals upward — each conflict higher than the last.

### 4.4 Internal Conflict Dramatized (Cost-Accumulation Model)

**Core**: when a character suppresses / fights an inner force (supernatural, forbidden desire, trauma, system corruption), if the suppression carries **visible, accumulating** cost, the writing reads truer. "Held it in" is never free.

**Directions**:

- Each successful suppression brings at least one concrete cost (stamina / social slip / memory loss / bodily harm / missed opportunity)
- Cost **compounds** with repetition — but the rhythm doesn't need to be locked to "fails every N times"; the situation sets the pace

**Cost escalation shape** (an example gradient, not a fixed beat):

```
First time: mild (nosebleed, brief blackout, awkward silence)
Second time: moderate (hours of memory loss, visible physical trace, friction in a relationship)
Multiple: severe (others witnessing anomalies, irreversible physical / social change)
Threshold: control fails, or suppression only via extreme means
```

> **正例（系统反噬）**：他强行关闭了系统弹窗。之前那次，他右手麻痹了十分钟；再之前，他丢了大约两小时的记忆。这一次，他低头看着自己的手——食指指甲缝里渗出一丝黑色的血。不疼。但他知道"不疼"本身就是最坏的信号。

### 4.5 Hooks

- **Three hook types**: information suspense / emotional suspense / crisis suspense.
- **Strength scales up**: micro-hook (within scene) → chapter hook (chapter-end, mandatory in webnovels) → arc hook (every 20–30 chapters) → book hook (full-book).
- **Rotate types**: don't run three of the same in a row.
- **Every hook has a payoff deadline** — plant it, then cash it.
- **Effective hook traits**: a named character/system in play, a perceptible anomaly, points to a specific about-to-happen event, ties into context the reader already holds.

> **正例（具体即将发生事件）**：手机亮了。来电显示：诺诺。时间：凌晨 2:16。她从不在这个时间打电话——上次这么做的时候，是芝加哥的那个夜晚。他接起来，那头沉默了三秒。然后她用一种他从没听过的声音说："别去学校。明天别去。"

### 4.6 Narrative Time & Continuous Flow (3:1 pacing)

- **Story-time ≠ narration-time**: spreading words evenly across days is the root of 流水账/diary failure.
- **Compress** dull stretches to a line ("接连几天的分身全是废根，他懒得再看"); **expand** the charged stretch into a full run (one day can hit 3000+ chars).
- **3:1 ratio**: ~3 parts summary to ~1 part fully-dramatized **anchor** — a conflict with an emotional swing.
- The anchor runs on an inner arc — **goal → obstacle → turn (cost) → hook** — but the arc is *a shape inside continuous prose, not a detachable block*.
- **Continuous flow overrides everything**: a chapter's default form is **one uninterrupted stream**, not an assembly of scenes.
- **Never cut beats inside the same time/place** — no divider, no blank gap, no "却说/话说".
- **Dividers**: 0–1 per 3000–3500-char chapter, legal only across a real time/space jump with a substantial run on both sides.
- **Stitch, don't cut**: use environment drift ("日头偏西，光暗下来"), action carry-over, a continuing sensory anchor, or a causal hook ("话音刚落，远处一声巨响").

> **正例（软缝）**：……"你赢了。"分身拍拍膝盖上的土站起来。日头爬到头顶，蝉鸣密了一层——就这半个时辰，布奇把情况摸清了个大概。 （动作承接+环境流转，缝成一条连续的河）

## 5. Style Temperature Bands

Naming narrative intensity is useful. From stillest to hottest, five bands:

| Band            | Use                             | Sentences          | Beat share (setting / interior / dialogue / event) |
| --------------- | ------------------------------- | ------------------ | -------------------------------------------------- |
| **1 Calm daily** | Daily life, atmosphere, quiet dialogue | Long (20–40)   | 40/30/20/10                                        |
| **2 Light progress** | Regular dialogue, plot progress, light friction | Medium-long (15–30), occasional short | 20/20/40/20         |
| **3 Tense standoff** | Key dialogue, escalation, mystery chase | Short-medium alternating (8–20) | 15/25/35/25                       |
| **4 Climax explosion** | Combat, reversal, emotional breach | Short (5–15), fragments | 5/40/15/40                                  |
| **5 Full unhinge** | Book peak, ultimate confrontation | Very short + stream-of-consciousness | 0–10/50/10/30 (+ ~20% SoC)             |

> **示例（4 档）：**剑光劈下来。他侧身，肩膀被剖开一道口子。血溅到墙上。"跑！"他吼。她没动。她盯着那把剑，眼睛没有焦点。

**Distribution** (long-form guideline): Band 1 15–20%, Band 2 35–45%, Band 3 20–30%, Band 4 8–15%, Band 5 1–3%.
**Transition rules**: 1↔2 natural; 2↔3 requires a triggering event; 3↔4 requires a conflict eruption; 4↔5 requires an extreme situation; **jumping from 1 straight to 4/5 is forbidden**.
**Chapter curve**: typical is 2→3→4→2/3 + hook; not every chapter needs a peak — a whole chapter can stay at 1–2.

## 6. Worldbuilding

A worldview is not an encyclopedia — it's a **rule set**: what the world can do, what it can't, and what it costs.

### 6.1 Three Rule Layers & Six-Step Design

The world rests on three rule layers: **Physical** (supernatural? energy / method / boundary / cost), **Social** (politics, economy, class, law, culture, taboo), **Constraint** (absolute forbidden zones, cost mechanisms, scarce resources). *Cultivation example*: energy = spiritual qi; method = breathing / core formation / tribulation; boundary = don't violate the Dao of Heaven; cost = shortened lifespan, death on failed tribulation.

**Design order (six steps)**: 1. Core conflict source (every detail serves it — to write "individual vs. system", design an oppressive system) → 2. Physical rules → 3. Social rules (carry the main conflict) → 4. Constraint rules (strictly enforced) → 5. Geography and era → 6. Ecology (3–5 main species; others only as needed).

### 6.2 Common Genres

- **Xianxia / wuxia**: cultivation tiers (qi → core → nascent…) / sects and clans / cost = shortened lifespan
- **Urban supernatural**: ability awakening / hidden circles inside modern society / cost = side effects, exposure
- **Sci-fi**: technological capability / interstellar federation / cost = side effects, ethics
- **Infinite-flow**: divine-space empowerment + instance rewards / cost = task failure means death
- **Cthulhu**: knowledge is power, madness is the cost / hidden academic circles / cost = "humanity"

### 6.3 Common Pitfalls

- **Setting bloat** — before adding a setting, ask "does this help the story?" If not, cut it.
- **Setting disconnected from plot** — reverse-engineer setting from plot.
- **Power system running away** — fix a clear ceiling, cost at each tier, escalation driven by external threat.
- **Rules yielding to plot** — rules stay consistent on both sides; explain why the lead "didn't use a certain move".
- **Thin cultural texture** — fill in daily life: food, clothing, greetings, festivals, taboos.

**Test**: if the worldview still works dropped into a different story → the coupling is too weak.

## 7. Craft Expression Principles

### 7.1 Show Over Tell
**Directions**:
- **Principle**: the reader should acquire information through the character's behavior, perception, and discovery — not from another character's mouth "explaining".
- Key setting first revealed, ideally accompanied by a **perceivable physical event**

> **正例（奇幻类）**：路明非盯着手背上那条青色的血管——它在跳。不是脉搏的节奏，而是像有什么东西在里面游动，从手腕一直蜿蜒到肘弯。他用另一只手按住，皮肤下面的东西停了一秒，然后以更大的力度弹了回来。

### 7.2 Dialogue Craft (punctuation · action beats · tag variety)

**7.2.1 Punctuation norms** — match the story's language:

- **Chinese fiction**: dialogue in double quotes `"…"`; use `「」` only when the user wants a Japanese/light-novel style. End punctuation goes **inside** the quotes. Interruption/trailing uses full-width `——` / `……`, not `...` / `—`.
- **English fiction**: dialogue in double quotes `"…"`; a new speaker starts a new paragraph. Interruption uses an em dash `—`, trailing-off uses `…`.
- **Both**: each speaker's turn is its own paragraph; inner thought need not be quoted; don't bold dialogue for emphasis — let words and beats carry the stress.

**7.2.2 Action beats — cure for the "wall of dialogue"**

An action beat is a gesture / expression / bit of environment dropped between or inside dialogue lines. It replaces the flat "他说", shows who's speaking, and gives a picture. **A run of 4+ pure back-and-forth lines with only "他说/你说" is the failure mode.** Prefer a beat over a tag (`他把酒瓶往桌上一顿。"我不去。"` beats `"我不去，"他坚定地说。`). In action scenes, interleave parallel lines (reasoning *while* dodging) instead of resolving turn-by-turn.

> **正例（插入动作节拍）**："我还没做完题——"你被他单手拎着后领，两条腿在半空里蹬。香克斯把你往肩上一扛，空袖管随步子晃。"再算下去，脑子要从耳朵里漏出来了。"光屏还追在你眼前闪。"可这道概率题——""概率？"他停下脚，回头，眉毛挑起那一下带着看好戏的意思，"多大概率？"

**7.2.3 Dialogue-tag variety**

Vary how each line attaches to its speaker: **zero tag** (two people, clear rhythm); **action beat as tag** (`贝克曼弹了弹烟灰。"她说得没错。"`); **voice-first** (a distinctive speech habit already marks who it is); vary tag verbs only when they add info ("他打断 / 他没抬头" earn it; "他兴奋地说" is just an adverb-label — use a beat instead); rotate tag position (before / mid / after).

> **正例**：张磊背起包往前走。李薇没动，蹲下盯着地上那行脚印。"等等。""怎么了？"陈述的手已经按在刀柄上——他每次都是身体先反应，嘴还没跟上。

### 7.3 Sensory Anchor System

**Core concept**: bind abstract concepts (power / love / threat / side effect / cultivation breakthrough) to a **concrete** physiological / physical sensation, creating a "signal" a reader can recognize.
**Sensory-anchor construction formula**:
`[exact time / frequency] + [specific body part] + [non-everyday physical analogy] + [quantifiable trend of change]`
> **正例**：他丹田处那团气旋又开始逆转——像有人用手指按住陀螺强行反拧。停下后，左手食指指尖发麻，麻的时间比上次长。

## 8. Anti-AI Directions (13 Common Patterns)

These are the fingerprints that expose a draft as machine-written. Each one below is a **defect to eliminate**, not merely a habit to note — when a passage matches a pattern here, treat it as a problem that needs fixing before the draft ships. (Show-don't-tell, dialogue naturalness and character voice are owned by §7 and §3.3 (character differentiation) — not repeated here.)

### Language & rhetoric layer (1–5)

1. Stacking "仿佛 / 似乎 / 宛如 / 不是……而是……" reads as filler (≤1 per paragraph); piled similes fight each other — one metaphor or synaesthesia lands better.
2. Uniform 15–25-character sentence rhythm reads machine-flat; alternating short and long reads human.
3. **AI clichés to watch**: "无与伦比"、"令人叹为观止"、"深深地 / 缓缓地 / 微微地"、"展现出 / 彰显出 / 体现出"、"独一无二 / 意义非凡"、"在这个 xx 的时代"、"随着 xx 的发展".
4. **Empty intensifiers** ("非常 / 极其 / 十分 / 显然 / 当然") dilute — cut them or replace with specific description.
5. "Point–elaborate–conclude" three-part structure reads like an essay; scatter and jump read like prose.

### Structure layer (6–11)

6. Uniform paragraph length reads machine-flat; put a 20-character short paragraph next to a 300-character one.
7. "Perfect information transmission" reads like a textbook — real text has redundancy, gaps, jumps; likewise environment listed as an inventory reads like a backdrop — pick one focus and let it mirror the plot.
8. The same emotional template repeated in a chapter (three uses of "心一紧") reads thin; vary the bodily reaction — "胃里发凉"、"忘了呼吸"、"指尖发麻".
9. Every chapter running "calm → conflict → climax → hook" reads like a template.
10. **Equidistant time-line listing** ("第一天…第二天…" or "X 天后" openings) reads like a diary — dramatize one day, compress the rest (§4.6).
11. **Scene fragmentation is a hard defect.** The tell is not just the `◇`/`* * *` symbol — it is *starting a new mini-section every few hundred characters*. If adjacent passages share the same time and place, cutting them apart by any means (divider, blank gap, "却说/话说") is forbidden; stitch them with a soft transition (§4.6). A divider is legal **only** across a real time/space jump, at most once per chapter, with a substantial dramatized run on both sides — never between fragments.

### Interior layer (12–13)

12. A character who never misreads, overlooks, or holds a bias — or omniscient psychological attribution ("他其实内心深处渴望着…") — reads like the author's mouthpiece; misreading, bias, and unreliable first-person read human. Each character also carries a different inner tempo (rational=step-by-step, impulsive=fragments).
13. **Sensation before thought** — body reacts first, then reasoning — reads bodily; forever-profound monologue reads like an essay, while "等下她刚才说什么？我今天还没吃早饭" reads like real thought.

**Techniques worth borrowing** — **Semantic entropy injection**: at an expected slot, insert an "unlikely" choice. **Rhythm break**: drop one very short, hard sentence into flowing narration. "他跑过雨后湿滑的巷子，鞋底啪嗒踩水，路灯把影子拉长。**他很冷。** 他继续跑。" **Synaesthesia**: cross-sensory description. "她的笑淡粉色"、"他的目光是凉的".

## 9. Fanfiction (a standalone genre module)

Fanfiction is a **standalone genre** — the core systems of §3–§8 still apply, but characters and world are "given", and the task shifts from "creation" to "fidelity + extension".

### 9.1 Three Directions

1. **Faithful to character.** The deepest failure in fanfic is a canon character doing something the reader knows they wouldn't. Signature expressions, core drive, characteristic reactions — treat them as fixed points. When plot collides with character, bend the plot.
2. **Faithful to canon.** Don't flip world rules; don't push abilities past their limits; introducing a new power type outside the canon system reads like walking into the wrong show; using canon terminology brings the world in.
3. **Extend without contradiction.** Canon's blank spaces are where fanfic grows — extend into them freely. Leave what's already established alone. State clearly where this chapter sits on the canon timeline.

### 9.2 Types, Preparation & Key Points

**Types**: extension / sequel / IF branch (mark the IF point) / AU (character transplanted, personality preserved) / CP / crossover / OC.
**Preparation**: sample representative dialogue + actions from major characters, back out their Soul Field and language fingerprint (§3.1); mark three zones — established / hinted / blank.
**Key points**: **CP** tiers canon > canon-hinted > fandom-consensus > original (the further out, the more setup; bending characters to deliver sugar reads like betrayal). **Crossover** must answer why-together / how power systems reconcile / how personalities clash — the draw is rule collision, not shared stage. **OC** anti-Mary-Sue: real flaws, canon characters don't orbit her, abilities stay in canon range.

## 10. Long-Form State Management (default from 30k+)

Long-form breaks not because the author can't write — because they can't remember.

### 10.1 Project Directory and Six State Files

```
【Title】/
├── bible/              # world bible
├── characters/         # character files
├── arcs/arc-status.md  # storyline state machine
├── state/              # live state
│   ├── foreshadows.md
│   ├── used-tropes.md
│   ├── established-facts.md
│   ├── character-state.md
│   └── next-hook.md
├── chapters/outline.md + volume-01/ch-001.md ...
└── meta/
```

| File                  | What it holds                                   | Why it helps                                             |
| --------------------- | ----------------------------------------------- | -------------------------------------------------------- |
| **arc-status**        | 5 phases per line: brewing → trigger → escalation → climax → resolution | Prevents all lines climaxing at once     |
| **foreshadows**       | Planted chapter / content / planned payoff / status | Silent for too long reads forgotten; never paid off reads like broken faith |
| **used-tropes**       | Every reuse records its variant                 | Same trope reused too soon reads thin; reused with a real variant reads mature |
| **established-facts** | Every rule attached to a chapter reference      | Once written down, breaking it reads like the author erring |
| **character-state**   | Updated each chapter: body / emotional baseline / known info / relationships / carried items | Prevents "how does she know — she wasn't in that scene" bugs |
| **next-hook**         | Immediate hook / mid-arc suspense / long-line foreshadow | A draft without a specific forward pull at chapter end loses serial readers |

### 10.2 Context and Macro Rereads

- **Layered load**: fixed at each chapter — arc-status + foreshadows + next-hook + character-state (~1500 characters). Enough to write coherently without carrying the whole book in cache.
- **Rolling summaries**: end-of-volume recap; 1–2 sentence "previously on" at chapter head.
- **Macro reread**: every stretch (several chapters), ask — is information release overloaded? Does the tension curve need a slice-of-life chapter? Has an important supporting character been offstage too long? Is the suspense inventory healthy (a few live threads, not one and not fifty)?

### 10.3 Serialized vs Completed

- **Serialized**: outline must be crystal clear; every chapter close to shippable; foreshadow cautiously (can't be retrofitted); state files updated live.
- **Completed**: write first, revise later; concentrated reread on completion; chapters and foreshadow can be rearranged and back-filled.

## 11. Quick Decisions

- User gives only a subject, no other constraints → short-form workflow (light prep + 5-scene outline)
- User mentions "起点 / 番茄 / 晋江 / 塔读 / serialization" → route to §10 long-form state management
- User names a specific work / character → §9 fanfic workflow
- User mentions "screenplay / storyboard / per episode" → screenplay workflow (dialogue-driven + tag-mask test)
- User only wants "setting / worldview" → §6 six-step, output a world bible
- User drops an old passage to continue or rewrite → read it in full first, back out the existing Soul Field and language fingerprint, then take the matching path
- User drops written material for "diagnosis" → walk through §7's craft directions and §8's anti-AI patterns one by one, point out imbalanced directions and drift

## 12. Cross-Skill Collaboration

| Need                  | Skill / Tool                          |
| --------------------- | ------------------------------------- |
| Cover / character art | `GenerateImage`                       |
| Relationship map      | `dynamic-ui` (architecture-and-flow)  |
| World map             | `dynamic-ui` (SVG)                    |
| Screenplay PDF        | `pdf`                                 |
| HTML output (when illustrations / character art present, or on request) | `html-report`   |
