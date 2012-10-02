;NSIS Modern User Interface
;@prj.appname@ Font NSIS Installer script
;Written by Martin Hosken

; Some useful definitions that may need changing for different font versions
!ifndef VERSION
  !define VERSION @prj.version@
!endif

!define PACKNAME "@prj.desc_name or prj.appname.title()@"
!define SRC_ARCHIVE "fonts-@prj.appname@-${VERSION}.zip"
+for f in fonts :
!define FONT_@f.id@_FILE "@f.target@"
-
!define INSTALL_SUFFIX "SIL\Fonts\@prj.appname.title()@"
!define FONT_DIR "$WINDIR\Fonts"
var UninstFile
var UnDebugFile
!define Uninst "UnInstall.log"

SetCompressor lzma

;-----------------------------
; Macros for Font installation
;-----------------------------
!addplugindir @os.path.join('..', basedir)@
!addincludedir @os.path.join('..', basedir)@
!include FileFunc.nsh
!include WordFunc.nsh
!include x64.nsh

!insertmacro VersionCompare
!insertmacro GetParent
!insertmacro un.GetFileName

!ifmacrondef GetUnixFileNameCall
		!macro GetUnixFileNameCall _PATHSTRING _RESULT
				Push `${_PATHSTRING}`
				Call GetUnixFileName
				Pop ${_RESULT}
		!macroend
!endif

!define GetUnixFileName `!insertmacro GetUnixFileNameCall`

Function GetUnixFileName
	Exch $0
	Push $1
	Push $2

	StrCpy $2 $0 1 -1
	StrCmp $2 '/' 0 +3
	StrCpy $0 $0 -1
	goto -3

	StrCpy $1 0
	IntOp $1 $1 - 1
	StrCpy $2 $0 1 $1
	StrCmp $2 '' end
	StrCmp $2 '/' 0 -3
	IntOp $1 $1 + 1
	StrCpy $0 $0 '' $1

	end:
	Pop $2
	Pop $1
	Exch $0
FunctionEnd

### End Code From ###

!macro InstallTTF FontFile
  Push $0
  Push $R0
  Push $R1
  Push $R2
  Push $R3

  !define Index 'Line${__LINE__}'

; Get the Font's File name
  ${GetUnixFileName} ${FontFile} $0
  !define FontFileName $0

  SetOutPath ${FONT_DIR}
  IfFileExists "${FONT_DIR}\${FontFileName}" ${Index} "${Index}-New"

  !ifdef FontBackup
	"${Index}-New:"
	;Implementation of Font Backup Store
	  WriteRegStr HKLM "${FontBackup}" "${FontFileName}" "OK"
	  File /r '${FontFile}'
	  goto ${Index}
  !else
	"${Index}-New:"
	  File /r '${FontFile}'
	  goto ${Index}
  !endif

${Index}:
  ClearErrors
  ReadRegStr $R0 HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion" "CurrentVersion"
  IfErrors "${Index}-9x" "${Index}-NT"

"${Index}-NT:"
  StrCpy $R1 "Software\Microsoft\Windows NT\CurrentVersion\Fonts"
  goto "${Index}-GO"

"${Index}-9x:"
  StrCpy $R1 "Software\Microsoft\Windows\CurrentVersion\Fonts"
  goto "${Index}-GO"

"${Index}-GO:"
  ClearErrors
  System::Call "GDI32::AddFontResourceA(t) i ('${FontFileName}') .s"
  !insertmacro FontName "${FONT_DIR}\${FontFileName}"
  pop $R2
  IfErrors 0 "${Index}-Add"
	MessageBox MB_OK "$R2"
	goto "${Index}-End"

"${Index}-Add:"
  StrCpy $R2 "$R2 (TrueType)"
  ClearErrors
  ReadRegStr $R0 HKLM "$R1" "$R2"
  StrCmp $R0 "" 0 "${Index}-End"
	WriteRegStr HKLM "$R1" "$R2" "${FontFileName}"
	goto "${Index}-End"

"${Index}-End:"

  !undef Index
  !undef FontFileName

  pop $R3
  pop $R2
  pop $R1
  Pop $R0
  Pop $0
!macroend

