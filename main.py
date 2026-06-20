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
    app = YafwApp(
        on_start_processing=start_processing,
        on_cancel_processing=cancel_processing
    )
    
    # Intercept window close protocols to prevent orphaned processes
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()
