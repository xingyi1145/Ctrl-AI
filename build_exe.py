import os
import PyInstaller.__main__
import customtkinter

# 1. Get the installation path of customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)
print(f"Found customtkinter at: {ctk_path}")

# 2. Define the add-data argument
# Format: "source_path;destination_folder" (on Windows)
add_data_arg = f'{ctk_path}{os.pathsep}customtkinter/'
assets_arg = f'src/assets{os.pathsep}assets/'

# 3. Run PyInstaller
print("Starting PyInstaller build for Ctrl-AI...")

PyInstaller.__main__.run([
    'src/main.py',                  # Entry point
    '--name=Ctrl-AI',               # Name of the executable
    '--onefile',                    # Create a single executable file
    '--noconsole',                  # No console window (GUI application)
    f'--add-data={add_data_arg}',   # Include customtkinter theme/json files
    f'--add-data={assets_arg}',     # Include assets folder
    '--clean',                      # Clean PyInstaller cache and remove temp files
])
