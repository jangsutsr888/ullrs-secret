from pathlib import Path

from setuptools import find_packages, setup


PROJECT_ROOT = Path(__file__).parent
LONG_DESCRIPTION = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

setup(
    name="ullrs-secret",
    version="1.0.1",
    description="Ullr's Secret — backcountry ski snow conditions forecaster",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/jangsutsr888/ullrs-secret",
    project_urls={
        "Documentation": "https://ullrs-secret.readthedocs.io/",
        "Issues": "https://github.com/jangsutsr888/ullrs-secret/issues",
        "Source": "https://github.com/jangsutsr888/ullrs-secret",
    },
    license="AGPL-3.0-or-later",
    license_files=("LICENSE",),
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
    ],
    python_requires=">=3.10",
    packages=find_packages(include=["ullrs_secret*"]),
    install_requires=[
        "click>=8.0",
        "matplotlib>=3.8",
        "pandas>=2.2",
        "scipy==1.13.1",
        "pytz>=2024.1",
        "cdsapi",
        "xarray",
        "netCDF4",
        "numpy",
        "requests",
    ],
    extras_require={
        "test": ["pytest"],
        "docs": ["sphinx>=8,<9"],
    },
    entry_points={
        "console_scripts": [
            "ullrs-secret=ullrs_secret.cli:cli",
        ],
    },
)
