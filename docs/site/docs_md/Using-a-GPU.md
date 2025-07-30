# Using a GPU

## Choose How GPU Features Run

-   Mirumoji uses a large transcription AI model and tools for video processing which require an NVIDIA GPU.
-   If you don't have one, or prefer not to run it on your local one, Mirumoji is set up to work with [`MODAL`](https://modal.com) **without any additional configuration**

## About Modal

-   [`MODAL`](https://modal.com) is a platform which provides cloud computing services, **allowing the application's features which require a GPU to be run remotely**
-   Although it's a **paid** platform they have a very generous **free-tier** which you should be able to use for a long time.