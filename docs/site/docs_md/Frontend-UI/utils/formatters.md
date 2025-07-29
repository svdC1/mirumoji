This file contains formatter functions.

## Functions

### hexToRgba()

```ts
function hexToRgba(hex, alpha): string;
```

Defined in: [src/utils/formatters.ts:24](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/formatters.ts#L24)

Converts a hex color string to an rgba color string.

#### Parameters

| Parameter | Type     | Description                         |
| --------- | -------- | ----------------------------------- |
| `hex`     | `string` | The hex color string to convert.    |
| `alpha`   | `number` | The alpha value for the rgba color. |

#### Returns

`string`

The rgba color string.

---

### toSec()

```ts
function toSec(t): number;
```

Defined in: [src/utils/formatters.ts:11](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/formatters.ts#L11)

Converts a time string in the format "hh:mm:ss,ms" to seconds.

#### Parameters

| Parameter | Type     | Description                 |
| --------- | -------- | --------------------------- |
| `t`       | `string` | The time string to convert. |

#### Returns

`number`

The time in seconds.
