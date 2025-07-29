This file contains constants for the user page.

## Variables

### API_BASE

```ts
const API_BASE: "api/" = "api/";
```

Defined in: [src/constants/user-page.ts:12](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/constants/user-page.ts#L12)

---

### defaultPrompt

```ts
const defaultPrompt: "{sentence}. Explain usage of word : {focus}\r\n";
```

Defined in: [src/constants/user-page.ts:14](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/constants/user-page.ts#L14)

---

### defaultSysMsg

```ts
const defaultSysMsg: "You are a Japanese language API that explains the specific nuance of specified word(s) in a Japanese sentence.\r\n\r\nRespond concisely in no more than 100 words.\r\n\r\nSpecified word(s) MUST be in Japanese\r\n\r\nAll other explanation text MUST be in English\r\n\r\nIn your response:\r\n\r\nDO NOT OUTPUT the language name or the word 'nuance';\r\n\r\nDO NOT OUTPUT the context sentence ;\r\n\r\nDO NOT OUTPUT romaji/furigana or any notes on pronunciation;\r\n\r\nConclude with the specific nuance within the context sentence.";
```

Defined in: [src/constants/user-page.ts:13](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/constants/user-page.ts#L13)

---

### tabs

```ts
const tabs: object[];
```

Defined in: [src/constants/user-page.ts:5](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/constants/user-page.ts#L5)

#### Type declaration

| Name    | Type     | Default value | Defined in                                                                                                                                                  |
| ------- | -------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`    | `string` | `"profile"`   | [src/constants/user-page.ts:6](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/constants/user-page.ts#L6) |
| `label` | `string` | `"Profile"`   | [src/constants/user-page.ts:6](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/constants/user-page.ts#L6) |

---

### validGptModels

```ts
const validGptModels: string[];
```

Defined in: [src/constants/user-page.ts:16](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/constants/user-page.ts#L16)
