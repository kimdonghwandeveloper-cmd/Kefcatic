"""Ensure every connector module registers itself into CONNECTOR_REGISTRY."""
import importlib

import pytest

_CONNECTOR_MODULES = {
    "youtube": "youtube",
    "gmail": "gmail",
    "google_drive": "google_drive",
    "google_calendar": "google_calendar",
    "google_sheets": "google_sheets",
    "slack": "slack",
    "hubspot": "hubspot",
}


@pytest.mark.parametrize("connector_type,module", _CONNECTOR_MODULES.items())
def test_connector_registered(connector_type, module):
    importlib.import_module(f"app.connectors.{module}")
    from app.connectors.base import CONNECTOR_REGISTRY

    assert connector_type in CONNECTOR_REGISTRY
    cls = CONNECTOR_REGISTRY[connector_type]
    assert cls.connector_type == connector_type


def test_all_connectors_have_auth_helpers():
    """Each connector module exposes build_auth_url + exchange_code."""
    for module in _CONNECTOR_MODULES.values():
        mod = importlib.import_module(f"app.connectors.{module}")
        assert hasattr(mod, "build_auth_url"), f"{module} missing build_auth_url"
        assert hasattr(mod, "exchange_code"), f"{module} missing exchange_code"
