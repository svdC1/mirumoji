![GitHub Release](https://img.shields.io/github/v/release/svdC1/mirumoji?display_name=release&style=for-the-badge&logoSize=auto&label=Version)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/svdC1/mirumoji/total?style=for-the-badge&logoSize=auto&label=GitHub%20Downloads&link=https%3A%2F%2Fgithub.com%2FsvdC1%2Fmirumoji%2Freleases)
![Docker Pulls](https://img.shields.io/docker/pulls/svdc1/mirumoji?style=for-the-badge&logoSize=auto&link=https%3A%2F%2Fhub.docker.com%2Frepository%2Fdocker%2Fsvdc1%2Fmirumoji%2F)

---

# Overview

> Mirumoji is an open-source, self-hosted Japanese immersion toolkit. Drop in any video, anime episode, drama or audio clip and it gives you: clickable tokenized subtitles with dictionary pop-ups, Whisper-powered transcription, instant SRT/clip extraction, and one-click Anki deck export — all in Docker, all running on your own machine.

> Optional [`OpenAI`](https://platform.openai.com/docs/overview) Integration &rarr; Customizable GPT Breakdowns of Subtitles

> Optional [`Modal`](https://modal.com) Integration &rarr; Install a CPU only version and run all GPU tasks on the cloud

---

# Preview

> View a [`Preview`](https://svdc1.github.io/mirumoji) of the frontend _(No backend running)_

# Documentation

> Access full [`Documentantion`](https://svdc1.github.io/mirumoji_docs)

# Features

## **Interactive Video Player**

![alt-text](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/player.png?raw=true)

> Upload your local anime/J-Drama espisodes or any Japanese video and `.SRT` subtitles.

## **Clickable Japanese Subtitles**

![alt-text](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/word_dialog.png?raw=true)

> Subtitles are tokenized ([`kuromoji.js`](https://github.com/takuyaa/kuromoji.js)), allowing you to click individual words for information

## **OpenAI Integration**

![alt-text](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/gpt_template.png?raw=true)

> Modify System Message and User Prompt with `{sentence}` and `{word}` variables.

## **Local Media Processing**

### **Video Conversion**

> Upload videos in various formats; they can be converted to MP4 for optimal playback.

### **SRT Generation**

> Generate subtitles for your videos. Runs [`FasterWhisper`](https://github.com/SYSTRAN/faster-whisper) with modified parameters to increase accuracy for longer media such as Anime/ J-Drama episodes.

## **Audio Transcription**

![alt-text](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/transcription.png?raw=true)

> Transcribe Japanese audio from recordings or uploaded files.

## **Profile-Based Data Management**

### **Persistent Storage**

![alt-img](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/profile.png?raw=true)

> Profile configurations and all other profile-related data is stored and managed via SQLite database by the backend.

### **Clip Saving**

![alt-img](https://github.com/svdC1/mirumoji/blob/main/.github/example_imgs/clips.png?raw=true)

> Save important video segments with their associated word breakdowns and export as an Anki Deck

---

# Setup

> Both the [`frontend`](https://github.com/svdC1/mirumoji/tree/main/apps/frontend) and [`backend`](https://github.com/svdC1/mirumoji/tree/main/apps/backend) have pre-built [`Docker`](https://www.docker.com/) images and are set up to work with Docker Compose.

> The easiest setup is to run the [`launcher`](https://github.com/svdC1/mirumoji/tree/main/apps/cli) for your platform. **For detailed instructions please refer to the [`Setup Guide`](https://svdc1.github.io/mirumoji_docs)**

> You can also choose to [`build`](https://docs.docker.com/build/) the images locally with the Dockerfiles provided.

---

# Image Sizes

> Compressed sizes for the Docker Images

> -   ![Docker Image Size (tag)](https://img.shields.io/docker/image-size/svdc1/mirumoji/backend-gpu-latest?style=for-the-badge&&logoSize=auto&label=GPU%20Backend%20Image&link=https%3A%2F%2Fhub.docker.com%2Frepository%2Fdocker%2Fsvdc1%2Fmirumoji%2Ftags%2Fbackend-gpu-latest%2F)
> -   ![Docker Image Size (tag)](https://img.shields.io/docker/image-size/svdc1/mirumoji/backend-cpu-latest?style=for-the-badge&logoSize=auto&label=CPU%20Backend%20Image&link=https%3A%2F%2Fhub.docker.com%2Frepository%2Fdocker%2Fsvdc1%2Fmirumoji%2Ftags%2Fbackend-cpu-latest%2F)
> -   ![Docker Image Size (tag)](https://img.shields.io/docker/image-size/svdc1/mirumoji/frontend-latest?style=for-the-badge&logoSize=auto&label=Frontend%20Image&link=https%3A%2F%2Fhub.docker.com%2Frepository%2Fdocker%2Fsvdc1%2Fmirumoji%2Ftags%2Ffrontend-latest%2F)
