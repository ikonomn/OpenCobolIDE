# OpenCobolIDE modern11.6+project8 — Closing and switching projects

Date: 26 October 2026

## Problem addressed

The previous version selected the correct folder for Compile Project, but opening another project could leave source tabs from the previous project visible. Identical source basenames made that confusing, and F8 could still compile whichever old source was selected.

This update adds an explicit project lifecycle to the File menu.

## File → Close Project

Close Project is enabled when a project is active. It:

- Closes documents inside the active project, including source files, copybooks or configuration files opened as tabs.
- Includes split editor views and detached editor windows.
- Closes the project's Configure Project window.
- Clears the old project tree, tree lock and build/error/run output.
- Clears the active project selection and disables project-specific actions.
- Returns to the opening screen when no other documents remain.

Files on disk, configuration, binaries and listings are preserved. Unrelated standalone tabs are kept open, including their unsaved edits.

## Opening a different project

The IDE checks an existing target configuration before leaving the current project. It then resolves unsaved changes, initializes the new project's configuration if needed, closes the old project's tabs and opens the new sources.

The tree, title, settings review and Compile Project context follow the new project. Sources with identical names in different projects do not remain open from the previous project.

Opening the same project again keeps its existing source editors and unsaved changes.

## Unsaved changes

A single prompt lists dirty documents belonging to the project:

| Choice | Behavior |
| --- | --- |
| Save | Saves the changed project documents before closing their tabs. |
| Discard | Closes the project views without saving their edits. |
| Cancel | Keeps the current project, tabs, unsaved edits, tree and review window. |

A canceled Save As or a failed save also keeps the project and its tabs open. If one document was saved before a later document failed, that completed save remains on disk; the tabs are still retained.

Unrelated dirty standalone documents are not included in this prompt.

## Active work and empty projects

The IDE blocks closing/switching while a compilation, pending Run request or embedded console program is active. The user can stop the active operation and retry.

Closing the last source tab alone does not close its project. The project view and menus remain available, including Close Project. Empty projects can therefore be configured or closed explicitly.

## Editor cleanup fixes

The new lifecycle tests exposed two underlying editor issues, corrected in this update:

1. A closed text editor could lose Qt ownership of its text document while a delayed cursor callback still targeted it. The document now remains owned by the closed editor or a surviving clone.
2. Detached-window cleanup confused the window wrapper with its contained editor manager, and could destroy the window before tab cleanup finished. Cleanup now identifies the correct window and emits the final-tab signal after editor cleanup.

## Verification

Focused lifecycle tests cover closing, switching identical basenames, Save/Discard/Cancel, canceled and failed saves, invalid target configuration, reopening the same project, empty projects, active-work guards, unrelated standalone files, split/detached views and rapid repeated open/close with pending GUI callbacks.

The existing portable settings, automatic executable/module detection, internal builder, GixSQL preprocessing and listing/cross-reference workflows remain in place.
