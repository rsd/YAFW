[Setup]
AppId={{D35F6BC1-8B1E-4F3D-94D5-50DA15F7D242}}
AppName=YAFW Video Optimizer
AppVersion=1.1.19
AppPublisher=YAFW Team
DefaultDirName={localappdata}\YAFW
PrivilegesRequired=lowest
DefaultGroupName=YAFW Video Optimizer
AllowNoIcons=yes
OutputDir=dist-installer
OutputBaseFilename=YAFW_Setup_1.1.19
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy PyInstaller output folder contents recursively
Source: "dist\YAFW\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\YAFW Video Optimizer"; Filename: "{app}\YAFW.exe"
Name: "{group}\{cm:UninstallProgram,YAFW Video Optimizer}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\YAFW Video Optimizer"; Filename: "{app}\YAFW.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\YAFW.exe"; Description: "{cm:LaunchProgram,YAFW Video Optimizer}"; Flags: nowait postinstall skipifsilent
