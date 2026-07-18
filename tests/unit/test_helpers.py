"""
Unit tests for general-purpose helper utilities.
"""

from __future__ import annotations

import uuid

from app.utils.helpers import (
    calculate_pagination,
    chunk,
    generate_request_id,
    slugify,
    truncate,
)


def test_generate_request_id() -> None:
    """generate_request_id must return a valid 32-character hex string."""
    request_id = generate_request_id()
    assert isinstance(request_id, str)
    assert len(request_id) == 32
    # Should be valid hex
    uuid.UUID(request_id)


def test_calculate_pagination() -> None:
    """calculate_pagination must return correct metadata."""
    res = calculate_pagination(total=25, page=2, page_size=10)
    assert res["total"] == 25
    assert res["page"] == 2
    assert res["page_size"] == 10
    assert res["total_pages"] == 3
    assert res["offset"] == 10
    assert res["has_next"] is True
    assert res["has_previous"] is True

    # Page size 0 or page 1
    res_zero = calculate_pagination(total=5, page=1, page_size=0)
    assert res_zero["total_pages"] == 1
    assert res_zero["has_next"] is False
    assert res_zero["has_previous"] is False


def test_slugify() -> None:
    """slugify must convert strings to URL-safe format."""
    assert slugify("Hello World!") == "hello-world"
    assert slugify("  test__slug--ify  ") == "test-slug-ify"
    assert slugify("foo/bar") == "foobar"


def test_truncate() -> None:
    """truncate must shorten string to max_length including suffix."""
    assert truncate("hello", max_length=10) == "hello"
    assert truncate("hello world", max_length=10, suffix="...") == "hello w..."
    assert truncate("hello world", max_length=5, suffix="") == "hello"


def test_chunk() -> None:
    """chunk must split list into sub-lists of given size."""
    assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert chunk([], 3) == []
