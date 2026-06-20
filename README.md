# YAFW (Yet Another FFmpeg Wrapper)

YAFW is a premium, lightweight desktop utility designed to optimize long-form talking-head videos, online lectures, and Zoom recordings. It automates silence cutting, speeds up video playback to 1.2x (preserving original audio pitch), normalizes varying audio levels, and compresses the final output using high-efficiency H.265 (HEVC) encoding.

![YAFW GUI Concept Mockup](https://raw.githubusercontent.com/raul/YAFW/main/docs/mockup.png) *(Concept visualization from design phase)*

---

## Key Features

- **Silence Trimming**: Leverages automated decibel-threshold analysis to identify and strip silent pauses from the video.
- **Pitch-Preserved Speedup**: Speeds up active video sections to 1.2x while preserving original voice pitch using FFmpeg's `atempo` filter.
- **Voice Boost (Dynamic Audio Normalization)**: Levels speech volumes automatically (utilizing FFmpeg's `dynaudnorm` filter) so quiet student comments and loud lectures match comfortable listening levels.
- **H.265 (HEVC) Compression**: Defaults to H.265 CPU encoding with a Constant Rate Factor (CRF) of 26, optimal for slide presentations (visually lossless text with file size reductions up to 90%).
- **Single-Pass Pipeline**: Generates an Edit Decision List (EDL) and compiles it into a single, complex FFmpeg filtergraph script. The cutting, speed adjustment, audio normalization, and transcoding happen in one pass to avoid massive intermediate files and save CPU cycles.
- **Zero-Setup Portability**: Leverages `static-ffmpeg` to automatically fetch, verify, and bundle static platform-specific FFmpeg/FFprobe binaries on the first run.

---

## Installation & Running

Follow the instructions below matching your environment path.

### 1. For Native/Local Users (Recommended Setup)

To run YAFW natives on your local workstation (e.g. Arch Linux rig):

1. **Verify Python**: Ensure Python 3.8+ is installed.
   ```bash
   python3 --version
   ```

2. **Clone and Navigate**:
   ```bash
   git clone <repository_url> YAFW
   cd YAFW
   ```

3. **Initialize Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Run the Application**:
   ```bash
   python3 main.py
   ```

---

### 2. For Docker/Sail Users (Standard Containerized GUI)

If you run services in isolated containers, you must forward the X11 display socket from your host to the container to render the Tkinter GUI.

#### Dockerfile Configuration
Create a `Dockerfile` in the root directory:
```dockerfile
FROM python:3.11-slim

# Install system dependencies for Tkinter and X11
RUN apt-get update && apt-get install -y \
    python3-tk \
    libx11-6 \
    libxext-6 \
    libxrender-1 \
    libxkbcommon-x11-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

#### Docker Compose Configuration
Create a `docker-compose.yml` to set up environment mapping:
```yaml
version: '3.8'

services:
  yafw:
    build: .
    container_name: yafw_app
    environment:
      - DISPLAY=${DISPLAY}
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:ro
      - .:/app
    ipc: host
    network_mode: host
```

#### Running Containerized
1. **Grant local container display access**:
   ```bash
   xhost +local:docker
   ```
2. **Build and start the container**:
   ```bash
   docker compose build
   docker compose up
   ```
3. **Revoke display access after closing**:
   ```bash
   xhost -local:docker
   ```

---

## Advanced Adjustments

Clicking **Advanced Settings** in the GUI expands details for custom parameter tuning:
- **Quality (CRF)**: Set constant rate factor. Defaults to `26` (highly compressed slide presentation). Lower values (e.g. `20-22`) result in near-lossless output at the cost of file size.
- **Encoding Preset**: Select encoding speeds. Default is `medium` which balances file size compression and time.
- **Silence Threshold**: Specify decibel limits (e.g. `-35dB` for quiet rooms, `-25dB` for noisy rooms) or percentage markers (e.g. `4%`) to tweak silent cut points.
- **Cut Margin**: Adjust padding buffers (default `0.2s`) before and after loud sections to prevent word truncation.

---

## Code Architecture

- **[main.py](file:///home/raul/Devel/Utilities/YAFW/main.py)**: Application entry. Orchestrates safe event mapping and handles main window closing protocols.
- **[ui.py](file:///home/raul/Devel/Utilities/YAFW/ui.py)**: CustomTkinter layout widgets and window behaviors.
- **[processor.py](file:///home/raul/Devel/Utilities/YAFW/processor.py)**: Threaded file processing engine, timeline parser, and progress tracker.
