from setuptools import setup, find_packages

setup(
    name="wetbulb-calc",
    version="0.1.0",
    description="Wet bulb temperature calculator for backcountry ski forecasting",
    python_requires=">=3.10",
    packages=find_packages(include=["wetbulb_calc*"]),
    install_requires=[
        "click>=8.0",
        "matplotlib>=3.8",
        "pandas>=2.2",
        "scipy==1.13.1",
        "pytz>=2024.1",
    ],
    entry_points={
        "console_scripts": [
            "wetbulb-calc=wetbulb_calc.cli:cli",
        ],
    },
)
