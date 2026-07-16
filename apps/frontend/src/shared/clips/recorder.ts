/**
 * @packageDocumentation Cross-browser recording of a MediaStream from an
 * HTMLVideoElement. Uses native `captureStream` where available and falls back
 * to a canvas-based approach (iOS Safari). Also picks a supported MIME type.
 */

// One shared AudioContext for the canvas-fallback recording path (iOS Safari).
// Created lazily so it is born inside a user gesture rather than suspended at
// page load, which a later recording cannot reliably resume.
let sharedAudioCtx: AudioContext | null = null;

function getAudioContext(): AudioContext {
    if (!sharedAudioCtx) {
        const Ctor =
            window.AudioContext ||
            (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        sharedAudioCtx = new Ctor();
    }
    return sharedAudioCtx;
}

/**
 * Warms the recorder's AudioContext from within a user gesture.
 *
 * The canvas-fallback recording path (iOS Safari) draws its audio from this
 * shared AudioContext, which only leaves the "suspended" state when resumed
 * during a user activation. A save-clip flow can await a breakdown stream for
 * several seconds before recording, by which point the click's activation is
 * spent and the context can no longer resume. Call this synchronously from the
 * click handler so the context is already running when recording starts.
 */
export function warmupRecorder(): void {
    const ctx = getAudioContext();
    if (ctx.state === "suspended") {
        void ctx.resume();
    }
}

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

    const audioCtx = getAudioContext();
    // The context may still be suspended if the gesture was never warmed; try
    // to resume it here too so the audio track produces data.
    if (audioCtx.state === "suspended") {
        await audioCtx.resume();
    }

    let sourceNode = elementSourceMap.get(videoElement);
    if (!sourceNode) {
        sourceNode = audioCtx.createMediaElementSource(videoElement);
        elementSourceMap.set(videoElement, sourceNode);
        sourceNode.connect(audioCtx.destination);
    }

    const destinationNode = audioCtx.createMediaStreamDestination();
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
        let settled = false;
        const stopTracks = () => stream.getTracks().forEach((track) => track.stop());
        // Settle exactly once. Guards against a late safety-timeout firing after
        // a normal onstop, and against onstop never firing at all.
        const finish = (run: () => void) => {
            if (settled) return;
            settled = true;
            run();
        };

        try {
            const recorder = new MediaRecorder(stream, { mimeType: recordingOptions.mimeType });
            const chunks: BlobPart[] = [];

            recorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) chunks.push(event.data);
            };

            recorder.onstop = () => {
                stopTracks();
                if (chunks.length === 0) {
                    finish(() => reject(new Error("No video data was recorded.")));
                    return;
                }
                const blob = new Blob(chunks, { type: recordingOptions.mimeType });
                const file = new File([blob], `clip.${recordingOptions.fileExtension}`, {
                    type: recordingOptions.mimeType,
                });
                finish(() => resolve(file));
            };

            recorder.onerror = (event: Event) => {
                stopTracks();
                const err = (event as unknown as { error?: { name?: string } }).error;
                finish(() =>
                    reject(new Error("MediaRecorder error: " + (err?.name || "Unknown error")))
                );
            };

            recorder.start();
            // Stop at the intended clip length.
            window.setTimeout(() => {
                try {
                    if (recorder.state === "recording") recorder.stop();
                } catch {
                    // Nothing to do; the safety timeout below is the backstop.
                }
            }, duration);
            // Backstop: if the stream's tracks died so the recorder went inactive
            // without ever firing onstop, settle anyway so the caller is never
            // stuck on "Recording..." forever.
            window.setTimeout(() => {
                finish(() => {
                    stopTracks();
                    reject(new Error("Recording timed out."));
                });
            }, duration + 4000);
        } catch (e) {
            stopTracks();
            finish(() => reject(e));
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
