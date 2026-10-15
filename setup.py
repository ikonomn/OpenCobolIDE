#!/usr/bin/env python3
"""
Setup script for OpenCobolIDE

You will need to install PyQt5 and GnuCOBOL on your own.

"""
import ast
from pathlib import Path
import sys
import os
import shutil

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py
# Build backends need not add the source tree to sys.path. Read metadata
# without importing the application or any of its runtime dependencies.
ROOT = Path(__file__).resolve().parent
version_source = ast.parse(
    (ROOT / 'open_cobol_ide' / '__init__.py').read_text(encoding='utf-8'))
__version__ = next(
    ast.literal_eval(node.value)
    for node in version_source.body
    if isinstance(node, ast.Assign)
    and any(isinstance(target, ast.Name) and target.id == '__version__'
            for target in node.targets)
)

try:
    from pyqt_distutils.build_ui import build_ui
    cmdclass = {'build_ui': build_ui}
except ImportError:
    build_ui = None
    cmdclass = {}


class CleanBuildPy(_build_py):
    """Prevent excluded legacy files leaking in from an earlier build."""

    def run(self):
        package_build_dir = os.path.join(self.build_lib, 'open_cobol_ide')
        if os.path.isdir(package_build_dir):
            shutil.rmtree(package_build_dir)
        super().run()


cmdclass['build_py'] = CleanBuildPy


DESCRIPTION = ('OpenCobolIDE 4.7.6 legacy release updated to run on modern '
               'Python')

# get long description
with (ROOT / 'README.md').open(encoding='utf-8') as readme:
    if 'bdist_deb' in sys.argv or 'sdist_dsc' in sys.argv:
        LONG_DESC = DESCRIPTION + ' based on GnuCOBOL and PyQode'
    else:
        LONG_DESC = readme.read()


setup(
    name='OpenCobolIDE',
    version=__version__,
    keywords=['Cobol; OpenCobol; IDE'],
    url='https://github.com/OpenCobolIDE/OpenCobolIDE',
    license='GPL v3',
    author='Colin Duquesnoy',
    author_email='colin.duquesnoy@gmail.com',
    description=DESCRIPTION,
    long_description=LONG_DESC,
    long_description_content_type='text/markdown',
    packages=[p for p in find_packages() if 'test' not in p],
    include_package_data=True,
    # Pygments and future used to be bundled.  Pygments is now a normal
    # dependency and Python 3 no longer needs the future compatibility layer,
    # so Python 3.12+ does not compile either obsolete bundled copy.
    install_requires=[
        'PyQt5>=5.15,<6',
        'Pygments>=2.11,<3',
    ],
    exclude_package_data={
        'open_cobol_ide': [
            'extlibs/pygments/*',
            'extlibs/pygments/**/*',
            'extlibs/future/*',
            'extlibs/future/**/*',
        ],
    },
    entry_points={
        'gui_scripts': ['opencobolide = open_cobol_ide.main:main']},
    cmdclass=cmdclass,
    zip_safe=False,
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later '
        '(GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Text Editors :: Integrated Development Environments (IDE)']
)
