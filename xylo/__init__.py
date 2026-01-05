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
__all__ = ["xylo", "UserRaisedException", "DEFAULT_MAX_ITERATIONS"]


def xylo(text, context=None, max_iterations=DEFAULT_MAX_ITERATIONS):
    """
    Process a xylo template string and return the rendered result.

    Args:
        text: The template string to process.
        context: Optional dictionary of variables available in the template.
        max_iterations: Maximum iterations for while loops (default: 1000).

    Returns:
        The rendered string result.

    Example:
        >>> from xylo import xylo
        >>> xylo("text $(1 + 5)")
        'text 6'
    """
    result, _ = _xylo_internal(text, context, max_iterations)
    return result

