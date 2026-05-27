"""
CLI and GUI launcher for the `mirumoji` package.

Sub-packages are imported lazily so that the base CLI install (without the
``server`` or ``gui`` extras) doesn't pull in fastapi / flaskwebgui at import
time.
"""
