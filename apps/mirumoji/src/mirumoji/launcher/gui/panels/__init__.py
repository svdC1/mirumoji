"""
Defines Flet Panels For The Mirumoji GUI

Each module defines a single panel (`ft.Column`) containing functionality
similar to that of a Mirumoji CLI command

Since the GUI is supposed to hold a persistent state across panels
(`AppState`), it uses a desktop sidebar application layout with a fixed
`ft.NavigationRail` that re-renders a `ft.AnimatedSwitcher` body with the
relevant panel upon clicking a destination. This sub-package defines the
panels that are rendered for each one of the destinations
"""
