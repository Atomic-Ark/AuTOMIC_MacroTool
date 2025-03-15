from setuptools import setup, find_packages
import os
from pathlib import Path

# Read requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read README
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

# Get version from package
def get_version():
    init_path = Path(__file__).parent / 'src' / '__init__.py'
    with open(init_path) as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"\'')
    return '1.0.0'

setup(
    name='atomic-macro-tool',
    version=get_version(),
    author='AtomicArk',
    author_email='atomicark@example.com',
    description='Advanced Macro Recording and Automation Tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/atomicark/atomic-macro-tool',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    package_data={
        'atomic_macro_tool': [
            'resources/langs/*.json',
            'resources/icons/*.png',
            'resources/themes/*.qss',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: Microsoft :: Windows',
        'Environment :: Win32 (MS Windows)',
        'Natural Language :: English',
        'Natural Language :: Polish',
        'Natural Language :: German',
        'Natural Language :: French',
        'Natural Language :: Italian',
        'Natural Language :: Spanish',
    ],
    python_requires='>=3.8',
    install_requires=requirements,
    extras_require={
        'dev': [
            'black>=23.3.0',
            'pylint>=2.17.0',
            'pytest>=7.3.1',
            'pytest-qt>=4.2.0',
            'pytest-cov>=4.1.0',
            'sphinx>=7.0.1',
            'sphinx-rtd-theme>=1.2.0',
        ],
        'stealth': [
            'interception-driver>=1.0.1',
        ],
    },
    entry_points={
        'console_scripts': [
            'atomic-macro=atomic_macro_tool.main:main',
        ],
        'gui_scripts': [
            'atomic-macro-gui=atomic_macro_tool.main:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/atomicark/atomic-macro-tool/issues',
        'Source': 'https://github.com/atomicark/atomic-macro-tool',
        'Documentation': 'https://atomic-macro-tool.readthedocs.io/',
    },
    keywords=[
        'macro',
        'automation',
        'recording',
        'playback',
        'input',
        'mouse',
        'keyboard',
        'windows',
        'gui',
        'qt',
    ],
    platforms=['win32', 'win64'],
    zip_safe=False,
    options={
        'bdist_wheel': {
            'python_tag': 'py38.py39.py310.py311',
            'plat_name': 'win_amd64',
        },
    },
)
