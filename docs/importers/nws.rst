National Weather Service
========================

Summary
-------

The NWS importer downloads the digital DWML forecast returned by the NWS
MapClick endpoint. It requires no credentials and is limited to locations
served by the United States National Weather Service.

Usage
-----

.. code-block:: console

   $ ullrs-secret import nws [OPTIONS]

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Option
     - Default
     - Meaning
   * - ``--lat FLOAT``
     - required
     - Requested latitude
   * - ``--lon FLOAT``
     - required
     - Requested longitude
   * - ``-o, --output TEXT``
     - ``weather_data.json``
     - Output JSON path

.. code-block:: console

   $ ullrs-secret import nws \
       --lat 46.8523 --lon -121.7603 \
       --output rainier_weather.json

How it works
------------

The importer requests this endpoint shape:

.. code-block:: text

   https://forecast.weather.gov/MapClick.php?lat=LAT&lon=LON&FcstType=digitalDWML

It reads the resolved NWS point, elevation, hourly valid times, hourly air
temperature, dew point, relative humidity, and total cloud cover from the XML.
The output length is the shortest of the time, air-temperature, and humidity
arrays. Optional dew-point and cloud arrays are filled with null if they end
early.

The log reports the distance and bearing from the requested coordinate to the
resolved NWS point. The resolved coordinate and its elevation are stored in the
standard JSON.

Limitations
-----------

NWS coverage is intended for the United States and associated forecast areas.
The parser is coupled to the ``k-p1h-n1-0`` DWML time layout and the current
MapClick XML structure. An upstream layout change can cause an empty or
incomplete series.

The source is a forecast product, not a station observation. Mountain terrain
between grid points may differ sharply in elevation, wind exposure, cloud, and
precipitation regime.

Troubleshooting
---------------

``Download failed``
   Confirm the coordinate is in NWS coverage and that the endpoint is
   reachable.

``XML parse failed``
   Save the response for inspection. NWS may have returned an error page or a
   document whose schema no longer matches the parser.

Very few observations
   The importer truncates to the shortest required series. Missing humidity or
   temperature data can shorten the result.

NWS source walkthrough
----------------------

The following repository screenshots show where the importer's data originates.
The current CLI performs the DWML request automatically; these manual screens
are useful for understanding and troubleshooting the upstream source.

1. Find the forecast location
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure:: ../_generated/examples/nws-base-page.png
   :alt: National Weather Service home page with Inter Glacier entered in the location search.
   :width: 100%

   Search for the intended mountain forecast point.

2. Confirm the resolved point
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure:: ../_generated/examples/nws-details-page.png
   :alt: NWS point forecast page for a location northeast of Mount Rainier.
   :width: 100%

   The saved example resolves to a point two miles northeast of Mount Rainier.
   The page exposes the ``Hourly Weather Forecast`` link.

3. Inspect the hourly fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure:: ../_generated/examples/nws-data-page.png
   :alt: NWS hourly graph showing temperature, dew point, humidity, and sky cover.
   :width: 100%

   Temperature, dew point, relative humidity, and sky cover correspond to the
   core observation fields written by the importer. The orange XML control
   exposes the digital forecast.

4. Inspect the DWML feed
~~~~~~~~~~~~~~~~~~~~~~~~

.. figure:: ../_generated/examples/nws-xml-page.png
   :alt: Raw NWS DWML showing location, elevation, and hourly valid times.
   :width: 100%

   The DWML includes the resolved coordinate, 8,730-foot elevation, hourly
   timestamps, and the parameter arrays parsed by ``ullrs-secret``.

The supported CLI path remains coordinate based:

.. code-block:: console

   $ ullrs-secret import nws \
       --lat 46.87 --lon -121.72 \
       --output weather_data.json
