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
    src_png = "/home/raul/.gemini/antigravity-ide/brain/3c4a1371-9057-4862-9b1e-82175d6f2350/yafw_icon_1781985723280.png"
    dest_ico = "assets/icon.ico"
    generate_ico(src_png, dest_ico)
