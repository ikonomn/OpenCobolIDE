from enum import IntEnum


class FileType(IntEnum):
    """
    Enumerates the different source file types:
        - executable (.exe)
        - module (.dll)
    """
    #: Executable file (produces an executable binary that can be run)
    EXECUTABLE = 0
    #: Module file (produces a shared library that can be used from other
    #: modules or executables)
    MODULE = 1


class GnuCobolStandard(IntEnum):
    """
    Enumerates the different GnuCOBOL standards.
    """
    default = 0
    cobol2002 = 1
    cobol85 = 2
    ibm = 3
    mvs = 4
    bs2000 = 5
    mf = 6
    cobol2014 = 7
    acu = 8
    none = 9


def gnucobol_standard_name(value):
    """Return the GnuCOBOL command-line name for a standard setting.

    Python 3.11 changed ``IntEnum.__str__`` to return the numeric value, so
    deriving the compiler option from ``str(value)`` produced values such as
    ``-std=6`` instead of ``-std=mf``.  Enum member names are stable across
    supported Python versions.
    """
    return GnuCobolStandard(value).name
