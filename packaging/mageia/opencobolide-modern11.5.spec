Name:           opencobolide
Version:        4.7.6
Release:        11.5%{?dist}
Summary:        COBOL IDE updated for modern Python and PyQt5

License:        GPLv3+
URL:            https://github.com/ikonomn/OpenCobolIDE
Source0:        %{name}-%{version}-modern11.5.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-rpm-macros
BuildRequires:  desktop-file-utils
Requires:       python3
Requires:       python3-qt5-gui >= 5.15
Requires:       python3-pygments >= 2.11
Recommends:     gnucobol

%description
OpenCobolIDE is a graphical editor and development environment for COBOL
programs using GnuCOBOL. This package updates the legacy 4.7.6 release for
modern Python and PyQt5 and includes the modern11.5 Linux improvements.

%prep
%setup -q -n OpenCobolIDE-%{version}-modern11.5

%build
%py3_build

%install
%py3_install

install -Dpm 0644 share/OpenCobolIDE.desktop \
    %{buildroot}%{_datadir}/applications/OpenCobolIDE.desktop
install -Dpm 0644 share/OpenCobolIDE.png \
    %{buildroot}%{_datadir}/pixmaps/OpenCobolIDE.png
install -Dpm 0644 share/opencobolide.1 \
    %{buildroot}%{_mandir}/man1/opencobolide.1
install -Dpm 0644 doc/OpenCobolIDE-modern11.5.html \
    %{buildroot}%{_docdir}/%{name}/manual.html

desktop-file-validate \
    %{buildroot}%{_datadir}/applications/OpenCobolIDE.desktop

%check
%{__python3} -m compileall -q \
    %{buildroot}%{python3_sitelib}/open_cobol_ide

%files
%license LICENSE
%doc README.md RELEASE_NOTES_MODERN11.5.md
%{_bindir}/opencobolide
%{python3_sitelib}/open_cobol_ide/
%{python3_sitelib}/OpenCobolIDE-*.egg-info/
%{_datadir}/applications/OpenCobolIDE.desktop
%{_datadir}/pixmaps/OpenCobolIDE.png
%{_docdir}/%{name}/manual.html
%{_mandir}/man1/opencobolide.1*

%changelog
* Wed Oct 21 2026 Nikos <noreply@opencobolide.invalid> - 4.7.6-11.5
- Package OpenCobolIDE modern11.5 for testing on Mageia 10.
- Add per-source compiler settings and copybook environment overrides.
- Detect FREE and FIXED source directives automatically in the editor.
- Preserve GixSQL project preprocessing and callable-module compilation.
