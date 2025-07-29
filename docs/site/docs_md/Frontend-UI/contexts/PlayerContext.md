This file defines the context for managing the state of the video player.
It allows the player's state (e.g., loaded video, subtitles, settings) to persist
across component mounts and unmounts, enabling navigating
between pages.

## Interfaces

### PlayerContextState

Defined in: [src/contexts/PlayerContext.tsx:14](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L14)

PlayerContextState
Defines the shape of the data stored in the PlayerContext.

#### Properties

| Property                                         | Type                                                                | Defined in                                                                                                                                                            |
| ------------------------------------------------ | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="clearplayerstate"></a> `clearPlayerState` | () => `void`                                                        | [src/contexts/PlayerContext.tsx:29](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L29) |
| <a id="draweropen"></a> `drawerOpen`             | `boolean`                                                           | [src/contexts/PlayerContext.tsx:25](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L25) |
| <a id="setdraweropen"></a> `setDrawerOpen`       | (`open`) => `void`                                                  | [src/contexts/PlayerContext.tsx:26](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L26) |
| <a id="setshowfurigana"></a> `setShowFurigana`   | (`show`) => `void`                                                  | [src/contexts/PlayerContext.tsx:28](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L28) |
| <a id="setsrt"></a> `setSrt`                     | (`file`) => `void`                                                  | [src/contexts/PlayerContext.tsx:20](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L20) |
| <a id="setsrtfilename"></a> `setSrtFileName`     | (`name`) => `void`                                                  | [src/contexts/PlayerContext.tsx:22](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L22) |
| <a id="setvideo"></a> `setVideo`                 | (`file`) => `void`                                                  | [src/contexts/PlayerContext.tsx:16](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L16) |
| <a id="setvideofilename"></a> `setVideoFileName` | (`name`) => `void`                                                  | [src/contexts/PlayerContext.tsx:18](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L18) |
| <a id="setvideourl"></a> `setVideoUrl`           | (`url`) => `void`                                                   | [src/contexts/PlayerContext.tsx:24](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L24) |
| <a id="showfurigana"></a> `showFurigana`         | `boolean`                                                           | [src/contexts/PlayerContext.tsx:27](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L27) |
| <a id="srt"></a> `srt`                           | `null` \| [`File`](https://developer.mozilla.org/docs/Web/API/File) | [src/contexts/PlayerContext.tsx:19](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L19) |
| <a id="srtfilename"></a> `srtFileName`           | `null` \| `string`                                                  | [src/contexts/PlayerContext.tsx:21](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L21) |
| <a id="video"></a> `video`                       | `null` \| [`File`](https://developer.mozilla.org/docs/Web/API/File) | [src/contexts/PlayerContext.tsx:15](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L15) |
| <a id="videofilename"></a> `videoFileName`       | `null` \| `string`                                                  | [src/contexts/PlayerContext.tsx:17](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L17) |
| <a id="videourl"></a> `videoUrl`                 | `null` \| `string`                                                  | [src/contexts/PlayerContext.tsx:23](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L23) |

---

### PlayerProviderProps

Defined in: [src/contexts/PlayerContext.tsx:38](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L38)

PlayerProviderProps
Defines the shape of the Player Provider Props

#### Properties

| Property                         | Type        | Defined in                                                                                                                                                            |
| -------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="children"></a> `children` | `ReactNode` | [src/contexts/PlayerContext.tsx:39](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L39) |

## Variables

### PlayerProvider

```ts
const PlayerProvider: React.FC<PlayerProviderProps>;
```

Defined in: [src/contexts/PlayerContext.tsx:48](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L48)

The provider component that supplies the PlayerContext to its children.
It encapsulates the state logic and provides the state and action functions to its descendants.

#### Param

The props for the component.

#### Returns

The provider component.

## Functions

### usePlayer()

```ts
function usePlayer(): PlayerContextState;
```

Defined in: [src/contexts/PlayerContext.tsx:100](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/PlayerContext.tsx#L100)

A custom hook for consuming the PlayerContext.

#### Returns

[`PlayerContextState`](#playercontextstate)

The state and actions from the PlayerContext.

#### Throws

If the hook is used outside of a PlayerProvider.
