#!/usr/bin/env python3

from setuptools import setup
from setuptools import find_packages


setup(
    name="litedram",
    description="Small footprint and configurable DRAM core",
    author="Florent Kermarrec",
    author_email="florent@enjoy-digital.fr",
    url="http://enjoy-digital.fr",
    download_url="https://github.com/enjoy-digital/litedram",
    test_suite="test",
    license="BSD",
    python_requires="~=3.6",
    install_requires=["pyyaml"],
    packages=find_packages(exclude=("test*", "sim*", "doc*", "examples*")),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "litedram_gen=litedram.gen:main",
        ],
    },
)