!macro unFontName FONTFILE
  push ${FONTFILE}
  call un.GetFontName
!macroend

!macro FontName FONTFILE
  push ${FONTFILE}
  call GetFontName
!macroend

Function GetFontName
  Exch $R0
  Push $R1
  Push $R2

  System::Call *(i${NSIS_MAX_STRLEN})i.R1
  System::Alloc ${NSIS_MAX_STRLEN}
  Pop $R2
  System::Call gdi32::GetFontResourceInfoW(wR0,iR1,iR2,i1)i.R0
  IntCmp $R0 0 GFN_error
	System::Call *$R2(&w${NSIS_MAX_STRLEN}.R0)
	Goto GFN_errordone
  GFN_error:
	StrCpy $R0 error
  GFN_errordone:
  System::Free $R1
  System::Free $R2

  Pop $R2
  Pop $R1
  Exch $R0
FunctionEnd

Function un.GetFontName
  Exch $R0
  Push $R1
  Push $R2

  System::Call *(i${NSIS_MAX_STRLEN})i.R1
  System::Alloc ${NSIS_MAX_STRLEN}
  Pop $R2
  System::Call gdi32::GetFontResourceInfoW(wR0,iR1,iR2,i1)i.R0
  IntCmp $R0 0 GFN_error
	System::Call *$R2(&w${NSIS_MAX_STRLEN}.R0)
	Goto GFN_errordone
  GFN_error:
	StrCpy $R0 error
  GFN_errordone:
  System::Free $R1
  System::Free $R2

  Pop $R2
  Pop $R1
  Exch $R0
FunctionEnd

!macro RemoveTTF FontFile
  Push $0
  Push $R0
  Push $R1
  Push $R2
  Push $R3
  Push $R4

  !define Index 'Line${__LINE__}'

; Get the Font's File name
  ${GetUnixFileName} ${FontFile} $0
  !define FontFileName $0

  IfFileExists "${FONT_DIR}\${FontFileName}" ${Index} "${Index}-End"

${Index}:
  ClearErrors
  ReadRegStr $R0 HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion" "CurrentVersion"
  IfErrors "${Index}-9x" "${Index}-NT"

"${Index}-NT:"
  StrCpy $R1 "Software\Microsoft\Windows NT\CurrentVersion\Fonts"
  goto "${Index}-GO"

"${Index}-9x:"
  StrCpy $R1 "Software\Microsoft\Windows\CurrentVersion\Fonts"
  goto "${Index}-GO"

  !ifdef FontBackup
  "${Index}-GO:"
  ;Implementation of Font Backup Store
	StrCpy $R2 ''
	ReadRegStr $R2 HKLM "${FontBackup}" "${FontFileName}"
	StrCmp $R2 'OK' 0 "${Index}-Skip"

	ClearErrors
	!insertmacro FontName "${FONT_DIR}\${FontFileName}"
	pop $R2
	IfErrors 0 "${Index}-Remove"
	MessageBox MB_OK "$R2"
	goto "${Index}-End"

  "${Index}-Remove:"
	StrCpy $R2 "$R2 (TrueType)"
	System::Call "GDI32::RemoveFontResourceA(t) i ('${FontFileName}') .s"
	DeleteRegValue HKLM "$R1" "$R2"
	DeleteRegValue HKLM "${FontBackup}" "${FontFileName}"
	EnumRegValue $R4 HKLM "${FontBackup}" 0
	IfErrors 0 "${Index}-NoError"
	  MessageBox MB_OK "FONT (${FontFileName}) Removal.$\r$\n(Registry Key Error: $R4)$\r$\nRestart computer and try again. If problem persists contact your supplier."
	  Abort "EnumRegValue Error: ${FontFileName} triggered error in EnumRegValue for Key $R4."
  "${Index}-NoError:"
	StrCmp $R4 "" 0 "${Index}-NotEmpty"
	  DeleteRegKey HKLM "${FontBackup}" ; This will delete the key if there are no more fonts...
  "${Index}-NotEmpty:"
	Delete /REBOOTOK "${FONT_DIR}\${FontFileName}"
	goto "${Index}-End"
  "${Index}-Skip:"
	goto "${Index}-End"
  !else
  "${Index}-GO:"

	ClearErrors
	!insertmacro FontName "${FONT_DIR}\${FontFileName}"
	pop $R2
	IfErrors 0 "${Index}-Remove"
	MessageBox MB_OK "$R2"
	goto "${Index}-End"

  "${Index}-Remove:"
	StrCpy $R2 "$R2 (TrueType)"
	System::Call "GDI32::RemoveFontResourceA(t) i ('${FontFileName}') .s"
	DeleteRegValue HKLM "$R1" "$R2"
	delete /REBOOTOK "${FONT_DIR}\${FontFileName}"
	goto "${Index}-End"
  !endif

