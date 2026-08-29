"""Sphinx configuration for the Ullr's Secret documentation."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

project = "Ullr's Secret"
author = "Ullr's Secret contributors"
copyright = "2026, Ullr's Secret contributors"
release = "1.0.1"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
nitpicky = True

html_theme = "classic"
html_theme_options = {
    "stickysidebar": True,
    "collapsiblesidebar": False,
}
html_title = "Ullr's Secret 1.0.1 documentation"
html_short_title = "Ullr's Secret"
html_static_path = []
html_show_sourcelink = True
html_copy_source = True
html_show_sphinx = True
html_show_copyright = True
html_last_updated_fmt = "%Y-%m-%d"
html_sidebars = {
    "**": [
        "globaltoc.html",
        "localtoc.html",
        "relations.html",
        "searchbox.html",
    ]
}

autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False
