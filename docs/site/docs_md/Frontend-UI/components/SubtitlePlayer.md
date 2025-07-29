This component is a video player with interactive subtitles.
It displays subtitles on top of the video, and allows the user to click on
words to get more information about them.

## Functions

### SubtitlePlayer()

```ts
function SubtitlePlayer(props): Element;
```

Defined in: [src/components/SubtitlePlayer.tsx:28](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/components/SubtitlePlayer.tsx#L28)

The SubtitlePlayer component.

This component is responsible for the following:

- Playing a video with subtitles.
- Parsing and displaying subtitles.
- Allowing the user to click on words in the subtitles to get more information.

#### Parameters

| Parameter | Type                                                           | Description                  |
| --------- | -------------------------------------------------------------- | ---------------------------- |
| `props`   | [`SubtitlePlayerProps`](../types/types.md#subtitleplayerprops) | The props for the component. |

#### Returns

`Element`

The SubtitlePlayer component.
