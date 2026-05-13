import os

# Package shim: allow `import cinema_crm.<sub>` to resolve modules located
# in the project root (parent directory). This keeps tests that import
# `cinema_crm.routers` working without moving large parts of the codebase.
# Prepend the project root to the package search path.
proj_root = os.path.dirname(os.path.dirname(__file__))
if proj_root not in __path__:
    __path__.insert(0, proj_root)

__all__ = []
