# Как установить в проект агента

Скопировать с заменой, сохраняя пути. Копировать **файлы целиком** (не вставлять текст через
чат): прошлая версия workflow в проекте оказалась обрезанной — начиналась с §7, и агент
работал без инвариантов, хука и каталога механик.

| Файл здесь | Куда в проекте агента |
|---|---|
| `AGENTS.md` | `AGENTS.md` (корень) |
| `workflows/continuous-ui-tech-explainer.md` | `workflows/continuous-ui-tech-explainer.md` |
| `workflows/_shared/production-qa.md` | `workflows/_shared/production-qa.md` |
| `workflows/continuous-ui-tech-explainer/reference/` | `workflows/continuous-ui-tech-explainer/reference/` |

Проверка после копирования: `continuous-ui-tech-explainer.md` начинается со строки
`# Workflow: Continuous UI Tech Explainer` и заканчивается разделом `## 13. Переиспользование`;
`production-qa.md` содержит части A, B и C.

После копирования попросить агента:

```
Прочитай заново AGENTS.md, workflows/_shared/production-qa.md (целиком, особенно часть A
U01–U16) и workflows/continuous-ui-tech-explainer.md (§0–§13). Затем:
1. Сверь с ними .agents/skills/continuous-ui-tech-explainer/SKILL.md: убери всё, что
   противоречит (кегли меньше U03, обязательные панели/чипы, ссылки на несуществующие
   разделы, длительности в кадрах без fps).
2. Сверь assets/styles/continuous-ui-tech/DESIGN.md с U03/U05/U06: главный текст 88–120 px
   (а не 76), пояснение 44–48, UI ≥28; центр композиции x=540 (зона x=70–890 — не рамка
   центрирования, а только граница, правее которой нет смысла); панели и чипы не обязательны;
   один акцент на активном элементе. Исправь DESIGN.md и покажи diff.
3. Применяй top-ranking и любые другие workflow тоже с частью A production-qa.
4. В каждом новом проекте создавай media/spec.md и media/change-log.md.
```
