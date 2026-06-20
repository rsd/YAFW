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

        # Ensure bundled ffmpeg/ffprobe are on PATH before auto_editor loads
        bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        if bundle_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = bundle_dir + os.pathsep + os.environ.get("PATH", "")

        import auto_editor.__main__ as ae_mod

        # Monkey-patch: auto_editor.download_binary() tries to mkdir inside
        # its own package directory (e.g. C:\Program Files\...\auto_editor\bin),
        # which is read-only on Windows. Since we bundle ffmpeg, return
        # the already-available binary path instead.
        def _use_bundled_binary():
            ffmpeg_path = shutil.which("ffmpeg")
            if ffmpeg_path:
                return os.path.dirname(os.path.abspath(ffmpeg_path))
            raise FileNotFoundError("Bundled ffmpeg not found on PATH")

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

