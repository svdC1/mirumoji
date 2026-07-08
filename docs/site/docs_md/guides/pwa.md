# Installing The App (PWA)

`Mirumoji` is a [`Progressive Web App`](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps), meaning that, on any device, it can be installed like a native app (with its own icon and window) and cache its interface for instant loads

???+ question "Why Is There An Extra Step"
    - Browsers only register the [`service worker`](https://web.dev/learn/pwa/service-workers?hl=en#register) that powers installation and offline caching on a `fully trusted HTTPS origin`

    - On the machine running Mirumoji, `https://localhost` is automatically trusted, so no extra step is needed there

    - Other devices on your network reach Mirumoji through the certificate it generates for your LAN IP, and since that certificate is issued by Mirumoji's own [`local certificate authority (CA)`](https://securew2.com/blog/public-vs-private-certificate-authority) rather than a public one, each device must trust that CA `once`

    - Clicking through the browser's `connection is not private` warning is enough to `use` Mirumoji, but not enough for the browser to allow the service worker, so the app stays non-installable until the `CA` is trusted

## Get The Certificate

The `CA` certificate is served by your Mirumoji instance at

```
http://<your-machine-LAN-IP>/mirumoji-ca.crt
```

The exact URL (with your IP filled in) is printed by `mirumoji up` and shown in the desktop launcher when the app starts

???+ info "What You Are Trusting"
    - The CA is generated `on your machine` by the frontend container when it first starts, and never leaves it except through this download

    - It is stored in a `Docker Volume`, so it survives restarts and updates (devices stay trusted)

    - Trusting it means your devices will accept certificates signed by `your` Mirumoji instance

    - Treat the file like a credential and don't share it outside your household

## Install It Per Device

=== "Windows"

    - Download the certificate, double-click it, and choose `Install Certificate`

    - Select `Local Machine` &rarr; `Place all certificates in the following store` &rarr; `Trusted Root Certification Authorities`

    - Restart the browser

=== "macOS"

    - Download the certificate and double-click it to add it to `Keychain Access`

    - In `Keychain Access`, find `Mirumoji Local CA`

    - Open it, expand `Trust`, and set `When using this certificate` to `Always Trust`

    - Restart the browser

=== "iOS / iPadOS"

    - Open the certificate URL in `Safari` and allow the configuration profile download

    - Go to `Settings` &rarr; `General` &rarr; `VPN & Device Management`

    - Select the `Mirumoji Local CA` profile and install it

    - Go to `Settings` &rarr; `General` &rarr; `About` &rarr; `Certificate Trust Settings`

    - Enable `Full Trust` for `Mirumoji Local CA` *(Without this step iOS doesn't trust it)*

    - Re-open the site in Safari and use `Share` &rarr; `Add to Home Screen`

=== "Android"

    - Download the certificate

    - Go to `Settings` &rarr; `Security & privacy` &rarr; `More security settings` &rarr; `Install from device storage` &rarr; `CA certificate` *(Naming varies slightly by vendor)* and pick the downloaded file

    - Re-open the site in Chrome and use `Install App` from the menu

=== "Firefox (Any Platform)"

    - Firefox keeps its own certificate store

    - Go to `Settings` &rarr; `Privacy & Security` &rarr; `Certificates` &rarr; `View Certificates` &rarr; `Authorities` &rarr; `Import`, pick the file, and check `Trust this CA to identify websites`

## Verify

- Open `https://<your-machine-LAN-IP>` on the device

- The certificate warning should be gone, and the browser should offer to `Install` the app *(Chrome / Edge show an install icon in the address bar, Safari uses `Add to Home Screen`)*

## Alternatives

If you would rather not install a `CA` on your devices, any setup that puts a `publicly trusted` certificate in front of Mirumoji achieves the same result

- [`Tailscale Serve`](sharing.md#tailscale-private-access) &rarr; A trusted certificate via your private tailnet name, no ports opened

- A reverse proxy you already run *(`Caddy`, `Traefik`, `Nginx Proxy Manager`)* with a real domain and a `Let's Encrypt` certificate

- [`Cloudflare Tunnel`](sharing.md#cloudflare-tunnel-public-sharing) when sharing with other people
