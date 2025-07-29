This file contains utility functions for working with files.

## Functions

### formatStaticUrl()

```ts
function formatStaticUrl(API_BASE, url): string;
```

Defined in: [src/utils/fileUtils.ts:46](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/fileUtils.ts#L46)

Formats a static URL for the API

#### Parameters

| Parameter  | Type     | Description                             |
| ---------- | -------- | --------------------------------------- |
| `API_BASE` | `string` | The base URL of the API. (`/` included) |
| `url`      | `string` | The URL to format.                      |

#### Returns

`string`

The formatted URL.

---

### getFileExtension()

```ts
function getFileExtension(filenameOrUrl): string;
```

Defined in: [src/utils/fileUtils.ts:33](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/fileUtils.ts#L33)

Gets the extension of a file.

#### Parameters

| Parameter       | Type                    | Description                                    |
| --------------- | ----------------------- | ---------------------------------------------- |
| `filenameOrUrl` | `undefined` \| `string` | The filename or URL to get the extension from. |

#### Returns

`string`

The file extension.

---

### truncateFilename()

```ts
function truncateFilename(filename, startChars?, endChars?): string;
```

Defined in: [src/utils/fileUtils.ts:13](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/fileUtils.ts#L13)

Truncates a filename to a specified length.

#### Parameters

| Parameter     | Type                    | Default value | Description                                                        |
| ------------- | ----------------------- | ------------- | ------------------------------------------------------------------ |
| `filename`    | `undefined` \| `string` | `undefined`   | The filename to truncate.                                          |
| `startChars?` | `number`                | `8`           | The number of characters to keep at the beginning of the filename. |
| `endChars?`   | `number`                | `4`           | The number of characters to keep at the end of the filename.       |

#### Returns

`string`

The truncated filename.

---

### truncateText()

```ts
function truncateText(text, maxLength?): string;
```

Defined in: [src/utils/fileUtils.ts:57](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/utils/fileUtils.ts#L57)

Truncates a string to a specified length.

#### Parameters

| Parameter    | Type                    | Default value | Description                       |
| ------------ | ----------------------- | ------------- | --------------------------------- |
| `text`       | `undefined` \| `string` | `undefined`   | The string to truncate.           |
| `maxLength?` | `number`                | `50`          | The maximum length of the string. |

#### Returns

`string`

The truncated string.
