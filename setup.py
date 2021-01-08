#!/usr/bin/env python3

import os
import setuptools

setuptools.setup(
    name='ghrocker',
    version="0.0.1",
    packages=['ghrocker'],
    package_dir={'': 'src'},
    package_data={'ghrocker': ['templates/*.em']},
    author="Tully Foote",
    author_email="tfoote@osrfoundation.org",
    description="Plugins for rocker that inject noVNC",
    long_description="ASDF",
    long_description_content_type="text/markdown",
    url="https://github.com/tfoote/ghrocker",
    license='Apache 2.0',
    install_requires=[
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
