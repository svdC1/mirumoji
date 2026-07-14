"""
Contains helpers to deploy a fully-functioning `mirumoji` instance to `Modal`

The shared, app-agnostic (also used for the server's Modal offload worker)
deploy lifecycle lives in `mirumoji.modal`

info: Modules
    - `host` defines the deployable `mirumoji-host` Modal app

    - `app` builds the `FastAPI` application that the `mirumoji-host` app
      serves, which contain the built frontend + the server's routers under
      `/api` to mimic the conventional Nginx deployment

    - `constants`defines all pre-defined values used by the deploy and app
      construction process

    - `auth` provides an `HTTP Basic Auth` gate that prevents unauthorized
      access to the deployed `mirumoji-host` app
"""
