Installation
============

Requirements
------------

Ullr's Secret requires Python 3.10 or newer and Git. Use a virtual environment
so that its scientific Python dependencies do not modify the system Python
installation.

Install from source
-------------------

Clone the public repository and install the package from its checked-out
source tree:

.. code-block:: console

   $ git clone https://github.com/jangsutsr888/ullrs-secret.git
   $ cd ullrs-secret
   $ python3 -m venv .venv
   $ source .venv/bin/activate
   $ python -m pip install --upgrade pip
   $ python -m pip install .

On Windows PowerShell, activate the environment with
``.venv\Scripts\Activate.ps1`` instead.

Verify the installation before fetching weather or generating charts:

.. code-block:: console

   $ ullrs-secret --help
   $ python -c "import ullrs_secret; print(ullrs_secret.__version__)"

The second command should print ``1.0.0``.

Update a source installation
----------------------------

Pull the latest ``main`` branch and reinstall it into the active virtual
environment:

.. code-block:: console

   $ git pull --ff-only
   $ python -m pip install --upgrade .

Contributor installation
------------------------

The repository Makefile creates ``venv`` and installs the package in editable
mode with the test dependencies:

.. code-block:: console

   $ make install
   $ source venv/bin/activate
   $ make test

Use ``make docs-check`` to install the documentation extra, build the Sphinx
site with warnings treated as errors, and run the documentation acceptance
checks.
