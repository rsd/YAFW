import os
from PIL import Image

def generate_ico(png_path, ico_output_path):
    """
    Converts a PNG image to a multi-resolution ICO file using Pillow.
    """
    if not os.path.exists(png_path):
        print(f"Error: Source PNG icon not found at {png_path}")
        return False
        
    os.makedirs(os.path.dirname(ico_output_path), exist_ok=True)
    
    try:
        img = Image.open(png_path)
        # Sizes commonly recommended for Windows application icons
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(ico_output_path, format="ICO", sizes=sizes)
        print(f"Successfully generated Windows icon: {ico_output_path}")
        return True
    except Exception as e:
        print(f"Failed to convert icon: {e}")
        return False

if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Convert PNG icon to Windows multi-resolution ICO.")
    parser.add_argument("src_png", nargs="?", default="assets/icon.png", help="Path to source PNG icon")
    parser.add_argument("dest_ico", nargs="?", default="assets/icon.ico", help="Path to output ICO file")
    args = parser.parse_args()

    src_png = args.src_png
    if not os.path.exists(src_png):
        # Auto-detect any alternative PNG inside assets directory
        png_files = [f for f in os.listdir("assets") if f.endswith(".png")] if os.path.exists("assets") else []
        if png_files:
            src_png = os.path.join("assets", png_files[0])
            print(f"[YAFW Assets] Default PNG not found, using auto-detected: {src_png}")
        else:
            print(f"[YAFW Assets] Error: Source PNG icon not found. Please place a PNG at {src_png}")
            sys.exit(1)

    generate_ico(src_png, args.dest_ico)