"${Index}-End:"

  !undef Index
  !undef FontFileName

  pop $R4
  pop $R3
  pop $R2
  pop $R1
  Pop $R0
  Pop $0
!macroend

!macro unRemoveTTF FontFile
  Push $0
  Push $R0
  Push $R1
  Push $R2
  Push $R3
  Push $R4

  !define Index 'Line${__LINE__}'

; Get the Font's File name
  ${un.GetFileName} ${FontFile} $0
  !define FontFileName $0

;  DetailPrint "Testing that $FONT_DIR\${FontFileName} exists"
  IfFileExists "${FONT_DIR}\${FontFileName}" ${Index} "${Index}-End"

${Index}:
  ClearErrors
  ReadRegStr $R0 HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion" "CurrentVersion"
  IfErrors "${Index}-9x" "${Index}-NT"

"${Index}-NT:"
  StrCpy $R1 "Software\Microsoft\Windows NT\CurrentVersion\Fonts"
  goto "${Index}-GO"

"${Index}-9x:"
  StrCpy $R1 "Software\Microsoft\Windows\CurrentVersion\Fonts"
  goto "${Index}-GO"

  !ifdef FontBackup
  "${Index}-GO:"
  ;Implementation of Font Backup Store
	StrCpy $R2 ''
	ReadRegStr $R2 HKLM "${FontBackup}" "${FontFileName}"
	StrCmp $R2 'OK' 0 "${Index}-Skip"

	ClearErrors
	!insertmacro FontName "${FONT_DIR}\${FontFileName}"
	pop $R2
	IfErrors 0 "${Index}-Remove"
	MessageBox MB_OK "$R2"
	goto "${Index}-End"

  "${Index}-Remove:"
	StrCpy $R2 "$R2 (TrueType)"
	System::Call "GDI32::RemoveFontResourceA(t) i ('${FontFileName}') .s"
	DeleteRegValue HKLM "$R1" "$R2"
	DeleteRegValue HKLM "${FontBackup}" "${FontFileName}"
	EnumRegValue $R4 HKLM "${FontBackup}" 0
	IfErrors 0 "${Index}-NoError"
	  MessageBox MB_OK "FONT (${FontFileName}) Removal.$\r$\n(Registry Key Error: $R4)$\r$\nRestart computer and try again. If problem persists contact your supplier."
	  Abort "EnumRegValue Error: ${FontFileName} triggered error in EnumRegValue for Key $R4."
  "${Index}-NoError:"
	StrCmp $R4 "" 0 "${Index}-NotEmpty"
	  DeleteRegKey HKLM "${FontBackup}" ; This will delete the key if there are no more fonts...
  "${Index}-NotEmpty:"
	Delete /REBOOTOK "${FONT_DIR}\${FontFileName}"
	goto "${Index}-End"
  "${Index}-Skip:"
	goto "${Index}-End"
  !else
  "${Index}-GO:"

	ClearErrors
	!insertmacro unFontName "${FONT_DIR}\${FontFileName}"
	pop $R2
;    DetailPrint "Uninstalling font name $R2"
	IfErrors 0 "${Index}-Remove"
	MessageBox MB_OK "$R2"
	goto "${Index}-End"

  "${Index}-Remove:"
	StrCpy $R2 "$R2 (TrueType)"
	System::Call "GDI32::RemoveFontResourceA(t) i ('${FontFileName}') .s"
	DeleteRegValue HKLM "$R1" "$R2"
	delete /REBOOTOK "${FONT_DIR}\${FontFileName}"
	goto "${Index}-End"
  !endif

