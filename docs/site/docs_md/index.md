![GitHub Release](https://img.shields.io/github/v/release/svdC1/mirumoji?display_name=release&style=for-the-badge&logoSize=auto&label=Version)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/svdC1/mirumoji/total?style=for-the-badge&logoSize=auto&label=GitHub%20Downloads&link=https%3A%2F%2Fgithub.com%2FsvdC1%2Fmirumoji%2Freleases)
![Docker Pulls](https://img.shields.io/docker/pulls/svdc1/mirumoji?style=for-the-badge&logoSize=auto&link=https%3A%2F%2Fhub.docker.com%2Frepository%2Fdocker%2Fsvdc1%2Fmirumoji%2F)

---

# Overview

Mirumoji is an open-source, self-hosted Japanese immersion toolkit. Drop in any video, anime episode, drama or audio clip and it gives you: clickable tokenized subtitles with dictionary pop-ups, Whisper-powered transcription, instant SRT/clip extraction, and one-click Anki deck export — all in Docker, all running on your own machine.

??? tip "Optional Integrations"

    -   [`OpenAI`](https://platform.openai.com/docs/overview) Integration: Customizable GPT Breakdowns of Subtitles
    -   [`Modal`](https://modal.com) Integration: Install a CPU only version and run all GPU tasks on the cloud

---

??? info "Preview"

    > View a [`Preview`](https://svdc1.github.io/mirumoji) of the frontend _(No backend running)_

??? Documentation

    > Access full [`Documentantion`](https://svdc1.github.io/mirumoji/docs)

# Features

=== "**Interactive Video Player**"

    <figure markdown="span">
    ![player](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/player.png?raw=true)
    <figcaption>Upload your local anime/J-Drama espisodes or any Japanese video and `.SRT` subtitles.</figcaption>
    </figure>


=== "**Clickable Japanese Subtitles**"

    <figure markdown="span">
    ![word_dialog](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/word_dialog.png?raw=true)
    <figcaption>Subtitles are tokenized ([`kuromoji.js`](https://github.com/takuyaa/kuromoji.js)), allowing you to click individual words for information</figcaption>
    </figure>

=== "**Dictionary**"

    <figure markdown="span">
    ![dictionary](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/dictionary.png?raw=true)
    <figcaption>Dictionary ([`kotobase`](https://github.com/svdC1/kotobase)) page allowing wildcard searches.</figcaption>
    </figure>

=== "**Text Analyzer**"

    <figure markdown="span">
    ![text_analyzer](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/text_analyzer.png?raw=true)
    <figcaption>Copy and paste text for tokenized output with furigana and clickable words.</figcaption>
    </figure>

=== "**OpenAI Integration**"

    <figure markdown="span">
    ![gpt_template](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/gpt_template.png?raw=true)
    <figcaption>Modify System Message and User Prompt with `{sentence}` and `{word}` variables.</figcaption>
    </figure>

=== "**Local Media Processing**"

    ???+ info "**Video Conversion**"
        Upload videos in various formats; they can be converted to MP4 for optimal playback.

    ???+ info "**SRT Generation**"
        Generate subtitles for your videos. Runs [`FasterWhisper`](https://github.com/SYSTRAN/faster-whisper) with modified parameters to increase accuracy for longer media such as Anime/ J-Drama episodes.

=== "**Audio Transcription**"

    <figure markdown="span">
    ![transcription](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/transcription.png?raw=true)
    <figcaption>Transcribe Japanese audio from recordings or uploaded files.</figcaption>
    </figure>

=== "**Profile-Based Data Management**"

    ??? info "**Persistent Storage**"

        <figure markdown="span">
        ![profile](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/profile.png?raw=true)
        <figcaption>Profile configurations and all other profile-related data is stored and managed via SQLite database by the backend.</figcaption>
        </figure>

    ??? info "**Clip Saving**"

        <figure markdown="span">
        ![clips](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/clips.png?raw=true)
        <figcaption>Save important video segments with their associated word breakdowns and export as an Anki Deck</figcaption>
        </figure>
---

# Setup

???+ info "Docker Images"
    Both the [`frontend`](https://github.com/svdC1/mirumoji/tree/main/apps/frontend) and [`backend`](https://github.com/svdC1/mirumoji/tree/main/apps/backend) have pre-built [`Docker`](https://hub.docker.com/repository/docker/svdc1/mirumoji/general) images and are set up to work with Docker Compose.

???+ tip 
    The easiest setup is to run the [`GUI Launcher`](Launcher-GUI-Guide.md) for your platform.
    **For detailed instructions please refer to the [`Setup Guide`](Setup-Guide.md)**


---

# Image Sizes

???+ info "Compressed Image Sizes"
    ![Docker Image Size (tag)](https://img.shields.io/docker/image-size/svdc1/mirumoji/backend-gpu-latest?style=for-the-badge&&logoSize=auto&label=GPU%20Backend%20Image&link=https%3A%2F%2Fhub.docker.com%2Frepository%2Fdocker%2Fsvdc1%2Fmirumoji%2Ftags%2Fbackend-gpu-latest%2F)
    ![Docker Image Size (tag)](https://img.shields.io/docker/image-size/svdc1/mirumoji/backend-cpu-latest?style=for-the-badge&logoSize=auto&label=CPU%20Backend%20Image&link=https%3A%2F%2Fhub.docker.com%2Frepository%2Fdocker%2Fsvdc1%2Fmirumoji%2Ftags%2Fbackend-cpu-latest%2F)
    ![Docker Image Size (tag)](https://img.shields.io/docker/image-size/svdc1/mirumoji/frontend-latest?style=for-the-badge&logoSize=auto&label=Frontend%20Image&link=https%3A%2F%2Fhub.docker.com%2Frepository%2Fdocker%2Fsvdc1%2Fmirumoji%2Ftags%2Ffrontend-latest%2F)
