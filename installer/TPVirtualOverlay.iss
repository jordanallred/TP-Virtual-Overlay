; Inno Setup script for TP Virtual Overlay.
; Builds a per-user installer (no admin rights required) around the
; standalone exe produced by `pyinstaller TPVirtualOverlay.spec`.
;
; Build locally:
;   uv run pyinstaller TPVirtualOverlay.spec --noconfirm --clean
;   iscc installer\TPVirtualOverlay.iss
;
; CI builds this automatically on every version tag (see
; .github/workflows/release.yml) using the Inno Setup install that ships on
; GitHub's windows-latest runners.

#define MyAppName "TP Virtual Overlay"
; CI passes the real released version via `iscc /DMyAppVersion=X.Y.Z ...`;
; this is just a fallback so a plain local `iscc` invocation still works.
#ifndef MyAppVersion
  #define MyAppVersion "0.5.0"
#endif
#define MyAppPublisher "Jordan Allred"
#define MyAppURL "https://github.com/jordanallred/TP-Virtual-Overlay"
#define MyAppExeName "TPVirtualOverlay.exe"

[Setup]
AppId={{2F1E9F0A-3B7C-4B8E-9A6B-7C9B6E9F1A2D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; No admin rights needed: installs entirely within the current user's profile.
PrivilegesRequired=lowest
OutputDir=..\installer_dist
OutputBaseFilename=TPVirtualOverlaySetup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "startupicon"; Description: "&Launch TP Virtual Overlay automatically when Windows starts"; \
    GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; \
    Flags: nowait postinstall skipifsilent unchecked