"${Index}-End:"

  !undef Index
  !undef FontFileName

  pop $R4
  pop $R3
  pop $R2
  pop $R1
  Pop $R0
  Pop $0
!macroend

;--------------------------------
;Include Modern UI

  !include "MUI.nsh"

;--------------------------------
;General

  ;Name and file
  Name "${PACKNAME} Font (${VERSION})"
  Caption "@prj.desc_short@"

  OutFile "@prj.outdir or '.'@/${PACKNAME}-${VERSION}.exe"
  InstallDir $PROGRAMFILES\${INSTALL_SUFFIX}

  ;Get installation folder from registry if available
  InstallDirRegKey HKLM "Software\${INSTALL_SUFFIX}" ""

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_WELCOME
  @'!insertmacro MUI_PAGE_LICENSE "' + prj.license + '"' if prj.license else ''@
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  !define MUI_STARTMENUPAGE

  !define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKLM"
  !define MUI_STARTMENUPAGE_REGISTRY_KEY \
	"Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKNAME}"
  !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
  !define MUI_STARTMENUPAGE_FONT_VARIABLE $R9
  !define MUI_STARTMENUPAGE_FONT_DEFAULTFOLDER "SIL\Fonts\@prj.appname@"

;--------------------------------
;Languages

  !insertmacro MUI_LANGUAGE "English"

  VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductName" "${PACKNAME}"
  VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductVersion" "${VERSION}"
  VIAddVersionKey /LANG=${LANG_ENGLISH} "FileVersion" "${VERSION}"
  VIAddVersionKey /LANG=${LANG_ENGLISH} "CompanyName" "SIL International"
  VIAddVersionKey /LANG=${LANG_ENGLISH} "Comments" "@prj.desc_short or ""@"
  VIAddVersionKey /LANG=${LANG_ENGLISH} "FileDescription" "${PACKNAME} Font installer"
  @'VIAddVersionKey /LANG=${LANG_ENGLISH} "LegalCopyright" "' + prj.copyright + '"' if prj.copyright else ""@
  VIProductVersion @getattr(prj, 'WINDOWS_VERSION', ".".join((str(prj.version).split('.') + ["0", "0", "0", "0"])[0:4]))@

;--------------------------------
;Installer Sections


Section "@"!" if len(fonts) else "-"@${PACKNAME} Font" SecFont

  SetOutPath "$WINDIR\Fonts"

  IfErrors BranchDoit
  ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKNAME}" "Version"
  ${VersionCompare} $0 ${VERSION} $R0
  IntCmp $R0 1 BranchQuery BranchQuery BranchUninstall

  BranchQuery:
	MessageBox MB_YESNO|MB_ICONQUESTION "A newer or same version of ${PACKNAME} is already installed. Do you want me to force the installation of this font package?" /SD IDNO IDYES BranchUninstall

  Abort "Installation of ${PACKNAME} aborting"

  BranchUninstall:
	; execute the uninstaller if it's there else abort
	ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKNAME}" "UninstallString"
	${GetParent} "$0" $1
	ExecWait '"$0" /S _?=$1'

  BranchDoit:

	SetOutPath "$INSTDIR"
	;Default installation folder

	;Store installation folder
	WriteRegStr HKLM "Software\${INSTALL_SUFFIX}" "" $INSTDIR

	; add keys for Add/Remove Programs entry
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKNAME}" \
				 "DisplayName" "${PACKNAME} ${VERSION}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKNAME}" \
				 "UninstallString" "$INSTDIR\Uninstall.exe"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKNAME}" \
				 "Version" "${VERSION}"
  BranchInstall:

+if len(fonts) :
  IfErrors BranchTestRem
+ for f in fonts :
	!insertmacro InstallTTF "@bld(f, f.target)@"
-

	SendMessage ${HWND_BROADCAST} ${WM_FONTCHANGE} 0 0 /TIMEOUT=5000

	Goto BranchDone

  BranchTestRem:
+ for f in fonts:
	IfFileExists "$WINDIR/Fonts/@f.target@" 0 BranchNoExist
-
	MessageBox MB_YESNO|MB_ICONQUESTION "Would you like to overwrite existing ${PACKNAME} fonts?" /SD IDYES IDYES BranchOverwrite ; skipped if file doesn't exist

	Abort

  BranchOverwrite:
