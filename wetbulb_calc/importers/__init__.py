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


def register(name):
    def decorator(fn):
        _REGISTRY[name] = fn
        return fn
    return decorator


def get_importer(name):
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown importer: {name!r}. Available: {available}")
    return _REGISTRY[name]


def list_importers():
    return sorted(_REGISTRY)


from . import nws  # noqa: E402, F401
