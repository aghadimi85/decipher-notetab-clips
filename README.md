# Decipher NoteTab Clips — Python 3 Compatibility

The original Decipher NoteTab clip library was designed to use Python 2.7.

This fork adds a small conversion utility that updates the legacy Python-dependent
clips for Python 3 while leaving the original Decipher-Surveys-Latest.clb unchanged.

## Files

- Decipher-Surveys-Latest.clb — original Decipher NoteTab library
- convert_decipher_clb_py3.py — Python 3 conversion utility
- run_decipher_converter.bat — Windows launcher

## Conversion

Place all three files in the same folder.

Double-click:

run_decipher_converter.bat

The converter will use Python 3.11 when available and create:

Decipher-Surveys-Python3.clb

The original Decipher-Surveys-Latest.clb is not modified.

## Install in NoteTab Light

Copy:

Decipher-Surveys-Python3.clb

to:

C:\Program Files (x86)\NoteTab Light\Libraries

Close NoteTab Light completely and reopen it.

Select the Decipher-Surveys-Python3 library.

## Test

Select values such as:

1. Male
2. Female
3. Other specify
4. Prefer not to answer

Then run:

Make Rows Match Values

The converted library has been tested successfully with Python 3.11 and NoteTab Light.

For company-managed computers, installation and scripts should be reviewed and approved
by IT or the appropriate technical team before deployment.
