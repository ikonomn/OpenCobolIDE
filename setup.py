#!/usr/bin/env python3
"""
Setup script for OpenCobolIDE

You will need to install PyQt5 and GnuCOBOL on your own.

"""
import sys
from setuptools import setup, find_packages
from open_cobol_ide import __version__

try:
    from pyqt_distutils.build_ui import build_ui
    cmdclass = {'build_ui': build_ui}
except ImportError:
    build_ui = None
    cmdclass = {}


DESCRIPTION = ('OpenCobolIDE 4.7.6 legacy release updated to run on modern '
               'Python')

# get long description
with open('README.md', 'r', encoding='utf-8') as readme:
    if 'bdist_deb' in sys.argv or 'sdist_dsc' in sys.argv:
        LONG_DESC = DESCRIPTION + ' based on GnuCOBOL and PyQode'
    else:
        LONG_DESC = readme.read()


data_files = []
if sys.platform == 'linux':
    data_files.append(('/usr/share/applications',
                       ['share/OpenCobolIDE.desktop']))
    data_files.append(('/usr/share/pixmaps', ['share/OpenCobolIDE.png']))


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
    data_files=data_files,
    include_package_data=True,
    install_requires=['PyQt5>=5.15,<6'],
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Text Editors :: Integrated Development Environments (IDE)']
)
