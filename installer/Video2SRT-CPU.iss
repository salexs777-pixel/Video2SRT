#define MyAppName "Video2SRT CPU"
#define MyAppVersion "0.1.0"
#define MyAppExeName "Video2SRT.exe"

[Setup]
AppId={{313A4407-1364-47AC-B0D8-97C90BC52A5E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName=C:\Video2SRT-CPU
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=output
OutputBaseFilename=Video2SRT-CPU-Setup-0.1.0
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=..\LICENSE

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительно:"; Flags: unchecked

[Dirs]
Name: "{app}\models"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\output"; Permissions: users-modify
Name: "{app}\config"; Permissions: users-modify

[Files]
Source: "..\dist\Video2SRT-CPU\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY_LICENSES"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\config\glossary.txt"; DestDir: "{app}\config"; Flags: onlyifdoesntexist
Source: "..\config\CPU_ONLY.marker"; DestName: "CPU_ONLY"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\bin\ffmpeg.exe"; DestDir: "{app}\bin"; Flags: ignoreversion
Source: "..\bin\ffprobe.exe"; DestDir: "{app}\bin"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Video2SRT CPU"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Video2SRT CPU"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить Video2SRT CPU"; Flags: nowait postinstall skipifsilent
