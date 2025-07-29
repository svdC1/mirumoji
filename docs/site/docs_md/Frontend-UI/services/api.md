This file contains the apiFetch function, which is a wrapper around the native fetch function.

## Functions

### apiFetch()

```ts
function apiFetch<T>(url, opts?): Promise<T>;
```

Defined in: [src/services/api.ts:21](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/services/api.ts#L21)

A fetch replacement that:

- Auto-prefixes BASE for relative URLs
- Adds X-Profile-ID header if a profile is set in localStorage
- Throws ApiError on non-2xx
- Parses JSON/text/blob based on content-type

#### Type Parameters

| Type Parameter | Default type | Description |
| -------------- | ------------ | ----------- |
| `T`            | `unknown`    |             |

#### Parameters

| Parameter | Type          | Description                        |
| --------- | ------------- | ---------------------------------- |
| `url`     | `string`      | The URL to fetch.                  |
| `opts?`   | `RequestInit` | The options for the fetch request. |

#### Returns

[`Promise`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Promise)\<`T`\>

A promise that resolves to the response data.
