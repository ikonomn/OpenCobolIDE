
.. image:: _static/silex-192x192.png
    :align: center

OpenCobolIDE 4.7.6 modern11.4 documentation
==========================================

OpenCobolIDE is a simple and lightweight COBOL IDE based on the
`OpenCOBOL/GnuCOBOL`_ compiler and the `pyQode`_ source code editor widget.

This documentation accompanies the unofficial ``4.7.6+modern11.4`` compatibility
polish for modern Python, PyQt5, GnuCOBOL, and Debian-family Linux. The
compatibility work was completed with assistance from OpenAI Codex. Original
ownership and maintainer attribution remain unchanged.

The maintained package supports Debian, Ubuntu, Linux Mint, and compatible
derivatives. References to other operating systems in :doc:`whats_new` describe
the original upstream release and are not supported build targets.

The original Read the Docs project is no longer available. Until a replacement
documentation site is published, the maintained documentation source is
available in the `modern-python documentation directory`_.


Documentation contents
======================

.. toctree::
    :maxdepth: 1
    :hidden:

    whats_new
    download
    getting_started
    settings
    advanced
    tipsandtricks
    faq
    hacking
    contribute
    license


.. hlist::
   :columns: 1

   * .. glossary::

      :doc:`whats_new`
         Modern compatibility changes followed by historical upstream notes.

   * .. glossary::

      :doc:`download`
         Install or upgrade the modern11.4 Debian package.

   * .. glossary::

      :doc:`getting_started`
         Create, open, compile, and run a COBOL program.

   * .. glossary::

      :doc:`settings`
         Configure the editor, GnuCOBOL compiler, and runtime.

   * .. glossary::

      :doc:`advanced`
         Debian-focused compiler, SQL precompiler, and developer topics.

   * .. glossary::

      :doc:`tipsandtricks`
         Tips and tricks.

   * .. glossary::

      :doc:`faq`
         Frequently asked questions and troubleshooting.

   * .. glossary::

      :doc:`hacking`
         Reset a missing menu bar or broken window layout.


Meta information:
=================

.. hlist::
   :columns: 2

   * .. glossary::

      :doc:`contribute`
        How to contribute and report bugs

   * .. glossary::

      :doc:`license`
        OpenCobolIDE license


Indices and tables:
===================

* :ref:`genindex`

* :ref:`search`


.. _pyQode: https://github.com/pyQode
.. _OpenCOBOL/GnuCOBOL: http://sourceforge.net/projects/open-cobol/
.. _`modern-python documentation directory`: https://github.com/ikonomn/OpenCobolIDE/tree/modern-python/doc/source


Program arguments (modern11.4)
----------------------------

When you select Run, a popup asks for optional program arguments. For
``bio2.cbl``, enter ``18090212 18650415`` to pass two dates. Do not enter
the program name. Quote arguments containing spaces, for example
``123 "customer name"``. Leave the entry empty to run without arguments,
or select Cancel to stop. The IDE remembers the last entry per source file.
Arguments work in the embedded console and external terminal.


Compiler workflow (modern11.4)
-----------------------------

Enable **COBOL > Automatic listing filename** to create a listing named after
its source, for example ``payapply1.cbl`` produces ``payapply1.prn``.
An explicit ``-T custom.prn`` remains unchanged. A bare ``-T`` uses the source
basename, and ``-T {stem}.prn`` is also supported. Listings are written relative
to the source directory. Syntax checking does not create listings.

Use **COBOL > Compiler options for this file...** to choose global defaults or
custom extra flags for the current saved source. Custom flags replace global
extra flags; an empty custom value means no extra flags. Other settings,
including SQL preferences, remain shared. Overrides are stored by source path.
Choose global defaults again to remove an override.

Normal compilation rebuilds the output so changed flags take effect. Projects
with their own ``build.sh`` continue to control their own compilation options.

To install an optional terminal launcher from source, run::

    OCIDE_INSTALL_LAUNCHER=1 bash scripts/install_from_source.sh

The launcher is installed at ``~/.local/bin/opencobolide``. Ensure that directory
is in your PATH. Existing unrelated commands are not overwritten. Keep the
installation folder and its virtual environment in place.


Linux shutdown lifecycle (modern11.4)
------------------------------------

Application references are kept alive until the Qt event loop has returned.
Python-side cleanup then runs once and is idempotent. This avoids destroying
Python wrappers while their C++ Qt objects are still participating in shutdown.

The correction applies to Linux source installations across distributions and
desktop sessions. It was identified from diagnostic traces on Mageia 10 with
Python 3.13, Qt 5.15, Wayland and glibc 2.42. The Debian package remains intended
for Debian-family systems; other Linux distributions should install from source.

Optional native-crash tracing can be enabled with::

    OCIDE_TRACE_LOG="$HOME/opencobolide-trace.jsonl" .venv/bin/opencobolide
