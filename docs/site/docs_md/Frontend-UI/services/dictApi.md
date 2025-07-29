This file contains functions for querying the dictionary API.

## Functions

### apiWildcardQuery()

```ts
function apiWildcardQuery(pattern): Promise<DictWildcardLookup>;
```

Defined in: [src/services/dictApi.ts:27](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/services/dictApi.ts#L27)

Queries the dictionary API for a wildcard pattern.

#### Parameters

| Parameter | Type     | Description           |
| --------- | -------- | --------------------- |
| `pattern` | `string` | The pattern to query. |

#### Returns

[`Promise`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Promise)\<[`DictWildcardLookup`](../types/types.md#dictwildcardlookup)\>

A promise that resolves to the dictionary wilcard lookup data.

---

### apiWordQuery()

```ts
function apiWordQuery(word): Promise<DictLookup>;
```

Defined in: [src/services/dictApi.ts:14](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/services/dictApi.ts#L14)

Queries the dictionary API for a word.

#### Parameters

| Parameter | Type     | Description        |
| --------- | -------- | ------------------ |
| `word`    | `string` | The word to query. |

#### Returns

[`Promise`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Promise)\<[`DictLookup`](../types/types.md#dictlookup)\>

A promise that resolves to the dictionary lookup data.

---

### filterDictLookup()

```ts
function filterDictLookup(dictLookup): null | DictLookup;
```

Defined in: [src/services/dictApi.ts:46](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/services/dictApi.ts#L46)

Filters empty placeholders from a `DictLookup` response object
and returns `null` in case the response object is considered empty

#### Parameters

| Parameter    | Type                                                   | Description           |
| ------------ | ------------------------------------------------------ | --------------------- |
| `dictLookup` | `null` \| [`DictLookup`](../types/types.md#dictlookup) | The DictLookup object |

#### Returns

`null` \| [`DictLookup`](../types/types.md#dictlookup)

The filtered object or null

---

### filterDictWildcardLookup()

```ts
function filterDictWildcardLookup(dictLookup): null | DictWildcardLookup;
```

Defined in: [src/services/dictApi.ts:94](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/services/dictApi.ts#L94)

Filters empty placeholders from a `DictWildcardLookup` response object
and returns `null` in case the response object is considered empty

#### Parameters

| Parameter    | Type                                                                   | Description                   |
| ------------ | ---------------------------------------------------------------------- | ----------------------------- |
| `dictLookup` | `null` \| [`DictWildcardLookup`](../types/types.md#dictwildcardlookup) | The DictWildcardLookup object |

#### Returns

`null` \| [`DictWildcardLookup`](../types/types.md#dictwildcardlookup)

The filtered object or null
