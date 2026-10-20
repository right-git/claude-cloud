# ai-detect-redteam

Red-team тест детектора AI-изображений (хакатон hivedetect.ai).

## Почему удаление C2PA не помогает
На скриншоте Hive: «No Content Credentials found» и всё равно 99.2% `gptimage2`.
Значит, детектор смотрит **на пиксели**: классификатор ищет отпечаток генератора
(периодические артефакты апсемплинга в ВЧ-спектре, слишком «чистый» шум,
отсутствие следов камеры). Репозитории вроде C2PAremover / c2pastrip чистят только
метаданные, поэтому скор не меняют.

## Что делает `camerafy.py`
Прогоняет картинку через симуляцию камеры, чтобы заменить статистику генератора
на статистику реального сенсора:

1. сброс всех метаданных (C2PA/EXIF/XMP/ICC)
2. поворот на доли градуса + кроп со сдвигом + ресемплинг (ломает сетку апсемплинга)
3. подавление периодических пиков в ВЧ-спектре FFT
4. оптика: хроматическая аберрация, лёгкий блюр, виньетка
5. Bayer RGGB мозаика → шум сенсора (Poisson-Gaussian + PRNU) → демозаикинг
6. ISP: тон-кривая, unsharp mask, JPEG 4:2:0

Пресет по умолчанию — `light` (на шаблоне: 99.2% → **0.3%** в hivedetect.ai).
Остальные: `medium` → `strong` → `heavy` (сильнее обработка, ниже качество).

## Установка

Нужен Python 3.9+.

```bash
git clone https://github.com/right-git/claude-cloud.git
cd claude-cloud
git checkout claude/peaceful-cori-mbh8lr
cd ai-detect-redteam

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Конвертация

Одно фото:
```bash
python3 camerafy.py photo.png photo_out.jpg
```

Вся папка (jpg/jpeg/png/webp/bmp/tif) → в другую папку, имена сохраняются, на выходе `.jpg`:
```bash
python3 camerafy.py photos/ photos_out/
python3 camerafy.py photos/ photos_out/ -r          # вместе с подпапками
```

Другие опции:
```bash
python3 camerafy.py photos/ out/ --preset medium     # другой пресет
python3 camerafy.py photos/ out/ --sweep             # все 4 пресета: name_light.jpg, name_medium.jpg, ...
python3 camerafy.py photo.png out.jpg --seed 1       # воспроизводимый результат (шаблон делали с --seed 1)
python3 camerafy.py photo.png out.jpg --passes 2     # прогнать пайплайн дважды
```

Битые/нечитаемые файлы в папке пропускаются с пометкой `[fail]`, остальные обрабатываются.
Шум случайный: если какое-то фото получило высокий скор, перезапусти с другим `--seed`
или возьми `--preset medium`.

## Как подбирать
1. Загрузить `out/*.jpg` в hivedetect.ai, записать скор для каждого пресета.
2. Взять самый слабый пресет, который даёт ~0%, и при необходимости поиграть
   параметрами в `PRESETS` (больше всего обычно влияют `scale`, `iso`, `bayer`, `fft`).
3. Если пиксельной обработки не хватает — следующий шаг: img2img через
   open-source диффузионку (SD/Flux) с denoise 0.1–0.25, затем снова `camerafy.py`;
   либо физический ре-кэпчур (снять экран/распечатку на телефон).

Используйте оригинал из генератора (PNG), а не пережатую копию из мессенджера.
