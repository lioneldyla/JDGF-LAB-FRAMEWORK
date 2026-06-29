import argparse

import pytest

from jdgf_framework.cli import _port


@pytest.mark.parametrize("value", ["1024", "8765", "65535"])
def test_port_accepts_unprivileged_range(value: str) -> None:
    assert _port(value) == int(value)


@pytest.mark.parametrize("value", ["0", "80", "65536"])
def test_port_rejects_out_of_range_values(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="between 1024 and 65535"):
        _port(value)


def test_port_rejects_non_numeric_value() -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="integer"):
        _port("invalid")
