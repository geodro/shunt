<div align="center">

# 🛤️ Shunt

### The browser chooser that remembers where you came from, for KDE Plasma 6

Click a link in Slack and it opens in your work browser. Click one in your feed reader and it opens in the other. You say it once, per application, and Shunt stops asking. When it does ask, the window is already under your pointer.

![KDE Plasma 6](https://img.shields.io/badge/KDE%20Plasma-6-1d99f3?logo=kde&logoColor=white)
![Wayland](https://img.shields.io/badge/Wayland-tested-2ea043)
![X11](https://img.shields.io/badge/X11-untested-lightgrey)
![KWin Script](https://img.shields.io/badge/KWin-Script-blueviolet)
![Python](https://img.shields.io/badge/Python-PySide6-3776ab?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)

</div>

---

## ✨ What it does

- 🧠 **Knows which application you clicked from.** Not the window focused now, the one focused when the link fired. That's what lets it ask once per application instead of every time.
- 🖱️ **Opens under the pointer.** Your hand is already there.
- ⚡ **Rules skip the question.** Set Slack to Brave once and Slack links go straight to Brave, no window at all. A notification says which browser took it and has a *Choose another* button for when it got it wrong.
- ✋ **Nothing is learned behind your back.** A rule is saved when you tick *Remember for …* or hold **Shift** while choosing. Never on its own.
- 🎯 **A rule can be about the address, the application, or both.** GitHub always opens in Brave; links from Slack open in Chrome; GitHub from Slack opens in Firefox. Narrower rules are filed above wider ones for you, and you can still reorder by hand.
- ⌨️ **Keyboard.** `1`-`9` pick a browser, arrows and `Enter` navigate, `Ctrl+C` copies the link instead of opening it, `Esc` closes.
- 🎨 **Breeze widgets, Breeze colours, icons from your theme, Plasma notifications.** Not a GTK window wearing a KDE hat.
- 🌍 **English and Romanian**, picked from your locale. An untranslated string stays English instead of going blank.
- 🔕 **The notification and the tray icon both have off switches.** The tray icon starts off.
- 📦 **`.deb`, `.rpm`, or from source.** `shunt update` moves you to the newest release tag.

---

## 🤔 Why?

Work in one browser profile behind the corporate SSO, personal things in another, and a third for whatever needs the ad blocker. Which one should open a link depends on where the link came from, and nothing on the desktop keeps track of that.

macOS has [Velja](https://sindresorhus.com/velja), which handles it well. On Linux the usual answer is [Junction](https://github.com/sonnyp/Junction). Junction is good software, but it asks every single time, and it can't do much else: it ships as a Flatpak, and the sandbox rules out the one component that could tell it where the click came from. Being GTK, it also never quite fits a Plasma desktop.

Shunt is the same idea built the other way round. A KWin script handles the parts that need the compositor, and a small resident Qt application handles the window.

The name is what a railway yard does: push a wagon off the main line onto the track it belongs on. Which is the whole job here, once per link.

---

## 🖥️ Does it run on my system?

| | |
|---|---|
| Plasma 6, Wayland | tested |
| Plasma 6, X11 | same scripting API, should work, untested |
| Plasma 5 | no: the scripting API differs (`clientActivated`, `activeClient`) |
| GNOME, wlroots, any other compositor | no: finding the active window would need a different mechanism |

That's a consequence of the design rather than an oversight. The part that sets Shunt apart from other choosers lives in a KWin script, so it depends on KWin, not on Qt.

Without that script Shunt still starts and still lets you pick a browser. It just shows up in the middle of the screen and has no idea where you clicked from.

Beyond Plasma it needs **Python 3.10+**, **PySide6**, **`gio`** (glib2), and **`notify-send`** (libnotify) for the notification. `install.sh` checks all of it before touching anything and says what's missing; `SHUNT_SKIP_CHECKS=1` skips the checks. Any distribution will do.

---

## 📦 Installation

### Option A: one line

```bash
curl -fsSL https://raw.githubusercontent.com/geodro/shunt/main/install.web.sh | bash
```

It checks that this is a Plasma 6 desktop, picks a `.deb` or `.rpm` if your
distribution takes one and falls back to a source install otherwise, then offers
to hand it the links. Append `-s -- --default` to skip that question, `--source`
to force the source route, or `--tag v0.1.0` to pin a release.

Piping a script from the internet into a shell is a decision, not a convention.
Read it first if you would rather: it is the same file, at
[install.web.sh](install.web.sh).

### Option B: a package

Grab a `.deb` or `.rpm` from [Releases](https://github.com/geodro/shunt/releases):

```bash
sudo apt install ./shunt_0.1.0_all.deb        # Debian, Ubuntu
sudo dnf install ./shunt-0.1.0-1.noarch.rpm   # Fedora
```

Packages start the daemon at login for every user and enable the KWin script by default. All that's left:

```bash
xdg-settings set default-web-browser co.dumitres.Shunt.desktop
```

### Option C: from source

```bash
git clone https://github.com/geodro/shunt.git
cd shunt
./install.sh --default      # drop --default to keep your current browser
```

### Uninstall

```bash
shunt uninstall            # add --purge to drop rules and preferences too
```

Rules and preferences stay in `~/.config/shunt/` unless you pass `--purge`.
Uninstalling and giving up are not the same thing, and a reinstall next week
shouldn't start from nothing. If Shunt came from a `.deb` or `.rpm`, remove it
with your package manager instead.

---

## ⌨️ Using it

Shunt shows up in the launcher, and clicking it opens the settings window. In the chooser:

| Key | Effect |
|---|---|
| `1`-`9` | pick that browser |
| arrows + `Enter` | navigate and pick |
| `Shift` + click, or `Shift` + digit | pick and save a rule for the source application |
| `Ctrl+C` | copy the link instead of opening it |
| `Esc` | close |

Clicking outside the window closes it too.

### From the command line

| Command | Effect |
|---|---|
| `shunt` | start the daemon, or open settings if it's already running |
| `shunt open <url>...` | open links through Shunt |
| `shunt <url>...` | the same, shorthand |
| `shunt update` | move to the newest release tag and reinstall |
| `shunt uninstall` | remove it for this user (`--purge` drops rules too) |
| `shunt --version` | print the version |

`shunt update` fetches tags, checks out the newest `v*` and runs `install.sh`. It moves to a tag and never to `main`, so you don't end up on unreleased code. If you have local changes the checkout fails instead of discarding them. From a system package it prints the right command for your package manager and stops there; downloading and unpacking into `/usr` behind your package manager's back isn't something this should be doing.

---

## ⚙️ Rules

The settings window has a form for new rules and a list you can reorder and prune. Order matters: the first matching rule wins.

| Field | Meaning |
|---|---|
| *When I click from* | the source application, or *any application* |
| *And the address is* | a host glob: `*`, `*.zoom.us`, `github.com` |
| *Open in* | one of the browsers Shunt found |

Either field can be left wide, which is what makes the interesting rules
possible. Leave the application on *any application* and you get a rule about
the address alone: GitHub opens in Brave no matter where the link came from.
Leave the address at `*` and you get a rule about the application alone.

```json
[
  {"source": "com.slack.Slack", "host": "github.com", "browser": "org.mozilla.firefox.desktop"},
  {"source": "*",               "host": "github.com", "browser": "com.brave.Browser.desktop"},
  {"source": "com.slack.Slack", "host": "*",          "browser": "com.google.Chrome.desktop"}
]
```

Read top to bottom: GitHub from Slack goes to Firefox, any other GitHub link
goes to Brave, anything else from Slack goes to Chrome.

You don't have to get that order right by hand. A new rule is filed above every
wider rule it would otherwise never beat: address and application first, then
address alone, then application alone, then the catch-all. The address counts
for more than the application, because "GitHub opens in Brave" is a firmer
intention than "links from Slack open in Chrome" and would look broken if the
second one swallowed it. Move up and Move down override all of that whenever
you disagree.

*Add exception* under the list starts a narrower rule for the application in the
selected row, with the address cleared and waiting.

A host written plainly also covers its subdomains, so `github.com` catches
`gist.github.com` too. Write a glob when you want something else: `*.github.com`
matches the subdomains and not the apex.

The file lives at `~/.config/shunt/rules.json` and can be edited by hand.

`source` is the window's `resourceClass`, which for Flatpak applications is the app-id itself (`com.slack.Slack`). The interface only ever appends to the file, so a hand-written one survives.

Two preferences live in `~/.config/shunt/config.json`: `notifications` (on) and `tray_icon` (off).

---

## 🧠 How it works

Wayland doesn't let a normal client find out which window was active a moment ago, or where the pointer is, or place its own window. KWin can do all three. So that part lives in a KWin script that talks to a resident daemon over D-Bus.

```
click a link → xdg-open → co.dumitres.Shunt.desktop (DBusActivatable)
             → org.freedesktop.Application.Open(uri)
             → rule match?  yes → launch the browser + "Choose another" notification
                            no  → the chooser, placed under the cursor by the KWin script
```

The script does two things. On `windowActivated` it sends the window's caption and `resourceClass` to the daemon with `callDBus`, skipping Shunt's own windows, so the last window reported before a link arrives is the one you clicked from. On `windowAdded` it recognises the chooser, sets `skipTaskbar` and `skipSwitcher` on it, and moves `frameGeometry` to `workspace.cursorPos`, clamped to the screen's work area.

The chooser's window title is the untranslated string `Shunt Chooser`, and it has to stay that way. On Wayland every window of an application carries the same `app_id`, and xdg-shell publishes no window type, so the title is the only per-window information KWin gets. It needs something to tell the chooser apart from the settings window, which should be placed normally and should show up in the taskbar.

The daemon starts at login rather than on demand. `callDBus` from a KWin script won't start a stopped service, so an on-demand daemon would miss every window activation that happened before the link, which is the one thing Shunt needs to know. It's a systemd user unit, `Type=dbus`, still D-Bus-activatable if you kill it. Around 90 MB RSS and 37 MB PSS, most of it Qt, shared with the rest of Plasma.

Browsers come from `.desktop` entries that declare `x-scheme-handler/https`, Flatpak exports included, and are launched with `gio launch`, which sorts out `%u`, Flatpak and `DBusActivatable`.

The *Choose another* notification goes through `notify-send --action` instead of D-Bus. `replaces_id` in `org.freedesktop.Notifications` is a `uint32`, PySide6 sends every Python `int` as `int32`, the notification server rejects the call, and there's no clean way to force the type from PySide6.

A related limitation explains a feature that isn't there: holding Ctrl to force the chooser even when a rule matches. A process that has just been launched can't read the keyboard state on Wayland. The notification covers the same ground from the other side, once you've already seen the wrong browser open.

---

## 🩹 Troubleshooting

- **"Remember for …" is greyed out.** The KWin script isn't reporting. Check it with
  `qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.isScriptLoaded shunt`.
  If it says `false`, tick **Shunt** under *System Settings → Window Management → KWin Scripts*, or re-run `./install.sh`.
- **The window opens in the middle of the screen.** Same cause. The script is what places it; without it you get Qt's default.
- **Links don't reach Shunt.** `xdg-settings get default-web-browser` should print `co.dumitres.Shunt.desktop`.
- **Nothing happens at all.** Try `systemctl --user status shunt`, then `journalctl --user -u shunt -f` while you click a link. For a chattier log: `systemctl --user set-environment SHUNT_DEBUG=1 && systemctl --user restart shunt`.
- **No tray icon after enabling it.** Plasma hides new tray items when they first appear. It's behind the `˄` arrow, and *Configure System Tray* can pin it.
- **A rule points at a browser I uninstalled.** The list shows it as *missing* and Shunt falls back to asking. Delete the row.

---

## 🛠️ Packaging

```bash
packaging/build-deb.sh    # dist/shunt_<version>_all.deb      (needs dpkg-deb)
packaging/build-rpm.sh    # dist/shunt-<version>-1.noarch.rpm (needs rpmbuild)
```

Both call `packaging/stage.sh`, so the installed layout is written down in one place.

CI is split in two. `ci.yml` runs checks only, on pushes to `main` and on pull requests: Python, shell and KWin-script syntax. `release.yml` builds the packages and publishes the release on a `v*` tag, and refuses to build if the tag doesn't match `__version__` in `shunt/__init__.py`.

---

## 📄 License

[MIT](LICENSE) © George Dumitrescu
