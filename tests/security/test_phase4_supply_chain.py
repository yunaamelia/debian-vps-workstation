"""Supply chain security tests for Phase 4."""

from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule


class TestZshSupplyChain:
    """Test Zsh installation supply chain security."""

    @pytest.fixture
    def module(self):
        config = {"zsh": {"enabled": True}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    def test_oh_my_zsh_installation_secure(self, module):
        """Test that OMZ installation is secure."""
        with patch.object(module, "run") as mock_run:
            mock_run.return_value = Mock(success=True)
            with patch("configurator.modules.desktop.pwd") as mock_pwd:
                user = Mock(pw_name="test", pw_uid=1000, pw_dir="/home/test")
                mock_pwd.getpwall.return_value = [user]
                with patch("os.path.exists", return_value=False):
                    with patch("configurator.modules.desktop.SecureDownloader") as MockDownloader:
                        with patch(
                            "configurator.modules.desktop.SupplyChainValidator"
                        ) as MockValidator:
                            mock_validator_instance = MockValidator.return_value
                            # Configure validator to return empty dicts so defaults are used
                            mock_validator_instance.checksums = {}

                            mock_downloader = MockDownloader.return_value
                            mock_downloader.download_script.return_value = True

                            module._install_oh_my_zsh()

                            # Verify secure download used
                            assert mock_downloader.download_script.called

                            # Verify URL is HTTPS
                            call_args = mock_downloader.download_script.call_args
                            url = call_args[0][0]
                            assert "https://" in url

                            # Verify execution
                            install_calls = [
                                str(c)
                                for c in mock_run.call_args_list
                                if "ohmyzsh_install.sh" in str(c)
                            ]
                            assert len(install_calls) > 0
