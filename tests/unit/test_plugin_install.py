from unittest.mock import patch

import pytest

from configurator.plugins.loader import PluginManager


@pytest.fixture
def temp_home(tmp_path):
    # Mock Path.home() to return tmp_path
    with patch("pathlib.Path.home", return_value=tmp_path):
        yield tmp_path


def test_install_local_file_plugin(temp_home):
    manager = PluginManager()

    # Create a dummy plugin file source
    source_dir = temp_home / "source"
    source_dir.mkdir()
    plugin_file = source_dir / "my_plugin.py"
    plugin_file.write_text("class MyPlugin: pass")

    # Install
    success = manager.install_plugin(str(plugin_file))
    assert success is True

    # Check if installed
    installed_path = temp_home / ".config/debian-vps-configurator/plugins/my_plugin.py"
    assert installed_path.exists()
    assert installed_path.read_text() == "class MyPlugin: pass"


def test_install_local_dir_plugin(temp_home):
    manager = PluginManager()

    # Create dummy plugin dir
    source_dir = temp_home / "source_pkg"
    source_dir.mkdir()
    (source_dir / "__init__.py").write_text("# init")

    # Install
    success = manager.install_plugin(str(source_dir))
    assert success is True

    # Check if installed
    installed_path = temp_home / ".config/debian-vps-configurator/plugins/source_pkg"
    assert installed_path.exists()
    assert (installed_path / "__init__.py").exists()


@patch("subprocess.run")
def test_install_git_plugin(mock_run, temp_home):
    manager = PluginManager()
    git_url = "https://github.com/example/my-plugin.git"

    success = manager.install_plugin(git_url)
    assert success is True

    # Check git clone called
    expected_dest = temp_home / ".config/debian-vps-configurator/plugins/my-plugin"
    mock_run.assert_called_with(["git", "clone", git_url, str(expected_dest)], check=True)


@patch("urllib.request.urlretrieve")
def test_install_zip_url(mock_retrieve, temp_home):
    manager = PluginManager()
    zip_url = "https://example.com/plugin.zip"

    # We need to mock _install_archive too or mock what's downloaded
    # Simpler to just verify urlretrieve is called and then mock _install_archive
    with patch.object(manager, "_install_archive", return_value=True) as mock_extract:
        success = manager.install_plugin(zip_url)
        assert success is True
        mock_retrieve.assert_called()
        mock_extract.assert_called()
