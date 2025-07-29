This file contains the tokenizer for the application.

## Type Aliases

### IpadicFeatures

```ts
type IpadicFeatures = kuromoji.IpadicFeatures;
```

Defined in: [src/services/tokenizer.ts:6](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/services/tokenizer.ts#L6)

---

### KuromojiTokenizer

```ts
type KuromojiTokenizer = kuromoji.Tokenizer<IpadicFeatures>;
```

Defined in: [src/services/tokenizer.ts:7](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/services/tokenizer.ts#L7)

## Functions

### getTokenizer()

```ts
function getTokenizer(): Promise<KuromojiTokenizer>;
```

Defined in: [src/services/tokenizer.ts:25](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/services/tokenizer.ts#L25)

Gets the Kurmoji tokenizer with the `DICT_PATH` constant set

#### Returns

[`Promise`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Promise)\<[`KuromojiTokenizer`](#kuromojitokenizer)\>

A promise that resolves to the tokenizer.
