This file contains a function for displaying API errors as toasts.

## Functions

### toastApiError()

```ts
function toastApiError(err, toastId?): void;
```

Defined in: [src/utils/apiErrorToaster.tsx:15](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/apiErrorToaster.tsx#L15)

Displays an API error as a toast.

#### Parameters

| Parameter  | Type      | Description                    |
| ---------- | --------- | ------------------------------ |
| `err`      | `unknown` | The error to display.          |
| `toastId?` | `string`  | The ID of the toast to update. |

#### Returns

`void`
