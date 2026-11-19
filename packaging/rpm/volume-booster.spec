Name:           volume-booster
Version:        1.1.2
Release:        1%{?dist}
Summary:        System tray volume booster for quiet audio
License:        MIT
URL:            https://github.com/VanguardArts/volume-booster
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
# pactl ships in pulseaudio-utils on Fedora/RHEL/openSUSE (works with PipeWire
# via pipewire-pulse). python3-qt6 is the PyQt6 bindings package name.
Requires:       python3
Requires:       python3-qt6
Requires:       pulseaudio-utils

%description
Boost the default audio output above 100% using PipeWire/PulseAudio software
gain. Useful for YouTube videos and other sources that are inherently quiet
even when every volume slider is at maximum.

Left-click the tray icon to open a 0-200%% slider; right-click for quick
presets (100-200%%) and reset.

%prep
%autosetup

%install
mkdir -p %{buildroot}%{_bindir} \
         %{buildroot}%{_datadir}/applications \
         %{buildroot}%{_datadir}/icons/hicolor/scalable/apps

install -m 0755 volume_booster.py %{buildroot}%{_bindir}/volume-booster
install -m 0644 packaging/volume-booster.desktop \
    %{buildroot}%{_datadir}/applications/volume-booster.desktop
install -m 0644 packaging/volume-booster.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/volume-booster.svg

for sz in 16 24 32 48 64 96 128 256 512; do
    install -Dm 0644 "packaging/icons/hicolor/${sz}x${sz}/apps/volume-booster.png" \
        "%{buildroot}%{_datadir}/icons/hicolor/${sz}x${sz}/apps/volume-booster.png"
done

%files
%{_bindir}/volume-booster
%{_datadir}/applications/volume-booster.desktop
%{_datadir}/icons/hicolor/scalable/apps/volume-booster.svg
%{_datadir}/icons/hicolor/16x16/apps/volume-booster.png
%{_datadir}/icons/hicolor/24x24/apps/volume-booster.png
%{_datadir}/icons/hicolor/32x32/apps/volume-booster.png
%{_datadir}/icons/hicolor/48x48/apps/volume-booster.png
%{_datadir}/icons/hicolor/64x64/apps/volume-booster.png
%{_datadir}/icons/hicolor/96x96/apps/volume-booster.png
%{_datadir}/icons/hicolor/128x128/apps/volume-booster.png
%{_datadir}/icons/hicolor/256x256/apps/volume-booster.png
%{_datadir}/icons/hicolor/512x512/apps/volume-booster.png

%changelog
* Fri Nov 20 2026 Vanguard Arts SRL <support@vanguardarts.com> - 1.1.2-1
- Add in-app "Launch at startup" toggle.
* Fri Nov 20 2026 Vanguard Arts SRL <support@vanguardarts.com> - 1.1.1-1
- Update app icon (speaker with boost badge).
* Fri Nov 20 2026 Vanguard Arts SRL <support@vanguardarts.com> - 1.1.0-1
- Initial RPM packaging for Fedora / RHEL / Rocky / Alma / openSUSE.
