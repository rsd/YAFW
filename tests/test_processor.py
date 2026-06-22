import unittest
from unittest.mock import patch, MagicMock, mock_open
import subprocess
import json
import os
import io

from processor import get_video_duration, build_filtergraph, VideoProcessorThread, _atempo_chain

# Safe side-effect wrapper for os.close to ignore mocked file descriptor 99
# while keeping original closing functionality for other descriptors
original_os_close = os.close
def safe_os_close(fd):
    if fd == 99:
        return
    try:
        original_os_close(fd)
    except OSError:
        pass

class TestGetVideoDuration(unittest.TestCase):
    @patch("subprocess.run")
    def test_get_duration_success(self, mock_run):
        # Setup mock CompletedProcess
        mock_res = MagicMock()
        mock_res.stdout = " 124.56 \n"
        mock_run.return_value = mock_res
        
        duration = get_video_duration("dummy_path.mp4")
        self.assertEqual(duration, 124.56)
        
        # Verify ffprobe was called correctly
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        self.assertIn("ffprobe", cmd)
        self.assertIn("dummy_path.mp4", cmd)

    @patch("subprocess.run")
    def test_get_duration_failure(self, mock_run):
        # Simulate process error
        mock_run.side_effect = subprocess.CalledProcessError(1, "ffprobe")
        
        duration = get_video_duration("dummy_path.mp4")
        self.assertEqual(duration, 0.0)

    @patch("subprocess.run")
    def test_get_duration_invalid_value(self, mock_run):
        # Setup mock returning non-float
        mock_res = MagicMock()
        mock_res.stdout = "not_a_float\n"
        mock_run.return_value = mock_res
        
        duration = get_video_duration("dummy_path.mp4")
        self.assertEqual(duration, 0.0)


class TestAtempoChain(unittest.TestCase):
    def test_in_range_single_filter(self):
        self.assertEqual(_atempo_chain(1.2), "atempo=1.2000")
        self.assertEqual(_atempo_chain(2.0), "atempo=2.0000")
        self.assertEqual(_atempo_chain(0.5), "atempo=0.5000")

    def test_above_two_is_chained(self):
        # 2.5 = 2.0 * 1.25, both within ffmpeg's per-filter [0.5, 2.0] range
        self.assertEqual(_atempo_chain(2.5), "atempo=2.0000,atempo=1.2500")

    def test_far_above_two_is_chained(self):
        # 5.0 = 2.0 * 2.0 * 1.25
        self.assertEqual(_atempo_chain(5.0), "atempo=2.0000,atempo=2.0000,atempo=1.2500")

    def test_below_half_is_chained(self):
        # 0.25 = 0.5 * 0.5
        self.assertEqual(_atempo_chain(0.25), "atempo=0.5000,atempo=0.5000")


class TestBuildFiltergraph(unittest.TestCase):
    def test_single_pass_no_cuts_no_speed_no_boost(self):
        # Without cuts, speed, or boost, filtergraph should be empty
        graph, v_out, a_out, duration = build_filtergraph(
            timeline_json_path=None,
            cut_silence=False,
            speed_up=False,
            voice_boost=False,
            total_duration=100.0
        )
        self.assertEqual(graph, "")
        self.assertEqual(v_out, "[0:v]")
        self.assertEqual(a_out, "[0:a]")
        self.assertEqual(duration, 100.0)

    def test_single_pass_no_cuts_speed_and_boost(self):
        # Speed up and voice boost applied to the whole file
        graph, v_out, a_out, duration = build_filtergraph(
            timeline_json_path=None,
            cut_silence=False,
            speed_up=True,
            speed_val=1.2,
            voice_boost=True,
            total_duration=120.0
        )
        # Should apply setpts and atempo
        self.assertIn("[0:v]setpts=PTS/1.2000[outv_raw]", graph)
        self.assertIn("[0:a]atempo=1.2000[outa_raw]", graph)
        self.assertIn("[outa_raw]dynaudnorm=f=150:g=15[outa]", graph)
        self.assertEqual(v_out, "[outv_raw]")
        self.assertEqual(a_out, "[outa]")
        self.assertAlmostEqual(duration, 100.0)

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_two_pass_with_cuts_and_custom_speed(self, mock_json_load, mock_file):
        # Mock timeline json contents
        mock_timeline = {
            "timebase": "30/1",
            "v": [[
                {"offset": 0, "dur": 150, "effects": []},
                {"offset": 300, "dur": 300, "effects": ["speed:2.0"]}
            ]],
            "a": [[
                {"offset": 0, "dur": 150, "effects": []},
                {"offset": 300, "dur": 300, "effects": ["speed:2.0"]}
            ]]
        }
        mock_json_load.return_value = mock_timeline
        
        graph, v_out, a_out, duration = build_filtergraph(
            timeline_json_path="mock_timeline.json",
            cut_silence=True,
            speed_up=True,
            speed_val=1.2,
            voice_boost=True,
            total_duration=15.0
        )
        
        # Two clips:
        # Clip 0: dur=150, offset=0. Original speed=1.0. Speeded up to 1.2x.
        # Clip 1: dur=300, offset=300. Original speed=2.0. Speeded up to 2.0x (maintains preset speed).
        # Expected duration = (150/1.2)/30 + (300/2.0)/30 = 4.166 + 5.0 = 9.166 seconds.
        self.assertAlmostEqual(duration, 9.1666666, places=5)
        
        # Verify trimmer filters
        self.assertIn("[0:v]trim=start=0.0000:end=5.0000,setpts=PTS-STARTPTS,setpts=PTS/1.2000[v0]", graph)
        self.assertIn("[0:v]trim=start=10.0000:end=30.0000,setpts=PTS-STARTPTS,setpts=PTS/2.0000[v1]", graph)
        self.assertIn("[v0][v1]concat=n=2:v=1:a=0[outv_raw]", graph)
        self.assertIn("[outa_raw]dynaudnorm=f=150:g=15[outa]", graph)
        
        self.assertEqual(v_out, "[outv_raw]")
        self.assertEqual(a_out, "[outa]")


