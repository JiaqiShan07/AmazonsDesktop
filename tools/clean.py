"""Remove generated build/cache files; --dist also removes the executable."""
import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    targets = [root / 'build']
    for folder in ('src', 'desktop', 'tests', 'tools'):
        targets.extend((root / folder).rglob('__pycache__'))
    if args.dist:
        targets.append(root / 'dist')
    for target in targets:
        resolved = target.resolve()
        if not resolved.is_relative_to(root) or resolved == root:
            raise ValueError(f'Cleanup target outside repository: {resolved}')
        if resolved.exists():
            shutil.rmtree(resolved)


if __name__ == '__main__':
    main()
