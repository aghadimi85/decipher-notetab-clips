#!/usr/bin/env python3
r"""
Convert the legacy Decipher NoteTab clip library from Python 2.7 syntax
to Python 3.x syntax, without overwriting the original file.

Designed for:
    Decipher-Surveys-Latest.clb

The script:
1) Finds NoteTab ^!RunScript commands that call C:\python27\python.exe.
2) Repoints those commands to the Python interpreter running this converter.
3) Converts only the embedded Python script sections referenced by those
   ^!RunScript commands. Normal NoteTab clips and Decipher XML are untouched.
4) Validates every converted embedded Python section with compile().
5) Writes Decipher-Surveys-Python3.clb beside the original file.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

SOURCE_NAME = "Decipher-Surveys-Latest.clb"
OUTPUT_NAME = "Decipher-Surveys-Python3.clb"

RUNSCRIPT_RE = re.compile(
    r'(?mi)^(\^!RunScript\s+)C:\\python27\\python\.exe(\s+)([^\s\r\n]+)'
)
HEADER_RE = re.compile(r'^H="(.*)"\s*$')


def read_text_preserving_encoding(path: Path) -> Tuple[str, str]:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise RuntimeError("Could not decode the CLB file.")


def quote_executable(path: str) -> str:
    return f'"{path}"' if " " in path else path


def get_lib2to3_tool():
    """Use Python's standard 2to3 engine when available (it is present in Python 3.11)."""
    try:
        from lib2to3.refactor import RefactoringTool, get_fixers_from_package
        return RefactoringTool(get_fixers_from_package("lib2to3.fixes"))
    except Exception:
        return None


def convert_print_statement(line: str) -> str:
    """
    Convert the simple Python-2 print statements used in this Decipher library.
    This is a fallback; Python 3.11 normally uses lib2to3 instead.
    """
    ending = ""
    if line.endswith("\r\n"):
        ending = "\r\n"
        core = line[:-2]
    elif line.endswith("\n"):
        ending = "\n"
        core = line[:-1]
    else:
        core = line

    m = re.match(r'^(\s*)print(?:\s+)(.*)$', core)
    if not m:
        return line

    indent, expr = m.groups()

    # Already Python-3 style.
    if expr.lstrip().startswith("("):
        return line

    # Python 2: print expr,  -> suppress newline.
    if expr.rstrip().endswith(","):
        expr = expr.rstrip()[:-1].rstrip()
        return f"{indent}print({expr}, end=' '){ending}"

    # Python 2: print a, b -> Python 3 print(a, b)
    return f"{indent}print({expr}){ending}"


def manual_py2_to_py3(code: str) -> str:
    """Fallback conversion for the Python-2 constructs used by this clip library."""
    # except Exception, e:  -> except Exception as e:
    code = re.sub(
        r'(?m)^(\s*)except\s+([^:\n]+),\s*([A-Za-z_]\w*)\s*:',
        r'\1except \2 as \3:',
        code,
    )

    code = "".join(convert_print_statement(line) for line in code.splitlines(True))

    # Common Python-2 names. These are mostly defensive; the upstream file
    # appears to rely primarily on old print and except syntax.
    code = re.sub(r'\bxrange\(', 'range(', code)
    code = re.sub(r'\braw_input\(', 'input(', code)
    code = code.replace(".iteritems()", ".items()")
    code = code.replace(".iterkeys()", ".keys()")
    code = code.replace(".itervalues()", ".values()")
    code = code.replace("from itertools import izip", "from builtins import zip")
    code = code.replace("itertools.izip(", "zip(")
    return code


def convert_python_section(name: str, body: str, tool) -> Tuple[str, str]:
    """
    Return (converted_body, method_used).
    Raises SyntaxError if the result is not valid Python 3.
    """
    had_final_newline = body.endswith(("\n", "\r"))
    work = body if had_final_newline else body + "\n"

    if tool is not None:
        try:
            converted = str(tool.refactor_string(work, name))
            method = "lib2to3"
        except Exception:
            converted = manual_py2_to_py3(work)
            method = "fallback"
    else:
        converted = manual_py2_to_py3(work)
        method = "fallback"

    # Validate as Python 3 before writing the output file.
    compile(converted, f"<Decipher clip: {name}>", "exec")

    if not had_final_newline:
        converted = converted.rstrip("\r\n")
    return converted, method


