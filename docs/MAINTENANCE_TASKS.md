# Targeted Maintenance Tasks

## 1) Typo fix task
**Issue:** The README section title is misspelled as `Socreenshots`.

**Proposed task:** Rename the heading to `Screenshots` and verify no anchors or links rely on the typo.

**Why this matters:** It improves polish and readability for first-time users.

## 2) Bug fix task
**Issue:** `detect_format()` falls back to returning a concrete format for malformed JSON/XML files (`.json` -> `RMM_JSON`, `.xml` -> `RIMPY_XML`) even when parsing fails, which can route imports into the wrong parser and produce misleading errors.

**Proposed task:** Change format detection fallback for invalid JSON/XML to `UNKNOWN`, and update `import_file()` to return a clear parse error path for unknown/invalid structured files.

**Why this matters:** It avoids false-positive detection and improves error quality for broken files.

## 3) Documentation discrepancy task
**Issue:** README quick-start and installation sections instruct users to install `PyQt6 PyQt6-WebEngine`, while `requirements.txt` only requires `PyQt6` and comments WebEngine as optional.

**Proposed task:** Align docs and dependency declarations by either (a) adding `PyQt6-WebEngine` as a required dependency, or (b) updating README to present WebEngine as optional with lightweight-mode implications.

**Why this matters:** Prevents setup confusion and reduces support churn.

## 4) Test improvement task
**Issue:** Importer tests verify happy paths and malformed JSON rejection, but there is no test that guards against format misclassification for malformed XML/JSON with valid extensions.

**Proposed task:** Add tests in `tests/test_mod_importer.py` asserting that malformed `.json` and malformed `.xml` are detected as `UNKNOWN` (or current intended behavior, if explicitly documented), with precise assertions on reported error messages.

**Why this matters:** It protects against regressions in auto-detection and error reporting quality.
