# Nix package for Volume Booster.
#
# Build with:  nix build
# Uses the python3 with PyQt6 and ensures `pactl` (from libpulse) is on PATH.
{ lib, stdenv, python3, libpulse, makeWrapper }:

let
  py = python3.withPackages (ps: [ ps.pyqt6 ]);
in
stdenv.mkDerivation rec {
  pname = "volume-booster";
  version = "1.1.4";

  src = ./.;

  nativeBuildInputs = [ makeWrapper ];

  installPhase = ''
    runHook preInstall
    install -Dm755 volume_booster.py "$out/libexec/volume-booster/volume_booster.py"
    makeWrapper "${py}/bin/python3" "$out/bin/volume-booster" \
      --prefix PATH : "${libpulse}/bin" \
      --add-flags "$out/libexec/volume-booster/volume_booster.py"
    install -Dm644 packaging/volume-booster.desktop \
      "$out/share/applications/volume-booster.desktop"
    install -Dm644 packaging/volume-booster.svg \
      "$out/share/icons/hicolor/scalable/apps/volume-booster.svg"
    for sz in 16 24 32 48 64 96 128 256 512; do
      install -Dm644 packaging/icons/hicolor/''${sz}x''${sz}/apps/volume-booster.png \
        "$out/share/icons/hicolor/''${sz}x''${sz}/apps/volume-booster.png"
    done
    runHook postInstall
  '';

  meta = with lib; {
    description = "System tray volume booster for quiet audio";
    homepage = "https://github.com/VanguardArts/volume-booster";
    license = licenses.mit;
    mainProgram = "volume-booster";
    platforms = platforms.linux;
  };
}
