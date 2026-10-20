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

## Второе задание: невидимый водяной знак (SynthID check)

`camerafy.py` обманывает классификатор «AI vs камера», но **не снимает водяной знак**
(SynthID / сигнал OpenAI): он вшит глубоко в пиксели и переживает JPEG, шум и ресайз.
Поэтому sample (= наша `light`-версия) всё ещё даёт ~99% на SynthID check.

Если не хочется качать тяжёлую модель — есть два варианта полегче, пробуй по порядку.

**Вариант A — без скачивания моделей вообще (пресет `scrub`).**
Делает сильный локальный «warp» (плавно сдвигает пиксели на пару пикселей) плюс
усиленную спектральную/сенсорную обработку. Многие пространственные водяные знаки
детектятся по точному выравниванию пикселей, и такой сдвиг их рассинхронизирует.
Лицо и композиция сохраняются.
```bash
python3 camerafy.py samples/sample_synthid.png out/scrub.jpg --preset scrub
```
Это сразу и первый детектор держит низким. Если знак уцелел — вариант B.

**Вариант B — лёгкая модель VAE (~320 МБ вместо 7 ГБ).**
Прогоняет картинку через автоэнкодер (кодирует и декодирует), пиксели пересобираются
заново и хрупкий знак стирается. Нужен torch, но модель маленькая.
```bash
pip install -r requirements-regen.txt
python3 regen.py samples/sample_synthid.png out/vae.png --vae-only
python3 camerafy.py out/vae.png out/final.jpg          # добить первый детектор
```

**Вариант C — полноценная диффузия (ниже), если A и B не сняли знак.**

Самая надёжная атака — **регенерация через диффузию**: open-source модель заново перерисовывает
мелкую структуру пикселей (img2img с малой силой), лицо и композиция сохраняются,
а точные пиксели со знаком исчезают. Скрипт — `regen.py`, работает на Apple Silicon (MPS).

### Установка (на Mac M1 Pro)
```bash
cd ai-detect-redteam
source .venv/bin/activate
pip install -r requirements-regen.txt     # torch + diffusers, модель SDXL-Turbo ~7 ГБ скачается при первом запуске
```

### Снятие знака
```bash
# 1) перерисовать (убирает водяной знак)
python3 regen.py samples/sample_synthid.png out/regen.png --strength 0.4

# 2) прогнать через камеру, чтобы и первый детектор остался ~0%
python3 camerafy.py out/regen.png out/final.jpg
```

Залей `out/final.jpg` в hivedetect.ai и проверь оба детектора.

### Подбор силы
Сила `--strength` — главный параметр: меньше = ближе к оригиналу, но знак может уцелеть;
больше = знак точно уходит, но лицо «плывёт». Найди минимальную, при которой SynthID = 0%:
```bash
python3 regen.py samples/sample_synthid.png out/ --sweep    # 0.25 / 0.35 / 0.45 / 0.55
```
Если при 0.4 знак ещё держится — подними силу или возьми более сильную модель:
```bash
python3 regen.py in.png out.png --model stabilityai/stable-diffusion-xl-base-1.0 --strength 0.35
```

Папка целиком — так же: `python3 regen.py photos/ photos_out/ --strength 0.4`.

> Проверено, что `regen.py` корректно компилируется, но **прогнать диффузию в облачной
> сессии я не мог** (нет GPU/torch) — финальные скоры SynthID измеряй у себя на Mac
> и, если надо, пришли мне, подкрутим силу.

## Как подбирать
1. Загрузить `out/*.jpg` в hivedetect.ai, записать скор для каждого пресета.
2. Взять самый слабый пресет, который даёт ~0%, и при необходимости поиграть
   параметрами в `PRESETS` (больше всего обычно влияют `scale`, `iso`, `bayer`, `fft`).
3. Если пиксельной обработки не хватает — следующий шаг: img2img через
   open-source диффузионку (SD/Flux) с denoise 0.1–0.25, затем снова `camerafy.py`;
   либо физический ре-кэпчур (снять экран/распечатку на телефон).

Используйте оригинал из генератора (PNG), а не пережатую копию из мессенджера.
