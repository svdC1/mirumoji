This file provides a context for managing the subtitle settings.

## Interfaces

### SubtitleSettingsContextType

Defined in: [src/contexts/SubtitleSettingsContext.tsx:19](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/SubtitleSettingsContext.tsx#L19)

SubtitleSettingsContextType
Shape of the Subtitle Settings Context

#### Properties

| Property                                             | Type                                               | Defined in                                                                                                                                                                                |
| ---------------------------------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="resetsubtitlestyle"></a> `resetSubtitleStyle` | () => `void`                                       | [src/contexts/SubtitleSettingsContext.tsx:22](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/SubtitleSettingsContext.tsx#L22) |
| <a id="setsubtitlestyle"></a> `setSubtitleStyle`     | (`style`) => `void`                                | [src/contexts/SubtitleSettingsContext.tsx:21](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/SubtitleSettingsContext.tsx#L21) |
| <a id="subtitlestyle"></a> `subtitleStyle`           | [`SubtitleStyle`](../types/types.md#subtitlestyle) | [src/contexts/SubtitleSettingsContext.tsx:20](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/SubtitleSettingsContext.tsx#L20) |

## Functions

### SubtitleSettingsProvider()

```ts
function SubtitleSettingsProvider(props): Element;
```

Defined in: [src/contexts/SubtitleSettingsContext.tsx:46](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/SubtitleSettingsContext.tsx#L46)

A provider for the SubtitleSettingsContext.

#### Parameters

| Parameter        | Type                           | Description                  |
| ---------------- | ------------------------------ | ---------------------------- |
| `props`          | \{ `children`: `ReactNode`; \} | The props for the component. |
| `props.children` | `ReactNode`                    | -                            |

#### Returns

`Element`

The SubtitleSettingsProvider component.

---

### useSubtitleSettings()

```ts
function useSubtitleSettings(): SubtitleSettingsContextType;
```

Defined in: [src/contexts/SubtitleSettingsContext.tsx:104](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/SubtitleSettingsContext.tsx#L104)

A hook for using the SubtitleSettingsContext.

#### Returns

[`SubtitleSettingsContextType`](#subtitlesettingscontexttype)

The SubtitleSettingsContext.
