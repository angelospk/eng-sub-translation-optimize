"""Pytest fixtures for interjection remover tests."""

import pytest
from src.interjection_remover import InterjectionRemoveContext, RemoveInterjection
from src.interjections_en import INTERJECTIONS_EN, INTERJECTIONS_SKIP_EN


@pytest.fixture
def remover() -> RemoveInterjection:
    """Return a RemoveInterjection instance."""
    return RemoveInterjection()


@pytest.fixture
def interjections() -> list[str]:
    """Return the default English interjections list."""
    return INTERJECTIONS_EN.copy()


@pytest.fixture
def skip_list() -> list[str]:
    """Return the default skip list."""
    return INTERJECTIONS_SKIP_EN.copy()


def make_context(
    text: str,
    only_separated_lines: bool = False,
    interjections: list[str] | None = None,
    skip_list: list[str] | None = None,
) -> InterjectionRemoveContext:
    """Helper to create an InterjectionRemoveContext."""
    return InterjectionRemoveContext(
        text=text,
        interjections=interjections if interjections is not None else INTERJECTIONS_EN.copy(),
        interjections_skip_if_starts_with=skip_list if skip_list is not None else INTERJECTIONS_SKIP_EN.copy(),
        only_separated_lines=only_separated_lines,
    )
