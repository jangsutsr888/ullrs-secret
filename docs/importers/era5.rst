ERA5 reanalysis
===============

Summary
-------

The ERA5 importer retrieves historical hourly single-level reanalysis from the
Copernicus Climate Data Store. Use it to reconstruct past snow-surface loading,
not for a current operational forecast.

Prerequisites
-------------

Create a Copernicus Climate Data Store account, accept the terms for the ERA5
single-level dataset, and configure ``cdsapi`` credentials in the standard
location expected by ``cdsapi.Client()``. The Python dependencies are installed
by ``make install``.

Credential format and dataset terms are managed by Copernicus and can change;
follow the current CDS API setup instructions for your account rather than
copying credentials into the repository.

Usage
-----

.. code-block:: console

   $ ullrs-secret import era5 [OPTIONS]

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
   * - ``--start-date YYYY-MM-DD``
     - required
     - First local calendar date
   * - ``--end-date YYYY-MM-DD``
     - required
     - Last local calendar date
   * - ``--timezone TEXT``
     - ``America/Los_Angeles``
     - IANA zone used to define the local date window
   * - ``-o, --output TEXT``
     - ``weather_data.json``
     - Output JSON path

.. code-block:: console

   $ ullrs-secret import era5 \
       --lat 46.8523 --lon -121.7603 \
       --start-date 2025-04-10 --end-date 2025-04-15 \
       --timezone America/Los_Angeles \
       --output rainier_era5.json

How the request is built
------------------------

The importer requests ``reanalysis-era5-single-levels`` for all 24 UTC hours
and these variables:

* 2 m temperature;
* 2 m dew-point temperature;
* total cloud cover;
* geopotential.

It builds a bounding box 0.2 degrees north, south, east, and west of the target,
then selects the nearest grid point from the returned NetCDF file. One extra
UTC day is fetched to ensure that the requested local end date is covered. The
dataframe is then filtered strictly to the requested local calendar dates.

Kelvin values are converted to Fahrenheit. Relative humidity is derived from
air temperature and dew point. Cloud fraction is converted to percent.
Geopotential is converted to elevation with standard gravity, and the resolved
grid coordinate and elevation are stored in the JSON.

Temporary files and caching
---------------------------

The downloaded NetCDF file is created with the operating system's temporary
file mechanism and removed in a ``finally`` block. Completed results are cached
in memory for 1,800 seconds within the current Python process.

Limitations
-----------

ERA5 is a gridded reconstruction. It can be useful for regional historical
comparison, but its grid cannot resolve a specific couloir, treeline opening,
or summit microclimate. Retrievals may be slow and CDS may queue large
requests. Keep date ranges focused.
