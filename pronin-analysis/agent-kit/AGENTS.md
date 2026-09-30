This file provides guidance to Agents when working with code in this repository.

# What this repo is

An agent-driven video production workspace, not an application. Videos (Russian-language Instagram Reels, 9:16, 1080×1920; FPS set by the workflow, 30 by default) are built from local assets with Remotion or HyperFrames, reviewed in Storybook, and rendered with ffmpeg-backed tooling. There is no app-level build, lint, or test suite; each sub-project (`style-review`, `projects/*`) has its own `package.json`.

Read the matching file in `workflows/` before starting any video. It is the authoritative process for that video type and overrides generic skill guidance. Skills live in `.agents/skills/<name>/SKILL.md` (≈60 of them: remotion-*, hyperframes-*, storybook, deepgram-transcribe, remove-image-background, icons, extracting-design-styles, humanizer-ru, media-use, etc.). Subagents live in `.agents/agents/<name>.md`; their Codex copies are generated into the `video-agents` skill by `scripts/sync-agents.py`, and that skill's SKILL.md is the roster.

Read `workflows/_shared/production-qa.md` **in full** before creating or revising any video, in every workflow (including `top-ranking` and any future one). Part A of that file, «Видео, а не презентация» (U01–U16), is the owner's universal video standard: frames built around one large object doing an action, no presentation chrome, the thing to remember as the largest text, plain-language on-screen text, a hook that is clear from its first sentence, voice-led timing, overlapping transitions with no instant swaps, one accent on the active element. A workflow may tighten these values but never drop a rule. Part B is the error register (G01–G44), Part C the stage checks. Existing user authorization takes precedence; these checks do not add approval gates.

Precedence: user instruction in this session → production-qa Part A and the workflow's invariants → the rest of the workflow → `assets/styles/<name>/DESIGN.md`. If a style sheet sets smaller type, an off-centre layout box or mandatory panels/chips, follow Part A and note the conflict in `media/change-log.md`.

**Check the workflow is complete before using it.** A workflow lists its sections at the top; if any section it or its companion SKILL.md refers to is missing (for example the file starts mid-way), stop and tell the user — never fill the gap from memory.

**One living spec per video.** Keep all current requirements in the project's `media/spec.md`. A new user request replaces the conflicting old decision there (it is not appended next to it), and a structural remark («looks like slides», «monotone», «unclear», «too small») changes the scene template for every scene, not one frame. Track every request of the current round in `media/change-log.md`; never send a version while a row of the current round is unverified, and name any row you did not do.

Before sending any video to the user — a test scene or a final render — run the selected workflow's creative self-review on the **encoded MP4** (contact sheets, seam frames, word-timing check, a frame scaled to 360 px width), fix what it finds, then send. Report three kinds of verification separately, each with its own evidence: technical (ffprobe, decoded frames), visual (composition, legibility, transitions), speech/audio (whole phrases, pronunciation, SFX on clicks). Evidence of one kind never closes an item of another; build success, `hyperframes check` or audio correlation do not prove the video is good.

Specify all animation timings in seconds/ms in plans, specs and messages. Use frame counts only together with an explicit fps: reference measurements may come from a 30 fps source while the project renders at 60 fps.

# Channel defaults — apply to every video, every workflow

These are the owner's standing requirements. They apply automatically to every new video
and every revision without asking; only a direct instruction from the user for a specific
video overrides them.

- **Format: Instagram Reels, 9:16, 1080×1920.** Never produce another aspect ratio unless
  the user asks for it in that request. Keep semantic content inside the Reels safe zones
  (see cross-cutting rules): Instagram UI covers the bottom and right edge.
- **Channel:** name `milanko.ai`, logo `assets/logos/milanko.ai/logo.jpg`. Always use this
  local file as the channel logo/avatar. Never generate, redraw, or substitute a placeholder;
  if the file is missing, stop the CTA work and report it instead of inventing one.
