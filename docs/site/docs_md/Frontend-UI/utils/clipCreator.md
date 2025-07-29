Provides a utility for creating and saving video clips.
This module orchestrates the recording process, data preparation, and API submission.

## Functions

### createAndSaveClip()

```ts
function createAndSaveClip(
  videoElementId,
  cueStart,
  cueEnd,
  gptData,
  onProgress,
): Promise<void>;
```

Defined in: [src/utils/clipCreator.ts:20](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/clipCreator.ts#L20)

Creates and saves a video clip by recording a segment from a video element,
bundling it with GPT data, and uploading it to the server.

#### Parameters

| Parameter        | Type                                               | Description                                         |
| ---------------- | -------------------------------------------------- | --------------------------------------------------- |
| `videoElementId` | `string`                                           | The ID of the HTMLVideoElement to record from.      |
| `cueStart`       | `number`                                           | The start time of the clip in seconds.              |
| `cueEnd`         | `number`                                           | The end time of the clip in seconds.                |
| `gptData`        | [`BreakdownData`](../types/types.md#breakdowndata) | The GPT breakdown data associated with the clip.    |
| `onProgress`     | (`message`, `type`) => `void`                      | A callback to report the progress of the operation. |

#### Returns

[`Promise`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Promise)\<`void`\>

A promise that resolves when the operation is complete or rejects on error.
