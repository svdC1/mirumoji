This component is the text analyzer page of the application.
It allows the user to input a text and have it tokenized and displayed with furigana.
The user can then click on the tokens to get more information about them.

## Variables

### TextPage

```ts
const TextPage: React.FC;
```

Defined in: [src/pages/TextPage.tsx:27](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/pages/TextPage.tsx#L27)

The TextPage component.

This component is responsible for the following:

- Allowing the user to input a text.
- Tokenizing the text and displaying it as a series of clickable tokens.
- Displaying furigana above the tokens.
- Allowing the user to toggle the visibility of the furigana.
- Displaying a dialog with more information about a token when it is clicked.

#### Returns

The TextPage component.