- **Subscribe CTA at the end of every video.** The last scene asks the viewer to subscribe
  to `milanko.ai`:
  - a spoken line in the video's voice (default wording: «Подписывайся — разбираю эй-ай и айти
    простыми словами: что это такое и зачем оно нужно»; adapt only to the topic if needed,
    keep "эй-ай"/"айти" pronunciation);
  - a channel card with the logo, the name `milanko.ai`, and a readable one-line promise
    (≥27 px at 1080 width), plus a visible subscribe action (e.g. a cursor clicks
    «подписаться» and it changes to «вы подписаны ✓»);
  - the CTA scene lasts as long as its measured spoken line plus its tail, never
    truncated; motion continues to the final frame; styled in the selected workflow's
    visual language.
  - The CTA line is part of the script and is approved together with it; it is not a reason
    to re-ask for approval on its own.
- Verify all three in the encoded MP4 before sending: 1080×1920 via ffprobe, the correct
  logo file on the last scene, and the CTA line audible in the final audio.

# Workflow selection and reuse

Every video must use a workflow. The user may name it explicitly or describe the
format in ordinary language. When the request unambiguously matches an existing
workflow, select it automatically, briefly state the selection and proceed under
its rules without asking for confirmation. An explicit user choice takes precedence.
A selection established for the current project remains valid for edits.
Record the selection in the project's `media/workflow.json` with a repo-relative
`workflow` path.

Requests to create a top-3/5/10 or ranking video (including Russian «топ», «рейтинг»
and English “top”, “ranking”) route to `workflows/top-ranking.md` when they describe
the video's format. Load `top-ranking` and `workflow-kit`; extract the topic, explicit
count and language from the request and use the workflow's remaining defaults.
For example, «Создай видео “Топ-10 фильмов с Райаном Гослингом” на русском языке»
is sufficient to start the top-ranking workflow, including service preflight,
existing style/template, specified voice, music/SFX and autonomous production.
Do not ask the user to repeat paths, voice IDs or settings already fixed there.

If multiple workflows plausibly fit and the request/project does not resolve the
choice, offer the matching workflows and wait before production. If none fits,
explain that a suitable workflow must be created first and help define and create
it. Do not force a mismatched workflow. A generic video skill is not a substitute.

Each workflow must have a companion reusable skill in `.agents/skills/`, linked from
the workflow. Use `workflow-kit` for shared inventory and reuse conventions; use the
format's companion skill for its components, commands and checks. The workflow owns
requirements and approval gates; skills implement them without duplicating policy.
New workflows ship with a small working, verified starter kit. Existing workflows
without one receive a companion kit when next used, before production, rather than
through a speculative bulk migration. The first implementation is `top-ranking`.

Before creating anything, inventory the existing reusable assets and components.
Reuse verified backgrounds, typography tokens, ranking tables, captions, transitions
and sound palettes. Keep text/language/count-dependent visuals parameterized; cache
static elements as ready assets. Store shared Remotion code in `projects/remotion/_shared/`,
scripts in `scripts/<area>/`, media in the appropriate `assets/` category, and format
specs beside their workflow. Keep style folders limited to `DESIGN.md` and `preview.png`.
Per-video scripts, speech, transcripts and subject-specific media stay in the project.

Promote useful solutions to the shared library after functional and visual verification;
record supported inputs and verification evidence beside the implementation. Expand
kits from actual production needs. Recheck changed shared components and affected
examples; caching never replaces preflight, per-video QA, or service failure rules.

# Project structure

## Where things go