def locate_source() -> Path:
    if len(sys.argv) >= 2:
        p = Path(sys.argv[1]).expanduser()
        if p.is_file():
            return p.resolve()
        raise SystemExit(f"Source file not found:\n{p}")

    candidates: List[Path] = [
        Path.cwd() / SOURCE_NAME,
        Path.home() / "Downloads" / SOURCE_NAME,
        Path.home() / "Desktop" / SOURCE_NAME,
    ]

    for p in candidates:
        if p.is_file():
            return p.resolve()

    raise SystemExit(
        f"Could not find {SOURCE_NAME}.\n\n"
        "Put this converter in the same folder as the CLB file, or run:\n"
        '  python convert_decipher_clb_py3.py "C:\\path\\to\\Decipher-Surveys-Latest.clb"'
    )


def main() -> None:
    source = locate_source()
    text, encoding = read_text_preserving_encoding(source)

    matches = list(RUNSCRIPT_RE.finditer(text))
    script_names: Set[str] = {m.group(3) for m in matches}

    if not script_names:
        raise SystemExit(
            "No legacy C:\\python27\\python.exe RunScript commands were found.\n"
            "The file may already be converted or may be a different clip library."
        )

    python_exe = quote_executable(str(Path(sys.executable).resolve()))

    # Repoint NoteTab from Python 2.7 to the interpreter running this converter.
    text, runscript_count = RUNSCRIPT_RE.subn(
        lambda m: f"{m.group(1)}{python_exe}{m.group(2)}{m.group(3)}",
        text,
    )

    lines = text.splitlines(keepends=True)

    headers: List[Tuple[int, str]] = []
    for idx, line in enumerate(lines):
        m = HEADER_RE.match(line.rstrip("\r\n"))
        if m:
            headers.append((idx, m.group(1)))

    tool = get_lib2to3_tool()
    converted_count = 0
    methods: Dict[str, str] = {}
    errors: List[str] = []

    # Bottom-to-top replacement keeps earlier header indexes valid.
    for pos in range(len(headers) - 1, -1, -1):
        start_idx, section_name = headers[pos]
        if section_name not in script_names:
            continue

        end_idx = headers[pos + 1][0] if pos + 1 < len(headers) else len(lines)
        body = "".join(lines[start_idx + 1:end_idx])

        try:
            converted_body, method = convert_python_section(section_name, body, tool)
        except Exception as exc:
            errors.append(f"{section_name}: {exc}")
            continue

        replacement = [lines[start_idx]] + converted_body.splitlines(keepends=True)
        lines[start_idx:end_idx] = replacement
        converted_count += 1
        methods[section_name] = method

    missing_sections = sorted(script_names - set(methods))

    if errors or missing_sections:
        print("\nConversion stopped. The original CLB was NOT changed.")
        if errors:
            print("\nPython sections that failed validation:")
            for item in errors:
                print("  -", item)
        if missing_sections:
            print("\nReferenced script sections not successfully converted:")
            for item in missing_sections:
                print("  -", item)
        raise SystemExit(1)

    output = source.with_name(OUTPUT_NAME)
    output.write_bytes("".join(lines).encode(encoding))

    fallback_count = sum(1 for method in methods.values() if method == "fallback")

    print("=" * 72)
    print("DECIPHER NOTETAB PYTHON 3 CONVERSION COMPLETE")
    print("=" * 72)
    print(f"Source:                  {source}")
    print(f"Output:                  {output}")
    print(f"Python interpreter:      {Path(sys.executable).resolve()}")
    print(f"RunScript paths changed: {runscript_count}")
    print(f"Python sections changed: {converted_count}")
    print(f"Fallback conversions:    {fallback_count}")
    print()
    print("The original CLB file was left unchanged.")
    print()
    print("NEXT:")
    print("1. Copy Decipher-Surveys-Python3.clb into:")
    print(r"   C:\Program Files (x86)\NoteTab Light\Libraries")
    print("2. Close NoteTab Light completely and reopen it.")
    print("3. Select the Decipher-Surveys-Python3 library.")
    print('4. Test "Make Rows Match Values".')


if __name__ == "__main__":
    main()