+ for f in fonts :
	!insertmacro RemoveTTF "@f.target@"
-
	  SetOverwrite try
	  Goto BranchInstall
  BranchNoExist:
	  SetOverwrite ifnewer ; NOT AN INSTRUCTION, NOT COUNTED IN SKIPPINGS
	  Goto BranchInstall
-
  BranchDone:
	;Create uninstaller
	WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "@"" if len(kbds) else "-"@Keyboards" SecKbd

	ReadRegStr $0 HKCU "Software\Tavultesoft" "Version"
	IfErrors NoKeyman
+if 'KMCOMP' in env:
+ for k in kbds :
	File "@bld(k, k.kmx)@"
	Exec "start.exe $OUTDIR\@k.kmx@"
-
-
	NoKeyman:

	@"\n".join(['File "' + bld(k, k.target) + '"' for k in kbds if hasattr(k, 'target')])@
	@"\n".join(['File "' + bld(k, k.pdf) + '"' for k in kbds if hasattr(k, 'pdf')])@

	ReadRegStr $0 HKLM "Software\ThanLwinSoft.org\Ekaya_x86" ""
	IfErrors NoEkaya32
+for k in kbds :
	CopyFiles "$OUTDIR\@k.target@" "$0\Ekaya\kmfl"
-
	NoEkaya32:
	FileOpen $UninstFile "$INSTDIR\${Uninst}" w

+for k in kbds : m = getattr(k, 'mskbd', None);
+ if m :
	IntOp $R1 0 + @m.lid@
	StrCpy $R2 "@m.dll.replace('.', '-86.')@"
	File "@bld(k, m.dll.replace('.', '-86.'))@"
	StrCpy $R4 $R2
+    if os.path.exists(bld(k, m.dll.replace('.', '-64.'))) :
	StrCpy $R3 "@m.dll.replace('.', '-64.')@"
	File "@bld(k, m.dll.replace('.', '-64.'))@"
	${If} ${RunningX64}
		StrCpy $R4 $R3
	${Endif}
-

	LidStart:
	ClearErrors
	IntFmt $R5 "SYSTEM\CurrentControlSet\Control\Keyboard Layouts\%08X" $R1
	ReadRegStr $0 HKLM $R5 "Layout File"
	StrCmp $0 "" LidDone
		IntOp $R1 $R1 + 0x10000
		Goto LidStart

	LidDone:
	WriteRegStr HKLM $R5 \
		"Layout Display Name" "@%SystemRoot%/system32/$R4,-1000"
	WriteRegStr HKLM $R5 \
		"Layout File" $R4
	WriteRegStr HKLM $R5 \
		"Layout Id" "$R1"
	WriteRegStr HKLM $R5 \
		"Layout Product Code" "{@m.guid@}"
	WriteRegStr HKLM $R5 \
		"Layout Text" "@%SystemRoot%/system32/$R4,-1100"
	FileWrite $UninstFile "$R1$\r$\n"

	CopyFiles "$OUTDIR\$R4" $SYSDIR
	${If} ${RunningX64}
		CopyFiles "$OUTDIR\$R2" "$WINDIR\WOW64"
	${Endif}
+  for l in getattr(m, 'lidinstall', []) :
	StrCpy $R2 @l@
	LidInstall:
	  ClearErrors
	  IntFmt $R5 "%08X" $R2
	  ReadRegStr $0 HKCU "Keyboard Layout\Substitutes" $R5
	  Strcmp $0 "" LidInstallDone
		IntOp $R2 $R2 + 0x10000
		Goto LidInstall

	LidInstallDone:
	IntFmt $R3 "%08X" $R1
	WriteRegStr HKCU "Keyboard Layout\Substitutes" $R5 $R3
	StrCpy $R4 1
	LidInstallLoop:
	  ClearErrors
	  ReadRegStr $R6 HKCU "Keyboard Layout\Preload" $R4
	  IntOp $R4 $R4 + 1
	  IfErrors 0 LidInstallLoop
	IntOp $R4 $R4 - 1
	WriteRegStr HKCU "Keyboard Layout\Preload" $R4 $R5
