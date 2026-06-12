# Third-Party Notices

Mirumoji is licensed under the [`MIT License`](https://github.com/svdC1/mirumoji/blob/main/.github/LICENSE)

This page acknowledges the third-party software and data Mirumoji depends on
and redistributes

???+ abstract "License Locations"
    - The full license text for every bundled dependency can be found `inside the distributed artifacts`
    
    - In the `Backend Docker Images`, they ship inside each `Python` package's metadata (`*.dist-info/`) and system package docs (`/usr/share/doc/...`)
    
    - In The `Frontend Docker Image`, they ship inside each `npm` package and system package docs (`usr/share/doc/...`)
    
    - The notices below cover the components whose licenses require explicit attribution

## Required Attributions

### JMdict / JMnedict &rarr; Dictionary Data

- Mirumoji's dictionary lookups use data derived from the `JMdict` and
`JMnedict` dictionary files, the property of the
[`Electronic Dictionary Research and Development Group (EDRDG)`](https://www.edrdg.org/),
used in conformance with the group's
[`Licence`](https://www.edrdg.org/edrdg/licence.html)

- These files are made available under the `Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0)` Licence

- This data is accessed via [`kotobase`](https://github.com/svdC1/kotobase), which also includes a similar notice

### UniDic &rarr; Morphological Analysis Dictionary

- Japanese tokenization on the server uses [`fugashi`](https://github.com/polm/fugashi) with `UniDic`

- `UniDic` is distributed under a `BSD-3-Clause` licence by the `National Institute for Japanese Language and Linguistics (NINJAL)`

- Attribution to `NINJAL` is preserved

### NVIDIA CUDA &rarr; Base GPU Docker Image

- The GPU server image is built on the `nvidia/cuda` base image

- Redistribution and use of that image are governed by the [`NVIDIA Deep Learning Container License`](https://developer.nvidia.com/ngc/nvidia-deep-learning-container-license)

- This applies only to the GPU image variant

## Notable Components

| Component | Role | License |
| --- | --- | --- |
| [`PyTorch`](https://github.com/pytorch/pytorch) | ML Runtime (Whisper) | `BSD-3-Clause` |
| [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) | Transcription | `MIT` |
| [`FFmpeg`](https://ffmpeg.org/) | Media Conversion | `LGPL / GPL` |
| [`MeCab`](https://taku910.github.io/mecab/) | Morphological Analyzer (Used By Fugashi) | `BSD-3-Clause` |
| [`FastAPI`](https://github.com/tiangolo/fastapi) | Python Server Framework | `MIT` |
| [`Flet`](https://github.com/flet-dev/flet) | Desktop GUI | `Apache-2.0` |
| [`React`](https://github.com/facebook/react) | Frontend Framework | `MIT` |
| [`Nginx`](https://nginx.org/) | Frontend Image Web Server | `BSD-2-Clause` |
| [`Node.js`](https://nodejs.org/) | Frontend Build / Runtime | `MIT (and others)` |

This list is not exhaustive

See each project's repository and the bundled metadata for complete terms
