This component displays a chat bubble.

## Functions

### ChatBubble()

```ts
function ChatBubble(props): Element;
```

Defined in: [src/components/ChatBubble.tsx:24](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/components/ChatBubble.tsx#L24)

The ChatBubble component.

This component is responsible for the following:

- Displaying a chat message.
- Displaying an audio player if the message is an audio message.
- Displaying a transcription of the audio if the message is a transcription.
- Displaying a GPT-powered explanation of the transcription if the message is an explanation.

#### Parameters

| Parameter | Type                                                   | Description                  |
| --------- | ------------------------------------------------------ | ---------------------------- |
| `props`   | [`ChatBubbleProps`](../types/types.md#chatbubbleprops) | The props for the component. |

#### Returns

`Element`

The ChatBubble component.
