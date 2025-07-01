/**
 * @fileoverview Provides a robust, cross-browser utility for recording a MediaStream from an HTMLVideoElement.
 * It uses the native `captureStream` where available and falls back to a canvas-based approach for browsers
 * like iOS Safari that do not support it. It also intelligently selects a supported MIME type for MediaRecorder.
 */

/**
 * Iterates through a list of preferred MIME types and returns the first one supported by the browser.
 * @returns {{ mimeType: string; fileExtension: string } | null} The best supported MIME type and corresponding file extension, or null if none are supported.
 */
function getSupportedMimeType(): {
    mimeType: string;
    fileExtension: string;
} | null {
    const mimeTypes = [
        { mimeType: "video/mp4;codecs=avc1,mp4a.40.2", fileExtension: "mp4" }, // Preferred for Safari/iOS
        { mimeType: "video/webm;codecs=vp8,opus", fileExtension: "webm" },
        { mimeType: "video/webm;codecs=vp9,opus", fileExtension: "webm" },
        { mimeType: "video/webm", fileExtension: "webm" },
        { mimeType: "video/mp4", fileExtension: "mp4" },
    ];

    for (const type of mimeTypes) {
        if (MediaRecorder.isTypeSupported(type.mimeType)) {
            return type;
        }
    }
    return null; // Fallback if no specific types are supported
}

/**
 * Records a clip from a video element between a start and end time.
 * This is the main function to be called from UI components.
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

    const originalTime = videoElement.currentTime;
    const wasPaused = videoElement.paused;
    const wasMuted = videoElement.muted;

    videoElement.currentTime = startTime;
    videoElement.muted = true; // Mute playback during capture to avoid echo

    try {
        await videoElement.play();
        await new Promise((r) => setTimeout(r, 150)); // Short delay for stability

        const recordingOptions = getSupportedMimeType();
        if (!recordingOptions) {
            throw new Error(
                "No supported MediaRecorder MIME type found for this browser."
            );
        }

        const stream = await getStream(videoElement, endTime);
        const recordedFile = await createRecordingPromise(
            stream,
            duration,
            recordingOptions
        );

        return recordedFile;
    } catch (error) {
        console.error("Error during media stream recording:", error);
        throw error;
    } finally {
        // Restore video element's state
        if (wasPaused) {
            videoElement.pause();
        } else {
            await videoElement.play();
        }
        videoElement.currentTime = originalTime;
        videoElement.muted = wasMuted;
    }
}

/**
 * Gets a MediaStream from a video element, using a canvas fallback if necessary.
 * @param {HTMLVideoElement} videoElement - The video element to get a stream from.
 * @param {number} endTime - The time when the recording should stop.
 * @returns {Promise<MediaStream>} A promise that resolves with the combined media stream.
 */
async function getStream(
    videoElement: HTMLVideoElement,
    endTime: number
): Promise<MediaStream> {
    if (typeof videoElement.captureStream === "function") {
        return videoElement.captureStream();
    }

    // Fallback for iOS/Safari
    console.log("Using canvas fallback for stream capture.");
    const canvas = document.createElement("canvas");
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext("2d");

    if (!ctx) {
        throw new Error("Could not create 2D canvas context.");
    }

    const audioContext = new (window.AudioContext ||
        (window as any).webkitAudioContext)();
    const sourceNode = audioContext.createMediaElementSource(videoElement);
    const destinationNode = audioContext.createMediaStreamDestination();
    sourceNode.connect(destinationNode);
    sourceNode.connect(audioContext.destination); // Ensure audio plays out if not muted

    const videoTrack = canvas.captureStream().getVideoTracks()[0];
    const audioTrack = destinationNode.stream.getAudioTracks()[0];

    const stream = new MediaStream([videoTrack, audioTrack]);

    let animationFrameId: number;
    const drawFrame = () => {
        if (
            videoElement.paused ||
            videoElement.ended ||
            videoElement.currentTime >= endTime
        ) {
            cancelAnimationFrame(animationFrameId);
            audioContext.close();
            return;
        }
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        animationFrameId = requestAnimationFrame(drawFrame);
    };
    drawFrame();

    return stream;
}

/**
 * Creates a promise that resolves with a recorded File object from a MediaStream.
 * @param {MediaStream} stream The stream to record.
 * @param {number} duration The duration to record in milliseconds.
 * @param {{ mimeType: string; fileExtension: string }} recordingOptions The selected mimeType and extension.
 * @returns {Promise<File>} A promise that resolves with the recorded video file.
 */
export function createRecordingPromise(
    stream: MediaStream,
    duration: number,
    recordingOptions: { mimeType: string; fileExtension: string }
): Promise<File> {
    return new Promise<File>((resolve, reject) => {
        try {
            const recorder = new MediaRecorder(stream, {
                mimeType: recordingOptions.mimeType,
            });
            const chunks: BlobPart[] = [];

            recorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) chunks.push(event.data);
            };

            recorder.onstop = () => {
                stream.getTracks().forEach((track) => track.stop());
                if (chunks.length === 0) {
                    return reject(new Error("No video data was recorded."));
                }
                const blob = new Blob(chunks, {
                    type: recordingOptions.mimeType,
                });
                const file = new File(
                    [blob],
                    `clip.${recordingOptions.fileExtension}`,
                    { type: recordingOptions.mimeType }
                );
                resolve(file);
            };

            recorder.onerror = (event: any) => {
                stream.getTracks().forEach((track) => track.stop());
                reject(
                    new Error(
                        "MediaRecorder error: " + event.error?.name ||
                            "Unknown error"
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
