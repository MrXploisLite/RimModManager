; RimModManager Windows Installer
; Built with Inno Setup
; Requires: PyInstaller .exe in dist/RimModManager-Windows-x64.exe

#define MyAppName "RimModManager"
#define MyAppVersion "0.6.0"
#define MyAppPublisher "MrXploisLite"
#define MyAppURL "https://github.com/MrXploisLite/RimModManager"
#define MyAppExeName "RimModManager.exe"

[Setup]
AppId={{B8F4A32B-9F5A-4A1C-8D7E-3F2A6C1E5D8B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=RimModManager-{#MyAppVersion}-Setup
SetupIconFile=resources\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
Source: "dist\RimModManager-Windows-x64.exe"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch RimModManager"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/c rmdir /s /q ""{app}\RimWorld_Workshop_Mods"""; Flags: runhidden; Description: "Remove Workshop download folder"
