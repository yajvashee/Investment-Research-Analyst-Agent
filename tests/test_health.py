"""Tests for the Phase 1 project foundation."""

from app.health import check_application_imports


def test_application_modules_import() -> None:
    assert check_application_imports() is True
