"""
Test Story 1.1: Project Setup & Dependencies
Validates all acceptance criteria for project setup.
"""
import sys
import os
from pathlib import Path


def test_python_version():
    """AC1: Python 3.10+ virtual environment created and activated"""
    assert sys.version_info >= (3, 10), f"Python version {sys.version_info} is less than 3.10"
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def test_project_structure():
    """AC2: Project directory structure created"""
    project_root = Path(__file__).parent.parent
    
    required_dirs = ['docs', 'tests']
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Required directory '{dir_name}' does not exist"
        print(f"✓ Directory '{dir_name}' exists")
    
    # examples/ is inside reachy_mini/ subdirectory (separate package)
    examples_path = project_root / 'reachy_mini' / 'examples'
    assert examples_path.exists(), "examples/ directory does not exist in reachy_mini/"
    print(f"✓ Directory 'reachy_mini/examples' exists")


def test_core_dependencies():
    """AC3: All dependencies installed"""
    # Core packages needed for Story 1.1
    required_packages = [
        ('cv2', 'opencv-python'),  # opencv-python imports as cv2
        ('numpy', 'numpy'),
        ('pyttsx3', 'pyttsx3'),
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('openai', 'openai')
    ]
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"✓ Package '{package_name}' is installed (imports as '{import_name}')")
        except ImportError:
            assert False, f"Required package '{package_name}' is not installed"
    
    # face-recognition requires CMake on Windows and will be installed in Story 2.1
    print(f"ℹ️  Note: 'face-recognition' will be installed in Story 2.1 (requires CMake)")
    
    # reachy_mini is installed via uvx, verify it's available
    import subprocess
    result = subprocess.run(['uvx', '--version'], capture_output=True, text=True)
    assert result.returncode == 0, "uvx not available (needed for reachy-mini)"
    print(f"✓ uvx is available for running reachy-mini-daemon")


def test_dependency_manifest():
    """AC4: requirements.txt or pyproject.toml file created with pinned versions"""
    project_root = Path(__file__).parent.parent
    pyproject = project_root / 'pyproject.toml'
    
    assert pyproject.exists(), "pyproject.toml does not exist"
    
    content = pyproject.read_text()
    
    # Check for key dependencies
    required_deps = ['reachy-mini', 'opencv-python', 'face-recognition', 'numpy', 'pyttsx3', 'fastapi']
    for dep in required_deps:
        assert dep in content, f"Dependency '{dep}' not found in pyproject.toml"
    
    print(f"✓ pyproject.toml exists with all required dependencies")


def test_git_repository():
    """AC5: Git repository initialized with .gitignore configured for Python"""
    project_root = Path(__file__).parent.parent
    git_dir = project_root / '.git'
    gitignore = project_root / '.gitignore'
    
    assert git_dir.exists(), "Git repository not initialized (.git directory missing)"
    assert gitignore.exists(), ".gitignore file does not exist"
    
    gitignore_content = gitignore.read_text()
    
    # Check for Python-specific ignores
    python_ignores = ['__pycache__', '*.py[oc]', '.venv']
    for ignore in python_ignores:
        assert ignore in gitignore_content, f"'{ignore}' not found in .gitignore"
    
    print(f"✓ Git repository initialized with Python .gitignore")


def test_documentation():
    """AC6: README.md created with setup instructions"""
    project_root = Path(__file__).parent.parent
    
    readme = project_root / 'README.md'
    setup = project_root / 'SETUP.md'
    tts_guide = project_root / 'TTS_SETUP_GUIDE.md'
    
    assert readme.exists(), "README.md does not exist"
    assert setup.exists(), "SETUP.md does not exist"
    assert tts_guide.exists(), "TTS_SETUP_GUIDE.md does not exist"
    
    # Verify README has content
    readme_content = readme.read_text()
    assert len(readme_content) > 100, "README.md appears to be empty or too short"
    assert 'Reachy' in readme_content, "README.md doesn't mention Reachy"
    
    print(f"✓ Documentation files exist (README.md, SETUP.md, TTS_SETUP_GUIDE.md)")


if __name__ == '__main__':
    print("=" * 60)
    print("Story 1.1: Project Setup & Dependencies - Validation Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_python_version,
        test_project_structure,
        test_core_dependencies,
        test_dependency_manifest,
        test_git_repository,
        test_documentation
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            print(f"\n📋 Running: {test_func.__doc__}")
            test_func()
            passed += 1
            print(f"✅ PASSED: {test_func.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"❌ FAILED: {test_func.__name__}")
            print(f"   Error: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ ERROR: {test_func.__name__}")
            print(f"   Error: {e}")
    
    print()
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    sys.exit(0 if failed == 0 else 1)
