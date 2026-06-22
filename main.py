import sys
from ui import YafwApp
from processor import VideoProcessorThread

# Track the running worker thread globally
active_thread = None

def start_processing(input_path, output_path, config):
    """
    Spawns the worker thread to process the video.
    """
    global active_thread
    
    def progress_callback(percent, status_message):
        # Update GUI on the main thread safely
        if app.winfo_exists():
            app.after(0, lambda: app.update_progress(percent, status_message))
        
    active_thread = VideoProcessorThread(input_path, output_path, config, progress_callback)
    active_thread.start()

def cancel_processing():
    """
    Cancels the active processor and clean up.
    """
    global active_thread
    if active_thread:
        active_thread.cancel()
        active_thread = None

def on_closing():
    """
    Handles cleanup if the user closes the main window.
    """
    cancel_processing()
    app.destroy()

if __name__ == "__main__":
    # Handle module execution in frozen PyInstaller bundles.
    # When processor.py spawns [sys.executable, "-m", "auto_editor", ...],
    # the frozen exe re-enters here. We intercept and route to auto_editor
    # directly, bypassing the GUI and patching out binary downloads that
    # would fail with PermissionError in read-only install directories.
    if len(sys.argv) > 2 and sys.argv[1] == "-m" and sys.argv[2] == "auto_editor":
        import os
        import shutil
        import tempfile

        # Ensure bundled ffmpeg/ffprobe are on PATH before auto_editor loads
        bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        if bundle_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = bundle_dir + os.pathsep + os.environ.get("PATH", "")

        # Create a writable cache directory for auto_editor.
        # auto_editor resolves Path(__file__).parent for binary downloads and
        # temp storage. Inside a frozen bundle (especially under Program Files)
        # that directory is read-only, causing WinError 5.
        ae_cache = os.path.join(tempfile.gettempdir(), "yafw_ae_cache")
        os.makedirs(ae_cache, exist_ok=True)

        import auto_editor
        import auto_editor.__main__ as ae_mod

        # Redirect __file__ so Path(__file__).parent resolves to the writable cache
        auto_editor.__file__ = os.path.join(ae_cache, "__init__.py")
        ae_mod.__file__ = os.path.join(ae_cache, "__main__.py")

        # Locate the bundled auto-editor binary
        ae_name = "auto-editor.exe" if sys.platform == "win32" else "auto-editor"
        bundled_bin = os.path.join(bundle_dir, ae_name)
        target_bin = os.path.join(ae_cache, "bin", ae_name)

        def _sync_bundled_binary():
            """
            Copies the bundled auto-editor binary into the writable cache (only
            when missing or stale) and returns its Path, or None if no bundled
            binary is present. Single source for both the cache pre-population
            and the download_binary monkeypatch below.
            """
            if not os.path.exists(bundled_bin):
                return None
            os.makedirs(os.path.dirname(target_bin), exist_ok=True)
            if not os.path.exists(target_bin) or os.path.getsize(target_bin) != os.path.getsize(bundled_bin):
                shutil.copy2(bundled_bin, target_bin)
                if sys.platform != "win32":
                    os.chmod(target_bin, 0o755)
            from pathlib import Path
            return Path(target_bin)

        # Pre-populate the cache if possible to skip download checks (best-effort).
        try:
            _sync_bundled_binary()
        except Exception:
            pass

        # Monkey-patch download_binary to copy and return the writable executable Path
        def _use_bundled_binary():
            target = _sync_bundled_binary()
            if target is None:
                raise FileNotFoundError("Bundled auto-editor binary not found")
            return target

        ae_mod.download_binary = _use_bundled_binary

        sys.argv = [sys.argv[0]] + sys.argv[3:]
        ae_mod.main()
        sys.exit(0)

    app = YafwApp(
        on_start_processing=start_processing,
        on_cancel_processing=cancel_processing
    )
    
    # Intercept window close protocols to prevent orphaned processes
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()

