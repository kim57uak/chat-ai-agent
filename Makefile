# Chat AI Agent Makefile
# Cross-platform build automation

.PHONY: help install build clean test package all

# Default target
help:
	@echo "Chat AI Agent Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  install    - Install dependencies"
	@echo "  build      - Build application for current platform"
	@echo "  package    - Create distributable package"
	@echo "  clean      - Clean build artifacts"
	@echo "  test       - Run tests"
	@echo "  all        - Install, build, and package"
	@echo ""
	@echo "Platform-specific targets:"
	@echo "  build-mac     - Build for macOS"
	@echo "  build-windows - Build for Windows"
	@echo "  build-linux   - Build for Linux"

# Detect platform
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    PLATFORM = mac
    PYTHON = python3
    VENV_ACTIVATE = source venv/bin/activate
endif
ifeq ($(UNAME_S),Linux)
    PLATFORM = linux
    PYTHON = python3
    VENV_ACTIVATE = source venv/bin/activate
endif
ifdef OS
    PLATFORM = windows
    PYTHON = python
    VENV_ACTIVATE = venv\Scripts\activate
endif

# Virtual environment setup
venv:
	$(PYTHON) -m venv venv

# Install dependencies
install: venv
	$(VENV_ACTIVATE) && pip install --upgrade pip
	$(VENV_ACTIVATE) && pip install -r requirements.txt
	$(VENV_ACTIVATE) && pip install pyinstaller

# Build for current platform
build: install
	$(VENV_ACTIVATE) && python build_scripts/build_universal.py

# Build for specific platforms
build-mac:
ifeq ($(UNAME_S),Darwin)
	chmod +x build_scripts/build_mac.sh
	./build_scripts/build_mac.sh
else
	@echo "Error: macOS build must be run on macOS"
endif

build-windows:
ifdef OS
	build_scripts\build_windows.bat
else
	@echo "Error: Windows build must be run on Windows"
endif

build-linux:
ifeq ($(UNAME_S),Linux)
	$(VENV_ACTIVATE) && python build_scripts/build_universal.py
else
	@echo "Error: Linux build must be run on Linux"
endif

# Package application
package: build
	@echo "Packaging complete for $(PLATFORM)"

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf build_output/
	rm -rf *.spec
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Run tests
test: install
	$(VENV_ACTIVATE) && python -m pytest tests/ -v

# Development setup
dev-setup: install
	$(VENV_ACTIVATE) && pip install pytest black flake8 mypy
	@echo "Development environment ready"

# Format code
format:
	$(VENV_ACTIVATE) && black .
	$(VENV_ACTIVATE) && flake8 .

# Type checking
typecheck:
	$(VENV_ACTIVATE) && mypy .

# All-in-one target
all: clean install build package

# Docker build (experimental)
docker-build:
	docker build -t chat-ai-agent .
	docker run --rm -v $(PWD)/build_output:/app/build_output chat-ai-agent

# Release preparation
release: clean all
	@echo "Release build complete"
	@echo "Artifacts available in build_output/"