"""Package configuration for ``fabula-extractor``."""

from pathlib import Path
import sys
import subprocess

# When executed without arguments, install the package using pip.
# This avoids deprecated ``setup.py install`` and handles user-site installs
# automatically when not running inside a virtual environment.
if len(sys.argv) == 1:
    try:
        import ensurepip
        ensurepip.bootstrap()
    except Exception:
        pass

    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    cmd = [sys.executable, "-m", "pip", "install", "."]
    if not in_venv:
        cmd.insert(4, "--user")
    subprocess.check_call(cmd)
    raise SystemExit

try:
    from setuptools import find_packages, setup
except ModuleNotFoundError:
    import ensurepip

    ensurepip.bootstrap()
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "pip",
        "setuptools",
    ])
    import importlib, site
    site.main()  # refresh sys.path with user site directories
    importlib.invalidate_caches()
    from setuptools import find_packages, setup


def _read_requirements() -> list[str]:
    """Load dependencies from ``requirements.txt``."""

    req_path = Path("requirements.txt")
    return [
        line.strip()
        for line in req_path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


setup(
    name="fabula-extractor",
    version="0.1.0",
    description="Extract text and tables from Fabula Ultima PDFs.",
    author="Fabula Community",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=_read_requirements(),
    entry_points={
        "console_scripts": [
            "fabula-extractor=fabula_extractor.extractor:main",
        ]
    },
)

