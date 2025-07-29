This file contains specialized components for displaying different types of dictionary data,
such as JMdict entries, proper noun entries, and Kanji information.

## Functions

### ComprehensiveEntryCard()

```ts
function ComprehensiveEntryCard(props): Element;
```

Defined in: [src/components/DictDisplays.tsx:155](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/components/DictDisplays.tsx#L155)

A comprehensive card that displays multiple JMdict entries, JMnedict entries, Kanji information, and examples
in a well-divided, responsive card with a tabbed interface.

#### Parameters

| Parameter               | Type                                                                                                                                                                                                                                 | Description                         |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------- |
| `props`                 | \{ `examples`: `string`[]; `jmdictEntries`: [`JMEntry`](../types/types.md#jmentry)[]; `jmnedictEntries`: [`JMNEntry`](../types/types.md#jmnentry)[]; `kanjiInfo`: [`KanjiInfo`](../types/types.md#kanjiinfo)[]; `word`: `string`; \} | The component props.                |
| `props.examples`        | `string`[]                                                                                                                                                                                                                           | The example sentences.              |
| `props.jmdictEntries`   | [`JMEntry`](../types/types.md#jmentry)[]                                                                                                                                                                                             | The standard dictionary entries.    |
| `props.jmnedictEntries` | [`JMNEntry`](../types/types.md#jmnentry)[]                                                                                                                                                                                           | The proper noun dictionary entries. |
| `props.kanjiInfo`       | [`KanjiInfo`](../types/types.md#kanjiinfo)[]                                                                                                                                                                                         | The Kanji information.              |
| `props.word`            | `string`                                                                                                                                                                                                                             | The word that was looked up.        |

#### Returns

`Element`

The rendered comprehensive card.

---

### ExampleDisplay()

```ts
function ExampleDisplay(props): Element;
```

Defined in: [src/components/DictDisplays.tsx:47](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/components/DictDisplays.tsx#L47)

Displays an example sentence.

#### Parameters

| Parameter       | Type                                            | Description                                                         |
| --------------- | ----------------------------------------------- | ------------------------------------------------------------------- |
| `props`         | \{ `example`: `string`; `isLast`: `boolean`; \} | The component props.                                                |
| `props.example` | `string`                                        | The example sentence text.                                          |
| `props.isLast`  | `boolean`                                       | True if this is the last item in a list, to omit the bottom border. |

#### Returns

`Element`

The rendered example.

---

### JmdictEntryDisplay()

```ts
function JmdictEntryDisplay(props): Element;
```

Defined in: [src/components/DictDisplays.tsx:16](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/components/DictDisplays.tsx#L16)

Displays a standard dictionary entry from JMdict.

#### Parameters

| Parameter      | Type                                                                        | Description                                                         |
| -------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `props`        | \{ `entry`: [`JMEntry`](../types/types.md#jmentry); `isLast`: `boolean`; \} | The component props.                                                |
| `props.entry`  | [`JMEntry`](../types/types.md#jmentry)                                      | The dictionary entry data.                                          |
| `props.isLast` | `boolean`                                                                   | True if this is the last item in a list, to omit the bottom border. |

#### Returns

`Element`

The rendered JMdict entry.

---

### JMEntryRow()

```ts
function JMEntryRow(props): Element;
```

Defined in: [src/components/DictDisplays.tsx:335](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/components/DictDisplays.tsx#L335)

Renders a clickable row for a JMdict entry.

#### Parameters

| Parameter        | Type                                                                                   | Description                           |
| ---------------- | -------------------------------------------------------------------------------------- | ------------------------------------- |
| `props`          | \{ `entry`: [`JMEntry`](../types/types.md#jmentry); `onSelect`: (`word`) => `void`; \} | The component props.                  |
| `props.entry`    | [`JMEntry`](../types/types.md#jmentry)                                                 | The JMdict entry.                     |
| `props.onSelect` | (`word`) => `void`                                                                     | Callback for when the row is clicked. |

#### Returns

`Element`

The JMdict entry row component.

---

### JmnedictEntryDisplay()

```ts
function JmnedictEntryDisplay(props): Element;
```

Defined in: [src/components/DictDisplays.tsx:72](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/components/DictDisplays.tsx#L72)

Displays a proper noun dictionary entry from JMnedict.

#### Parameters

| Parameter      | Type                                                                          | Description                                                         |
| -------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `props`        | \{ `entry`: [`JMNEntry`](../types/types.md#jmnentry); `isLast`: `boolean`; \} | The component props.                                                |
| `props.entry`  | [`JMNEntry`](../types/types.md#jmnentry)                                      | The proper noun entry data.                                         |
| `props.isLast` | `boolean`                                                                     | True if this is the last item in a list, to omit the bottom border. |

#### Returns

`Element`

The rendered JMnedict entry.

---

### KanjiInfoDisplay()

```ts
function KanjiInfoDisplay(props): Element;
```

Defined in: [src/components/DictDisplays.tsx:96](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/components/DictDisplays.tsx#L96)

Displays detailed information about a single Kanji character.

#### Parameters

| Parameter         | Type                                                                                | Description                                                         |
| ----------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `props`           | \{ `isLast`: `boolean`; `kanjiInfo`: [`KanjiInfo`](../types/types.md#kanjiinfo); \} | The component props.                                                |
| `props.isLast`    | `boolean`                                                                           | True if this is the last item in a list, to omit the bottom border. |
| `props.kanjiInfo` | [`KanjiInfo`](../types/types.md#kanjiinfo)                                          | The Kanji information object.                                       |

#### Returns

`Element`

The rendered Kanji information display.

---

### KanjiRow()

```ts
function KanjiRow(props): Element;
```

Defined in: [src/components/DictDisplays.tsx:385](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/components/DictDisplays.tsx#L385)

Renders a clickable row for a Kanji character.

#### Parameters

| Parameter        | Type                                                                                       | Description                           |
| ---------------- | ------------------------------------------------------------------------------------------ | ------------------------------------- |
| `props`          | \{ `kanji`: [`KanjiInfo`](../types/types.md#kanjiinfo); `onSelect`: (`word`) => `void`; \} | The component props.                  |
| `props.kanji`    | [`KanjiInfo`](../types/types.md#kanjiinfo)                                                 | The Kanji information.                |
| `props.onSelect` | (`word`) => `void`                                                                         | Callback for when the row is clicked. |

#### Returns

`Element`

The Kanji row component.

---

### WildcardResults()

```ts
function WildcardResults(props): Element;
```

Defined in: [src/components/DictDisplays.tsx:252](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/components/DictDisplays.tsx#L252)

Displays the tabbed results from a wildcard search.

#### Parameters

| Parameter            | Type                                                                                                               | Description                                 |
| -------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------- |
| `props`              | \{ `onWordSelect`: (`word`) => `void`; `results`: [`DictWildcardLookup`](../types/types.md#dictwildcardlookup); \} | The component props.                        |
| `props.onWordSelect` | (`word`) => `void`                                                                                                 | Callback to handle when a word is selected. |
| `props.results`      | [`DictWildcardLookup`](../types/types.md#dictwildcardlookup)                                                       | The wildcard search results.                |

#### Returns

`Element`

The wildcard results component.
