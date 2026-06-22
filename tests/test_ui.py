import sys
import unittest
from unittest.mock import MagicMock, patch

# Substitute customtkinter module before importing ui
mock_ctk = MagicMock()
class MockCTk(MagicMock):
    pass

mock_ctk.CTk = MockCTk
mock_ctk.CTkFrame = MagicMock
mock_ctk.CTkButton = MagicMock
mock_ctk.CTkLabel = MagicMock
mock_ctk.CTkSwitch = MagicMock
mock_ctk.CTkOptionMenu = MagicMock
mock_ctk.CTkSlider = MagicMock
mock_ctk.CTkEntry = MagicMock
mock_ctk.CTkProgressBar = MagicMock
mock_ctk.CTkFont = MagicMock

sys.modules['customtkinter'] = mock_ctk

# Substitute tkinter.Label before importing ui
import tkinter as tk
tk.Label = MagicMock

# Now import YafwApp
from ui import YafwApp

class TestYafwAppLogic(unittest.TestCase):
    def setUp(self):
        # Instantiate YafwApp using our MockCTk base class.
        # Bypasses all Tk/Tcl engine calls.
        self.app = YafwApp(MagicMock(), MagicMock())

    def test_get_config_basic_view(self):
        # Manually create mock widgets
        self.app.cut_switch = MagicMock()
        self.app.cut_switch.get.return_value = 1
        
        self.app.speed_switch = MagicMock()
        self.app.speed_switch.get.return_value = 1
        
        self.app.boost_switch = MagicMock()
        self.app.boost_switch.get.return_value = 0
        
        self.app.preset_menu = MagicMock()
        self.app.preset_menu.get.return_value = "Quiet Room (Low -35dB)"
        
        self.app.advanced_visible = False
        
        config = self.app.get_config()
        self.assertTrue(config["cut_silence"])
        self.assertTrue(config["speed_up"])
        self.assertFalse(config["voice_boost"])
        self.assertEqual(config["noise_threshold"], "-35dB")
        self.assertEqual(config["crf"], 35)
        self.assertEqual(config["preset"], "slow")
        self.assertEqual(config["margin"], 0.2)

    def test_get_config_advanced_view(self):
        self.app.cut_switch = MagicMock()
        self.app.cut_switch.get.return_value = 0
        
        self.app.speed_switch = MagicMock()
        self.app.speed_switch.get.return_value = 1
        
        self.app.boost_switch = MagicMock()
        self.app.boost_switch.get.return_value = 1
        
        self.app.thresh_entry = MagicMock()
        self.app.thresh_entry.get.return_value = " -22dB "
        
        self.app.crf_slider = MagicMock()
        self.app.crf_slider.get.return_value = 22.0
        
        self.app.adv_preset_menu = MagicMock()
        self.app.adv_preset_menu.get.return_value = "fast"
        
        self.app.margin_slider = MagicMock()
        self.app.margin_slider.get.return_value = 0.4

        self.app.advanced_visible = True
        self.app.advanced_used = True

        config = self.app.get_config()
        self.assertFalse(config["cut_silence"])
        self.assertTrue(config["speed_up"])
        self.assertTrue(config["voice_boost"])
        self.assertEqual(config["noise_threshold"], "-22dB")
        self.assertEqual(config["crf"], 22)
        self.assertEqual(config["preset"], "fast")
        self.assertEqual(config["margin"], 0.4)

    def test_get_config_advanced_collapsed_keeps_values(self):
        # Regression: opening advanced, customizing, then collapsing the panel
        # must still honor the advanced widgets (advanced_used stays True).
        self.app.cut_switch = MagicMock()
        self.app.cut_switch.get.return_value = 1

        self.app.speed_switch = MagicMock()
        self.app.speed_switch.get.return_value = 1

        self.app.boost_switch = MagicMock()
        self.app.boost_switch.get.return_value = 0

        self.app.thresh_entry = MagicMock()
        self.app.thresh_entry.get.return_value = "-22dB"

        self.app.crf_slider = MagicMock()
        self.app.crf_slider.get.return_value = 24.0

        self.app.adv_preset_menu = MagicMock()
        self.app.adv_preset_menu.get.return_value = "medium"

        self.app.margin_slider = MagicMock()
        self.app.margin_slider.get.return_value = 0.3

        # Panel is collapsed, but the user engaged it earlier.
        self.app.advanced_visible = False
        self.app.advanced_used = True

        config = self.app.get_config()
        self.assertEqual(config["noise_threshold"], "-22dB")
        self.assertEqual(config["crf"], 24)
        self.assertEqual(config["preset"], "medium")
        self.assertEqual(config["margin"], 0.3)

    def test_toggle_advanced(self):
        self.app.advanced_frame = MagicMock()
        self.app.advanced_header = MagicMock()
        
        # Initial: hidden
        self.app.advanced_visible = False
        self.app.toggle_advanced()
        self.assertTrue(self.app.advanced_visible)
        self.app.advanced_frame.grid.assert_called_once_with(row=6, column=0, sticky="ew", pady=(0, 16))
        self.app.advanced_header.configure.assert_called_with(text="▲ Advanced Settings")
        
        # Toggle back to hidden
        self.app.toggle_advanced()
        self.assertFalse(self.app.advanced_visible)
        self.app.advanced_frame.grid_forget.assert_called_once()
        self.app.advanced_header.configure.assert_called_with(text="▼ Advanced Settings")

    def test_toggle_cut_settings(self):
        self.app.cut_switch = MagicMock()
        self.app.preset_menu = MagicMock()
        self.app.thresh_entry = MagicMock()
        self.app.margin_slider = MagicMock()
        
        # When cut_switch is ON (get returns 1)
        self.app.cut_switch.get.return_value = 1
        self.app.toggle_cut_settings()
        self.app.preset_menu.configure.assert_called_with(state="normal")
        self.app.thresh_entry.configure.assert_called_with(state="normal")
        self.app.margin_slider.configure.assert_called_with(state="normal")
        
        # When cut_switch is OFF (get returns 0)
        self.app.cut_switch.get.return_value = 0
        self.app.toggle_cut_settings()
        self.app.preset_menu.configure.assert_called_with(state="disabled")
        self.app.thresh_entry.configure.assert_called_with(state="disabled")
        self.app.margin_slider.configure.assert_called_with(state="disabled")

    def test_update_crf_val(self):
        self.app.crf_val_lbl = MagicMock()
        
        self.app.update_crf_val(19)
        self.app.crf_val_lbl.configure.assert_called_with(text="19 (Near Lossless)")
        
        self.app.update_crf_val(23)
        self.app.crf_val_lbl.configure.assert_called_with(text="23 (High Quality)")
        
        self.app.update_crf_val(26)
        self.app.crf_val_lbl.configure.assert_called_with(text="26 (Highly Compressed)")
        
        self.app.update_crf_val(30)
        self.app.crf_val_lbl.configure.assert_called_with(text="30 (Extreme Compression)")

    def test_update_margin_val(self):
        self.app.margin_val_lbl = MagicMock()
        self.app.update_margin_val(0.456)
        self.app.margin_val_lbl.configure.assert_called_with(text="0.46s")

if __name__ == "__main__":
    unittest.main()
