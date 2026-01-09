"""
Xylo - A powerful template engine with Python expression evaluation.

Example usage:
    >>> from xylo import xylo
    >>> xylo("text $(1 + 5)")
    'text 6'
"""

from .core import xylo as _xylo_internal
from .core import UserRaisedException, DEFAULT_MAX_ITERATIONS

__version__ = "0.1.1"
__all__ = ["xylo", "xylo_set_path", "xylo_get_path", "UserRaisedException", "DEFAULT_MAX_ITERATIONS"]

_global_path = None


def xylo_set_path(path):
    """
    Set the global default path for resolving $include directives.

    Args:
        path: The file path to use as default. Set to None to clear.

    Example:
        >>> from xylo import xylo, xylo_set_path
        >>> xylo_set_path("/path/to/templates/main.sdf")
        >>> xylo('$include("header.sdf")')
    """
    global _global_path
    _global_path = path


def xylo_get_path():
    """
    Get the current global default path.

    Returns:
        The current global path or None if not set.
    """
    return _global_path


def xylo(text, context=None, path=None, max_iterations=DEFAULT_MAX_ITERATIONS):
    """
    Process a xylo template string and return the rendered result.

    Args:
        text: The template string to process.
        context: Optional dictionary of variables available in the template.
        path: Optional file path for resolving $include directives.
              Falls back to global path set via xylo_set_path() if not provided.
        max_iterations: Maximum iterations for while loops (default: 1000).

    Returns:
        The rendered string result.

    Example:
        >>> from xylo import xylo
        >>> xylo("text $(1 + 5)")
        'text 6'
    """
    effective_path = path if path is not None else _global_path
    result, _ = _xylo_internal(text, context, effective_path, max_iterations)
    return result
