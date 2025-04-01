#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import platform
from typing import List, Optional, Tuple
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def build_for_platform(target_system: str, dist_dir: str) -> bool:
    """Build the application for a specific platform."""
    print(Fore.CYAN + f"\nBuilding for {target_system}...")
    
    # Set platform-specific variables
    path_separator = ';' if target_system == 'Windows' else ':'
    executable_extension = '.exe' if target_system == 'Windows' else ''
    icon_extension = '.ico' if target_system == 'Windows' else '.icns'
    
    # Path to cli.py file
    cli_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cli.py')
    if not os.path.exists(cli_path):
        print(Fore.RED + f"❌ cli.py file not found at: {cli_path}")
        return False
    
    # Add icon if it exists
    icon_param = []
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'icon{icon_extension}')
    if os.path.exists(icon_path):
        icon_param = ["--icon", icon_path]
        print(Fore.GREEN + f"✓ Using icon from: {os.path.basename(icon_path)}")
    
    # List of files to include in the package
    print(Fore.BLUE + "\n⏳ Preparing necessary files...")
    
    # Find any config.json file
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    data_files = []
    
    if os.path.exists(config_path):
        data_files.append((config_path, "."))
        print(Fore.GREEN + "✓ Found config.json - will be included")
    
    # Find and include .env file if it exists
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        data_files.append((env_path, "."))
        print(Fore.GREEN + "✓ Found .env file - will be included")
    
    # Format data files for PyInstaller
    datas = []
    for file_path, dest_dir in data_files:
        datas.extend(["--add-data", f"{file_path}{path_separator}{dest_dir}"])
    
    # List of hidden imports required by CLI
    hiddenimports = [
        "--hidden-import", "watchdog.observers.polling",
        "--hidden-import", "watchdog.observers.inotify",
        "--hidden-import", "watchdog.observers.fsevents",
        "--hidden-import", "watchdog.observers.kqueue",
        "--hidden-import", "google.generativeai",
        "--hidden-import", "google.ai.generativelanguage",
        "--hidden-import", "python-dotenv",
        "--hidden-import", "colorama",
        "--hidden-import", "rich",
        "--hidden-import", "tqdm",
    ]
    
    # Add platform-specific hidden imports
    if target_system == 'Windows':
        hiddenimports.extend([
            "--hidden-import", "msvcrt",
        ])
    elif target_system == 'Darwin':  # macOS
        hiddenimports.extend([
            "--hidden-import", "termios",
            "--hidden-import", "fcntl",
        ])
    
    # Add common hidden imports for both platforms
    hiddenimports.extend([
        "--hidden-import", "select",
        "--hidden-import", "shutil",
    ])
    
    # Other options
    options = [
        "--name", f"CursorFocus_{target_system.lower()}",
        "--onefile",
        "--console",
        "--noconfirm",
    ]
    
    # All parameters
    pyinstaller_args = [
        "pyinstaller",
        *options,
        *icon_param,
        *datas,
        *hiddenimports,
        cli_path
    ]
    
    print(Fore.CYAN + "\n⚙️ PyInstaller Configuration:")
    print(Fore.WHITE + f"• Application name: {Fore.CYAN}CursorFocus_{target_system.lower()}")
    print(Fore.WHITE + f"• Source file: {Fore.MAGENTA}{cli_path}")
    print(Fore.WHITE + f"• Package type: {Fore.CYAN}Single file executable")
    print(Fore.WHITE + f"• Platform: {Fore.CYAN}{target_system}")
    
    # Start packaging
    print(Fore.BLUE + "\n🚀 Packaging the application...")
    try:
        subprocess.run(pyinstaller_args, check=True)
        
        # Set the expected executable name based on the platform
        executable_name = f"CursorFocus_{target_system.lower()}{executable_extension}"
        executable_path = os.path.join(dist_dir, executable_name)
        
        if os.path.exists(executable_path):
            print(Fore.GREEN + f"\n✅ Packaging successful for {target_system}!")
            print(Fore.WHITE + f"📦 Executable file: {Fore.MAGENTA}{executable_path}")
            
            # Make executable on macOS
            if target_system == 'Darwin':
                try:
                    subprocess.run(["chmod", "+x", executable_path], check=True)
                    print(Fore.GREEN + "✅ Made executable file runnable on macOS")
                except subprocess.SubprocessError as e:
                    print(Fore.YELLOW + f"⚠️ Could not set executable permissions: {e}")
            return True
        else:
            print(Fore.RED + f"\n❌ Could not find {executable_name} file after packaging")
            return False
    except subprocess.SubprocessError as e:
        print(Fore.RED + f"\n❌ Error during packaging for {target_system}: {e}")
        return False

def build_executable():
    """Build the application into executable files for multiple platforms."""
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print(Fore.CYAN + Style.BRIGHT + "                CURSORFOCUS PACKAGER".center(60))
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    
    # Detect current operating system
    current_system = platform.system()
    print(Fore.CYAN + f"Current operating system: {current_system}")
    
    # Create dist directory if it doesn't exist
    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)
    
    # Build for current platform
    success = build_for_platform(current_system, dist_dir)
    
    # Copy example files if they exist
    examples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'examples')
    if os.path.exists(examples_dir):
        examples_dist = os.path.join(dist_dir, 'examples')
        if not os.path.exists(examples_dist):
            os.makedirs(examples_dist)
            
        for item in os.listdir(examples_dir):
            src = os.path.join(examples_dir, item)
            dst = os.path.join(examples_dist, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
        
        print(Fore.GREEN + f"✅ Example files copied to: {examples_dist}")
    
    if success:
        print(Fore.GREEN + "\n✅ Build process completed successfully!")
        print(Fore.CYAN + "\n📦 Build outputs:")
        executable_name = f"CursorFocus_{current_system.lower()}{'.exe' if current_system == 'Windows' else ''}"
        executable_path = os.path.join(dist_dir, executable_name)
        if os.path.exists(executable_path):
            print(Fore.WHITE + f"• {executable_name}")
    else:
        print(Fore.RED + "\n❌ Build process completed with errors")
        sys.exit(1)  # Exit with error code for GitHub Actions

def check_dependencies():
    """Check and install required dependencies."""
    required_packages = [
        "colorama",
        "rich",
        "python-dotenv",
        "google-generativeai",
        "watchdog",
        "tqdm",
        "requests"
    ]
    
    print(Fore.CYAN + "Checking required dependencies...")
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(Fore.GREEN + f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(Fore.YELLOW + f"⚠️ {package} is not installed")
    
    if missing_packages:
        if input(Fore.GREEN + "Install missing dependencies? (y/n): " + Style.RESET_ALL).lower() == 'y':
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", *missing_packages], check=True)
                print(Fore.GREEN + "✓ All dependencies installed successfully")
                return True
            except subprocess.SubprocessError as e:
                print(Fore.RED + f"❌ Error installing dependencies: {e}")
                return False
        else:
            print(Fore.YELLOW + "Dependencies installation skipped")
            return False
    
    return True

if __name__ == "__main__":
    print(Fore.CYAN + Style.BRIGHT + "\nCURSORFOCUS BUILDER\n")
    
    # Check dependencies first
    if check_dependencies():
        build_executable() 