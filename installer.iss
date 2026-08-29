; LayerDock installer script (Inno Setup) — branded, polished wizard

#define MyAppName "LayerDock"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "obligator11"
#define MyAppURL "https://github.com/obligator11/layerdock"
#define MyAppExeName "LayerDock.exe"

[Setup]
AppId={{8F3B2C1A-4D5E-4F6A-9B7C-1A2B3C4D5E6F}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE.txt
OutputDir=installer_output
OutputBaseFilename=LayerDock-Setup-{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
SetupIconFile=src\frontend\assets\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=LayerDock Setup

; --- Modern branded wizard ---
WizardStyle=modern
WizardSizePercent=100
WizardImageFile=installer_wizard_large.bmp
WizardSmallImageFile=installer_wizard_small.bmp
WizardImageStretch=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\LayerDock\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Messages]
WelcomeLabel1=Welcome to the [name] Setup Wizard
WelcomeLabel2=This will install [name/ver] on your computer.%n%nPixel-perfect PDF to Word conversion, fully offline.%n%nIt's recommended you close all other applications before continuing.
FinishedHeadingLabel=Completing the [name] Setup Wizard
FinishedLabel=Setup has finished installing [name] on your computer. The application may be launched by selecting the installed shortcuts.