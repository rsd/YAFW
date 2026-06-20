import unittest
from unittest.mock import patch, MagicMock
import main

class TestMainControlFlow(unittest.TestCase):
    def setUp(self):
        # Reset the global active_thread state before each test
        main.active_thread = None

    @patch("main.VideoProcessorThread")
    def test_start_processing(self, mock_thread_class):
        mock_thread_instance = MagicMock()
        mock_thread_class.return_value = mock_thread_instance
        
        # Setup mock app
        main.app = MagicMock()
        main.app.winfo_exists.return_value = True
        
        main.start_processing("input.mp4", "output.mp4", {"some": "config"})
        
        # Verify thread was instantiated and started
        mock_thread_class.assert_called_once_with(
            "input.mp4", "output.mp4", {"some": "config"}, unittest.mock.ANY
        )
        mock_thread_instance.start.assert_called_once()
        self.assertEqual(main.active_thread, mock_thread_instance)
        
        # Retrieve the progress callback passed to the thread and test it
        passed_callback = mock_thread_class.call_args[0][3]
        passed_callback(50, "Encoding halfway")
        
        # Check that it triggers GUI updates safely on main thread via app.after()
        main.app.after.assert_called_once_with(0, unittest.mock.ANY)

    def test_cancel_processing(self):
        # Setup active thread mock
        mock_thread = MagicMock()
        main.active_thread = mock_thread
        
        main.cancel_processing()
        
        mock_thread.cancel.assert_called_once()
        self.assertIsNone(main.active_thread)

    def test_cancel_processing_no_active_thread(self):
        # Should not raise exception
        main.active_thread = None
        main.cancel_processing()
        self.assertIsNone(main.active_thread)

    @patch("main.cancel_processing")
    def test_on_closing(self, mock_cancel):
        # Setup mock app
        main.app = MagicMock()
        
        main.on_closing()
        
        mock_cancel.assert_called_once()
        main.app.destroy.assert_called_once()

if __name__ == "__main__":
    unittest.main()
