#define MyAppName "MM SimpleTools FileRenamer"
#define MyAppVersion "1.0"
#define MyAppPublisher "MM SimpleTools"
#define MyAppExeName "FileRenamer.exe"

[Setup]
AppId={{A7F9F1E2-5B4D-4F18-9A2E-FILERENAMER10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\MM SimpleTools\FileRenamer
DefaultGroupName=MM SimpleTools\FileRenamer
DisableProgramGroupPage=yes
OutputDir=C:\Strukturwerk\MM_SimpleTools\FileRenamer_Setup_V1\installer\output
OutputBaseFilename=MM_SimpleTools_FileRenamer_Setup_V1.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
; SetupIconFile=C:\Strukturwerk\MM_SimpleTools\FileRenamer_Setup_V1\app\icon.ico

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung erstellen"; GroupDescription: "Zusätzliche Symbole:"; Flags: unchecked

[Files]
Source: "C:\Strukturwerk\MM_SimpleTools\FileRenamer_Setup_V1\build\FileRenamer.exe"; DestDir: "{app}"; Flags: ignoreversion

Source: "C:\Strukturwerk\MM_SimpleTools\FileRenamer_Setup_V1\docs\README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Strukturwerk\MM_SimpleTools\FileRenamer_Setup_V1\docs\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Strukturwerk\MM_SimpleTools\FileRenamer_Setup_V1\docs\VERSION.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Strukturwerk\MM_SimpleTools\FileRenamer_Setup_V1\docs\CHANGELOG.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Strukturwerk\MM_SimpleTools\FileRenamer_Setup_V1\docs\Produktbeschreibung.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\MM SimpleTools FileRenamer"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\README"; Filename: "{app}\README.txt"
Name: "{group}\Deinstallieren"; Filename: "{uninstallexe}"
Name: "{autodesktop}\MM SimpleTools FileRenamer"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\README.txt"; Description: "README anzeigen"; Flags: postinstall shellexec skipifsilent
Filename: "{app}\{#MyAppExeName}"; Description: "MM SimpleTools FileRenamer starten"; Flags: nowait postinstall skipifsilent unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{app}"