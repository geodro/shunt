%global _source_root %{getenv:SHUNT_SOURCE_ROOT}

Name:           shunt
Version:        %{getenv:SHUNT_VERSION}
Release:        1%{?dist}
Summary:        Browser chooser for KDE Plasma 6
License:        MIT
URL:            https://github.com/geodro/shunt
BuildArch:      noarch

Requires:       python3 >= 3.10
Requires:       python3-pyside6
Requires:       glib2
Requires:       kwin >= 6.0
Recommends:     libnotify

%description
Asks which browser should open a link, remembers the answer per source
application, and shows up under the mouse pointer. Needs a KWin script for the
two things Wayland does not give a plain client: which window was active and
where the cursor is. Plasma 6 only; the Plasma 5 scripting API differs.

%install
%{_source_root}/packaging/stage.sh %{buildroot}

%files
%{_bindir}/shunt
%{_prefix}/lib/shunt/
%{_prefix}/lib/systemd/user/shunt.service
%{_prefix}/lib/systemd/user/graphical-session.target.wants/shunt.service
%{_datadir}/applications/co.dumitres.Shunt.desktop
%{_datadir}/dbus-1/services/co.dumitres.Shunt.service
%{_datadir}/kwin/scripts/shunt/
%{_datadir}/icons/hicolor/scalable/apps/co.dumitres.Shunt*.svg
%doc %{_datadir}/doc/shunt/README.md

%changelog
* Sun Aug 16 2026 George Dumitrescu <george@dumitres.co> - 0.1.0-1
- Prima versiune împachetată.
