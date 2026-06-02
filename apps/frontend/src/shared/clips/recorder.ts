/**
 * @packageDocumentation Cross-browser recording of a MediaStream from an
 * HTMLVideoElement. Uses native `captureStream` where available and falls back
 * to a canvas-based approach (iOS Safari). Also picks a supported MIME type.
 */

// Single shared audio context (created lazily-ish at module load).
const sharedAudioCtx = new (
    window.AudioContext ||
    (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
)();

// One MediaElementAudioSourceNode per <video> (a video may only ever connect to
// a single source node for the page's lifetime).
const elementSourceMap = new WeakMap<HTMLMediaElement, MediaElementAudioSourceNode>();

/**
 * Gets a MediaStream from a video element, with a canvas fallback.
 *
 * @param {HTMLVideoElement} videoElement The source video element.
 * @param {number} endTime When (seconds) the recording should stop.
 * @returns {Promise<MediaStream>} The combined media stream.
 */
export async function getStream(
    videoElement: HTMLVideoElement,
    endTime: number
): Promise<MediaStream> {
    if (videoElement.readyState < 1) {
        await new Promise<void>((res) =>
            videoElement.addEventListener("loadedmetadata", () => res(), { once: true })
        );
    }

    if (typeof videoElement.captureStream === "function") {
        return videoElement.captureStream();
    }

    // Fallback for iOS/Safari without captureStream on HTMLVideoElement.
    console.log("Capturing with HTMLCanvasElement Fallback");
    const canvas = document.createElement("canvas");
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
        throw new Error("Could not create 2D canvas context.");
    }

    let sourceNode = elementSourceMap.get(videoElement);
    if (!sourceNode) {
        sourceNode = sharedAudioCtx.createMediaElementSource(videoElement);
        elementSourceMap.set(videoElement, sourceNode);
        sourceNode.connect(sharedAudioCtx.destination);
    }

    const destinationNode = sharedAudioCtx.createMediaStreamDestination();
    sourceNode.connect(destinationNode);

    const videoTrack = canvas.captureStream(30).getVideoTracks()[0];
    const audioTrack = destinationNode.stream.getAudioTracks()[0];
    const stream = new MediaStream([videoTrack, audioTrack]);

    let animationFrameId: number;
    const drawFrame = () => {
        if (videoElement.paused || videoElement.ended || videoElement.currentTime >= endTime) {
            cancelAnimationFrame(animationFrameId);
            return;
        }
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        animationFrameId = requestAnimationFrame(drawFrame);
    };
    drawFrame();

    return stream;
}

/**
 * Records a MediaStream into a File for `duration` ms.
 *
 * @param {MediaStream} stream The stream to record.
 * @param {number} duration Duration in milliseconds.
 * @param {{ mimeType: string; fileExtension: string }} recordingOptions Codec choice.
 * @returns {Promise<File>} The recorded file.
 */
export function createRecordingPromise(
    stream: MediaStream,
    duration: number,
    recordingOptions: { mimeType: string; fileExtension: string }
): Promise<File> {
    return new Promise<File>((resolve, reject) => {
        try {
            const recorder = new MediaRecorder(stream, { mimeType: recordingOptions.mimeType });
            const chunks: BlobPart[] = [];

            recorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) chunks.push(event.data);
            };

            recorder.onstop = () => {
                stream.getTracks().forEach((track) => track.stop());
                if (chunks.length === 0) {
                    return reject(new Error("No video data was recorded."));
                }
                const blob = new Blob(chunks, { type: recordingOptions.mimeType });
                const file = new File([blob], `clip.${recordingOptions.fileExtension}`, {
                    type: recordingOptions.mimeType,
                });
                resolve(file);
            };

            recorder.onerror = (event: Event) => {
                stream.getTracks().forEach((track) => track.stop());
                const err = (event as unknown as { error?: { name?: string } }).error;
                reject(new Error("MediaRecorder error: " + (err?.name || "Unknown error")));
            };

            recorder.start();
            setTimeout(() => {
                if (recorder.state === "recording") recorder.stop();
            }, duration);
        } catch (e) {
            stream.getTracks().forEach((track) => track.stop());
            reject(e);
        }
    });
}

/**
 * Returns the first browser-supported recording MIME type + extension.
 *
 * @returns {{ mimeType: string; fileExtension: string } | null} The choice, or `null`.
 */
export function getSupportedMimeType(): { mimeType: string; fileExtension: string } | null {
    const mimeTypes = [
        { mimeType: "video/mp4;codecs=avc1,mp4a.40.2", fileExtension: "mp4" }, // Safari/iOS
        { mimeType: "video/webm;codecs=vp8,opus", fileExtension: "webm" },
        { mimeType: "video/webm;codecs=vp9,opus", fileExtension: "webm" },
        { mimeType: "video/webm", fileExtension: "webm" },
        { mimeType: "video/mp4", fileExtension: "mp4" },
    ];
    for (const type of mimeTypes) {
        if (MediaRecorder.isTypeSupported(type.mimeType)) return type;
    }
    return null;
}

/**
 * Records a clip from a video element between two timestamps, restoring the
 * element's prior state afterward.
 *
 * @param {HTMLVideoElement} videoElement The source element.
 * @param {number} startTime Start time (seconds).
 * @param {number} endTime End time (seconds).
 * @returns {Promise<File>} The recorded clip file.
 */
export async function recordMediaStream(
    videoElement: HTMLVideoElement,
    startTime: number,
    endTime: number
): Promise<File> {
    const duration = (endTime - startTime) * 1000;
    if (duration <= 0) {
        return Promise.reject(new Error("Recording duration must be positive."));
    }

    const originalTime = videoElement.currentTime;
    const wasPaused = videoElement.paused;
    const originalVolume = videoElement.volume;

    videoElement.currentTime = startTime;
    videoElement.volume = 0; // keep decoder alive (vs muting)

    try {
        await videoElement.play();
        await new Promise((r) => setTimeout(r, 150)); // short delay for stability

        const recordingOptions = getSupportedMimeType();
        if (!recordingOptions) {
            throw new Error("No supported MediaRecorder MIME type found for this browser.");
        }

        const stream = await getStream(videoElement, endTime);
        return await createRecordingPromise(stream, duration, recordingOptions);
    } catch (error) {
        console.error("Error during media stream recording:", error);
        throw error;
    } finally {
        videoElement.currentTime = originalTime;
        videoElement.volume = originalVolume;
        if (wasPaused) {
            videoElement.pause();
        } else {
            await videoElement.play();
        }
    }
}
