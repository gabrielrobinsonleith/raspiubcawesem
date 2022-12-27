import platform
from setuptools import find_packages, setup

required_pkgs = [
    "sphinx",
    "m2r",
    "sphinx-rtd-theme",
    "pytest",
    "numpy",
    "matplotlib",
    "pyserial",
    "numpy_indexed",
    "loguru",
    "flask",
    "pi-plates",
    "aenum",
    "pillow",
    "smbus"
]

# Packages that don't work on raspberry pi
# Note: This is for the original GUI, and is only kept around for legacy purposes
if not 'arm' in platform.uname().machine:
    required_pkgs.append([
        "pyqt5",
    ])

setup(
    name="awesem",
    version="1.0.0",
    description="Code to control the UBC AweSEM device",
    author="Justin Lam",
    author_email="justin@mistywest.com",
    url="https://bitbucket.org/mw_active/ua02-awesem-control",
    packages=find_packages(),
    scripts=[],
    install_requires=required_pkgs,
    zip_safe=False,
)
