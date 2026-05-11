"""
Base class and utilities for WCVS data fetchers.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple

from .cache import DataCache


class FetcherBase(ABC):
    """Abstract base for a data fetcher with caching and fallback."""

    def __init__(self, cache: DataCache):
        self.cache = cache

    @property
    @abstractmethod
    def cache_key(self) -> str:
        """Unique cache key for this metric."""
        ...

    @abstractmethod
    def fetch_live(self) -> Optional[Any]:
        """Attempt to fetch live data. Return None on failure."""
        ...

    def get(self, allow_stale: bool = True) -> Tuple[Optional[Any], bool, bool]:
        """
        Return (value, is_stale, is_cached).
        Priority: live fetch -> cached (fresh) -> cached (stale) -> None.
        """
        # Try live first
        live_value = self.fetch_live()
        if live_value is not None:
            self.cache.set(self.cache_key, live_value, source=self.__class__.__name__)
            return live_value, False, False

        # Fallback to cache
        cached_value, is_stale = self.cache.get(self.cache_key)
        if cached_value is not None:
            if not is_stale:
                return cached_value, False, True
            if allow_stale:
                return cached_value, True, True

        return None, False, False
