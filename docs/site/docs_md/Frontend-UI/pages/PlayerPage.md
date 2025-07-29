This component is the player page of the application.
It integrates the settings drawer and the main subtitle player, using the
global PlayerContext to manage and persist player state across navigation.

## Functions

### PlayerPage()

```ts
function PlayerPage(): Element;
```

Defined in: [src/pages/PlayerPage.tsx:22](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/pages/PlayerPage.tsx#L22)

The PlayerPage component.

This component serves as the main container for the video player experience.
It sources its state from the `PlayerContext` and passes the necessary state
and actions down to the `SettingsDrawer` and `SubtitlePlayer` components.

#### Returns

`Element`

The PlayerPage component.