| Path | Purpose | Rules |
|---|---|---|
| `workflows/` | One markdown file per video type describing the full production process, plus a same-named folder for that format's spec (zones, tokens, previews). | Read the matching workflow before starting a video. It overrides generic skill advice. |
| `scripts/` | Reusable scripts and shared gotchas, grouped by area (`reference-explainer/`, `remotion/`). | Anything needed more than once goes here. One-off, per-video tooling stays in `projects/remotion/<project>/tools/`. |
| `.agents/skills/<name>/SKILL.md` | Agent skills (Remotion, HyperFrames, Storybook, Deepgram, background removal, icons, style extraction, text humanizing, stealth browser, etc.). | Invoke by name. |
| `.agents/agents/<name>.md` | Subagent definitions (researcher, trender, scriptwriter, reference-breaker, assetfinder, proof-hunter, uieditor, sound-designer, qachecker). `README.md` there holds the exchange protocol. | A workflow names which agents to use; an agent never names a workflow. Delegate only for isolated context, fresh eyes or parallelism — otherwise do it inline. Edit the `.md`, then run `scripts/link-skills.sh` to relink and regenerate the Codex twins. |
| `.agents/mcp/<name>/` | Locally hosted MCP servers, one directory each. Currently `stealth/`: an anti-detect Firefox browser (uv project with `uv.lock` and a launcher). | Cross-platform by design. Start through `uv run` as configured in `.mcp.json`; see the README inside for setup. Read the `stealth-browser` skill before using its tools. |
| `docs/` | Plans and design specs in markdown (`docs/superpowers/{plans,specs}/`). | Write new plans and specs here, dated `YYYY-MM-DD-<topic>.md`. |
| `projects/remotion/` | Remotion video projects and their `node_modules`. | Remotion code lives only here. |
| `projects/hyperframes/` | HyperFrames video projects and their `node_modules`. | HyperFrames code lives only here. |
| `style-review/` | Storybook app for reviewing video screens and style references before rendering. | Stories must import the same beatmap and components the video project uses. Never duplicate screens in story-only JSX. |
| `videos/` | Final rendered videos. | Save as `videos/<timestamp>-<short-description>/<short-description>.mp4`. Verify with ffprobe before declaring done. |
| `temp/generated_images/` | Raw AI-generated images awaiting processing. | Move the processed result into `assets/`, then delete the temp file. |
| `temp/generated_voices/` | Raw AI-generated voice clips awaiting processing. | Concatenate into `assets/voice/<project>/`, then delete the temp files. |
| `pids/<name>.pid` | PID of each long-running process you start (Storybook, dev servers). | Write the PID when starting, remove it when stopping, so the process can be found and killed later. |

## Shared asset library (`assets/`)

**Only things reused across videos.** Fonts, music, SFX, stickers, icons, backgrounds. A single video's voiceover, transcript and script are not assets — they live with the project, in `projects/remotion/<project>/media/`. A format spec is not a style — it lives next to its workflow.

| Path | Contents |
|---|---|
| `fonts/<family>/` | Local font files. Always load fonts from here, never from remote URLs. |
| `music/unofficial/` | Background music tracks. Use only the track the user names. |
| `sfx/epidemic/` | Sound effects downloaded via the Epidemic Sound MCP. |
| `stickers/<subject>/` | Transparent PNG or SVG stickers (e.g. `bill-gates/`, `windows/`). |
| `icons/` | Icons, including `icons/animated/`. |
| `logos/<brand>/` | Brand logos. `logos/milanko.ai/logo.jpg` is the owner's channel logo, used in every CTA. |
| `backgrounds/static/<ratio>/`, `backgrounds/animated/<ratio>/` | Reusable backgrounds, grouped by aspect ratio (`9:16`, `16:9`). |
| `transitions/<ratio>/` | Ready-made transition clips. Use only when they match the style. |
| `animated-emojies/` | Short animated emoji clips (`.gif.mp4`). |
| `styles/<style-name>/DESIGN.md` + `preview.png` | A reusable style sheet — palette, type system, component examples — usable across formats. `preview.png` is a style sheet, not a frame from one video. Keep the folder to those two files. |
| ~~`voice/`, `transcripts/`~~ | Legacy. Per-video audio and Deepgram output now live in `projects/remotion/<project>/media/`. The folders still hold older projects; don't add new ones. |

## Environment and config

- `.venv/` - Python 3.12 virtualenv managed by `uv`. Install Python packages here, never globally. Run scripts with `.venv/bin/python`.
- `.env` (gitignored) - holds `DEEPGRAM_API_KEY`. Copy `.env.example` if missing.
- `.mcp.json` (gitignored) - MCP servers: `epidemic-sound` (sound effects only, not music), `fish-audio` (text-to-speech), `stealth` (anti-detect browser, runs from `.agents/mcp/stealth/` via `uv`). Copy `.mcp.json.example` on a fresh clone. Requires `uv` on `PATH`.

