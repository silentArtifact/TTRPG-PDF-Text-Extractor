"""Package configuration for ``fabula-extractor``."""

from pathlib import Path

try:
    from setuptools import find_packages, setup
except ModuleNotFoundError:
    import ensurepip
    import subprocess
    import sys

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

