/**
 * @fileoverview Provides a robust, cross-browser utility for recording a MediaStream from an HTMLVideoElement.
 * It uses the native `captureStream` where available and falls back to a canvas-based approach for browsers
 * like iOS Safari that do not support it.
 */

/**
 * Records a clip from a video element between a start and end time.
 *
 * This function first tries to use the efficient `video.captureStream()` method.
 * If that is not available, it falls back to a method of drawing video frames
 * to a canvas and capturing the stream from there, while simultaneously capturing
 * audio with the Web Audio API.
 *
 * @param {HTMLVideoElement} videoElement The video element to record from.
 * @param {number} startTime The time in seconds to start the recording.
 * @param {number} endTime The time in seconds to end the recording.
 * @returns {Promise<File>} A promise that resolves with the recorded video file.
 */
export async function recordMediaStream(
    videoElement: HTMLVideoElement,
    startTime: number,
    endTime: number
): Promise<File> {
    const duration = (endTime - startTime) * 1000;
    if (duration <= 0) {
        return Promise.reject(
            new Error("Recording duration must be positive.")
        );
    }

    // Set up the video element for recording
    const originalTime = videoElement.currentTime;
    const wasPaused = videoElement.paused;
    const wasMuted = videoElement.muted;

    videoElement.currentTime = startTime;
    videoElement.muted = true; // Mute playback during capture

    try {
        await videoElement.play();
        // A short delay can help ensure the stream is ready
        await new Promise((r) => setTimeout(r, 150));

        let mediaStream;

        if (typeof videoElement.captureStream === "function") {
            // Use the native, preferred method
            mediaStream = videoElement.captureStream();
        } else {
            // Use the canvas and AudioContext fallback for iOS and other browsers
            const canvas = document.createElement("canvas");
            canvas.width = videoElement.videoWidth;
            canvas.height = videoElement.videoHeight;
            const ctx = canvas.getContext("2d");

            if (!ctx) {
                throw new Error("Could not create 2D canvas context.");
            }

            const canvasStream = canvas.captureStream();
            const videoTrack = canvasStream.getVideoTracks()[0];

            const audioContext = new (window.AudioContext ||
                (window as any).webkitAudioContext)();
            const sourceNode =
                audioContext.createMediaElementSource(videoElement);
            const destinationNode = audioContext.createMediaStreamDestination();
            sourceNode.connect(destinationNode);
            // We don't connect to the main destination to avoid double playback sound
            const audioTrack = destinationNode.stream.getAudioTracks()[0];

            mediaStream = new MediaStream([videoTrack, audioTrack]);

            // Start drawing frames to the canvas
            let animationFrameId: number;
            const drawFrame = () => {
                if (
                    videoElement.paused ||
                    videoElement.ended ||
                    videoElement.currentTime >= endTime
                ) {
                    cancelAnimationFrame(animationFrameId);
                    return;
                }
                ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
                animationFrameId = requestAnimationFrame(drawFrame);
            };
            drawFrame();
        }

        const recordedFile = await createRecordingPromise(
            mediaStream,
            duration
        );

        // Restore video element state
        if (!wasPaused) {
            videoElement.currentTime = originalTime;
            await videoElement.play();
        } else {
            videoElement.pause();
            videoElement.currentTime = originalTime;
        }
        videoElement.muted = wasMuted;

        return recordedFile;
    } catch (error) {
        // Restore video state on error
        videoElement.pause();
        videoElement.currentTime = originalTime;
        videoElement.muted = wasMuted;
        throw error; // Re-throw the error to be caught by the caller
    }
}

/**
 * Creates a promise that resolves with a recorded File object from a MediaStream.
 *
 * @param {MediaStream} stream The stream to record.
 * @param {number} duration The duration to record in milliseconds.
 * @returns {Promise<File>} A promise that resolves with the recorded video file.
 */
export function createRecordingPromise(
    stream: MediaStream,
    duration: number
): Promise<File> {
    const mimeType = "video/webm;codecs=vp8,opus";
    if (!MediaRecorder.isTypeSupported(mimeType)) {
        console.warn(`${mimeType} not supported, falling back to default.`);
    }

    return new Promise<File>((resolve, reject) => {
        try {
            const recorder = new MediaRecorder(stream, { mimeType });
            const chunks: BlobPart[] = [];

            recorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) chunks.push(event.data);
            };

            recorder.onstop = () => {
                stream.getTracks().forEach((track) => track.stop());
                if (chunks.length === 0) {
                    return reject(new Error("No video data was recorded."));
                }
                const blob = new Blob(chunks, { type: mimeType });
                const file = new File([blob], "clip.webm", { type: mimeType });
                resolve(file);
            };

            recorder.onerror = (event) => {
                stream.getTracks().forEach((track) => track.stop());
                reject(
                    new Error(
                        "MediaRecorder error: " + (event as any).error.name
                    )
                );
            };

            recorder.start();
            setTimeout(() => {
                if (recorder.state === "recording") {
                    recorder.stop();
                }
            }, duration);
        } catch (e) {
            stream.getTracks().forEach((track) => track.stop());
            reject(e);
        }
    });
}