# Commands

Run every command from the repository root; use repo-relative or absolute paths.
A `cd` in one call never carries over to the next, and chained `cd ... && ...`
breaks `.venv`/asset-relative paths — anchor paths explicitly instead.

Storybook review server (runs on port 6006, no auto-open):
```bash
cd style-review && npm run storybook
cd style-review && npm run build-storybook   # static build to storybook-static/
```
Write the PID to `pids/storybook.pid` and keep the process alive while the user reviews. Share the exact URL the server prints.

Transcription with word timestamps (Deepgram nova-3, multilingual). Accepts video or audio, writes `assets/transcripts/<basename>/{transcript.txt,captions.json,deepgram.json,audio.wav}` — move the result into `projects/remotion/<project>/media/transcript/` afterwards:
```bash
.agents/skills/deepgram-transcribe/scripts/transcribe.sh assets/voice/<project>/voiceover.mp3
```

Background removal (isolated uv env, no project changes):
```bash
uv run --no-project --python 3.12 --with 'rembg[cpu,cli]' rembg i IN.png OUT.png
```

Icon search (UXWing):
```bash
.venv/bin/python .agents/skills/icons/scripts/find-icons.py "mouse cursor"
```

Remotion render and verification (run inside the Remotion project):
```bash
npx remotion render src/index.jsx <CompositionId> out/<name>.mp4 --codec=h264 --concurrency=6
ffprobe -v error -show_entries stream=width,height,r_frame_rate,codec_name -show_entries format=duration,size -of json out/<name>.mp4
```
Concurrency: start at 50–75% of logical cores; max threads can OOM Chromium.

Validate SVG assets: `xmllint --noout file.svg`. Audio duration: `ffprobe -i file.mp3`.

# Production pipeline (architecture)

The pipeline is gated by default: each stage needs explicit user approval before the next, and the final video is not rendered without permission. A workflow may define an autonomous mode that the user has switched on — then the gates are replaced by the machine acceptance criteria that workflow lists, and the agent takes the video all the way to a finished file. Currently on for `workflows/reference-driven-visual-explainer.md` (§3.1) and `workflows/presenter-screen-proof-listicle.md` (§3).

1. **Style / format spec** - a reusable style sheet lives in `assets/styles/<name>/`; a format spec tied to one workflow lives in `workflows/<workflow-name>/`. Scripts belong in `scripts/<area>/`, shared Remotion code in `projects/remotion/_shared/<name>/`. Created by the `extracting-design-styles` skill and approved via a `Styles/<name>/Reference` Storybook story. Look at `preview.png` first, read `DESIGN.md` for exact values.
2. **Script** - researched, written for speech, passed through `/humanizer-ru`, then approved. No visuals before this.
3. **Voice** - Fish Audio TTS, chunked by paragraph if needed, concatenated with ffmpeg, saved to `assets/voice/<project>/`. A TTS URL is not an asset; the file must be local.
4. **Timing** - the concatenated voiceover goes through Deepgram. `captions.json` (Remotion `Caption[]`: `text/startMs/endMs/timestampMs/confidence`) becomes the single timing source for subtitles, element entrances, and SFX.
5. **Assets** - inventory `assets/` first; generate images only when nothing local fits. Generated images/voices land in `temp/` and are deleted after being processed into `assets/`.
6. **Beatmap** - one typed array (`{id:'B01', startSec, endSec, voiceover, intent, component, props, reviewFrame}`) shared by both the video project and Storybook. IDs are permanent once review starts; never renumber.
7. **Agent visual QA (mandatory, before user review)** - includes the selected workflow's creative self-review (e.g. `continuous-ui-tech-explainer.md` §11), not only defect hunting. The agent must render and personally inspect the Overview and every individual beat at the actual composition aspect ratio. A successful build, valid JSX, reachable URL, or asset check is not visual verification. Capture screenshots and inspect the pixels for hierarchy, consistency, legibility, clipping, overlap, safe zones, dead space, caption placement, presenter placement, sticker usefulness, and whether the mechanism is understandable without narration. For materially animated beats, inspect representative start, middle, and end frames or play the preview. Fix defects and repeat the visual inspection until the agent would confidently present the result as finished work. Never delegate first-pass QA to the user.
8. **Storybook user review** - only after agent visual QA passes, share stories under `Video/<video-name>/Beatmap/{Overview, Screens/B01 - ...}` that render the real production components at composition size, frozen at `reviewFrame`. Storybook is a review surface for creative judgment—not a testing surface. The user should decide whether the design and explanation are effective, not discover broken rendering, clipping, inconsistent sizing, unreadable labels, or obvious implementation defects. Feedback arrives as `B03 — ...` lines.
9. **Render** - only after approval. Verify output with ffprobe (dimensions, fps, duration, h264 + aac) and place it under `videos/<timestamp-short-description>/`.

