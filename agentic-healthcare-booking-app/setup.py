# Copyright AGNTCY Contributors (https://github.com/agntcy)
#
# SPDX-License-Identifier: Apache-2.0

from gettext import install
from setuptools import setup, find_packages

setup(
    name="agentic-healthcare-booking-app",
    packages=find_packages(),
)


# run "pip install -r requirements.txt" for installing dependency libraries
# run "pip install -e ." for clean imports setup