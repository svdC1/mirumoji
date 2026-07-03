# Third-Party Notices

Mirumoji is licensed under the [`MIT License`](https://github.com/svdC1/mirumoji/blob/main/LICENSE)

This page acknowledges the third-party software and data Mirumoji depends on
and redistributes

???+ abstract "License Locations"
    - The full license text for every bundled dependency can be found `inside the distributed artifacts`

    - In the `Backend Docker Images`, they ship inside each `Python` package's metadata (`*.dist-info/`) and system package docs (`/usr/share/doc/...`)

    - In The `Frontend Docker Image`, they ship inside each `npm` package and system package docs (`usr/share/doc/...`)

    - The notices below cover the components whose licenses require explicit attribution

## Required Attributions

### JMdict / JMnedict / KANJIDIC2 / KRADFILE &rarr; Dictionary Data

- Mirumoji's dictionary lookups use data derived from the `JMdict`,
`JMnedict`, `KANJIDIC2`, and `KRADFILE / RADKFILE` files, the property of the
[`Electronic Dictionary Research and Development Group (EDRDG)`](https://www.edrdg.org/),
used in conformance with the group's
[`Licence`](https://www.edrdg.org/edrdg/licence.html)

- These files are made available under the `Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0)` Licence

- This data is accessed via [`kotobase`](https://github.com/svdC1/kotobase), which also includes a similar notice

### KanjiVG &rarr; Kanji Stroke-Order Diagrams

- The kanji stroke-order drawings are rendered from
[`KanjiVG`](https://kanjivg.tagaini.net/) data, copyright `Ulrich Apel`,
released under the
[`Creative Commons Attribution-ShareAlike 3.0`](https://creativecommons.org/licenses/by-sa/3.0/)
licence

- This data is accessed via [`kotobase`](https://github.com/svdC1/kotobase), which also includes a similar notice

### Tatoeba &rarr; Example Sentences

- Example sentences and their translations come from the
[`Tatoeba Project`](https://tatoeba.org/), released under the
[`Creative Commons Attribution 2.0 FR`](https://creativecommons.org/licenses/by/2.0/fr/)
licence

- This data is accessed via [`kotobase`](https://github.com/svdC1/kotobase), which also includes a similar notice

### Kanji Alive &rarr; Pronunciation Audio

- Kanji pronunciation clips come from the
[`Kanji Alive`](https://kanjialive.com/) project of the University of Chicago,
released under the
[`Creative Commons Attribution 4.0`](https://creativecommons.org/licenses/by/4.0/)
licence

- This data is accessed via [`kotobase`](https://github.com/svdC1/kotobase), which also includes a similar notice

### JmdictFurigana &rarr; Furigana Segmentation

- The per-kanji furigana segmentation comes from the
[`JmdictFurigana`](https://github.com/Doublevil/JmdictFurigana) project,
released under the `MIT` licence

- The underlying dictionary data falls under the `EDRDG` licence above

- This data is accessed via [`kotobase`](https://github.com/svdC1/kotobase), which also includes a similar notice

### UniDic &rarr; Morphological Analysis Dictionary

- Japanese tokenization on the server uses [`fugashi`](https://github.com/polm/fugashi) with `UniDic`

- `UniDic` is distributed under a `BSD-3-Clause` licence by the `National Institute for Japanese Language and Linguistics (NINJAL)`

- Attribution to `NINJAL` is preserved

### NVIDIA CUDA &rarr; Base GPU Docker Image

- The GPU server image is built on the `nvidia/cuda` base image

- Redistribution and use of that image are governed by the [`NVIDIA Deep Learning Container License`](https://developer.nvidia.com/ngc/nvidia-deep-learning-container-license)

- This applies only to the GPU image variant

### FFmpeg &rarr; Bundled Static Build (GPU / Modal Images)

- The `GPU` and `Modal` server images bundle a static `FFmpeg` build from [`BtbN/FFmpeg-Builds`](https://github.com/BtbN/FFmpeg-Builds), configured as `GPL` so it includes the `NVENC` / `NVDEC` encoders and the `scale_cuda` filter used for hardware-accelerated video conversion

- This build is redistributed under the [`GNU GPL v3`](https://www.gnu.org/licenses/gpl-3.0.html). The corresponding source is available from [`ffmpeg.org`](https://ffmpeg.org/download.html) and the build configuration from the `BtbN/FFmpeg-Builds` repository

- The `CPU` image variants keep the distribution's `LGPL` `FFmpeg` installed via `apt`

## Notable Components

| Component | Role | License |
| --- | --- | --- |
| [`CTranslate2`](https://github.com/OpenNMT/CTranslate2) | Whisper Inference Engine | `MIT` |
| [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) | Transcription | `MIT` |
| [`kotobase`](https://github.com/svdC1/kotobase) | Japanese Dictionary Database | `MIT`|
| [`FFmpeg`](https://ffmpeg.org/) | Media Conversion | `LGPL / GPL` |
| [`MeCab`](https://taku910.github.io/mecab/) | Morphological Analyzer (Used By Fugashi) | `BSD-3-Clause` |
| [`FastAPI`](https://github.com/tiangolo/fastapi) | Python Server Framework | `MIT` |
| [`Flet`](https://github.com/flet-dev/flet) | Desktop GUI | `Apache-2.0` |
| [`React`](https://github.com/facebook/react) | Frontend Framework | `MIT` |
| [`Nginx`](https://nginx.org/) | Frontend Image Web Server | `BSD-2-Clause` |
| [`Node.js`](https://nodejs.org/) | Frontend Build / Runtime | `MIT (and others)` |

This list is not exhaustive

See each project's repository and the bundled metadata for complete terms
