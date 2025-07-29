Provides a cross-browser utility for recording a MediaStream from an HTMLVideoElement.
It uses the native `captureStream` on the `HTMLVideoElement` iself where available and falls back to
a `HTMLCanvasElement` based approach for browsers like iOS Safari that do not support it.
It also automatically selects a supported MIME type for MediaRecorder by checking availability.

## Functions

### createRecordingPromise()

```ts
function createRecordingPromise(
  stream,
  duration,
  recordingOptions,
): Promise<File>;
```

Defined in: [src/utils/mediaRecorder.ts:100](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/mediaRecorder.ts#L100)

Creates a promise that resolves with a recorded File object from a MediaStream.

#### Parameters

| Parameter                        | Type                                                                    | Description                             |
| -------------------------------- | ----------------------------------------------------------------------- | --------------------------------------- |
| `stream`                         | [`MediaStream`](https://developer.mozilla.org/docs/Web/API/MediaStream) | The stream to record.                   |
| `duration`                       | `number`                                                                | The duration to record in milliseconds. |
| `recordingOptions`               | \{ `fileExtension`: `string`; `mimeType`: `string`; \}                  | The selected mimeType and extension.    |
| `recordingOptions.fileExtension` | `string`                                                                | -                                       |
| `recordingOptions.mimeType`      | `string`                                                                | -                                       |

#### Returns

[`Promise`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Promise)\<[`File`](https://developer.mozilla.org/docs/Web/API/File)\>

A promise that resolves with the recorded video file.

---

### getStream()

```ts
function getStream(videoElement, endTime): Promise<MediaStream>;
```

Defined in: [src/utils/mediaRecorder.ts:25](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/mediaRecorder.ts#L25)

Gets a MediaStream from a video element, using a canvas fallback if necessary.

#### Parameters

| Parameter      | Type                                                                              | Description                              |
| -------------- | --------------------------------------------------------------------------------- | ---------------------------------------- |
| `videoElement` | [`HTMLVideoElement`](https://developer.mozilla.org/docs/Web/API/HTMLVideoElement) | The video element to get a stream from.  |
| `endTime`      | `number`                                                                          | The time when the recording should stop. |

#### Returns

[`Promise`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Promise)\<[`MediaStream`](https://developer.mozilla.org/docs/Web/API/MediaStream)\>

A promise that resolves with the combined media stream.

---

### getSupportedMimeType()

```ts
function getSupportedMimeType(): null | {
  fileExtension: string;
  mimeType: string;
};
```

Defined in: [src/utils/mediaRecorder.ts:159](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/mediaRecorder.ts#L159)

Iterates through a list of preferred MIME types and returns the first one supported by the browser.

#### Returns

\| `null`
\| \{
`fileExtension`: `string`;
`mimeType`: `string`;
\}

The best supported MIME type and corresponding file extension, or null if none are supported.

---

### recordMediaStream()

```ts
function recordMediaStream(videoElement, startTime, endTime): Promise<File>;
```

Defined in: [src/utils/mediaRecorder.ts:188](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/mediaRecorder.ts#L188)

Records a clip from a video element between a start and end time.
This is the main function to be called from UI components.

#### Parameters

| Parameter      | Type                                                                              | Description                                 |
| -------------- | --------------------------------------------------------------------------------- | ------------------------------------------- |
| `videoElement` | [`HTMLVideoElement`](https://developer.mozilla.org/docs/Web/API/HTMLVideoElement) | The video element to record from.           |
| `startTime`    | `number`                                                                          | The time in seconds to start the recording. |
| `endTime`      | `number`                                                                          | The time in seconds to end the recording.   |

#### Returns

[`Promise`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Promise)\<[`File`](https://developer.mozilla.org/docs/Web/API/File)\>

A promise that resolves with the recorded video file.
