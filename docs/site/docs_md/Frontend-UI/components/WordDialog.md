This component displays a dialog with information about a word.
It includes a GPT-powered explanation, dictionary definitions, and the ability to save a clip of the word being used.

## Functions

### WordDialog()

```ts
function WordDialog(props): Element;
```

Defined in: [src/components/WordDialog.tsx:44](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/components/WordDialog.tsx#L44)

The WordDialog component.

This component is responsible for the following:

- Displaying information about a word, including a GPT-powered explanation and dictionary definitions.
- Allowing the user to save a clip of the word being used in the video.

#### Parameters

| Parameter | Type                                                   | Description                  |
| --------- | ------------------------------------------------------ | ---------------------------- |
| `props`   | [`WordDialogProps`](../types/types.md#worddialogprops) | The props for the component. |

#### Returns

`Element`

The WordDialog component.
