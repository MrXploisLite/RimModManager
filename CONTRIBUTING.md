# Contributing to RimModManager

First off, thanks for taking the time to contribute! 🎉

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

When creating a bug report, include:
- Your OS and version (Windows/macOS/Linux distro)
- Python version (`python --version`)
- PyQt6 version (`pip show PyQt6`)
- RimWorld installation type (Steam Native, Proton, Flatpak, Wine, GOG, etc.)
- Steps to reproduce the issue
- Expected vs actual behavior
- Screenshots if applicable
- Error logs from `~/.config/rimmodmanager/logs/` (Linux)

### Suggesting Features

Feature requests are welcome! Please:
- Check if the feature has already been requested
- Describe the feature and its use case
- Explain why it would be useful to most users

### Pull Requests

1. Fork the repo and create your branch from `main`
2. Follow the existing code style
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation if needed
6. Write a clear PR description

## Development Setup

### Prerequisites
- Python 3.10+
- Git

### Installation

**Linux (Arch/CachyOS/EndeavourOS):**
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/RimModManager.git
cd RimModManager

# Install dependencies
sudo pacman -S python python-pyqt6 python-pyqt6-webengine

# Optional: SteamCMD for Workshop downloads
yay -S steamcmd
```

**Linux (Ubuntu/Debian):**
```bash
git clone https://github.com/YOUR_USERNAME/RimModManager.git
cd RimModManager

pip install PyQt6 PyQt6-WebEngine
sudo apt install steamcmd  # optional
```

**Windows:**
```powershell
git clone https://github.com/YOUR_USERNAME/RimModManager.git
cd RimModManager

pip install PyQt6 PyQt6-WebEngine
```

**macOS:**
```bash
git clone https://github.com/YOUR_USERNAME/RimModManager.git
cd RimModManager

pip install PyQt6 PyQt6-WebEngine
brew install steamcmd  # optional
```

### Running the Application
```bash
python main.py
```

## Running Tests

We use Python's built-in `unittest` framework.

```bash
# Run all tests
python -m unittest discover tests/ -v

# Run specific test file
python -m unittest tests/test_mod_parser.py -v

# Run with coverage (requires coverage package)
pip install coverage
coverage run -m unittest discover tests/
coverage report -m
```

### Test Structure
```
tests/
├── __init__.py
├── test_config_handler.py   # Config save/load tests
├── test_game_detector.py    # Installation detection tests
├── test_mod_importer.py     # Import format tests
├── test_mod_parser.py       # XML parsing, load order tests
└── test_mod_presets.py      # Preset encoding tests
```

### Writing Tests
- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test methods `test_*`
- Use descriptive test names
- Mock external dependencies (filesystem, network)

## Code Style

### General Guidelines
- Follow PEP 8 guidelines
- Use type hints where possible
- Write docstrings for classes and functions
- Keep functions focused and small
- Maximum line length: 120 characters

### Linting
```bash
# Install flake8
pip install flake8

# Run linter
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

### Import Order
1. Standard library imports
2. Third-party imports (PyQt6, etc.)
3. Local imports

### Example
```python
"""Module docstring."""

import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QWidget

from config_handler import ConfigHandler


class MyClass:
    """Class docstring."""
    
    def my_method(self, param: str) -> Optional[str]:
        """Method docstring."""
        pass
```

## Pull Request Process

1. **Create a branch**: `git checkout -b feature/my-feature`
2. **Make changes**: Follow code style guidelines
3. **Add tests**: For new functionality
4. **Run tests**: `python -m unittest discover tests/ -v`
5. **Run linter**: `flake8 .`
6. **Commit**: Use clear commit messages
7. **Push**: `git push origin feature/my-feature`
8. **Open PR**: Against `main` branch

### Commit Messages
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Keep the first line under 72 characters
- Reference issues when applicable: `fix: resolve #123`

### PR Title Format
- `feat: add new feature`
- `fix: resolve bug in X`
- `docs: update README`
- `test: add tests for Y`
- `refactor: improve Z`
- `chore: update dependencies`

## Project Structure

```
rimmodmanager/
├── main.py                 # Entry point
├── config_handler.py       # Config management
├── game_detector.py        # Installation detection
├── mod_parser.py           # Mod parsing, profiles, backups
├── workshop_downloader.py  # SteamCMD integration
├── ui/
│   ├── main_window.py      # Main UI
│   ├── mod_widgets.py      # Mod list widgets
│   ├── workshop_browser.py # Workshop browser
│   ├── download_manager.py # Download progress
│   ├── profiles_manager.py # Profiles UI
│   └── tools_widgets.py    # Tools UI
├── tests/                  # Unit tests
└── docs/                   # Documentation
```

## Questions?

- Open an issue with the "question" label
- Discord: `romyr911`

Thank you for contributing! 🙏
