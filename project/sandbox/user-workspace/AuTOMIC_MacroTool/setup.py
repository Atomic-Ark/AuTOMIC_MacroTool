"""
Setup script for AuTOMIC MacroTool.
Copyright (c) 2025 AtomicArk
"""

import os
from setuptools import setup, find_packages

# Read requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read README
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

# Package info
PACKAGE_NAME = "atomic_macro"
VERSION = "1.0.0"
AUTHOR = "AtomicArk"
AUTHOR_EMAIL = "atomicarkft@gmail.com"
DESCRIPTION = "Advanced Macro Recording and Automation Tool"
URL = "https://github.com/Atomic-Ark/AuTOMIC_MacroTool"
LICENSE = "MIT"  # Using MIT License as it's permissive and suitable for open-source software

# Data files
data_files = [
    ('', ['LICENSE', 'README.md']),
    ('resources/langs', [
        'src/resources/langs/en_US.json',
        'src/resources/langs/pl_PL.json',
        'src/resources/langs/de_DE.json',
        'src/resources/langs/fr_FR.json',
        'src/resources/langs/it_IT.json',
        'src/resources/langs/es_ES.json'
    ]),
    ('resources/icons', []),  # Will be populated with icons later
    ('resources/themes', []),  # Will be populated with theme files later
]

# Package configuration
setup(
    name=PACKAGE_NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=URL,
    license=LICENSE,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    data_files=data_files,
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "atomic-macro=atomic_macro.main:main",
        ],
        "gui_scripts": [
            "atomic-macro-gui=atomic_macro.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Desktop Environment :: Window Managers",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
        "Environment :: Win32 (MS Windows)",
        "Natural Language :: English",
        "Natural Language :: Polish",
        "Natural Language :: German",
        "Natural Language :: French",
        "Natural Language :: Italian",
        "Natural Language :: Spanish",
    ],
    keywords=[
        "macro",
        "automation",
        "recording",
        "playback",
        "input",
        "mouse",
        "keyboard",
        "script",
        "windows",
        "gui"
    ],
    project_urls={
        "Bug Reports": f"{URL}/issues",
        "Source": URL,
        "Documentation": f"{URL}/wiki",
    },
    extras_require={
        "dev": [
            "black>=23.3.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
            "pytest>=7.3.1",
            "pytest-cov>=4.1.0",
            "pytest-qt>=4.2.0",
            "sphinx>=7.0.1",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx-autodoc-typehints>=1.23.0",
        ],
        "stealth": [
            "interception-python>=1.0.3",
            "opencv-python>=4.7.0",
            "numpy>=1.24.3",
        ],
    },
    platforms=["win32", "win-amd64"],
    zip_safe=False,
    options={
        "bdist_wheel": {
            "universal": False
        }
    }
)
