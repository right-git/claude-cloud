# Как установить в проект агента

Скопировать с заменой, сохраняя пути:

| Файл здесь | Куда в проекте агента |
|---|---|
| `AGENTS.md` | `AGENTS.md` (корень) |
| `workflows/continuous-ui-tech-explainer.md` | `workflows/continuous-ui-tech-explainer.md` |
| `workflows/_shared/production-qa.md` | `workflows/_shared/production-qa.md` |
| `workflows/continuous-ui-tech-explainer/reference/` | `workflows/continuous-ui-tech-explainer/reference/` (новая папка) |

После копирования попросить агента:
1. Прочитать новые версии трёх файлов.
2. Сверить с ними companion skill `.agents/skills/continuous-ui-tech-explainer/SKILL.md`
   и убрать из него всё, что противоречит (особенно длительности в кадрах без fps).
3. Создать `media/change-log.md` в текущем проекте.