class TestVideoProcessorThread(unittest.TestCase):
    @patch("processor.get_video_duration")
    @patch("shutil.which")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("subprocess.run")
    @patch("subprocess.Popen")
    @patch("os.remove")
    @patch("os.close", side_effect=safe_os_close)
    def test_run_success_two_pass(self, mock_close, mock_remove, mock_popen, mock_run, mock_getsize, mock_exists, mock_which, mock_duration):
        mock_duration.side_effect = [100.0, 50.0] # 100s source, 50s edited
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_exists.return_value = True # auto-editor exists
        
        # Setup mock subprocesses for auto-editor (Pass 1) and ffmpeg (Pass 2)
        mock_process_ae = MagicMock()
        # auto-editor uses read_progress_lines which reads char-by-char. Provide StringIO stream.
        mock_process_ae.stdout = io.StringIO(
            "Analyzing audio volume |###| 50.0%\n"
            "Applying cuts and speedup |#####| 100.0%\n"
        )
        mock_process_ae.returncode = 0
        
        mock_process_ffmpeg = MagicMock()
        mock_process_ffmpeg.stdout = io.StringIO(
            "frame=100\n"
            "fps=30.0\n"
            "out_time_us=25000000\n" # 25s of 50s edited -> 50% of Pass 2 -> 30 + 0.5 * 68 = 64%
            "speed=2.0x\n"
        )
        mock_process_ffmpeg.returncode = 0
        
        mock_popen.side_effect = [mock_process_ae, mock_process_ffmpeg]
        
        progress_calls = []
        def progress_callback(pct, msg):
            progress_calls.append((pct, msg))
            
        config = {
            "cut_silence": True,
            "speed_up": True,
            "voice_boost": True,
            "noise_threshold": "-30dB",
            "crf": 35,
            "preset": "slow",
            "margin": 0.2
        }
        
        thread = VideoProcessorThread(
            input_path="input.mp4",
            output_path="output.mp4",
            config=config,
            progress_callback=progress_callback
        )
        
        # Verify temporary file cleanup setup
        with patch("tempfile.mkstemp") as mock_mkstemp:
            mock_mkstemp.return_value = (99, "temp_edited_file.mp4")
            thread.run()
            
        # Check some progress callback levels
        self.assertTrue(len(progress_calls) > 0)
        # Should terminate with 100% success msg
        self.assertEqual(progress_calls[-1][0], 100)
        self.assertIn("optimized successfully", progress_calls[-1][1])
        
        # Check deletion of temporary files
        mock_remove.assert_called_with("temp_edited_file.mp4")
        mock_close.assert_any_call(99)

    @patch("processor.get_video_duration")
    @patch("subprocess.run")
    @patch("subprocess.Popen")
    @patch("os.remove")
    @patch("os.close", side_effect=safe_os_close)
    def test_run_cancellation(self, mock_close, mock_remove, mock_popen, mock_run, mock_duration):
        mock_duration.return_value = 100.0
        
        # Setup run loop to terminate upon is_running flag
        mock_process = MagicMock()
        mock_process.stdout = io.StringIO("Analyzing audio volume |###| 10.0%\n")
        mock_process.returncode = -9 # killed code
        mock_popen.return_value = mock_process
        
        progress_calls = []
        def progress_callback(pct, msg):
            progress_calls.append((pct, msg))
            
        config = {
            "cut_silence": True,
            "speed_up": True,
            "voice_boost": False
        }
        
        thread = VideoProcessorThread(
            input_path="input.mp4",
            output_path="output.mp4",
            config=config,
            progress_callback=progress_callback
        )
        
        # Cancel right after launch simulated in callback
        def cancel_on_first_progress(pct, msg):
            progress_calls.append((pct, msg))
            thread.cancel()
            
        thread.progress_callback = cancel_on_first_progress
        
        with patch("tempfile.mkstemp") as mock_mkstemp:
            mock_mkstemp.return_value = (99, "temp_edited_file.mp4")
            thread.run()
            
        # Verify process is terminated
        mock_process.terminate.assert_called_once()
        self.assertIn("cancelled", progress_calls[-1][1])
        mock_close.assert_any_call(99)

if __name__ == "__main__":
    unittest.main()
