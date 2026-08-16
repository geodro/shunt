#!/usr/bin/env bash
# Shunt installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/geodro/shunt/main/install.web.sh | bash
#   ... | bash -s -- --default        also make Shunt the http/https handler
#   ... | bash -s -- --source         build from the sources instead of a package
#   ... | bash -s -- --tag v0.1.0     pin a release
# Removal is `shunt uninstall`, or your package manager if a package was used.

set -euo pipefail

REPO="${SHUNT_REPO:-geodro/shunt}"
SRC_DIR="${SHUNT_SRC_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/shunt/src}"
API="https://api.github.com/repos/$REPO"

METHOD=""      # deb | rpm | source
TAG=""
SET_DEFAULT=0

if [ -t 1 ]; then
    RED=$'\033[0;31m'; YELLOW=$'\033[1;33m'; GREEN=$'\033[0;32m'
    CYAN=$'\033[0;36m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else
    RED=''; YELLOW=''; GREEN=''; CYAN=''; BOLD=''; RESET=''
fi

info()    { echo "  ${CYAN}-->${RESET} $*"; }
success() { echo "  ${GREEN}✓${RESET}  $*"; }
warn()    { echo "  ${YELLOW}!${RESET}  $*" >&2; }
die()     { echo "  ${RED}✗${RESET}  $*" >&2; exit 1; }
header()  { echo; echo "${BOLD}$*${RESET}"; }

# Piped into bash, stdin is the script itself, so a question has to be read from
# the terminal directly. No terminal means no question: we print and move on.
have_tty() { ( : >/dev/tty ) 2>/dev/null; }
ask() {
    local answer=""
    have_tty || return 1
    echo -n "  ${BOLD}?${RESET}  $* [y/N] "
    read -r answer </dev/tty || true
    [ "$answer" = "y" ] || [ "$answer" = "Y" ]
}

usage() {
    sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
}

while [ $# -gt 0 ]; do
    case "$1" in
        --default) SET_DEFAULT=1 ;;
        --source)  METHOD="source" ;;
        --tag)     TAG="${2:?--tag needs a version}"; shift ;;
        -h|--help) usage ;;
        *)         die "Unknown option: $1" ;;
    esac
    shift
done

# ── What Shunt needs before anything is downloaded ───────────────────────────

preflight() {
    header "Checking this desktop"

    command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1 ||
        die "Neither curl nor wget found."

    local plasma
    plasma="$(plasmashell --version 2>/dev/null | awk '{print $2}')" || true
    case "$plasma" in
        6.*) success "KDE Plasma $plasma" ;;
        "")  die "Plasma not found. Shunt is a Plasma 6 application; see $API" ;;
        *)   die "Plasma $plasma found. Shunt needs 6.x; the KWin scripting API differs." ;;
    esac

    if [ "$XDG_SESSION_TYPE" != "wayland" ]; then
        warn "Session is ${XDG_SESSION_TYPE:-unknown}; Shunt is only tested on Wayland."
    fi
}

fetch() {
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$1" ${2:+-o "$2"}
    else
        wget -qO "${2:--}" "$1"
    fi
}

latest_tag() {
    fetch "$API/releases/latest" 2>/dev/null |
        sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1
}

asset_url() {
    # $1 is the extension. One release, one .deb and one .rpm, so the first hit
    # is the right one.
    fetch "$API/releases/tags/$TAG" 2>/dev/null |
        sed -n "s/.*\"browser_download_url\": *\"\([^\"]*\\.$1\)\".*/\1/p" | head -1
}

# ── The three ways in ────────────────────────────────────────────────────────

detect_method() {
    [ -n "$METHOD" ] && return
    if command -v apt-get >/dev/null 2>&1; then
        METHOD="deb"
    elif command -v dnf >/dev/null 2>&1; then
        METHOD="rpm"
    else
        METHOD="source"
    fi
}

install_package() {
    local extension="$1" url file
    url="$(asset_url "$extension")"
    [ -n "$url" ] || die "No .$extension in release $TAG. Retry with --source."

    file="$(mktemp -d)/${url##*/}"
    info "Downloading ${url##*/}"
    fetch "$url" "$file"

    info "Installing (sudo)"
    case "$extension" in
        deb) sudo apt-get install -y "$file" ;;
        rpm) sudo dnf install -y "$file" ;;
    esac
    rm -rf "$(dirname "$file")"
}

install_source() {
    command -v git >/dev/null 2>&1 || die "git is needed for a source install."
    command -v python3 >/dev/null 2>&1 || die "python3 is needed."

    if [ -d "$SRC_DIR/.git" ]; then
        info "Updating the checkout in $SRC_DIR"
        git -C "$SRC_DIR" fetch --tags --force --quiet
    else
        info "Cloning into $SRC_DIR"
        mkdir -p "$(dirname "$SRC_DIR")"
        git clone --quiet "${SHUNT_GIT_URL:-https://github.com/$REPO.git}" "$SRC_DIR"
    fi
    git -C "$SRC_DIR" checkout --quiet --detach "$TAG"

    # install.sh runs its own dependency checks and reports what is missing.
    bash "$SRC_DIR/install.sh"
}

# ── Run ──────────────────────────────────────────────────────────────────────

preflight
detect_method

if [ -z "$TAG" ]; then
    TAG="$(latest_tag || true)"
    [ -n "$TAG" ] || die "No release found in $REPO. Retry with --tag or --source."
fi

header "Installing Shunt $TAG"
case "$METHOD" in
    deb)    install_package deb ;;
    rpm)    install_package rpm ;;
    source) install_source ;;
esac

if [ "$SET_DEFAULT" = 1 ] || ask "Make Shunt the handler for http and https links?"; then
    xdg-settings set default-web-browser co.dumitres.Shunt.desktop
    success "Shunt now handles links."
else
    echo
    info "To hand it the links later:"
    echo "      xdg-settings set default-web-browser co.dumitres.Shunt.desktop"
fi

header "Done"
echo "  Try it:    gio open https://example.com"
echo "  Rules:     open Shunt from the launcher"
echo "  Remove it: shunt uninstall"
