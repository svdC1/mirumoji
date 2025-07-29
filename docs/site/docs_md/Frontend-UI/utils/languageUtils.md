This file contains utility functions for working with Japanese characters.

## Functions

### isKanji()

```ts
function isKanji(char): boolean;
```

Defined in: [src/utils/languageUtils.ts:11](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/languageUtils.ts#L11)

Checks if a character is a Kanji character.

#### Parameters

| Parameter | Type     | Description             |
| --------- | -------- | ----------------------- |
| `char`    | `string` | The character to check. |

#### Returns

`boolean`

True if the character is a Kanji character, false otherwise.

---

### toHiragana()

```ts
function toHiragana(text): string;
```

Defined in: [src/utils/languageUtils.ts:23](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/languageUtils.ts#L23)

Converts a string from Katakana to Hiragana.

#### Parameters

| Parameter | Type     | Description            |
| --------- | -------- | ---------------------- |
| `text`    | `string` | The string to convert. |

#### Returns

`string`

The converted string.
