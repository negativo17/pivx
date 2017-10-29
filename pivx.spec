%define _hardened_build 1
#%global selinux_variants mls strict targeted
%global _compldir %{_datadir}/bash-completion/completions

# If firewalld macro is not defined, define it here:
%{!?firewalld_reload:%global firewalld_reload test -f /usr/bin/firewall-cmd && firewall-cmd --reload --quiet || :}

Name:       pivx
Version:    3.0.4
Release:    2%{?dist}
Summary:    Peer to Peer Cryptographic Currency
License:    MIT
URL:        https://pivx.org/

Source0:    http://github.com/PIVX-Project/PIVX/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:    %{name}-tmpfiles.conf
Source2:    %{name}.sysconfig
Source3:    %{name}.service
Source4:    %{name}.init
Source5:    %{name}.xml

BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  boost-devel
BuildRequires:  checkpolicy
BuildRequires:  desktop-file-utils
BuildRequires:  java
BuildRequires:  libdb4-cxx-devel
BuildRequires:  libevent-devel
BuildRequires:  libtool
BuildRequires:  miniupnpc-devel
BuildRequires:  protobuf-devel
BuildRequires:  qrencode-devel
BuildRequires:  qt5-linguist
BuildRequires:  qt5-qtbase-devel
BuildRequires:  systemd

%if 0%{?fedora} >= 26
BuildRequires:  compat-openssl10-devel
%else
BuildRequires:  openssl-devel
%endif

# There's one last Python 2 script left in the test suite, so we still need
# both Python 2 and 3 to run all tests.
%if 0%{?fedora}
BuildRequires:  python2
BuildRequires:  python3-zmq
BuildRequires:  zeromq-devel
%endif
%if 0%{?rhel}
BuildRequires:  python
BuildRequires:  python34
%endif

# Required for the firewall rules
# http://fedoraproject.org/wiki/PackagingDrafts/ScriptletSnippets/Firewalld
%if 0%{?rhel}
Requires:       firewalld
Requires(post): firewalld
%else
Requires:       firewalld-filesystem
Requires(post): firewalld-filesystem
%endif

Requires:   %{name}-common = %{version}-%{release}

%description
PIVX is a digital cryptographic currency that uses peer-to-peer technology to
operate with no central authority or banks; managing transactions and the
issuing of PIVs is carried out collectively by the network.

%package common
Summary:    PIVX common files
BuildArch:  noarch

%description common
PIVX is an experimental new digital currency that enables instant payments to
anyone, anywhere in the world. PIVX uses peer-to-peer technology to operate with
no central authority: managing transactions and issuing money are carried out
collectively by the network.

This package contains common files.

%package gui
Summary:    PIVX graphical client
Requires:   %{name}-common = %{version}-%{release}

%description gui
PIVX is a digital cryptographic currency that uses peer-to-peer technology to
operate with no central authority or banks; managing transactions and the
issuing of PIVs is carried out collectively by the network.

This package contains the Qt based graphical client and node. If you are looking
to run a PIVX wallet, this is probably the package you want.

%package utils
Summary:    PIVX command line utilities
Requires:   %{name}-common = %{version}-%{release}

%description utils 
PIVX is an experimental new digital currency that enables instant payments to
anyone, anywhere in the world. PIVX uses peer-to-peer technology to operate with
no central authority: managing transactions and issuing money are carried out
collectively by the network.

This package provides pivx-cli, a utility to communicate with and control a PIVX
server via its RPC protocol, and pivx-tx, a utility to create custom PIVX
transactions.

%package server
Summary:        PIVX server
Requires:       %{name}-utils%{_isa} = %{version}-%{release}
Requires:       %{name}-common = %{version}-%{release}
Requires(pre):  shadow-utils

%description server
This package provides a stand-alone PIVX daemon. For most users, this package is
only needed if they need a full-node without the graphical client.

Some third party wallet software will want this package to provide the actual
PIVX node they use to connect to the network.

If you use the graphical PIVX client then you almost certainly do not need this
package.

%prep
%setup -q -n PIVX-%{version}

%build
./autogen.sh
%configure \
    --disable-silent-rules \
    --enable-reduce-exports

make %{?_smp_mflags}

%check
# Run all the tests
# make check
# # Run all the other tests
# pushd src
# srcdir=. test/%{name}-util-test.py
# popd
# PYTHONUNBUFFERED=1 qa/pull-tester/rpc-tests.py

%install
cp contrib/debian/examples/%{name}.conf %{name}.conf.example

make INSTALL="install -p" CP="cp -p" DESTDIR=%{buildroot} install

