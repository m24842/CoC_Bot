import re
import sys
import shutil
import argparse
import subprocess

def create_build_config(local_gui=False):
    with open("src/configs.template.py", "r") as f:
        content = f.read()

    if local_gui:
        updated_content = re.sub(r"(LOCAL_GUI\s*=\s*)False", r"\1True", content)
    else:
        updated_content = re.sub(r"(LOCAL_GUI\s*=\s*)True", r"\1False", content)

    with open("src/configs_build.py", "w") as f:
        f.write(updated_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoC Bot Build Release")
    parser.add_argument("--version", type=str, required=True, help="Version number for the build")
    parser.add_argument("--gui", action="store_true", help="Build for GUI")
    parser.add_argument("--cli", action="store_true", help="Build for CLI")
    args = parser.parse_args()

    assert args.gui or args.cli, "Please specify at least one build option: --gui or --cmdline"

    if args.gui:
        # Build for gui
        create_build_config(local_gui=True)
        subprocess.run([
            "pyinstaller",
            "--name", "CoC Bot",
            "--windowed",
            "--icon", "media/CoC_Bot.icns",
            "--add-data", "assets:assets",
            "--add-data", "src/gui_server:gui_server",
            "--add-data", "src/sleep_helper.sh:.",
            "--additional-hooks-dir", "hooks",
            "src/main.py"
        ])
        zip_name = f"CoC_Bot-{args.version}-{sys.platform}-gui.zip"
        if sys.platform == "darwin":
            target_name = "dist/CoC Bot.app"
        elif sys.platform == "win32":
            target_name = "dist/CoC Bot.exe"
        shutil.make_archive(zip_name, 'zip', target_name)
    if args.cli:
        # Build for cli
        create_build_config(local_gui=False)
        subprocess.run([
            "pyinstaller",
            "--name", "CoC_Bot",
            "--onefile",
            "--icon", "media/CoC_Bot.icns",
            "--add-data", "assets:assets",
            "--add-data", "src/sleep_helper.sh:.",
            "--additional-hooks-dir", "hooks",
            "src/main.py"
        ])
        zip_name = f"CoC_Bot-{args.version}-{sys.platform}-cli.zip"
        if sys.platform == "darwin":
            target_name = "dist/CoC_Bot"
        elif sys.platform == "win32":
            target_name = "dist/CoC_Bot.exe"
        shutil.make_archive(zip_name, 'zip', target_name)
