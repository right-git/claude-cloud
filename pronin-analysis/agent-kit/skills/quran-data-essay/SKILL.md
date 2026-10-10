---
name: quran-data-essay
description: Компоненты, скрипты фактов и проверки для роликов формата Quran Data Essay (workflow `workflows/quran-data-essay.md`) — вертикальные эссе о тексте Корана на данных: подсчёты слов, порядок откровения, структура сур. Use when producing or revising a video under the quran-data-essay workflow, or when counting words/lemmas/roots in the Quran for a video.
---

# Quran Data Essay — companion skill

Политика (факты §F, инварианты, этапы) — в `workflows/quran-data-essay.md`. Здесь только
реализация. При конфликте прав workflow.

## Данные (§F1)

`assets/data/quran/`:
| Файл | Источник | Статус |
|---|---|---|
| `quran-morphology.txt` | github.com/mustafa0x/quran-morphology (форк QAC v0.4) | sha256 `742bfac59941b2cb09736d5b7aae694af50792261fb8450cbf6afafcc340645f`, selftest ok |
| `quranic-corpus-morphology-0.4.txt` | corpus.quran.com/download (оригинал, GNU GPL) | загрузить, если доступен; предпочтительнее форка |
| `quran-uthmani.txt` | tanzil.net/download (Uthmani, хафс) | загрузить; лицензию записать в `SOURCES.md` |
| `en.yusufali.txt` | tanzil.net/trans (Yusuf Ali) | загрузить; проверить, что это редакция 1934, лицензию записать |
| `quran-data.xml` | tanzil.net (метаданные сур: аяты, тип, порядок откровения) | загрузить |
Каждый файл — запись в `SOURCES.md` (URL, дата, версия, лицензия, sha256).

## Скрипты фактов

- Подсчёт: `.venv/bin/python scripts/quran/count.py --data assets/data/quran/quran-morphology.txt <cmd>`
  - `selftest` — запускать перед каждым подсчётом; все строки `ok`.
  - `verses`, `words`.
  - `match --lemma L [--root R] [--pos N|V|P] [--feat X ...] [--not-feat X ...] --name NAME
    --csv media/counts/NAME.csv --json media/counts/NAME.json`.
  - `--feat` — AND; род/число по компонентам (`F`, `MS`, `2MS`, `3MP`), точные теги (`IMPV`,
    `PERF`, `PASS`, `ADJ`).
  - Единица — слово (`сура:аят:слово`); в JSON также число стихов с вхождениями.
- Сборка `media/facts.json`: объединить JSON подсчётов + метаданные (даты оси, номера стихов
  для карточек). Композиция читает числа только отсюда.
- `scripts/quran/quote.py` (создать при первом ролике): `quote.py S:A --lang ar|en` → текст
  из закреплённого файла; `quote.py --check media/scene-plan.md` → побайтовая сверка всех
  цитат. После проверки на пилоте — закрепить в `scripts/quran/`.
- `scripts/quran/verify_facts.py` (создать при первом ролике): перечитывает `methods.md`,
  пересчитывает, сравнивает с `facts.json`; второй способ подсчёта — поиск поверхностных
  форм из CSV в `quran-uthmani.txt` (нормализовать диакритику одинаково); печатает таблицу
  расхождений; код возврата ≠ 0 при любом расхождении.

## Компоненты HyperFrames

| Компонент | Механика | Параметры |
|---|---|---|
| `Background` | I1 | глобальный слой, время ролика |
| `VerseGrid` | P1, P2, P9 | `units` (6236 или N), `cols` 79, `lit` (индексы из CSV), `accent` |
| `Counter` | P2, P3 | `valueFrom` = длина `lit` в текущий кадр (не отдельная анимация) |
| `Compare` | P3 | две `VerseGrid`-подсветки, «=», волна только при равенстве |
| `VerseCard` | P4 | `key` (S:A), `highlight` (индексы слов ar + en), текст из `quote.py` |
| `Timeline` | P5 | `start` 610, `end` 632, `order` (из метаданных), `hijra` 622 |
| `Reorder` | P6 | `from`/`to` порядок, seed |
| `RingBars` | P7 | секции из источника (`sources.md`), пары |
| `CountRow` | P8 | `n`, подпись |
| `EndCard` | P10 | логотип канала, строка методики из `methods.md` |

Разметка для линтера: `data-box`, `data-pad`, `data-overlay` (см. `scripts/qa/layout-lint.js`,
поля 72/1008: `window.__layoutLint({left:72,right:1008})`).
Частицы — фиксированный seed на сцену.

## Что прислать с каждым показом

`media/fact-sheet.md` (все строки `verified`), вывод `selftest` и `verify_facts.py`, кадры
покоя каждой сцены с сеткой I4, вывод линтера, таблица времени чтения §8, MP4.
