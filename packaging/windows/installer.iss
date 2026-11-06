[Setup]
AppId=OpenCobolIDE-modern
AppName=OpenCobolIDE modern12
AppVersion=4.7.6
DefaultDirName={localappdata}\Programs\OpenCobolIDE-modern
DefaultGroupName=OpenCobolIDE modern12
PrivilegesRequired=lowest
MinVersion=10.0.22000
ArchitecturesAllowed=x64compatible
OutputBaseFilename=OpenCobolIDE-modern12-win11-x64-setup
Compression=lzma2
SolidCompression=yes

[Files]
Source: "{#AppBinary}"; DestDir: "{app}"; DestName: "opencobolide.exe"; Flags: ignoreversion

[Icons]
Name: "{group}\OpenCobolIDE modern12"; Filename: "{app}\opencobolide.exe"
