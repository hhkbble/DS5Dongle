import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

from tools import config_tool


class FakeDevice:
    def __init__(self):
        self.reports = []
        self.closed = False

    def send_feature_report(self, report):
        self.reports.append(bytes(report))

    def close(self):
        self.closed = True


class ConfigToolPollingTests(unittest.TestCase):
    def test_mode_three_is_valid_and_set_prints_reconnect_action(self):
        self.assertEqual(config_tool.parse_assignment("polling_rate_mode=3"), ("polling_rate_mode", 3))
        with self.assertRaises(SystemExit):
            config_tool.parse_assignment("polling_rate_mode=4")

        output = io.StringIO()
        fake = FakeDevice()
        with (
            patch.object(config_tool, "open_device", return_value=fake),
            patch.object(config_tool, "read_config", side_effect=[{"polling_rate_mode": 1}, {"polling_rate_mode": 3}]),
            patch.object(config_tool, "write_config"),
            redirect_stdout(output),
        ):
            config_tool.cmd_set(SimpleNamespace(assignments=["polling_rate_mode=3"], no_save=True))

        self.assertIn("reconnect", output.getvalue().lower())
        self.assertIn("replug", output.getvalue().lower())
        self.assertTrue(fake.closed)

    def test_explicit_reconnect_command_uses_existing_f6_function_three(self):
        fake = FakeDevice()
        with patch.object(config_tool, "open_device", return_value=fake):
            config_tool.cmd_reconnect(SimpleNamespace())

        self.assertEqual(len(fake.reports), 1)
        self.assertEqual(len(fake.reports[0]), config_tool.FEATURE_REPORT_LEN)
        self.assertEqual(fake.reports[0][:2], bytes([config_tool.REPORT_SET, config_tool.FUNC_RECONNECT]))
        self.assertTrue(fake.closed)


if __name__ == "__main__":
    unittest.main()
