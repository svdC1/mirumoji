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

| Approach | Best for | Exposure |
| --- | --- | --- |
| [`Tailscale`](#recommended-tailscale-private-access) *(recommended)* | Just You + Your Own Devices | `None` &rarr; Private Encrypted Network, No Open Ports |
| [`Cloudflare Tunnel`](#alternative-cloudflare-tunnel-public-sharing) | Sharing With Other People | Public Hostname, Gated By Identity-Based Access |

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
