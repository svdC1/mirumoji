# Sharing Outside of Local Network

???+ question "When do I need to do this?"

    You only need to do this if you want to let someone outside of your local network access the application, or access it outside your local network yourself.

???+ tip "Proposed Solution"

    There are many ways you can expose the application to the internet, This guide instructs on setting it up with **[`Zrok`](https://zrok.io/) since it's open-source and offers a fast and efficient SaaS implementation with 5Gb of traffic free per day which works on all platforms.**

???+ info "Self Hosting (Optional)"

    Zrok also **offers you the ability to run a completely self-hosted version of the Zrok application if you don't want to use the SaaS**. Since the free quota of 5Gb per day should be enough for most users, and for the sake of simplicity, **this guide instructs you on running the SaaS pre-configured version. If you'd like to set up the self-hosted version on your own you can access their [`Self Hosting Guides`](https://docs.zrok.io/docs/category/self-hosting/)**

---

## Prerequisites

Your application is running in Docker and is reachable at your [`localhost`](https://localhost).

---

## Installation

### **Install Zrok**

1. Open the [`Zrok Website`](https://docs.zrok.io/docs/getting-started). You can read information about the service there and find the download and instructions for your system.

2. **Create a Free Account**:

    In the [`Getting Started`](https://docs.zrok.io/docs/getting-started) page, you’ll see options for Self-Hosting the service or using the SaaS implementation. This guide is for the SaaS implementation. Click on [`Create an Account`](https://myzrok.io/)

3. **Activate the CLI Once**:

    After you create an account and verify your email, you’ll receive a token.

    After downloading the Zrok binary for your platform, you’ll need to run this command once to store the token which allows connection with your account

    ```bash
    zrok enable <PASTE‑YOUR‑TOKEN>
    ```

---

## Starting the Service

### Start a Share with Basic‑Auth

> By running the command below, Zrok will proxy all requests between the generated HTTPS website and your local application.

```bash
# Replace user:pass with any credentials you like
zrok share public 443 --basic-auth user:pass
```

???+ tip 
    Setting up this `user` and `password` is optional. However, even though the URL is random and the chance of it accidentally getting found out by someone on the internet is minimal, this extra step to dismiss snoopers is recommended since the app will be globally available.

> The command will give you a random URL like `https://curly‑iguana‑27.share.zrok.io` which you can access from anywhere.

??? warning
    The first time you access you’ll see a Zrok page called an [`Interstitial`](https://docs.zrok.io/docs/guides/self-hosting/interstitial-page/) which is there for safety and to warn users that this is a Zrok Proxy. You can just click a button to dismiss it.

> Leave this terminal **open** while you want to share the application over the internet.

### Access From Any Device

???+ info
    > If you've setup `username` and `password` you'll be prompted them before the website loads
    > Enter the `username` and `password` you chose.

> With this you have a password protected website running the application which is accessible from anywhere.

??? warning 
    The free tier allows **5 GB of traffic per 24 h** and auto‑resets each day. You can check your usage at the [`Zrok Dashboard`](https://myzrok.io/dashboard)

---

## Stopping the Service

> Press **Ctrl +C** in the zrok window. The link stops working instantly. Run the share command again any time to get a fresh URL.

---
