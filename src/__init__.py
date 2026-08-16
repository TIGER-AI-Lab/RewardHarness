"""Compatibility namespace for RewardHarness 0.1 imports.

New code should import from :mod:`rewardharness`. The ``src`` namespace will
remain available through the 0.2 release series.
"""

from rewardharness import __version__

__all__ = ["__version__"]