Cross-cutting rules from `workflows/`:
- Remotion animation uses `useCurrentFrame`/`interpolate`/`spring` only; no CSS transitions/keyframes, no unseeded randomness. Assets via `staticFile()`, audio via `<Audio>`.
- Subtitles: show a whole semantic phrase at once, never re-flow lines per word, never advance before the last word's `endMs`. Phrase length and active-word treatment are set by the workflow in use: 4–9 words for the pixel-silver and grid-UI explainers; 2–4 with the active word recolored on a plate for the reference-driven visual explainer; 2–4 with no active-word highlight and no plate for the presenter screen-proof listicle; **no subtitles at all** for the continuous UI tech explainer (1–5 meaning words per moment instead).
- Reels safe zone on 1080×1920: ~150–190 px right, ~250–320 px bottom, ~100–150 px top. These are **exclusion zones** (no meaning inside them), not a layout box: compositions stay centred on x = 540 with symmetric margins. The full-width progress bar at `bottom: 0` is the deliberate exception for formats that define one and moves on global composition time.
- Voice leads the edit: cut voice only at word boundaries from Deepgram timestamps, keep 0.25–0.4 s between phrases, derive scene length from speech, and key every visual event to its trigger word (0.1–0.15 s before it, never more than 1 s early). Never cut or stretch speech to fit a scene.
- On-screen text and TTS text are separate: the screen shows `AI`, `IT` and product names as written; the TTS text carries the pronunciation («эй-ай», «шад-си-эн»).
- Music: use the user-specified local track only, ~0.06–0.14 gain under speech with fades. Epidemic Sound is for SFX only, and every SFX must map to a visible on-screen event.
- Don't apply ready-made `assets/transitions` unless they match the style; build transitions inside the composition.

# Current state and gotchas

- `style-review/.storybook/main.js` serves `../../assets` at `/assets` and the active HyperFrames project at `/composition`. The old `windows-history-hf` directory no longer exists; if `WindowsReel` stories iframe `/composition/index.html?review=<sec>` and 404, repoint `staticDirs` at the project under `projects/hyperframes/`. `projects/remotion` and `projects/hyperframes` hold the live video projects plus their `node_modules`.
- Skills live in `.agents/skills/`. If a SKILL.md (e.g. `icons`, `remove-image-background`, `clip.cafe`) still references an old skills location such as `.claude/skills/...`, substitute `.agents/skills/...`.
- Reference material for a workflow lives in the repo beside that workflow (e.g. `workflows/continuous-ui-tech-explainer/reference/`), never in `/tmp`, which does not survive restarts.
- The Storybook `preview.js` sorts stories `Styles` → `Pixel Silver Desktop` → `Reference`, with backgrounds addon disabled and fullscreen layout, so stories must paint their own background.
- `test.py` at the root is a throwaway scraper, gitignored; ignore it.
- Existing project data: `assets/transcripts/windows-history` and `assets/voice/windows-history` belong to the Windows-history Reel described in `workflows/vertical-historical-reels-pixel-silver.md`; `style-review/src/windows-beatmap.js` is its beatmap.
