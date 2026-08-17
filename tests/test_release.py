"""Tests for lightweight imports and canonical release identity."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

import rewardharness
import rewardharness.release as release_module
from rewardharness.cli import main as cli_main
from rewardharness.release import (
    ReleaseIdentity,
    package_version_to_tag,
    tag_to_package_version,
)
from rewardharness.release import main as release_main


@pytest.mark.parametrize(
    ("package_version", "tag"),
    [
        ("1.2.3", "v1.2.3"),
        ("1.2.3a1", "v1.2.3-a1"),
        ("1.2.3b2", "v1.2.3-b2"),
        ("1.2.3rc4", "v1.2.3-rc4"),
    ],
)
def test_release_version_round_trip(package_version, tag):
    assert package_version_to_tag(package_version) == tag
    assert tag_to_package_version(tag) == package_version


@pytest.mark.parametrize("value", ["1.2", "v1.2.3", "1.2.3-dev"])
def test_package_version_rejects_unsupported_values(value):
    with pytest.raises(ValueError, match="Unsupported package version"):
        package_version_to_tag(value)


@pytest.mark.parametrize("value", ["1.2.3", "v1.2", "v1.2.3-dev1"])
def test_tag_rejects_unsupported_values(value):
    with pytest.raises(ValueError, match="Unsupported release tag"):
        tag_to_package_version(value)


def test_current_release_identity_and_tag_validation():
    identity = ReleaseIdentity.current()
    assert identity.package_version == "0.2.0rc1"
    assert identity.tag == "v0.2.0-rc1"
    assert identity.prerelease is True
    identity.validate_tag(identity.tag)
    with pytest.raises(ValueError, match="package version"):
        identity.validate_tag("v0.2.0-rc2")


def test_release_status_cli(capsys):
    assert cli_main(["release-status"]) == 0
    assert json.loads(capsys.readouterr().out)["tag"] == "v0.2.0-rc1"


def test_release_module_cli_validates_tag(capsys):
    assert release_main(["--check-tag", "v0.2.0-rc1"]) == 0
    assert json.loads(capsys.readouterr().out)["package_version"] == "0.2.0rc1"


def test_release_identity_rejects_invalid_canonical_version(monkeypatch):
    monkeypatch.setattr(release_module, "__version__", "invalid")
    with pytest.raises(RuntimeError, match="Invalid package version"):
        ReleaseIdentity.current()


def test_top_level_exports_are_lazy_and_discoverable():
    assert rewardharness.Preference.A.value == "A"
    assert "Preference" in dir(rewardharness)
    missing_name = "not_a_public_export"
    with pytest.raises(AttributeError, match="has no attribute"):
        getattr(rewardharness, missing_name)


def test_package_import_does_not_eagerly_load_heavy_dependencies():
    code = (
        "import sys, rewardharness; "
        "assert rewardharness.__version__ == '0.2.0rc1'; "
        "assert 'datasets' not in sys.modules; "
        "assert 'transformers' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
