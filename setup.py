from setuptools import setup, find_packages

setup(
    name="ullrs-secret",
    version="0.1.0",
    description="Ullr's Secret — backcountry ski snow conditions forecaster",
    python_requires=">=3.10",
    packages=find_packages(include=["ullrs_secret*"]),
    install_requires=[
        "click>=8.0",
        "matplotlib>=3.8",
        "pandas>=2.2",
        "scipy==1.13.1",
        "pytz>=2024.1",
    ],
    entry_points={
        "console_scripts": [
            "ullrs-secret=ullrs_secret.cli:cli",
        ],
    },
)
