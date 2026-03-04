"""Test suite for CLI flag behavior."""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jbfoundry.runners.utils.dynamic_args_parser import DynamicArgumentParser


class TestCLIFlags:
    """Test suite for CLI flag behavior."""

    def test_restart_default(self):
        """Test that restart defaults to False (resume by default)."""
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args([])
        assert args.restart is False, "restart should default to False"

    def test_restart_flag_no_value(self):
        """Test that --restart without value enables it."""
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args(["--restart"])
        assert args.restart is True, "--restart should set restart to True"

    def test_restart_explicit_true(self):
        """Test --restart true explicitly enables."""
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args(["--restart", "true"])
        assert args.restart is True

    def test_restart_explicit_false(self):
        """Test --restart false explicitly disables."""
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args(["--restart", "false"])
        assert args.restart is False

    def test_retry_invalid_default(self):
        """Test that retry_invalid defaults to True."""
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args([])
        assert args.retry_invalid is True, "retry_invalid should default to True"

    def test_retry_invalid_flag_no_value(self):
        """Test --retry-invalid without value enables it."""
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args(["--retry-invalid"])
        assert args.retry_invalid is True

    def test_retry_invalid_explicit_false(self):
        """Test --retry-invalid false explicitly disables."""
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args(["--retry-invalid", "false"])
        assert args.retry_invalid is False

    def test_retry_failed_default(self):
        """Test that retry_failed defaults to False."""
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args([])
        assert args.retry_failed is False, "retry_failed should default to False"

    def test_retry_failed_flag_no_value(self):
        """Test --retry-failed without value enables it."""
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args(["--retry-failed"])
        assert args.retry_failed is True, "--retry-failed should enable retrying"

    def test_retry_failed_explicit_true(self):
        """Test --retry-failed true explicitly enables."""
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args(["--retry-failed", "true"])
        assert args.retry_failed is True

    def test_retry_failed_explicit_false(self):
        """Test --retry-failed false explicitly disables."""
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args(["--retry-failed", "false"])
        assert args.retry_failed is False

    def test_combined_flags(self):
        """Test combining --restart and --retry-failed."""
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args(["--restart", "--retry-failed"])
        assert args.restart is True
        assert args.retry_failed is True

    def test_retry_flags_case_insensitive(self):
        """Test that boolean values are case-insensitive."""
        parser = DynamicArgumentParser()

        args1 = parser.parser.parse_args(["--retry-failed", "True"])
        assert args1.retry_failed is True

        args2 = parser.parser.parse_args(["--retry-failed", "FALSE"])
        assert args2.retry_failed is False

        args3 = parser.parser.parse_args(["--retry-invalid", "yes"])
        assert args3.retry_invalid is True

        args4 = parser.parser.parse_args(["--retry-invalid", "no"])
        assert args4.retry_invalid is False

    def test_default_behavior_scenario(self):
        """
        Test default behavior: restart=False, retry_invalid=True, retry_failed=False
        This should skip successful + failed, retry invalid + unrun
        """
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args([])
        assert args.restart is False
        assert args.retry_invalid is True
        assert args.retry_failed is False

    def test_retry_failed_scenario(self):
        """
        Test --retry-failed scenario: restart=False, retry_invalid=True, retry_failed=True
        This should skip only successful, retry failed + invalid + unrun
        """
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args(["--retry-failed"])
        assert args.restart is False
        assert args.retry_invalid is True
        assert args.retry_failed is True

    def test_skip_all_scenario(self):
        """
        Test --retry-invalid false --retry-failed false: skip everything except unrun
        This should skip successful + failed + invalid, only run new queries
        """
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args(["--retry-invalid", "false", "--retry-failed", "false"])
        assert args.restart is False
        assert args.retry_invalid is False
        assert args.retry_failed is False

    def test_fresh_start_scenario(self):
        """
        Test --restart scenario: restart=True
        This should run all queries from scratch
        """
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args(["--restart"])
        assert args.restart is True

    def test_contradictory_flags_scenario(self):
        """
        Test --restart --retry-failed (should parse but warn at runtime)
        """
        parser = DynamicArgumentParser()
        args = parser.parser.parse_args(["--restart", "--retry-failed"])
        assert args.restart is True
        assert args.retry_failed is True
        # Note: Warning should be shown in initialize_results_file


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
