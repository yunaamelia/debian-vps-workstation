from unittest.mock import Mock, patch

import pytest

from configurator.utils.retry import retry


def test_retry_success():
    mock_func = Mock(return_value="success")

    @retry(max_retries=3, base_delay=0.01)
    def test_func():
        return mock_func()

    result = test_func()
    assert result == "success"
    assert mock_func.call_count == 1


def test_retry_failure_then_success():
    mock_func = Mock(side_effect=[ValueError("fail"), ValueError("fail"), "success"])

    @retry(max_retries=3, base_delay=0.01)
    def test_func():
        return mock_func()

    result = test_func()
    assert result == "success"
    assert mock_func.call_count == 3


def test_retry_failure_max_retries():
    mock_func = Mock(side_effect=ValueError("fail"))

    @retry(max_retries=3, base_delay=0.01)
    def test_func():
        return mock_func()

    with pytest.raises(ValueError):
        test_func()

    assert mock_func.call_count == 4  # Initial + 3 retries


def test_retry_specific_exception():
    mock_func = Mock(side_effect=TypeError("fail"))

    # Only retry ValueError
    @retry(max_retries=3, base_delay=0.01, exceptions=(ValueError,))
    def test_func():
        return mock_func()

    with pytest.raises(TypeError):
        test_func()

    assert mock_func.call_count == 1  # Should not retry


def test_backoff_timing():
    mock_func = Mock(side_effect=[ValueError("fail"), "success"])
    sleep_mock = Mock()

    with patch("time.sleep", sleep_mock):

        @retry(max_retries=3, base_delay=1.0, backoff_factor=2.0, jitter=False)
        def test_func():
            return mock_func()

        test_func()

    sleep_mock.assert_called_once_with(1.0)
