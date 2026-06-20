import os
import re
import sys
import urllib.request
import zipfile
import subprocess

def read_version():
    """
    Reads the current version from version.py.

    Returns:
        The version string (e.g. "1.1.5").
    """
    with open("version.py", "r") as f:
        content = f.read()
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if not match:
        print("[YAFW Build] Error: Could not parse version from version.py")
        sys.exit(1)
    return match.group(1)

def bump_patch_version(version_str):
    """
    Increments the patch component of a semantic version string.

    Args:
        version_str: A version string in "major.minor.patch" format.

    Returns:
        The bumped version string.
    """
    parts = version_str.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)

def write_version(new_version):
    """
    Writes the new version back to version.py.

    Args:
        new_version: The new version string to write.
    """
    with open("version.py", "w") as f:
        f.write(f'__version__ = "{new_version}"\n')
    print(f"[YAFW Build] Bumped version.py to {new_version}")

def update_setup_iss(new_version):
    """
    Updates AppVersion and OutputBaseFilename in setup.iss to include the new version.

    Args:
        new_version: The version string to embed.
    """
    with open("setup.iss", "r") as f:
        content = f.read()

    content = re.sub(r'AppVersion=.*', f'AppVersion={new_version}', content)
    content = re.sub(r'OutputBaseFilename=.*', f'OutputBaseFilename=YAFW_Setup_{new_version}', content)

    with open("setup.iss", "w") as f:
        f.write(content)
    print(f"[YAFW Build] Updated setup.iss to version {new_version}")

def download_ffmpeg_binaries():
    """
    Downloads static Windows FFmpeg/FFprobe binaries from gyan.dev and extracts them to bin/.
    """
    bin_dir = "bin"
    binaries = ["ffmpeg.exe", "ffprobe.exe"]
    target_paths = [os.path.join(bin_dir, b) for b in binaries]
    
    if all(os.path.exists(p) for p in target_paths):
        print("[YAFW Build] Windows FFmpeg binaries already present in bin/ folder.")
        return True

    os.makedirs(bin_dir, exist_ok=True)
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = "ffmpeg_temp.zip"

    print(f"[YAFW Build] Downloading Windows FFmpeg/FFprobe from {url}...")
    try:
        urllib.request.urlretrieve(url, zip_path)
        print("[YAFW Build] Extracting binaries to bin/...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                filename = os.path.basename(member)
                if filename in binaries:
                    # Extract directly to the bin directory
                    source = zip_ref.open(member)
                    target_path = os.path.join(bin_dir, filename)
                    with source, open(target_path, "wb") as target:
                        target.write(source.read())
                    print(f"[YAFW Build] Extracted: {target_path}")
        os.remove(zip_path)
        return True
    except Exception as e:
        print(f"[YAFW Build] Error obtaining FFmpeg binaries: {e}")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        return False

def run_docker_builds():
    """
    Runs PyInstaller and Inno Setup compilation commands using Docker.
    """
    current_dir = os.getcwd()
    
    # 1. Compile Windows Executable via batonogov/pyinstaller-windows:latest
    print("[YAFW Build] Step 1: Compiling Windows executable using batonogov/pyinstaller-windows Docker image...")
    pyinstaller_cmd = [
        "docker", "run", "--rm",
        "-v", f"{current_dir}:/src",
        "batonogov/pyinstaller-windows:latest",
        "pyinstaller --noconfirm YAFW.spec"
    ]
    
    try:
        subprocess.run(pyinstaller_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[YAFW Build] PyInstaller compilation failed: {e}")
        return False

    # 2. Compile Windows Installer via amake/innosetup
    print("[YAFW Build] Step 2: Compiling Windows Installer using amake/innosetup Docker image...")
    innosetup_cmd = [
        "docker", "run", "--rm",
        "-v", f"{current_dir}:/work",
        "amake/innosetup",
        "setup.iss"
    ]

    try:
        subprocess.run(innosetup_cmd, check=True)
        new_version = read_version()
        print(f"[YAFW Build] Build succeeded! Installer: dist-installer/YAFW_Setup_{new_version}.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[YAFW Build] Inno Setup compilation failed: {e}")
        return False

if __name__ == "__main__":
    # Step 0: Auto-increment patch version
    current_version = read_version()
    new_version = bump_patch_version(current_version)
    write_version(new_version)
    update_setup_iss(new_version)
    print(f"[YAFW Build] Building YAFW v{new_version}")

    if not download_ffmpeg_binaries():
        sys.exit(1)
        
    if not run_docker_builds():
        sys.exit(1)
