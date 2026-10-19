PYTHON ?= python
APP_NAME := AmazonsDesktop

.PHONY: help install install-build run check build clean distclean
.DEFAULT_GOAL := help

help:
	@$(PYTHON) -c "print('make install        Install runtime dependencies\nmake install-build  Install build dependencies\nmake run            Start the desktop application\nmake check          Compile Python sources\nmake build          Build dist/$(APP_NAME).exe\nmake clean          Remove build files and Python caches\nmake distclean      Also remove dist; close the app first')"

install:
	$(PYTHON) -m pip install -r requirements.txt

install-build:
	$(PYTHON) -m pip install -r requirements-build.txt

run:
	$(PYTHON) desktop/launcher.py

check:
	$(PYTHON) -m compileall -q src desktop tools tests

build: check
	$(PYTHON) -m PyInstaller --noconfirm --clean --onefile --windowed --paths "$(abspath src)" --manifest "$(abspath desktop/application.manifest)" --specpath build --workpath build/pyinstaller --distpath dist --name $(APP_NAME) desktop/launcher.py

clean:
	$(PYTHON) tools/clean.py

distclean:
	$(PYTHON) tools/clean.py --dist
