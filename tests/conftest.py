"""Pytest configuration for Ultraloq Wifi tests."""
import pytest


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test that requires real API access"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication-related (token request, login, addresses)"
    )
    config.addinivalue_line(
        "markers", "devices: mark test as device discovery-related"
    )
    config.addinivalue_line(
        "markers", "locks: mark test as lock control-related (status, toggle)"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()