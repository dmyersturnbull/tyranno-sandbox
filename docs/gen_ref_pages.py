# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

""" """

from pathlib import Path

import mkdocs_gen_files

OUT_DIR = Path("ref")
SRC_DIR = Path("src")
SUMMARY_FILE = "SUMMARY.md"

nav = mkdocs_gen_files.Nav()

for path in sorted(SRC_DIR.rglob("*.py")):
    module_path = path.relative_to(SRC_DIR).with_suffix("")
    doc_path = path.relative_to(SRC_DIR).with_suffix(".md")
    full_doc_path = Path(OUT_DIR, doc_path)
    parts = module_path.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1].startswith("_"):
        continue
    nav[parts] = doc_path.as_posix()
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        fd.write("::: " + ".".join(parts))
    mkdocs_gen_files.set_edit_path(full_doc_path, path)
with mkdocs_gen_files.open(OUT_DIR / SUMMARY_FILE, "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
