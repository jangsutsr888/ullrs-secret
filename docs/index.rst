Ullr's Secret documentation
============================

Ullr's Secret is a command-line snow-surface forecaster for backcountry
skiing. It imports hourly weather, estimates the effective temperature of a
specific slope, and produces charts for powder preservation, corn timing, and
melt-freeze consolidation.

The central question is not simply "What is the air temperature?" It is
"What thermal load does the snow surface experience after humidity, radiation,
elevation, slope, and aspect are accounted for?"

Quick example
-------------

.. code-block:: console

   $ python3 -m venv .venv
   $ source .venv/bin/activate
   $ python -m pip install --upgrade pip
   $ python -m pip install ullrs-secret
   $ ullrs-secret import openmeteo --lat 46.8523 --lon -121.7603 \
       --model best_match --output weather_data.json
   $ ullrs-secret corn-plot weather_data.json --slope 35 --aspect 135 \
       --elevation 9000 --no-show --output corn_forecast_chart.png

The import command writes the standard weather JSON contract. Any of the
three chart commands can then consume that file.

Documentation map
-----------------

* :doc:`installation` is the installation and verification runbook.
* :doc:`getting-started` covers the normal command workflow.
* :doc:`model` explains wet-bulb and radiative effective temperature.
* Chart commands: :doc:`charts/pow-plot`, :doc:`charts/corn-plot`, and
  :doc:`charts/consolidation-plot` each have a dedicated principle-and-usage
  page.
* Import sources: :doc:`importers/openmeteo`, :doc:`importers/nws`, and
  :doc:`importers/era5` each have a dedicated source page.
* :doc:`reference/weather-format` defines the importer-to-model data contract.
* :doc:`limitations` explains where the model should and should not be trusted.
* :doc:`feedback` explains how to report bugs, request improvements, and share
  field feedback.

.. warning::

   Ullr's Secret is a surface-condition decision aid, not an avalanche
   forecast. It does not model buried weak layers, wind slabs, terrain traps,
   or local avalanche hazard. Use the appropriate avalanche-center forecast,
   field observations, and conservative travel practices.

.. toctree::
   :maxdepth: 3
   :caption: User guide

   installation
   getting-started
   model
   charts/index
   importers/index
   limitations
   feedback

.. toctree::
   :maxdepth: 3
   :caption: Reference

   reference/weather-format
   reference/terrain-snotel
   reference/python-api
