This is the root component of the application.
It sets up the main layout and routing, and wraps the application
in necessary context providers.

## Functions

### App()

```ts
function App(): Element;
```

Defined in: [src/App.tsx:28](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/App.tsx#L28)

The main application component.

It renders the navigation menu and sets up the routes for the different pages.
It also wraps the entire application in the `PlayerProvider` to make the player's
state globally accessible and persistent across navigation.

#### Returns

`Element`

The main application component.
