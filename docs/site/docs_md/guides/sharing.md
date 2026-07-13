# Sharing Outside Your Network

By default `Mirumoji` is reachable only on your own machine and local network

This guide covers making it available on external networks so that you can access it from anywhere

???+ question "Do I Need This"
    - If every device that uses Mirumoji is on the same Wi-Fi/LAN, you don't need
    any of this

    - Just use `https://<your-machine-LAN-IP>`

## Choosing An Approach

- The old recommendation here was creating a public tunnel using `Zrok` that exposes a random
  public URL guarded by basic auth

- That works, but if the credentials you setup are weak, it makes your instance reachable by `anyone who learns the URL`

- For a personal immersion tool, a `private overlay network` is both simpler and far safer

- `Tailscale` and `Cloudflare Tunnel` expose the instance running `on your machine`. The [`Modal Host`](#modal-host-private-full-deploy) is different &rarr; it runs a separate private copy of Mirumoji `in the cloud`, so your machine doesn't have to stay on at all

| Approach | Best For | Exposure |
| --- | --- | --- |
| [`Tailscale`](#tailscale-private-access) *(recommended)* | Just You + Your Own Devices | `None` &rarr; Private Encrypted Network, No Open Ports |
| [`Modal Host`](#modal-host-private-full-deploy) | Access From Anywhere Without Keeping A Machine On | A Private Cloud Deploy, Gated By A Login |
| [`Cloudflare Tunnel`](#cloudflare-tunnel-public-sharing) | Sharing With Other People | Public Hostname, Gated By Identity-Based Access |

---

## Tailscale (Private Access)

[`Tailscale`](https://tailscale.com) builds a private, end-to-end-encrypted
(WireGuard) network between your devices

Your `Mirumoji` machine and your phone or laptop join the same `tailnet` and talk directly &rarr; Nothing is exposed to the public internet, and no ports are opened

It's `free` for personal use and runs on every platform

### Steps


### On The Machine Running Mirumoji

- [`Download Tailscale`](https://tailscale.com/download) And Sign In To Create Your `Tailnet`

- Find Your Machine's Tailscale Address

???+ tip "Linux Example"
    ```bash
    curl -fsSL https://tailscale.com/install.sh | sh
    sudo tailscale up
    tailscale ip -4  # 100.101.102.103
    ```

### On The Device You Want To Access

-  [`Download Tailscale`](https://tailscale.com/download) And Sign In With The `Same Account` As Above

- Open Your Tailscale Address (e.g `https://100.101.102.103`)




!!! warning "Certificate Warning"
    - Mirumoji's self-signed certificate is issued for your `LAN IP`, so reaching it
      by `Tailscale IP` shows the same one-time "not private" warning as on the LAN

      - To remove the warning, use the `Tailscale Serve` approach below

???+ tip "Removing The Certificate Warning"
    - [`Tailscale Serve`](https://tailscale.com/kb/1242/tailscale-serve) can put a valid HTTPS certificate (via your `*.ts.net` MagicDNS name) in front of Mirumoji

    - To use it, Run the command below on the machine running Mirumoji

    ```bash
    # Proxy your tailnet HTTPS name to the local frontend
    tailscale serve --bg https+insecure://localhost:443
    ```

    - You can then reach Mirumoji at `https://<machine-name>.<tailnet>.ts.net` with a trusted certificate

    - Flags vary slightly by Tailscale version. See the [`Tailscale Serve Docs`](https://tailscale.com/kb/1242/tailscale-serve)

---

## Modal Host (Private Full Deploy)

Instead of exposing the instance on your machine, [`mirumoji modal deploy`](../setup/modal-host.md) runs a `separate`, private copy of the whole app on your own [`Modal`](https://modal.com) account. Your machine does not have to stay on, and there is nothing to tunnel

See the [`Modal Host Setup Guide`](../setup/modal-host.md) for the full walkthrough. This section covers `only` how its access model compares to the options here

The deployed app is gated by `HTTP Basic Auth` *(a browser login prompt)*, the same mechanism that this guide cautions against for `Zrok`. That caution still holds for a public tunnel, but the Modal host is a bit more reliable

???+ question "Why Basic Auth Is Used Here"
    The main reason is that it's the only way to gate a mirumoji instance running in the cloud without   implementing auth tooling (login page, cookies / session store) to an application that was mainly
    built to run as a *self-hosted* tool

???+ info "How It Works"
    - A `401` response with a `WWW-Authenticate: Basic` header makes the browser show its own login prompt

    - Once you log in, the browser attaches the credentials to `every` later request automatically *(the page, the assets, the API, and the uploads)*

    - So one gate covers the whole app with no login page, cookie, or session store, which is why the server and frontend need no changes

??? question "Why It's More Reliable"
    - `mirumoji modal deploy` can automatically generate a strong password for you *(`--generate-password`)*, which removes that specific footgun

    - `Credentials Are Always Encrypted` &rarr; Modal serves everything over HTTPS with a real, publicly trusted certificate, so the login is never sent in the clear *(the `Zrok` caution was about a shared password being the only gate on a public URL)*


!!! tip "Identity-Based Access Instead"
    If you would rather log in with `Google` / `GitHub` / `Email Codes`, the same upgrade applies as with a tunnel &rarr; Put [`Cloudflare Access`](#cloudflare-tunnel-public-sharing) in front of the Modal URL. For non-browser clients, Modal's own proxy tokens are also an option

---

## Cloudflare Tunnel (Public Sharing)

If you need to share `Mirumoji` with `other people` who won't install Tailscale, [`Cloudflare Tunnel`](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
can give you a stable public hostname `without opening any inbound ports`

It lets you put [`Cloudflare Access`](https://developers.cloudflare.com/cloudflare-one/policies/access/)
(Identity-Based Login &rarr; `Google`, `GitHub`, `Email Codes`) in front of `Mirumoji`, which is an improvement over a random URL with shared basic-auth (`Zrok`)

You'll need a domain managed in Cloudflare (`Free Plan` Is Fine)

### Steps

### Install

Install `cloudflared` on the machine running `Mirumoji` + Authenticate

```bash
cloudflared tunnel login
cloudflared tunnel create mirumoji
```

### Route

Route a hostname to the tunnel and point it at the local frontend

Since the frontend uses a self-signed certificate, tell the connector not to verify the origin certificate

```yaml title="~/.cloudflared/config.yml"
tunnel: mirumoji
credentials-file: /home/you/.cloudflared/<TUNNEL-ID>.json
ingress:
  - hostname: mirumoji.example.com
    service: https://localhost:443
    originRequest:
      noTLSVerify: true
  - service: http_status:404
```

```bash
cloudflared tunnel route dns mirumoji mirumoji.example.com
cloudflared tunnel run mirumoji
```

### Setup

In the Cloudflare dashboard, add a `Zero Trust` &rarr; `Access` application for
`mirumoji.example.com` and a policy, for example, allow only your email

Now anyone visiting must authenticate first


???+ danger "You Are Publishing A Service"
    - A public tunnel makes `Mirumoji` reachable from the internet

    - Always keep an `Access Policy` in front of it

    - Remember that anyone you allow can `read` and `modify` the profiles, media, and
      clips on your machine

### Stopping

Stop `cloudflared` (Ctrl+C) and the public hostname goes offline immediately
