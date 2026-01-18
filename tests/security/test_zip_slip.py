import zipfile

import pytest

from configurator.plugins.loader import PluginError, PluginManager


def test_zip_slip_prevention(tmp_path):
    """
    Test that the loader prevents Zip Slip attacks (extraction outside target).
    """
    loader = PluginManager()

    # Create a malicious zip file
    malicious_zip = tmp_path / "evil.zip"
    target_dir = tmp_path / "plugins"
    target_dir.mkdir()

    # We create a zip manually
    with zipfile.ZipFile(malicious_zip, "w") as zf:
        # Add a safe file
        zf.writestr("safe.txt", "safe content")
        # Add a malicious file
        # Note: zipfile.writestr doesn't sanitize paths, allowing us to create the attack vector
        zf.writestr("../../../evil.txt", "hacked")

    # Attempt to extract
    with pytest.raises(PluginError) as exc:
        loader._safe_extract(zipfile.ZipFile(malicious_zip), target_dir)

    assert "Malicious path in archive" in str(exc.value)

    # Verify evil file was NOT written outside
    assert not (tmp_path / "evil.txt").exists()

    # Verify safe file was NOT written (since exception raised)
    # The current implementation iterates and checks. If one is bad, it raises.
    # It might process safe files before bad ones depending on order.
    # But extractall is called AFTER verification loop. So NOTHING should be extracted.
    assert not (target_dir / "safe.txt").exists()
