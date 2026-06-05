#define MyAppName "MM SimpleTools FileRenamer"
#define MyAppVersion "2.0"
#define MyAppPublisher "MM SimpleTools"
#define MyAppExeName "MM_SimpleTools_FileRenamer_V2.0.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\MM SimpleTools\FileRenamer
DefaultGroupName=MM SimpleTools\FileRenamer
DisableProgramGroupPage=yes
OutputDir=C:\Strukturwerk\MM_SimpleTools\FileRenamer\FileRenamer_Setup_V2\installer\output
OutputBaseFilename=MM_SimpleTools_FileRenamer_Setup_V2.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=C:\Strukturwerk\MM_SimpleTools\FileRenamer\FileRenamer_V2_DEV\app\icon.ico

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung erstellen"; GroupDescription: "Zusätzliche Symbole:"; Flags: unchecked

[Files]
Source: "C:\Strukturwerk\MM_SimpleTools\FileRenamer\FileRenamer_V2_DEV\dist\MM_SimpleTools_FileRenamer_V2.0.exe"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion
Source: "C:\Strukturwerk\MM_SimpleTools\FileRenamer\FileRenamer_V2_DEV\app\icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Strukturwerk\MM_SimpleTools\FileRenamer\FileRenamer_V2_DEV\docs\README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Strukturwerk\MM_SimpleTools\FileRenamer\FileRenamer_V2_DEV\docs\CHANGELOG.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Strukturwerk\MM_SimpleTools\FileRenamer\FileRenamer_V2_DEV\docs\Produktbeschreibung.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\MM SimpleTools FileRenamer"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\README"; Filename: "{app}\README.txt"
Name: "{group}\Deinstallieren"; Filename: "{uninstallexe}"
Name: "{autodesktop}\MM SimpleTools FileRenamer"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\README.txt"; Description: "README anzeigen"; Flags: postinstall shellexec skipifsilent
Filename: "{app}\{#MyAppExeName}"; Description: "MM SimpleTools FileRenamer starten"; Flags: nowait postinstall skipifsilent unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{app}"