# TODO: Upstream puts pivxd in the wrong directory. Need to fix the
# upstream Makefiles to relocate it.
mkdir -p -m 755 %{buildroot}%{_sbindir}
mv %{buildroot}%{_bindir}/pivxd %{buildroot}%{_sbindir}/pivxd

# Temporary files
mkdir -p %{buildroot}%{_tmpfilesdir}
install -m 0644 %{SOURCE1} %{buildroot}%{_tmpfilesdir}/%{name}.conf
install -d -m 0755 %{buildroot}/run/%{name}/
touch %{buildroot}/run/%{name}.pid
chmod 0644 %{buildroot}/run/%{name}.pid

# Install ancillary files
install -D -m644 -p contrib/debian/%{name}-qt.protocol %{buildroot}%{_datadir}/kde4/services/%{name}-qt.protocol
install -D -m600 -p %{SOURCE2} %{buildroot}%{_sysconfdir}/sysconfig/%{name}
install -D -m644 -p %{SOURCE3} %{buildroot}%{_unitdir}/%{name}.service
install -d -m750 -p %{buildroot}%{_localstatedir}/lib/%{name}
install -d -m750 -p %{buildroot}%{_sysconfdir}/%{name}

# Desktop file
desktop-file-install \
    --dir=%{buildroot}%{_datadir}/applications \
    --remove-key=Encoding \
    --set-key=Icon --set-value="%{name}" \
    contrib/debian/%{name}-qt.desktop
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}-qt.desktop

# Icons
for size in 16 32 64 128 256; do
    install -p -D -m 644 share/pixmaps/bitcoin${size}.png \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{name}.png
done
rm -f %{buildroot}%{_datadir}/pixmaps/%{name}*

# Bash completion
# install -D -m644 -p contrib/%{name}-cli.bash-completion %{buildroot}%{_compldir}/%{name}-cli
install -D -m644 -p contrib/pivxd.bash-completion %{buildroot}%{_compldir}/pivxd

# Man pages
mkdir -p %{buildroot}%{_mandir}/man1/
mkdir -p %{buildroot}%{_mandir}/man5/
install -m644 -p contrib/debian/manpages/pivxd.1 %{buildroot}%{_mandir}/man1/
install -m644 -p contrib/debian/manpages/pivx-qt.1 %{buildroot}%{_mandir}/man1/
install -m644 -p contrib/debian/manpages/pivx.conf.5 %{buildroot}%{_mandir}/man5/

# Remove test files so that they aren't shipped. Tests have already been run.
rm -f %{buildroot}%{_bindir}/test_*

install -D -m 644 -p %{SOURCE5} \
    %{buildroot}%{_prefix}/lib/firewalld/services/%{name}.xml

%post common
%firewalld_reload

%post gui
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

%postun gui
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%posttrans gui
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%pre server
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null ||
    useradd -r -g %{name} -d /var/lib/%{name} -s /sbin/nologin \
    -c "PIVX wallet server" %{name}
exit 0

%post server
%systemd_post %{name}.service

%posttrans server
/usr/bin/systemd-tmpfiles --create

%preun server
%systemd_preun %{name}.service

%postun server
%systemd_postun_with_restart %{name}.service

%files common
%license COPYING
%doc README.md %{name}.conf.example
%doc doc/assets-attribution.md doc/release-notes.md doc/tor.md
%{_mandir}/man5/pivx.conf.5*
%{_prefix}/lib/firewalld/services/%{name}.xml

%files gui
%{_bindir}/%{name}-qt
%{_datadir}/applications/%{name}-qt.desktop
%{_datadir}/kde4/services/%{name}-qt.protocol
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_mandir}/man1/%{name}-qt.1*

%files utils
%{_bindir}/%{name}-cli
%{_bindir}/%{name}-tx
#%{_mandir}/man1/%{name}-cli.1*
#%{_mandir}/man1/%{name}-tx.1*

%files server
%doc doc/REST-interface.md doc/zmq.md
%dir %attr(750,%{name},%{name}) %{_localstatedir}/lib/%{name}
%dir %attr(750,%{name},%{name}) %{_sysconfdir}/%{name}
%dir /run/%{name}/
%verify(not size mtime md5) /run/%{name}.pid
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/sysconfig/%{name}
%{_compldir}/pivxd
%{_mandir}/man1/pivxd.1*
%{_sbindir}/pivxd
%{_tmpfilesdir}/%{name}.conf
%{_unitdir}/%{name}.service

%changelog
* Sun Oct 29 2017 Simone Caronni <negativo17@gmail.com> - 3.0.4-2
- Rebuild for 3.0.4 re-release.

* Sun Oct 22 2017 Simone Caronni <negativo17@gmail.com> - 3.0.4-1
- First build.