-
-
-
	FileClose $UninstFile
	;Create uninstaller
	WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section -StartMenu
  @'File "' + prj.license + '"' if prj.license else ''@
+if hasattr(prj, 'docdir') :
+ for dp, dn, fs in os.walk(prj.docdir) :
+  for fn in fs :
+    if not fn.startswith('.') :
   File "/ONAME=$OUTDIR\@os.path.join(dp.replace(prj.docdir, 'docs'), fn).replace('/','\\')@" "@os.path.join('..', dp, fn)@"
-
-
-
-
  !insertmacro MUI_STARTMENU_WRITE_BEGIN "FONT"
  SetShellVarContext all
  CreateDirectory $SMPROGRAMS\${MUI_STARTMENUPAGE_FONT_VARIABLE}
  IfFileExists $SMPROGRAMS\${MUI_STARTMENUPAGE_FONT_VARIABLE} createIcons
	SetShellVarContext current
	CreateDirectory $SMPROGRAMS\${MUI_STARTMENUPAGE_FONT_VARIABLE}

  createIcons:
+if hasattr(prj, 'docdir') :
+ for dp, dn, fs in os.walk(prj.docdir) :
+  for fn in fs :
+    if not fn.startswith('.') :
   CreateShortCut $SMPROGRAMS/${MUI_STARTMENUPAGE_FONT_VARIABLE}/@fn@.lnk $OUTDIR/@os.path.join(dp.replace(prj.docdir, 'docs'), fn)@
-
-
-
-
	CreateShortCut $SMPROGRAMS\${MUI_STARTMENUPAGE_FONT_VARIABLE}\Uninstall.lnk $INSTDIR\Uninstall.exe
	WriteRegStr ${MUI_STARTMENUPAGE_REGISTRY_ROOT} "${MUI_STARTMENUPAGE_REGISTRY_KEY}" "Menus" "$SMPROGRAMS\${MUI_STARTMENUPAGE_FONT_VARIABLE}"
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

;Optional source font - as a compressed archive
Section "Documentation" SecSrc

  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  ;ADD YOUR OWN FILES HERE...
+d = {};
+ for f in getattr(prj, 'extra_dist', '').split(' ') :
+  if f and not os.path.dirname(f) in d :
  CreateDirectory @os.path.dirname(f).replace('/','\\')@
-d[f] = 1
-
-
+for f in getattr(prj, 'extra_dist', '').split(' ') :
  @'File "/ONAME=$OUTDIR\\' + f.replace('/','\\') + '" "' + f.replace('/', '\\') + '"' if f else ""@
-

SectionEnd


;--------------------------------
;Descriptions

  ;Language strings
  LangString DESC_SecFont ${LANG_ENGLISH} "Install the ${PACKNAME} font (version ${VERSION}). @prj.desc_short or ""@"

  ;Assign language strings to sections
  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecFont} $(DESC_SecFont)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
;Uninstaller Section

Section "Uninstall"

  ;ADD YOUR OWN FILES HERE...

  ;FileOpen $UnDebugFile "$INSTDIR\..\Uninstalled.log" w
  ;FileWrite $UnDebugFile "Debugging uninstall$\r$\n"

+for f in fonts :
	!insertmacro unRemoveTTF "@f.target@"
-
  SendMessage ${HWND_BROADCAST} ${WM_FONTCHANGE} 0 0 /TIMEOUT=5000

  ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKNAME}" "Menus"
+for f in getattr(prj, 'EXTRA_DIST', '').split(' ') :
+ if f:
  ;Delete "$INSTDIR\\@f.replace('/','\\')@"
-
-
+if hasattr(prj, 'docdir') :
+ for dp, dn, fs in os.walk(prj.docdir) :
+  for fn in fs :
+    if fn and not fn.startswith('.'):
   ;Delete "$INSTDIR\@os.path.join(dp.replace(prj.docdir, 'docs'), fn).replace('/','\\')@"
-
-
-
-
+d = {};
+for f in getattr(prj, 'extra_dist', '').split(' ') :
+ if os.path.dirname(f) and not os.path.dirname(f) in d :
   ;RmDir "$INSTDIR\@os.path.dirname(f).replace('/','\\')@"
