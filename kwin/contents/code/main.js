/*
 * Shunt — scriptul KWin.
 *
 * Wayland nu-i dă unui client obișnuit nici cine era fereastra activă, nici unde
 * e cursorul, nici dreptul de a se poziționa singur. KWin le are pe toate trei,
 * așa că partea asta trăiește aici și vorbește cu daemonul prin D-Bus.
 */

const SERVICE = "co.dumitres.Shunt";
const PATH = "/co/dumitres/Shunt";
const IFACE = "co.dumitres.Shunt.Kwin";
const SHUNT_CLASS = "co.dumitres.shunt";

// Pe Wayland toate ferestrele unei aplicații au același app_id și xdg-shell nu
// transmite tipul ferestrei, deci titlul e singurul semn după care KWin poate
// deosebi selectorul de fereastra de setări. Netradus dinadins; trebuie să
// rămână sincronizat cu WINDOW_TITLE din shunt/chooser.py.
const CHOOSER_TITLE = "Shunt Chooser";

function isShunt(window) {
    return (
        window &&
        typeof window.resourceClass === "string" &&
        window.resourceClass.toLowerCase() === SHUNT_CLASS
    );
}

function isChooser(window) {
    return (
        isShunt(window) &&
        typeof window.caption === "string" &&
        window.caption.indexOf(CHOOSER_TITLE) === 0
    );
}

// --- cine era fereastra activă -------------------------------------------

function onWindowActivated(window) {
    // Propria noastră fereastră nu e niciodată "sursa" link-ului.
    if (!window || isShunt(window)) {
        return;
    }
    callDBus(
        SERVICE,
        PATH,
        IFACE,
        "ActiveWindowChanged",
        String(window.caption || ""),
        String(window.resourceClass || ""),
        String(window.resourceName || "")
    );
}

// --- fereastra selectorului, sub cursor -----------------------------------

function placeUnderCursor(window) {
    const cursor = workspace.cursorPos;
    const area = workspace.clientArea(KWin.MaximizeArea, window);
    const size = window.frameGeometry;

    // Colțul din stânga-sus puțin peste cursor, ca pointerul să cadă în fereastră.
    let x = cursor.x - 24;
    let y = cursor.y - 24;

    x = Math.max(area.x, Math.min(x, area.x + area.width - size.width));
    y = Math.max(area.y, Math.min(y, area.y + area.height - size.height));

    window.frameGeometry = { x: x, y: y, width: size.width, height: size.height };
}

function onWindowAdded(window) {
    if (!isChooser(window)) {
        return;
    }
    // Fereastră trecătoare: n-are ce căuta în bara de activități sau în Alt+Tab.
    window.skipTaskbar = true;
    window.skipSwitcher = true;
    window.skipPager = true;

    placeUnderCursor(window);
    // Dimensiunea finală poate veni un commit mai târziu; repoziționăm o dată.
    window.frameGeometryChanged.connect(function once() {
        window.frameGeometryChanged.disconnect(once);
        placeUnderCursor(window);
    });
}

workspace.windowActivated.connect(onWindowActivated);
workspace.windowAdded.connect(onWindowAdded);

// La (re)încărcarea scriptului, raportăm imediat fereastra curentă.
onWindowActivated(workspace.activeWindow);
