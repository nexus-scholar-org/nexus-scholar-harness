; Inno Setup script of the Windows installer (M13 Part W; specification §4.1, §4.6, Q2).
;
; Per user, no administrator password: the program goes to %LOCALAPPDATA%\Programs\Nexus Scholar,
; a Start-menu entry and (ticked) a desktop icon. Before installing or uninstalling, a running
; Nexus Scholar is stopped with the app's own `--stop`, after asking. Installing an older version
; over a newer one warns first. The uninstaller removes the program; it offers, unticked, to remove
; the user's settings and saved keys too (the app's `--forget`); it never removes a review.
;
; Compiled by packaging/windows/build.py with /DAppVersion, /DVersionKey and /DSourceDir.

#define AppName "Nexus Scholar"
#define AppExe "Nexus Scholar.exe"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef VersionKey
  #define VersionKey "0"
#endif
#ifndef SourceDir
  #define SourceDir "..\..\dist\windows\bundle\Nexus Scholar"
#endif
; The installer's identity: never change it, or Windows sees a different app.
#define AppId "B92289BA-7653-4894-9FA0-58C7339814EE"

[Setup]
AppId={{{#AppId}}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Nexus Scholar
AppPublisherURL=https://github.com/nexus-scholar
DefaultDirName={userpf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputBaseFilename=NexusScholar-{#AppVersion}-setup
SetupIconFile=..\icons\nexus-scholar.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
LicenseFile=..\..\LICENSE
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=no

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Icons:"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; The installed version as one number, for the next installer's downgrade check.
Root: HKCU; Subkey: "Software\{#AppName}"; ValueType: string; ValueName: "VersionKey"; ValueData: "{#VersionKey}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#AppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#AppVersion}"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Start Nexus Scholar"; Flags: nowait postinstall skipifsilent

[Code]
const
  UninstallKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{{#AppId}}_is1';

function InstalledExe(): String;
var
  Location: String;
begin
  Result := '';
  if RegQueryStringValue(HKCU, UninstallKey, 'InstallLocation', Location) then
    Result := AddBackslash(Location) + '{#AppExe}';
end;

function EngineRunning(): Boolean;
begin
  { The running engine writes engine.json in the settings folder and removes it when it stops. }
  Result := FileExists(ExpandConstant('{userappdata}\{#AppName}\engine.json'));
end;

procedure StopEngine(Exe: String);
var
  Code, Tries: Integer;
begin
  if (Exe <> '') and FileExists(Exe) then
    Exec(Exe, '--stop', '', SW_HIDE, ewWaitUntilTerminated, Code);
  { The engine needs a few seconds to close its open pages; engine.json goes when it has stopped. }
  Tries := 0;
  while EngineRunning() and (Tries < 40) do
  begin
    Sleep(250);
    Tries := Tries + 1;
  end;
end;

function AskToStop(Exe: String): Boolean;
begin
  Result := True;
  if not EngineRunning() then
    exit;
  if not WizardSilent() then
    if MsgBox('Nexus Scholar is running. Stop it now and continue? Open browser tabs will stop working.',
              mbConfirmation, MB_YESNO) <> IDYES then
    begin
      Result := False;
      exit;
    end;
  StopEngine(Exe);
end;

function InitializeSetup(): Boolean;
var
  Installed, InstalledVersion: String;
begin
  Result := True;
  { An older version over a newer one: warn first (specification §4.5). }
  if RegQueryStringValue(HKCU, 'Software\{#AppName}', 'VersionKey', Installed) then
    if StrToInt64Def(Installed, 0) > StrToInt64Def('{#VersionKey}', 0) then
    begin
      if not RegQueryStringValue(HKCU, 'Software\{#AppName}', 'Version', InstalledVersion) then
        InstalledVersion := 'a newer version';
      if WizardSilent() then
        Result := False
      else
        Result := MsgBox('Nexus Scholar ' + InstalledVersion + ' is installed, which is newer than this installer ({#AppVersion}). ' +
                         'Install the older version over it? Your reviews are kept either way.',
                         mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
      if not Result then
        exit;
    end;
  Result := AskToStop(InstalledExe());
end;

var
  RemoveUserData: Boolean;

function InitializeUninstall(): Boolean;
begin
  Result := AskToStop(ExpandConstant('{app}\{#AppExe}'));
  if not Result then
    exit;
  { Unticked by default (specification §4.6): the answer No is the default button; a silent uninstall keeps them. }
  RemoveUserData := False;
  if not UninstallSilent() then
    RemoveUserData := MsgBox('Also remove your Nexus Scholar settings and saved keys?' + #13#10#13#10 +
                             'Your reviews are never removed.', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Code: Integer;
begin
  { Before the program's files go: the app removes its own settings, saved keys, logs and cache. }
  if (CurUninstallStep = usUninstall) and RemoveUserData then
    Exec(ExpandConstant('{app}\{#AppExe}'), '--forget', '', SW_HIDE, ewWaitUntilTerminated, Code);
end;
