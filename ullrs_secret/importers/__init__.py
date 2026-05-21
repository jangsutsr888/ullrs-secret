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


def fetch_weather(source: str, **kwargs) -> dict:
    """
    Fetch weather data using the specified importer source.
    
    :param source: The name of the importer to use (e.g., 'nws', 'era5', 'openmeteo').
    :type source: str
    :param kwargs: Arguments passed directly to the specific importer's fetch function.
    :return: A dictionary containing standard weather JSON data.
    :rtype: dict
    """
    importer = get_importer(source)
    return importer["fetch"](**kwargs)


from ullrs_secret.importers import nws  # noqa: E402, F401
from ullrs_secret.importers import era5  # noqa: E402, F401
from ullrs_secret.importers import openmeteo  # noqa: E402, F401
