import os
import sys
import subprocess
import shutil
import time

# Ensure we can load static-ffmpeg paths
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except ImportError:
    print("Could not import static_ffmpeg, relying on system PATH")

ffmpeg_bin = shutil.which("ffmpeg")
ffprobe_bin = shutil.which("ffprobe")
print(f"FFmpeg: {ffmpeg_bin}")
print(f"FFprobe: {ffprobe_bin}")

if not ffmpeg_bin:
    print("Error: ffmpeg binary not found!")
    sys.exit(1)

# Step 1: Generate a 10s test video with silent sections from t=2..6 and t=8..10
input_video = "test_input.mp4"
output_video = "test_output.mp4"

# Remove old test files if they exist
for f in [input_video, output_video]:
    if os.path.exists(f):
        os.remove(f)

print("Generating 10-second test video with silent sections...")
gen_cmd = [
    ffmpeg_bin,
    "-y",
    "-f", "lavfi", "-i", "testsrc=duration=10:size=1280x720:rate=30",
    "-f", "lavfi", "-i", "sine=frequency=440:beep_factor=4:duration=10",
    "-filter_complex", "[1:a]volume=enable='between(t,2,6)+between(t,8,10)':volume=0[a]",
    "-map", "0:v", "-map", "[a]",
    "-c:v", "libx264", "-c:a", "aac",
    input_video
]

res = subprocess.run(gen_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
if res.returncode != 0:
    print("Error generating test video:")
    print(res.stderr)
    sys.exit(1)

print(f"Successfully generated {input_video}")

# Step 2: Run the VideoProcessorThread from processor.py
from processor import VideoProcessorThread

config = {
    "cut_silence": True,
    "speed_up": True,
    "voice_boost": True,
    "noise_threshold": "-30dB",
    "crf": 35,
    "preset": "slow",
    "margin": 0.2
}

def progress_callback(pct, msg):
    print(f"[Progress {pct}%]: {msg}")

print("Starting YAFW processing thread...")
processor = VideoProcessorThread(
    input_path=input_video,
    output_path=output_video,
    config=config,
    progress_callback=progress_callback
)

start_time = time.time()
processor.start()
processor.join()
end_time = time.time()

print(f"Processing finished in {end_time - start_time:.2f} seconds.")

if os.path.exists(output_video) and os.path.getsize(output_video) > 0:
    print(f"Success! Output file generated at {output_video}")
    # Print output file size and duration
    try:
        from processor import get_video_duration
        orig_dur = get_video_duration(input_video)
        new_dur = get_video_duration(output_video)
        print(f"Original duration: {orig_dur:.2f}s")
        print(f"Optimized duration: {new_dur:.2f}s")
    except Exception as e:
        print(f"Error checking duration: {e}")
else:
    print("Error: Output file was not generated or is empty.")
