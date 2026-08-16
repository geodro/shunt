#!/usr/bin/env bash
# Construiește shunt-<versiune>-1.noarch.rpm în dist/. Cere rpmbuild.
set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$SRC/shunt/__init__.py")"
[ -n "$VERSION" ] || { echo "nu găsesc versiunea în shunt/__init__.py" >&2; exit 1; }

TOP="$(mktemp -d)"
trap 'rm -rf "$TOP"' EXIT

SHUNT_VERSION="$VERSION" SHUNT_SOURCE_ROOT="$SRC" rpmbuild -bb \
    --define "_topdir $TOP" \
    --define "_build_id_links none" \
    "$SRC/packaging/shunt.spec"

mkdir -p "$SRC/dist"
find "$TOP/RPMS" -name '*.rpm' -exec cp {} "$SRC/dist/" \;
echo "→ dist/$(ls "$SRC/dist" | grep '\.rpm$' | tail -1)"
