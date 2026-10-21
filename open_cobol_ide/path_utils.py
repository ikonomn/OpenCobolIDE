"""Helpers for detecting accidental whitespace in configured paths."""
import os
import re


def clean_directory_path(value):
    """Remove outer whitespace and whitespace next to path separators."""
    value = (value or '').strip()
    return re.sub(r'\s*([/\\])\s*', r'\1', value)


def clean_path_list(value, separator=None):
    """Clean every directory in a PATH-style list."""
    separator = os.pathsep if separator is None else separator
    return separator.join(
        clean_directory_path(part) for part in (value or '').split(separator))


def path_correction(value, list_separator=None):
    """Return ``(cleaned, changed)`` for a directory or directory list."""
    cleaned = (clean_path_list(value, list_separator)
               if list_separator is not None else clean_directory_path(value))
    return cleaned, cleaned != (value or '')
