#!/usr/bin/env python3

import os
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name='ghrocker',
    version="0.0.4",
    packages=['ghrocker'],
    package_dir={'': 'src'},
    package_data={'ghrocker': ['templates/*.em']},
    author="Tully Foote",
    author_email="tfoote@osrfoundation.org",
    description="A rocker extension to locally test github pages.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tfoote/ghrocker",
    license='Apache 2.0',
    install_requires=[
        'empy',
        'rocker',
    ],
    install_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'ghrocker = ghrocker.ghrocker:main',
	    ],
        'rocker.extensions': [
            'ghpages = ghrocker.ghpages_extension:GHPages',
        ]
    }
)