- d[f] = 1
-
-

+if hasattr(prj, 'docdir') :
+ for dp, dn, fs in os.walk(prj.docdir) :
+  for fn in fs :
+    if not fn.startswith('.') :
   Delete "$0\@fn@.lnk"
-
-
-
-

  IfFileExists "$INSTDIR\${Uninst}" dokbds
	goto donekbds
  dokbds:
	FileOpen $UninstFile "$INSTDIR\${Uninst}" r
	loopkbd:
	  ClearErrors
	  FileRead $UninstFile $R1
	  ;FileWrite $UnDebugFile "Read from Uninstall.log: $R1$\r$\n"
	  IfErrors donekbdloop
	  StrCmp $R1 "" donekbdloop
	  IntFmt $R5 "SYSTEM\CurrentControlSet\Control\Keyboard Layouts\%08X" $R1
	  DeleteRegKey HKLM $R5
	  ;FileWrite $UnDebugFile "DeleteRegKey: $R5$\r$\n"
	  StrCpy $1 0
	  loopinstalledkbd:
		ClearErrors
		EnumRegValue $2 HKCU "Keyboard Layout\Substitutes" $1
		StrCmp $2 "" doneinstallkbd
		IntOp $1 $1 + 1
		ReadRegStr $3 HKCU "Keyboard Layout\Substitutes" $2
		IntCmp $3 $R1 0 loopinstalledkbd loopinstalledkbd
		DeleteRegKey HKCU "Keyboard Layout\Substitutes\$2"
		;FileWrite $UnDebugFile "Delete Substitutes: $2$\r$\n"
		IntOp $1 $1 - 1
		StrCpy $4 0
		loopkbdinstallers:
		  ClearErrors
		  EnumRegValue $5 HKCU "Keyboard Layout\Preload" $4
		  StrCmp $5 "" loopinstalledkbd
		  IntOp $4 $4 + 1
		  ReadRegStr $6 HKCU "Keyboard Layout\Preload" $5
		  IntCmp $6 $2 0 loopkbdinstallers loopkbdinstallers
		  DeleteRegKey HKCU "Keyboard Layout\Preload\$5"
		  IntOp $4 $4 - 1
		  IfErrors loopinstalledkbd loopkbdinstallers

	  doneinstallkbd:
	  StrCmp $R5 "" 0 loopkbd

	donekbdloop:
	  FileClose $UninstFile

+for k in kbds : m = getattr(k, 'mskbd', None);
+ if m :
	  StrCpy $R2 "@m.dll.replace('.', '-86.')@"
	  ;Delete "$INSTDIR\$R2"
	  StrCpy $R4 $R2
+    if env['X86_64GCC'] :
	  StrCpy $R3 "@m.dll.replace('.', '-64.')@"
	  ;Delete "$INSTDIR\$R3"
	  ${If} ${RunningX64}
		StrCpy $R4 $R3
	  ${Endif}
-
	  Delete "$SYSDIR\$R4"
	  ${If} ${RunningX64}
		Delete "$WINDIR\WOW64\$R2"
	  ${Endif}
-
-
  donekbds:
+if 'KMCOMP' in env:
+ for k in kbds :
	;Delete "$INSTDIR\@os.path.basename(k.kmx)@"
-
-
	;@"\n".join(['Delete "$INSTDIR\\' + os.path.basename(k.target) + '"' for k in kbds if hasattr(k, 'target')])@
	;@"\n".join(['Delete "$INSTDIR\\' + os.path.basename(k.pdf) + '"' for k in kbds if hasattr(k, 'pdf')])@

  ;@'Delete "$INSTDIR\\' + prj.license + '"' if prj.license else ''@

  ;Delete "$0\Uninstall.lnk"
  ;RMDir "$0"

  noshortcuts:

  ;FileClose $UnDebugFile
  RMDir /r "$INSTDIR"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKNAME}"
  DeleteRegKey HKLM "Software\${INSTALL_SUFFIX}"
	;FileWrite $UnDebugFile "Cleared dir $INSTDIR, and key for ${PACKNAME}"
  doneall:
  ;FileClose $UnDebugFile
SectionEnd
