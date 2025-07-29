This file provides a context for managing the user's profile.

## Interfaces

### ProfileContextType

Defined in: [src/contexts/ProfileContext.tsx:19](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/ProfileContext.tsx#L19)

The context for managing the user's profile.

#### Properties

| Property                                 | Type               | Description                                    | Defined in                                                                                                                                                              |
| ---------------------------------------- | ------------------ | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="profileid"></a> `profileId`       | `null` \| `string` | The ID of the current profile.                 | [src/contexts/ProfileContext.tsx:20](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/ProfileContext.tsx#L20) |
| <a id="setprofileid"></a> `setProfileId` | (`id`) => `void`   | A function for setting the current profile ID. | [src/contexts/ProfileContext.tsx:21](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/ProfileContext.tsx#L21) |

## Variables

### ProfileProvider

```ts
const ProfileProvider: React.FC<{
  children: ReactNode;
}>;
```

Defined in: [src/contexts/ProfileContext.tsx:32](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/ProfileContext.tsx#L32)

A provider for the ProfileContext.

#### Param

The props for the component.

#### Returns

The ProfileProvider component.

## Functions

### useProfile()

```ts
function useProfile(): ProfileContextType;
```

Defined in: [src/contexts/ProfileContext.tsx:63](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/contexts/ProfileContext.tsx#L63)

A hook for using the ProfileContext.

#### Returns

[`ProfileContextType`](#profilecontexttype)

The ProfileContext.
