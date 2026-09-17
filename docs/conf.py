# Configuration file for the Sphinx documentation builder.

# -- Project information

import sys
from pathlib import Path

# I don't understand how to solve Pydantic + Sphinx mess properly
# os.environ["PROJECT_NAME"] = ""
# os.environ["TWITCH_CLIENT_ID"] = ""
# os.environ["TWITCH_CLIENT_SECRET"] = ""
# os.environ["POSTGRES_VPS"] = ""
# os.environ["POSTGRES_HOME"] = ""
# os.environ["STEAM_FRIEND_IRENE_ID64"] = "1"
# os.environ["STEAM_FRIEND_IRENE_ID32"] = "1"
# os.environ["STEAM_IRENESTEST_USERNAME"] = ""
# os.environ["STEAM_IRENESTEST_PASSWORD"] = ""
# os.environ["STEAM_IRENESBOT_USERNAME"] = ""
# os.environ["STEAM_IRENESBOT_PASSWORD"] = ""
# os.environ["STRATZ_BEARER"] = ""
# os.environ["STEAM_API_KEY"] = ""
# os.environ["SEVEN_TV_BEARER"] = ""
# os.environ["SPOTIFY_AIDENWALLIS"] = ""
# os.environ["EVENTSUB"] = ""
# os.environ["WEBHOOK_LOGGER"] = ""
# os.environ["WEBHOOK_ERROR"] = ""
# os.environ["WEBHOOK_STREAM_NOTIFS"] = ""
# os.environ["WEBHOOK_HEARTBEAT"] = ""
# os.environ["WEBHOOK_HEARTBEAT"] = ""

sys.path.insert(0, str(Path("..", "src").resolve()))

project = "IreBot"
copyright = "2020, Aluerie"
author = "Aluerie"

release = "0.1"
version = "0.1.0"


# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# -- Options for HTML output

html_theme = "shibuya"
# html_theme = "sphinx_rtd_theme"

# -- Options for EPUB output
epub_show_urls = "footnote"
