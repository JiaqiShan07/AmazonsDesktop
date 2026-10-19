"""Build the desktop application with platform-specific packaging options."""
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
               '--onefile', '--windowed', '--paths', str(root / 'src'),
               '--specpath', 'build', '--workpath', 'build/pyinstaller',
               '--distpath', 'dist', '--name', 'AmazonsDesktop']
    if sys.platform == 'win32':
        command.extend(['--manifest', str(root / 'desktop/application.manifest')])
    command.append(str(root / 'desktop/launcher.py'))
    subprocess.run(command, cwd=root, check=True)


if __name__ == '__main__':
    main()
