Reset a broken window layout
============================

OpenCobolIDE stores its window layout and preferences in a configuration file.
If the menu bar disappears or the window opens with unusable dimensions, close
the IDE and move that file out of the way. OpenCobolIDE will create a clean
configuration the next time it starts.

Locate the configuration
------------------------

List the files in the OpenCobolIDE configuration directory::

    find ~/.config/OpenCobolIDE -maxdepth 1 -type f -print

On a normal installation, the file is::

    ~/.config/OpenCobolIDE/OpenCobolIDE.conf

Back up and reset the configuration
-----------------------------------

Make sure OpenCobolIDE is closed, then rename the file instead of deleting it::

    mv ~/.config/OpenCobolIDE/OpenCobolIDE.conf \
       ~/.config/OpenCobolIDE/OpenCobolIDE.conf.backup

Start OpenCobolIDE again. It will create a new configuration with the default
layout and menu settings.

This reset changes IDE preferences only. It does not remove COBOL source files
or project data.

Restore the previous settings
-----------------------------

If the reset does not help, close OpenCobolIDE and restore the backup::

    mv ~/.config/OpenCobolIDE/OpenCobolIDE.conf.backup \
       ~/.config/OpenCobolIDE/OpenCobolIDE.conf

When the new layout works correctly and the backup is no longer needed, remove
it with::

    rm ~/.config/OpenCobolIDE/OpenCobolIDE.conf.backup
