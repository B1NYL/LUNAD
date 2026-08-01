{
  description = "Nix flake of Zhaoxiuya";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

        runtimeLibs = with pkgs; [
          stdenv.cc.cc.lib
          zlib
          mecab
          xorg.libX11
          xorg.libxcb
          glib
          libGL
          portaudio
        ];
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            pkg-config
            git
            uv
            python312
            mecab
            ffmpeg
          ];

          shellHook = ''
            export UV_PYTHON_PREFERENCE=only-system
            export UV_MANAGED_PYTHON=0
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath runtimeLibs}:$LD_LIBRARY_PATH"
          '';
        };
      }
    );
}
