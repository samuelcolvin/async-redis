__all__ = 'VERSION', 'COMPILED'

VERSION = '0.0.1'

try:
    import cython  # type: ignore
except ImportError:
    COMPILED: bool = False
else:  # pragma: no cover
    try:
        COMPILED = cython.compiled
    except AttributeError:
        COMPILED = False
