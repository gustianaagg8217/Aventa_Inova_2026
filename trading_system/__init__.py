# Shim package to allow legacy imports like "trading_system.core.*"
# This file makes the repository root available on the package __path__
# so `import trading_system.core.mt5_connector` will resolve to the
# top-level `core` package that exists in the repo root.
import os

# Add project root (two levels up from this file) to the package search path
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _repo_root not in __path__:
    __path__.insert(0, _repo_root)

# Optional: expose package metadata
__all__ = []
