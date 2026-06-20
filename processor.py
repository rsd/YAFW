import os
import sys
import json
import subprocess
import threading
import tempfile
import static_ffmpeg

# Initialize static-ffmpeg and add it to the environment PATH
static_ffmpeg.add_paths()

def get_video_duration(video_path):
    """
    Retrieves the total duration of the video in seconds using ffprobe.
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return 0.0

def build_filtergraph(timeline_json_path, cut_silence=True, speed_up=True, speed_val=1.2, voice_boost=False, total_duration=0.0):
    """
    Parses the auto-editor .v3 timeline JSON and constructs the ffmpeg filtergraph.
    If cut_silence is False, it will only apply speed and voice boost to the whole file.
    """
    if not cut_silence:
        # Simple path without cuts
        filter_parts = []
        video_out = "[0:v]"
        audio_out = "[0:a]"

        expected_output_duration = total_duration
        if speed_up and abs(speed_val - 1.0) > 1e-4:
            filter_parts.append(f"[0:v]setpts=PTS/{speed_val:.4f}[outv_raw]")
            filter_parts.append(f"[0:a]atempo={speed_val:.4f}[outa_raw]")
            video_out = "[outv_raw]"
            audio_out = "[outa_raw]"
            expected_output_duration = total_duration / speed_val

        if voice_boost:
            filter_parts.append(f"{audio_out}dynaudnorm=f=150:g=15[outa]")
            audio_out = "[outa]"
        elif audio_out == "[outa_raw]":
            filter_parts.append("[outa_raw]anull[outa]")
            audio_out = "[outa]"

        return ";\n".join(filter_parts), video_out, audio_out, expected_output_duration

    # Parse auto-editor timeline
    with open(timeline_json_path, 'r') as f:
        data = json.load(f)

    # Detect frame rate (timebase)
    timebase_str = data.get("timebase", "30/1")
    try:
        if "/" in timebase_str:
            num, den = timebase_str.split("/")
            fps = float(num) / float(den)
        else:
            fps = float(timebase_str)
    except Exception:
        fps = 30.0

    v_tracks = data.get("v", [])
    a_tracks = data.get("a", [])

    v_clips = v_tracks[0] if v_tracks else []
    a_clips = a_tracks[0] if a_tracks else []

    if not v_clips and not a_clips:
        # Fallback: empty timeline (everything cut)
        return "", None, None, 0.0

    filter_parts = []
    n_v = len(v_clips)
    n_a = len(a_clips)

    # Calculate expected final duration
    expected_output_duration = 0.0
    clips_for_duration = v_clips if v_clips else a_clips
    for clip in clips_for_duration:
        clip_speed = 1.0
        effects = clip.get("effects", [])
        for eff in effects:
            if eff.startswith("speed:"):
                try:
                    clip_speed = float(eff.split(":")[1])
                except ValueError:
                    pass
        if not speed_up:
            target_speed = 1.0
        else:
            target_speed = clip_speed if abs(clip_speed - 1.0) > 1e-4 else speed_val
        expected_output_duration += (clip["dur"] / target_speed) / fps

    # 1. Process Video clips
    for i, clip in enumerate(v_clips):
        offset = clip["offset"]
        dur = clip["dur"]
        
        # Determine speed multiplier in the clip
        clip_speed = 1.0
        effects = clip.get("effects", [])
        for eff in effects:
            if eff.startswith("speed:"):
                try:
                    clip_speed = float(eff.split(":")[1])
                except ValueError:
                    pass
        
        # Determine target speed for this segment
        if not speed_up:
            target_speed = 1.0
        else:
            # If the clip already has a speed, keep it, otherwise use speed_val
            target_speed = clip_speed if abs(clip_speed - 1.0) > 1e-4 else speed_val

        # Source duration is based on the original clip speed
        src_dur = dur * clip_speed
        start_sec = offset / fps
        end_sec = (offset + src_dur) / fps

        # Trim & speed adjustment
        filter_parts.append(
            f"[0:v]trim=start={start_sec:.4f}:end={end_sec:.4f},setpts=PTS-STARTPTS,setpts=PTS/{target_speed:.4f}[v{i}]"
        )

    # 2. Process Audio clips
    for i, clip in enumerate(a_clips):
        offset = clip["offset"]
        dur = clip["dur"]
        
        clip_speed = 1.0
        effects = clip.get("effects", [])
        for eff in effects:
            if eff.startswith("speed:"):
                try:
                    clip_speed = float(eff.split(":")[1])
                except ValueError:
                    pass

        if not speed_up:
            target_speed = 1.0
        else:
            target_speed = clip_speed if abs(clip_speed - 1.0) > 1e-4 else speed_val

        src_dur = dur * clip_speed
        start_sec = offset / fps
        end_sec = (offset + src_dur) / fps

        # Trim & speed stretch
        if abs(target_speed - 1.0) > 1e-4:
            # Handle stretching with atempo (requires chaining if speed > 2.0, but 1.2 is fine)
            filter_parts.append(
                f"[0:a]atrim=start={start_sec:.4f}:end={end_sec:.4f},asetpts=PTS-STARTPTS,atempo={target_speed:.4f}[a{i}]"
            )
        else:
            filter_parts.append(
                f"[0:a]atrim=start={start_sec:.4f}:end={end_sec:.4f},asetpts=PTS-STARTPTS[a{i}]"
            )

    # 3. Concatenate video segments
    if n_v > 0:
        v_inputs = "".join(f"[v{i}]" for i in range(n_v))
        filter_parts.append(f"{v_inputs}concat=n={n_v}:v=1:a=0[outv_raw]")
        video_out = "[outv_raw]"
    else:
        video_out = None

    # 4. Concatenate audio segments
    if n_a > 0:
        a_inputs = "".join(f"[a{i}]" for i in range(n_a))
        filter_parts.append(f"{a_inputs}concat=n={n_a}:v=0:a=1[outa_raw]")
        audio_out = "[outa_raw]"
    else:
        audio_out = None

    # 5. Apply voice boost / audio normalization if requested
    if audio_out and voice_boost:
        filter_parts.append(f"{audio_out}dynaudnorm=f=150:g=15[outa]")
        audio_out = "[outa]"
    elif audio_out == "[outa_raw]":
        filter_parts.append("[outa_raw]anull[outa]")
        audio_out = "[outa]"

    return ";\n".join(filter_parts), video_out, audio_out, expected_output_duration


def read_progress_lines(stream):
    """
    Generator that yields lines delimited by either \n or \r from a text stream.
    Useful for reading in-place progress updates from CLI tools.
    """
    buffer = []
    while True:
        char = stream.read(1)
        if not char:
            if buffer:
                yield "".join(buffer)
            break
        if char in ('\r', '\n'):
            if buffer:
                yield "".join(buffer)
                buffer = []
        else:
            buffer.append(char)


class VideoProcessorThread(threading.Thread):
    """
    Asynchronous thread to run the video analysis and processing pipeline.
    Prevents GUI freeze and posts progress updates.
    """
    def __init__(self, input_path, output_path, config, progress_callback):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.config = config  # Dict containing: cut_silence, speed_up, voice_boost, noise_threshold, crf, preset, margin
        self.progress_callback = progress_callback
        self.is_running = True
        self.process = None

    def run(self):
        temp_edited_path = None
        filter_script = None
        try:
            total_duration = get_video_duration(self.input_path)
            if total_duration <= 0.0:
                self.progress_callback(0, "Error: Invalid video file or could not read duration.")
                return

            # Determine virtual environment paths to call binaries
            python_dir = os.path.dirname(sys.executable)
            auto_editor_bin = os.path.join(python_dir, "auto-editor")
            if not os.path.exists(auto_editor_bin):
                # Fallback to general lookup
                auto_editor_bin = "auto-editor"

            if self.config.get("cut_silence", True):
                # =====================================================================
                # TWO-PASS PIPELINE (To prevent FFmpeg demuxer deadlock on long files)
                # =====================================================================
                self.progress_callback(2, "Initializing cut analysis...")
                
                # Create a temporary file to store the intermediate edited video
                fd, temp_edited_path = tempfile.mkstemp(suffix="_edited.mp4")
                os.close(fd)

                # Formulate auto-editor command to execute cuts and speedup
                threshold = self.config.get("noise_threshold", "-30dB")
                margin = self.config.get("margin", 0.2)
                speed_val = 1.2 if self.config.get("speed_up", True) else 1.0

                ae_cmd = [
                    auto_editor_bin,
                    self.input_path,
                    "--edit", f"audio:threshold={threshold}",
                    "--margin", f"{margin}s",
                    "--no-open",
                    "-o", temp_edited_path
                ]
                
                if self.config.get("speed_up", True):
                    ae_cmd.extend(["--when-normal", f"speed:{speed_val}"])

                # Run auto-editor and parse in-place progress reports
                print(f"\n[YAFW Backend] Running silence cut pass via auto-editor:\n{' '.join(ae_cmd)}\n")
                self.process = subprocess.Popen(
                    ae_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in read_progress_lines(self.process.stdout):
                    if not self.is_running:
                        break
                    
                    if "Analyzing audio" in line:
                        if "%" in line:
                            try:
                                pct_str = line.split("|")[2].split("%")[0].strip()
                                pct = float(pct_str)
                                overall_pct = int(pct * 0.05) # Map to 0-5%
                                self.progress_callback(overall_pct, f"Analyzing audio volume: {pct:.1f}%")
                            except Exception:
                                pass
                    elif "|" in line and "%" in line:
                        try:
                            pct_str = line.split("|")[2].split("%")[0].strip()
                            pct = float(pct_str)
                            overall_pct = 5 + int(pct * 0.65) # Map rendering cuts to 5-70%
                            self.progress_callback(overall_pct, f"Cutting silences and speedup: {pct:.1f}%")
                        except Exception:
                            pass

                self.process.wait()

                if self.process.returncode != 0:
                    if self.is_running:
                        self.progress_callback(0, "Error: Silence cutting pass failed.")
                    else:
                        self.progress_callback(0, "Process cancelled by user.")
                    return

                if not os.path.exists(temp_edited_path) or os.path.getsize(temp_edited_path) == 0:
                    self.progress_callback(0, "Error: Failed to generate intermediate edited video.")
                    return

                # Get duration of intermediate video for exact encoding progress metrics
                edited_duration = get_video_duration(temp_edited_path)

                # Pass 2: Run FFmpeg to normalize audio (dynaudnorm) and compress to H.265 (libx265)
                self.progress_callback(70, "Optimizing and encoding H.265 video...")
                crf = self.config.get("crf", 26)
                preset = self.config.get("preset", "medium")

                ffmpeg_cmd = [
                    "ffmpeg",
                    "-y",
                    "-progress", "-", # Send progress output to stdout
                    "-i", temp_edited_path
                ]

                # Apply Voice Boost (dynaudnorm) if requested
                if self.config.get("voice_boost", False):
                    ffmpeg_cmd.extend(["-filter_complex", "[0:a]dynaudnorm=f=150:g=15[outa]"])
                    ffmpeg_cmd.extend(["-map", "0:v", "-map", "[outa]"])
                else:
                    ffmpeg_cmd.extend(["-map", "0:v", "-map", "0:a"])

                # Video properties (H.265 optimal compression)
                ffmpeg_cmd.extend([
                    "-c:v", "libx265",
                    "-crf", str(crf),
                    "-preset", preset,
                    "-tag:v", "hvc1" # Ensure maximum compatibility with Apple QuickTime/macOS
                ])

                # Audio properties
                ffmpeg_cmd.extend([
                    "-c:a", "aac",
                    "-b:a", "128k"
                ])

                ffmpeg_cmd.append(self.output_path)

                print(f"\n[YAFW Backend] Running FFmpeg transcoding pass (H.265 + Voice Boost):\n{' '.join(ffmpeg_cmd)}\n")
                self.process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in self.process.stdout:
                    if not self.is_running:
                        break
                    
                    if line.startswith("out_time_us="):
                        try:
                            time_us = float(line.split("=")[1].strip())
                            current_sec = time_us / 1000000.0
                            
                            dur_limit = edited_duration if edited_duration > 0.0 else total_duration
                            pass2_ratio = min(1.0, max(0.0, current_sec / dur_limit))
                            overall_pct = 70 + int(pass2_ratio * 28) # Map 70% to 98%
                            self.progress_callback(overall_pct, f"H.265 Encoding: {overall_pct}%")
                        except Exception:
                            pass

                self.process.wait()

                if self.process.returncode == 0:
                    self.progress_callback(100, "Done! Video optimized successfully.")
                else:
                    if self.is_running:
                        self.progress_callback(0, f"Processing failed (exit code {self.process.returncode}).")
                    else:
                        self.progress_callback(0, "Process cancelled by user.")

            else:
                # =====================================================================
                # SINGLE-PASS PIPELINE (Only speedup and/or audio normalize, no cuts)
                # =====================================================================
                self.progress_callback(5, "Building optimization filters...")
                speed_val = 1.2 if self.config.get("speed_up", True) else 1.0
                
                filtergraph, video_out, audio_out, expected_output_duration = build_filtergraph(
                    timeline_json_path=None,
                    cut_silence=False,
                    speed_up=self.config.get("speed_up", True),
                    speed_val=speed_val,
                    voice_boost=self.config.get("voice_boost", False),
                    total_duration=total_duration
                )

                # Write the filtergraph to a temp file to avoid Windows command line limits
                fd_f, filter_script = tempfile.mkstemp(suffix=".txt")
                with open(fd_f, 'w') as f:
                    f.write(filtergraph)

                crf = self.config.get("crf", 26)
                preset = self.config.get("preset", "medium")

                ffmpeg_cmd = [
                    "ffmpeg",
                    "-y",
                    "-progress", "-", 
                    "-i", self.input_path,
                    "-filter_complex_script", filter_script
                ]

                if video_out:
                    ffmpeg_cmd.extend(["-map", video_out])
                if audio_out:
                    ffmpeg_cmd.extend(["-map", audio_out])

                ffmpeg_cmd.extend([
                    "-c:v", "libx265",
                    "-crf", str(crf),
                    "-preset", preset,
                    "-tag:v", "hvc1",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    self.output_path
                ])

                print(f"\n[YAFW Backend] Running FFmpeg single-pass optimization command:\n{' '.join(ffmpeg_cmd)}\n")
                self.process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in self.process.stdout:
                    if not self.is_running:
                        break
                    
                    if line.startswith("out_time_us="):
                        try:
                            time_us = float(line.split("=")[1].strip())
                            current_sec = time_us / 1000000.0
                            
                            dur_limit = expected_output_duration if expected_output_duration > 0.0 else total_duration
                            ratio = min(1.0, max(0.0, current_sec / dur_limit))
                            overall_pct = 10 + int(ratio * 88) # Map 10% to 98%
                            self.progress_callback(overall_pct, f"H.265 Encoding: {overall_pct}%")
                        except Exception:
                            pass

                self.process.wait()

                if self.process.returncode == 0:
                    self.progress_callback(100, "Done! Video optimized successfully.")
                else:
                    if self.is_running:
                        self.progress_callback(0, f"Processing failed (exit code {self.process.returncode}).")
                    else:
                        self.progress_callback(0, "Process cancelled by user.")

        except Exception as e:
            self.progress_callback(0, f"Exception during run: {str(e)}")

        finally:
            # Clean up temp files
            if temp_edited_path and os.path.exists(temp_edited_path):
                try:
                    os.remove(temp_edited_path)
                except OSError:
                    pass
            if filter_script and os.path.exists(filter_script):
                try:
                    os.remove(filter_script)
                except OSError:
                    pass

    def cancel(self):
        """
        Kills the running subprocesses and stops the thread.
        """
        self.is_running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
