[Setup]
AppId={{B650EA00-6B13-4BAD-8750-11F50203BCB5}
AppName=TwitchLink
AppVersion={{APP_VERSION}}
AppPublisher=DevHotteok
AppPublisherURL=https://twitchlink.github.io
AppSupportURL=https://twitchlink.github.io
AppUpdatesURL=https://twitchlink.github.io
DefaultDirName={pf}\TwitchLink
DisableProgramGroupPage=yes
LicenseFile=LICENSE
OutputBaseFilename=TwitchLinkSetup-{{APP_VERSION}}
SetupIconFile=setup.ico
UninstallDisplayIcon={app}\TwitchLink.exe
UninstallDisplayName=TwitchLink
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}";

[Files]
Source: "dist\TwitchLink\TwitchLink.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\TwitchLink\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{commonprograms}\TwitchLink"; Filename: "{app}\TwitchLink.exe"
Name: "{commondesktop}\TwitchLink"; Filename: "{app}\TwitchLink.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TwitchLink.exe"; Description: "{cm:LaunchProgram,TwitchLink}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\TwitchLink"
