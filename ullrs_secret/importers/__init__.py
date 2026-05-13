"""Extensible weather data importers.

Each importer fetches raw weather data from a source and returns it in a
standard dict format::

    {
        "source": "<importer_name>",
        "elevation_ft": <float>,
        "observations": [
            {
                "time_iso": "<ISO-8601 timestamp with timezone>",
                "air_temp_f": <float|null>,
                "relative_humidity_pct": <float|null>,
            },
            ...
        ],
    }
"""

_REGISTRY = {}


def register(name, decorators):
    def wrapper(fn):
        _REGISTRY[name] = {"fetch": fn, "decorators": decorators}
        return fn
    return wrapper


def get_importer(name):
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown importer: {name!r}. Available: {available}")
    return _REGISTRY[name]


def list_importers():
    return sorted(_REGISTRY)


def get_registry():
    return dict(_REGISTRY)


from . import nws  # noqa: E402, F401
from . import era5  # noqa: E402, F401
from . import openmeteo  # noqa: E402, F401
