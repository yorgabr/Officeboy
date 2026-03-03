"""Officeboy - MS Access Version Control and Automation CLI Tool.

This package provides tools for exporting, importing, and testing
MS Access database applications using version control systems.

Author: Yorga Babuscan <yorgabr@gmail.com>
License: GPL-3.0-or-later
"""

try:
    from ._version import version as __version__
    from ._version import version_tuple as __version_tuple__
except ImportError:
    __version__ = "0.0.0+unknown"
    __version_tuple__ = (0, 0, 0, "unknown")

__author__ = "Yorga Babuscan"
__email__ = "yorgabr@gmail.com"
__license__ = "GPL-3.0-or-later"
