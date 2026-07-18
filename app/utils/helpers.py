"""
General-purpose helper utilities.

Contains small, pure helper functions used across the codebase.
Each function is stateless, thoroughly typed, and independently testable.
"""

from __future__ import annotations

import math
import re
import uuid
from typing import TypeVar

T = TypeVar("T")


# --------------------------------------------------------------------------- #
# Identifiers
# --------------------------------------------------------------------------- #


def generate_request_id() -> str:
    """
    Generate a unique request correlation ID.

    Returns:
        A UUID4 hex string (no hyphens) suitable for use as a request ID.
    """
    return uuid.uuid4().hex


# --------------------------------------------------------------------------- #
# Pagination
# --------------------------------------------------------------------------- #


def calculate_pagination(
    *,
    total: int,
    page: int,
    page_size: int,
) -> dict[str, int]:
    """
    Calculate pagination metadata.

    Args:
        total: Total number of records.
        page: Current page number (1-indexed).
        page_size: Number of records per page.

    Returns:
        A dictionary with pagination metadata keys:
        ``total``, ``page``, ``page_size``, ``total_pages``,
        ``offset``, ``has_next``, ``has_previous``.
    """
    total_pages = max(1, math.ceil(total / page_size)) if page_size > 0 else 1
    offset = (page - 1) * page_size
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "offset": offset,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


# --------------------------------------------------------------------------- #
# String Utilities
# --------------------------------------------------------------------------- #


def slugify(text: str) -> str:
    """
    Convert a string to a URL-safe slug.

    Args:
        text: The input string to slugify.

    Returns:
        A lowercase, hyphen-separated slug with no special characters.

    Example::

        >>> slugify("Hello World! 123")
        'hello-world-123'
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def truncate(text: str, max_length: int = 100, suffix: str = "…") -> str:
    """
    Truncate a string to a maximum length, appending a suffix if truncated.

    Args:
        text: The string to truncate.
        max_length: Maximum allowed character length (including suffix).
        suffix: The string appended when truncation occurs.

    Returns:
        The original string if within ``max_length``; otherwise a truncated string.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


# --------------------------------------------------------------------------- #
# Collection Utilities
# --------------------------------------------------------------------------- #


def chunk(items: list[T], size: int) -> list[list[T]]:
    """
    Split a list into chunks of the given size.

    Args:
        items: The list to split.
        size: Maximum size of each chunk.

    Returns:
        A list of sub-lists, each of length <= size.

    Example::

        >>> chunk([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    return [items[i : i + size] for i in range(0, len(items), size)]
