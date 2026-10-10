# Как установить в проект агента

Скопировать с заменой, сохраняя пути. Копировать **файлы целиком** (не вставлять текст через
чат): прошлая версия workflow в проекте оказалась обрезанной — начиналась с §7, и агент
работал без инвариантов, хука и каталога механик.

| Файл здесь | Куда в проекте агента |
|---|---|
| `AGENTS.md` | `AGENTS.md` (корень) |
| `workflows/_shared/production-qa.md` | `workflows/_shared/production-qa.md` |
| `workflows/continuous-ui-tech-explainer.md` | `workflows/continuous-ui-tech-explainer.md` |
| `workflows/continuous-ui-tech-explainer/reference/` | `workflows/continuous-ui-tech-explainer/reference/` |
| `workflows/quran-data-essay.md` + папка `workflows/quran-data-essay/` (SKILL.md, scripts/, decisions.md, reference/) | те же пути |
| `skills/workflow-builder/` (папка целиком) | `.agents/skills/workflow-builder/` |
| `scripts/qa/layout-lint.js` | `scripts/qa/layout-lint.js` |

**Раскладка.** Всё, что относится к одному workflow (его скилл, скрипты, решения, референс),
лежит в `workflows/<name>/`. В `.agents/skills/` и `scripts/` — только универсальное, чем
пользуются несколько форматов. Подробно — `AGENTS.md`, раздел «Workflow selection and reuse».

Данные для `quran-data-essay` в репозиторий не кладутся — скачать в `assets/data/quran/`:
```bash
curl -L -o assets/data/quran/quran-morphology.txt \
  https://raw.githubusercontent.com/mustafa0x/quran-morphology/master/quran-morphology.txt
sha256sum assets/data/quran/quran-morphology.txt   # 742bfac59941b2cb09736d5b7aae694af50792261fb8450cbf6afafcc340645f
.venv/bin/python workflows/quran-data-essay/scripts/count.py --data assets/data/quran/quran-morphology.txt selftest
```
Остальные файлы (Tanzil Uthmani, Yusuf Ali, метаданные) — по списку в
`workflows/quran-data-essay/SKILL.md`, с записью в `assets/data/quran/SOURCES.md`.

Скилл `workflow-builder` требует скилл `grilling` в `.agents/skills/grilling/` (если он
установлен как `grill-me` — переименовать папку или поправить имя в
`workflow-builder/SKILL.md`, этап 3). После копирования выполнить `scripts/link-skills.sh`,
чтобы скилл появился у Codex (скиллы из `workflows/<name>/` туда не линкуются — так и задумано).

Проверка после копирования: `continuous-ui-tech-explainer.md` начинается со строки
`# Workflow: Continuous UI Tech Explainer` и заканчивается разделом `## 13. Переиспользование`;
`production-qa.md` содержит части A, B и C.

После копирования попросить агента:

```
Прочитай заново AGENTS.md, workflows/_shared/production-qa.md (целиком, особенно часть A
U01–U16) и workflows/continuous-ui-tech-explainer.md (§0–§13). Затем:
1. Сверь с ними workflows/continuous-ui-tech-explainer/SKILL.md (после переноса, см. ниже): убери всё, что
   противоречит (кегли меньше U03, обязательные панели/чипы, ссылки на несуществующие
   разделы, длительности в кадрах без fps).
2. Сверь assets/styles/continuous-ui-tech/DESIGN.md с U03/U05/U06: главный текст 88–120 px
   (а не 76), пояснение 44–48, UI ≥28; центр композиции x=540 (зона x=70–890 — не рамка
   центрирования, а только граница, правее которой нет смысла); панели и чипы не обязательны;
   один акцент на активном элементе. Исправь DESIGN.md и покажи diff.
3. Применяй top-ranking и любые другие workflow тоже с частью A production-qa.
4. В каждом новом проекте создавай media/spec.md и media/change-log.md.
```

## Перенос существующих скиллов форматов из `.agents/skills/`

В проекте агента скиллы отдельных форматов сейчас лежат в `.agents/skills/` рядом с
универсальными. Попросить агента:

```
Наведи порядок в скиллах по правилу из AGENTS.md («Everything that belongs to one workflow
lives in that workflow's folder»):
1. Составь таблицу всех папок .agents/skills/: скилл → какие workflow на него ссылаются →
   универсальный (используется ≥2 workflow или вне workflow) / формата (ровно один workflow).
   Покажи таблицу до переноса.
2. Скиллы формата перенеси через git mv: .agents/skills/<name>/SKILL.md →
   workflows/<workflow>/SKILL.md, их scripts/ и прочие файлы → workflows/<workflow>/scripts/
   (и т.п.). Точно туда: continuous-ui-tech-explainer, top-ranking и другие companion-скиллы.
   Скрипты в scripts/<area>/, которые нужны только одному формату, — туда же.
3. Обнови все ссылки (workflow, AGENTS.md, другие скиллы, код проектов) — grep по старым
   путям должен быть пуст.
4. Запусти scripts/link-skills.sh, проверь, что у Codex остались только универсальные скиллы.
5. Сомнительные случаи не переноси — спроси меня.
```
