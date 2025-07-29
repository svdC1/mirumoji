This component provides a settings drawer for the video player.
It allows the user to load video and subtitle files, generate subtitles,
convert videos to MP4, and customize the appearance of the subtitles.

## Functions

### SettingsDrawer()

```ts
function SettingsDrawer(props): Element;
```

Defined in: [src/components/SettingsDrawer.tsx:76](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/components/SettingsDrawer.tsx#L76)

The SettingsDrawer component.

This component is responsible for the following:

- Allowing the user to load video and subtitle files.
- Generating subtitles from a video file.
- Converting a video file to MP4 format.
- Customizing the appearance of the subtitles.

#### Parameters

| Parameter | Type                                                           | Description                  |
| --------- | -------------------------------------------------------------- | ---------------------------- |
| `props`   | [`SettingsDrawerProps`](../types/types.md#settingsdrawerprops) | The props for the component. |

#### Returns

`Element`

The SettingsDrawer component.
