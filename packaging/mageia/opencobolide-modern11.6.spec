Name:           opencobolide
Version:        4.7.6
Release:        11.6.1%{?dist}
Summary:        COBOL IDE with portable projects for modern Python and PyQt5
License:        GPLv3+
URL:            https://github.com/ikonomn/OpenCobolIDE
Source0:        %{name}-%{version}-modern11.6.tar.gz
Group:          Development/Other
BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
BuildRequires:  desktop-file-utils
BuildRequires:  python3-qt5-gui >= 5.15
BuildRequires:  python3-pygments >= 2.11
Requires:       python3 >= 3.8
Requires:       bash
Requires:       python3-qt5-gui >= 5.15
Requires:       python3-pygments >= 2.11
Recommends:     gnucobol
BuildRequires:  python3-rpm-macros

%description
An unofficial modern build of OpenCobolIDE retaining its original authorship
and adding portable projects, per-source settings, internal builds, automatic
executable/module detection, GixSQL routing and cross-reference listings.

%prep
%setup -q -n OpenCobolIDE-%{version}-modern11.6

%build
%py3_build

%install
%py3_install
install -Dpm 0644 share/OpenCobolIDE.desktop %{buildroot}%{_datadir}/applications/OpenCobolIDE.desktop
install -Dpm 0644 share/OpenCobolIDE.png %{buildroot}%{_datadir}/pixmaps/OpenCobolIDE.png
install -Dpm 0644 share/opencobolide.1 %{buildroot}%{_mandir}/man1/opencobolide.1
install -Dpm 0644 doc/OpenCobolIDE-modern11.6.html %{buildroot}%{_docdir}/%{name}/manual.html
install -pm 0644 README.md HOWTO_MODERN11.6.md REVIEW_MODERN11.6.md RELEASE_NOTES_MODERN11.6.md INSTALL_FROM_SOURCE.md AUTHORS.rst LICENSE %{buildroot}%{_docdir}/%{name}/
install -d %{buildroot}%{_docdir}/%{name}/packaging
install -pm 0644 packaging/RPM_MODERN11.6.md packaging/NATIVE_FIX_MODERN11.6.md %{buildroot}%{_docdir}/%{name}/packaging/
cp -a examples %{buildroot}%{_docdir}/%{name}/
find %{buildroot}%{_docdir}/%{name}/examples -type f \( -name '.gitkeep' -o -name '.gitignore' -o -name '*.pyc' \) -delete
find %{buildroot}%{_docdir}/%{name}/examples -type d -name __pycache__ -prune -exec rm -rf {} +
# Documentation scripts are examples, invoked explicitly with bash/python3.
find %{buildroot}%{_docdir}/%{name}/examples -type f -exec chmod 0644 {} +
find %{buildroot}%{_docdir}/%{name}/examples -type f \( -name '*.sh' -o -name '*.py' \) -exec sed -i '1{ /^#!/d; }' {} +
# Internal builder is invoked with bash; keep its script metadata consistent.
chmod 0755 %{buildroot}%{python3_sitelib}/open_cobol_ide/build_tools/build.sh
sed -i '1s|.*|#!/bin/bash|' %{buildroot}%{python3_sitelib}/open_cobol_ide/build_tools/build.sh
# Python modules and backends are loaded through the selected interpreter.
find %{buildroot}%{python3_sitelib}/open_cobol_ide -name '*.py' -exec chmod 0644 {} +
find %{buildroot}%{python3_sitelib}/open_cobol_ide -name '*.py' -exec sed -i '1{ /^#!/d; }' {} +
desktop-file-validate %{buildroot}%{_datadir}/applications/OpenCobolIDE.desktop

%check
%{__python3} -c 'from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork; import pygments'
%{__python3} -m compileall -q %{buildroot}%{python3_sitelib}/open_cobol_ide

%files
%license LICENSE
%{_bindir}/opencobolide
%{python3_sitelib}/open_cobol_ide/
%{python3_sitelib}/OpenCobolIDE-*.egg-info/
%{_datadir}/applications/OpenCobolIDE.desktop
%{_datadir}/pixmaps/OpenCobolIDE.png
%doc %{_docdir}/%{name}/
%{_mandir}/man1/opencobolide.1*

%changelog
* Mon Oct 26 2026 OpenCobolIDE modern build <noreply@opencobolide.invalid> - 4.7.6-11.6.1%{?dist}
- Fix plain builds and GnuCOBOL 3.2 diagnostics; clean documentation payload.

* Mon Oct 26 2026 OpenCobolIDE modern build <noreply@opencobolide.invalid> - 4.7.6-11.6
- Consolidate modern11.6 project workflow, copybooks and editor lifecycle fixes.
- Install offline guides and the portable main/module/copybook example.
