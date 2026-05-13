# Ghidra Integrity Focus

Program: `system_stream1_0x24bbb5_inflated.bin`

## String Hits And Xrefs

- `aUpgradeMgrImpl.cpp` at `008e8734`: `.mp4....HighComp....MedComp.LowComp.IMAGE.BIN...aUpgradeMgrImpl.cpp.m_fwInstaller.MountUpgradeFileSystem()..dicomDirUpgradeIsOk.userDirUpgradeIsOk..aUpgradeMgrImpl::CheckForUpgrade...`
  - no Ghidra xrefs
- `aUpgradeMgrImpl::CheckForUpgrades` at `008e8798`: `stem()..dicomDirUpgradeIsOk.userDirUpgradeIsOk..aUpgradeMgrImpl::CheckForUpgrades Storage device not ready, delaying upgrade\n...IsUpgradeInProgress()...0.0.0.0.0.0.0.0.0.0.0.0.0.0...`
  - no Ghidra xrefs
- `aUpgradeReader.cpp` at `008f78f0`: `e/CParm.h...m_isValid...bad_alloc...IMAGE.BIN...aUpgradeReader.cpp..m_upgradeSelected......... .......v.......v.......v....... ....... ....... ....... .........14aUpgradeReader.......`
  - no Ghidra xrefs
- `aUpgradeFWReader` at `008f6ada`: `...S ......U ......Q .....0T ......T .........16aUpgradeFWReader..bad_alloc...r:/c2arm/libs/afc/include/CParm.h...m_isValid...IMAGE.BIN...aUpgradeSHInstaller.cpp.false...aUpgradeSH...`
  - no Ghidra xrefs
- `aUpgradeSHReader` at `008f6864`: `50.29.999.999...rb..\opt\TurboSHDb..%s\%s...%s..aUpgradeSHReader.cpp....NULL != packHeader..versionStr..(OK == upgradeFile.Open(m_upgradeImageInfo.imagePath, "rb"))....(sizeof(dSHD...`
  - no Ghidra xrefs
- `aUpgradeSHReader` at `008f69c6`: `...J ......J ......K ....... ......L .........16aUpgradeSHReader..bad_alloc...r:/c2arm/libs/afc/include/CParm.h...m_isValid...IMAGE.BIN....XML.....DAT.....HTML....jpg.....bmp.....m...`
  - no Ghidra xrefs
- `aUpgradeFWInstaller.cpp` at `008f6c78`: `.mp4....HighComp....MedComp.LowComp.IMAGE.BIN...aUpgradeFWInstaller.cpp.false...NULL != pRamDiskMem.Failed to create upgrade filesystem cbio device./flshUpg0/..Failed to create upg...`
  - no Ghidra xrefs
- `aUpgradeSHInstaller.cpp` at `008f6b34`: `s/afc/include/CParm.h...m_isValid...IMAGE.BIN...aUpgradeSHInstaller.cpp.false...aUpgradeSHInstaller::BeginUpgrade()\r\n...tSHMgr..NULL != m_workerThread.......X .....DV .....$W ......`
  - no Ghidra xrefs
- `IMAGE.BIN` at `008dcd90`: ``.......`...........12aStdCRegTest..bad_alloc...IMAGE.BIN...AUpgradeMgr.cpp.m_impl..r:/c2arm/libs/afc/include/CParm.h...m_isValid...bad_alloc....XML.....DAT.....HTML....jpg.....`
  - no Ghidra xrefs
- `IMAGE.BIN` at `008e8728`: `.....bmp.....mp4....HighComp....MedComp.LowComp.IMAGE.BIN...aUpgradeMgrImpl.cpp.m_fwInstaller.MountUpgradeFileSystem()..dicomDirUpgradeIsOk.userDirUpgradeIsOk..aUpgradeMgrImpl::`
  - no Ghidra xrefs
- `IMAGE.BIN` at `008f67dc`: `r:/c2arm/libs/afc/include/CParm.h...m_isValid...IMAGE.BIN....XML.....DAT.....HTML....jpg.....bmp.....mp4....HighComp....MedComp.LowComp.50.29.999.999...rb..\opt\TurboSHDb..%s\%s`
  - no Ghidra xrefs
- `IMAGE.BIN` at `008f6a14`: `r:/c2arm/libs/afc/include/CParm.h...m_isValid...IMAGE.BIN....XML.....DAT.....HTML....jpg.....bmp.....mp4....HighComp....MedComp.LowComp.\opt\TurboSystem_sw.%s\%s...%s..rb......<`
  - no Ghidra xrefs
- `IMAGE.BIN` at `008f6b28`: `r:/c2arm/libs/afc/include/CParm.h...m_isValid...IMAGE.BIN...aUpgradeSHInstaller.cpp.false...aUpgradeSHInstaller::BeginUpgrade()\r\n...tSHMgr..NULL != m_workerThread.......X .....D`
  - no Ghidra xrefs
- `IMAGE.BIN` at `008f6c6c`: `.....bmp.....mp4....HighComp....MedComp.LowComp.IMAGE.BIN...aUpgradeFWInstaller.cpp.false...NULL != pRamDiskMem.Failed to create upgrade filesystem cbio device./flshUpg0/..Faile`
  - no Ghidra xrefs
- `IMAGE.BIN` at `008f78e4`: `s/afc/include/CParm.h...m_isValid...bad_alloc...IMAGE.BIN...aUpgradeReader.cpp..m_upgradeSelected......... .......v.......v.......v....... ....... ....... ....... .........14aUp`
  - no Ghidra xrefs
- `IMAGE.BIN` at `008f7980`: `...... .........14aUpgradeReader....bad_alloc...IMAGE.BIN....'..d......... .......v.....8. .......v.......v.........17aUpgradeInstaller.r:/c2arm/libs/afc/include/CParm.h...m_isV`
  - no Ghidra xrefs
- `\opt\TurboSystem_sw` at `008f6a6c`: `.....bmp.....mp4....HighComp....MedComp.LowComp.\opt\TurboSystem_sw.%s\%s...%s..rb......<U .....TN .....DR ......S ......U ......Q .....0T ......T .........16aUpgradeFWReader..bad_...`
  - no Ghidra xrefs
- `\opt\TurboSHDb` at `008f6848`: `HighComp....MedComp.LowComp.50.29.999.999...rb..\opt\TurboSHDb..%s\%s...%s..aUpgradeSHReader.cpp....NULL != packHeader..versionStr..(OK == upgradeFile.Open(m_upgradeImageInfo.image...`
  - no Ghidra xrefs
- `NULL != packHeader` at `008f687c`: `\TurboSHDb..%s\%s...%s..aUpgradeSHReader.cpp....NULL != packHeader..versionStr..(OK == upgradeFile.Open(m_upgradeImageInfo.imagePath, "rb"))....(sizeof(dSHDbRoot::TurboSHDbPackHead...`
  - no Ghidra xrefs
- `NULL != packHeader` at `0092f0ac`: ` != m_pShCharacteristics......../sh0....false...NULL != packHeader..(OK == sdSHDbReleaseMutex(0)).......81).......).........9DScanhead.......\n.................................. .....`
  - no Ghidra xrefs
- `upgradeFile.Open` at `008f68a3`: `r.cpp....NULL != packHeader..versionStr..(OK == upgradeFile.Open(m_upgradeImageInfo.imagePath, "rb"))....(sizeof(dSHDbRoot::TurboSHDbPackHeader) == upgradeFile.Read((void*)packHead...`
  - no Ghidra xrefs
- `TURBO_FLASH_UPGRADE_START` at `008f6ea6`: ` <= UpgradeRegionSize)....(unsigned int)addr >= TURBO_FLASH_UPGRADE_START && (unsigned int)addr < TURBO_FLASH_UPGRADE_START + TURBO_FLASH_UPGRADE_SIZE....TheUserPrefs().SetBootMode...`
  - no Ghidra xrefs
- `TURBO_FLASH_UPGRADE_START` at `008f6ed8`: `RBO_FLASH_UPGRADE_START && (unsigned int)addr < TURBO_FLASH_UPGRADE_START + TURBO_FLASH_UPGRADE_SIZE....TheUserPrefs().SetBootMode(BSYSCFG_ARM7_APP_IMAGE)..SystemUpgradeBuffer.IO u...`
  - no Ghidra xrefs
- `SystemUpgradeBuffer` at `008f6f44`: `serPrefs().SetBootMode(BSYSCFG_ARM7_APP_IMAGE)..SystemUpgradeBuffer.IO upgrade and exit\r\n...IO upgrade and continue\r\n...No IO upgrade action\r\n..tFWMgr..NULL != m_workerThread...`
  - no Ghidra xrefs
- `STATE_UPGRADE_STAGED` at `008f6fc4`: `grade action\r\n..tFWMgr..NULL != m_workerThread..STATE_UPGRADE_STAGED == m_state......o .....$Y ......l .....`m ......l .........19aUpgradeFWInstaller...bad_alloc...r:/c2arm/libs/...`
  - no Ghidra xrefs

## Focus Function Decompilation

### `FUN_0020459c` at `0020459c`

```c
int FUN_0020459c(int *param_1)

{
  int iVar1;
  
  if (*param_1 == 1) {
    FUN_0001610c(&LAB_000018ec_1,(char)param_1[0xa2],DAT_002045f4,0xb8,DAT_002045f8,0);
    iVar1 = param_1[0xa4];
  }
  else {
    iVar1 = 0;
  }
  return iVar1;
}
```

### `FUN_0020462c` at `0020462c`

```c
void FUN_0020462c(int param_1,uint param_2)

{
  undefined4 uVar1;
  int iVar2;
  int iVar3;
  
  uVar1 = DAT_00204878;
  *(undefined4 *)(param_1 + 0x29c) = DAT_0020487c;
  *(undefined4 *)(param_1 + 0x294) = uVar1;
  FUN_00580fa4(param_1 + 0x288,2);
  FUN_00580fa4(param_1 + 0x27c,2);
  FUN_00580fa4(param_1 + 0x270,2);
  FUN_00580fa4(param_1 + 0x264,2);
  FUN_00580fa4(param_1 + 600,2);
  FUN_00580fa4(param_1 + 0x24c,2);
  FUN_00580fa4(param_1 + 0x240,2);
  FUN_00580fa4(param_1 + 0x234,2);
  FUN_00580fa4(param_1 + 0x228,2);
  FUN_00580fdc(param_1 + 0x21c,2);
  FUN_00580f6c(param_1 + 0x210,2);
  FUN_00580fa4(param_1 + 0x204,2);
  FUN_00580fa4(param_1 + 0x1f8,2);
  FUN_00580fa4(param_1 + 0x1ec,2);
  FUN_00580fa4(param_1 + 0x1e0,2);
  FUN_00580fa4(param_1 + 0x1d4,2);
  *(undefined4 *)(param_1 + 0x1d0) = DAT_00204880;
  FUN_00580fdc(param_1 + 0x1c4,2);
  FUN_00580fa4(param_1 + 0x1b8,2);
  FUN_00580fa4(param_1 + 0x1ac,2);
  FUN_00580fa4(param_1 + 0x1a0,2);
  *(undefined4 *)(param_1 + 0x19c) = DAT_00204884;
  FUN_00580fa4(param_1 + 0x18c,2);
  FUN_00580f6c(param_1 + 0x180,2);
  FUN_00580fa4(param_1 + 0x174,2);
  iVar2 = param_1 + 0x15c;
  FUN_00580fa4(param_1 + 0x168,2);
  FUN_00580fa4(iVar2,2);
  if ((param_1 != -0x6c) && (param_1 + 0x6c != iVar2)) {
    do {
      iVar3 = iVar2 + -0xc;
      (**(code **)(*(int *)(iVar2 + -8) + 0xc))(iVar3 + *(short *)(*(int *)(iVar2 + -8) + 8),2);
      iVar2 = iVar3;
    } while (param_1 + 0x6c != iVar3);
  }
  FUN_00580fa4(param_1 + 0x60,2);
  FUN_00580fdc(param_1 + 0x54,2);
  FUN_00580fdc(param_1 + 0x48,2);
  FUN_00580fa4(param_1 + 0x3c,2);
  FUN_00580fa4(param_1 + 0x30,2);
  FUN_00580fa4(param_1 + 0x24,2);
  FUN_00580fa4(param_1 + 0x18,2);
  if (param_1 != -4) {
    iVar2 = param_1 + 0x14;
    while (param_1 + 4 != iVar2) {
      (**(code **)(*(int *)(iVar2 + -4) + 0xc))
                (iVar2 + -8 + (int)*(short *)(*(int *)(iVar2 + -4) + 8),2);
      iVar2 = iVar2 + -8;
    }
  }
  if ((param_2 & 1) == 0) {
    return;
  }
  FUN_006ec18c(param_1);
  return;
}
```

### `FUN_00204abc` at `00204abc`

```c
void FUN_00204abc(int param_1,uint param_2)

{
  *(undefined4 *)(param_1 + 0xc0) = DAT_00204ba4;
  FUN_00580fa4(param_1 + 0xb4,2);
  FUN_00580fa4(param_1 + 0xa8,2);
  FUN_00580fa4(param_1 + 0x9c,2);
  FUN_00580fa4(param_1 + 0x90,2);
  FUN_00580fa4(param_1 + 0x84,2);
  FUN_00580fa4(param_1 + 0x78,2);
  FUN_00580fa4(param_1 + 0x6c,2);
  FUN_00580fa4(param_1 + 0x60,2);
  FUN_00580fa4(param_1 + 0x54,2);
  FUN_00580fdc(param_1 + 0x48,2);
  FUN_00580f6c(param_1 + 0x3c,2);
  FUN_00580fa4(param_1 + 0x30,2);
  FUN_00580fa4(param_1 + 0x24,2);
  FUN_00580fa4(param_1 + 0x18,2);
  FUN_00580fa4(param_1 + 0xc,2);
  FUN_00580fa4(param_1,2);
  if ((param_2 & 1) == 0) {
    return;
  }
  FUN_006ec18c(param_1);
  return;
}
```

### `FUN_00204ba8` at `00204ba8`

```c
undefined4 * FUN_00204ba8(undefined4 *param_1)

{
  undefined4 uVar1;
  
  FUN_0010521c();
  *param_1 = DAT_00204c74;
  FUN_00580f0c(param_1 + 1);
  uVar1 = DAT_00204c7c;
  param_1[2] = DAT_00204c78;
  *(undefined1 *)(param_1 + 3) = 0;
  *(undefined1 *)(param_1 + 1) = 1;
  *(undefined1 *)((int)param_1 + 5) = 1;
  FUN_00580f0c(param_1 + 4);
  *(undefined1 *)(param_1 + 4) = 1;
  *(undefined1 *)((int)param_1 + 0x11) = 1;
  param_1[5] = uVar1;
  param_1[6] = 0;
  FUN_00580f0c(param_1 + 7);
  *(undefined1 *)(param_1 + 7) = 1;
  *(undefined1 *)((int)param_1 + 0x1d) = 1;
  param_1[8] = uVar1;
  param_1[9] = 0;
  FUN_00580f0c(param_1 + 10);
  *(undefined1 *)(param_1 + 10) = 1;
  *(undefined1 *)((int)param_1 + 0x29) = 1;
  param_1[0xb] = uVar1;
  param_1[0xc] = 0;
  FUN_00580f0c(param_1 + 0xd);
  *(undefined1 *)(param_1 + 0xd) = 1;
  param_1[0xe] = uVar1;
  *(undefined1 *)((int)param_1 + 0x35) = 1;
  param_1[0xf] = 0;
  FUN_00581140(param_1 + 0x10);
  *(undefined1 *)(param_1 + 0x35) = 0;
  FUN_00204d54(param_1);
  return param_1;
}
```

### `FUN_00204c80` at `00204c80`

```c
void FUN_00204c80(int param_1,int param_2)

{
  char cVar1;
  
  FUN_0001610c(0x182,param_2 != 0,DAT_00204d08,0x30,DAT_00204d04,0);
  if ((*(char *)(param_1 + 0x40) != '\0') &&
     (cVar1 = FUN_00010c94(param_1 + 0x48,param_2), cVar1 == '\0')) {
    *(undefined1 *)(param_1 + 0x41) = 1;
  }
  FUN_00010a20(param_1 + 0x48,param_2);
  *(undefined1 *)(param_1 + 0x40) = 1;
  return;
}
```

### `FUN_00204d60` at `00204d60`

```c
void FUN_00204d60(int param_1)

{
  char cVar1;
  undefined4 uVar2;
  
  if ((*(char *)(param_1 + 0x40) != '\0') &&
     (cVar1 = FUN_00010c94(param_1 + 0x48,DAT_00204de8), cVar1 == '\0')) {
    *(undefined1 *)(param_1 + 0x41) = 1;
  }
  FUN_00010a20(param_1 + 0x48,DAT_00204de8);
  *(undefined1 *)(param_1 + 0x40) = 1;
  uVar2 = *(undefined4 *)(param_1 + 0x14);
  *(undefined4 *)(param_1 + 0x10) = *(undefined4 *)(param_1 + 0x28);
  *(undefined4 *)(param_1 + 0x14) = *(undefined4 *)(param_1 + 0x2c);
  *(undefined4 *)(param_1 + 0x18) = *(undefined4 *)(param_1 + 0x30);
  *(undefined4 *)(param_1 + 0x14) = uVar2;
  uVar2 = *(undefined4 *)(param_1 + 0x20);
  *(undefined4 *)(param_1 + 0x1c) = *(undefined4 *)(param_1 + 0x34);
  *(undefined4 *)(param_1 + 0x20) = *(undefined4 *)(param_1 + 0x38);
  *(undefined4 *)(param_1 + 0x24) = *(undefined4 *)(param_1 + 0x3c);
  *(undefined4 *)(param_1 + 0x20) = uVar2;
  return;
}
```

### `FUN_00204e50` at `00204e50`

```c
void FUN_00204e50(int param_1,int param_2,int param_3)

{
  if ((*(char *)(param_1 + 0x10) == '\0') || (param_2 != *(int *)(param_1 + 0x18))) {
    *(undefined1 *)(param_1 + 0x11) = 1;
  }
  *(undefined1 *)(param_1 + 0x10) = 1;
  *(int *)(param_1 + 0x18) = param_2;
  if ((*(char *)(param_1 + 0x1c) == '\0') || (param_3 != *(int *)(param_1 + 0x24))) {
    *(undefined1 *)(param_1 + 0x1d) = 1;
  }
  *(undefined1 *)(param_1 + 0x1c) = 1;
  *(int *)(param_1 + 0x24) = param_3;
  return;
}
```

### `FUN_002051c8` at `002051c8`

```c
void FUN_002051c8(int param_1,int *param_2)

{
  char cVar1;
  
  cVar1 = FUN_00204ec4();
  if (cVar1 == '\0') {
    return;
  }
  (**(code **)(*param_2 + 0x1c))
            ((int)param_2 + (int)*(short *)(*param_2 + 0x18),DAT_0020528c,param_1 + 4);
  (**(code **)(*param_2 + 0x2c))
            ((int)param_2 + (int)*(short *)(*param_2 + 0x28),DAT_00205290,param_1 + 0x10);
  (**(code **)(*param_2 + 0x2c))
            ((int)param_2 + (int)*(short *)(*param_2 + 0x28),DAT_00205294,param_1 + 0x1c);
  (**(code **)(*param_2 + 0x2c))
            ((int)param_2 + (int)*(short *)(*param_2 + 0x28),DAT_00205298,param_1 + 0x28);
  (**(code **)(*param_2 + 0x2c))
            ((int)param_2 + (int)*(short *)(*param_2 + 0x28),DAT_0020529c,param_1 + 0x34);
  (**(code **)(*param_2 + 0x6c))
            ((int)param_2 + (int)*(short *)(*param_2 + 0x68),DAT_002052a0,param_1 + 0x40);
  return;
}
```

### `FUN_002052e0` at `002052e0`

```c
void FUN_002052e0(undefined4 *param_1,undefined4 param_2)

{
  *param_1 = DAT_0020534c;
  FUN_00581168(param_1 + 0x10,2);
  FUN_00580fdc(param_1 + 0xd,2);
  FUN_00580fdc(param_1 + 10,2);
  FUN_00580fdc(param_1 + 7,2);
  FUN_00580fdc(param_1 + 4,2);
  FUN_00580f6c(param_1 + 1,2);
  FUN_0010522c(param_1,param_2);
  return;
}
```

### `FUN_00205498` at `00205498`

```c
int FUN_00205498(int param_1)

{
  FUN_0021a0f4();
  FUN_0021a198(param_1 + 8);
  FUN_0021a23c(param_1 + 0x10);
  FUN_0021a2e0(param_1 + 0x18);
  FUN_0021a384(param_1 + 0x20);
  FUN_0021a428(param_1 + 0x28);
  FUN_0021a4cc(param_1 + 0x30);
  FUN_0021a570(param_1 + 0x38);
  FUN_0021a614(param_1 + 0x40);
  FUN_0021a6b8(param_1 + 0x48);
  FUN_0021a75c(param_1 + 0x50);
  FUN_0021a800(param_1 + 0x58);
  FUN_0021a8a4(param_1 + 0x60);
  FUN_0021a948(param_1 + 0x68);
  FUN_0021a9ec(param_1 + 0x70);
  FUN_0021aa90(param_1 + 0x78);
  FUN_0021ab34(param_1 + 0x80);
  FUN_0021abd8(param_1 + 0x88);
  FUN_0021ac7c(param_1 + 0x90);
  FUN_0021ad20(param_1 + 0x98);
  FUN_0021adc4(param_1 + 0xa0);
  FUN_0021ae68(param_1 + 0xa8);
  FUN_0021af0c(param_1 + 0xb0);
  FUN_0021afb0(param_1 + 0xb8);
  FUN_0021b054(param_1 + 0xc0);
  FUN_0021b0f8(param_1 + 200);
  FUN_0021b19c(param_1 + 0xd0);
  FUN_0021b2e4(param_1 + 0xd8);
  FUN_0021b388(param_1 + 0xe0);
  FUN_0021b42c(param_1 + 0xe8);
  FUN_0021b4d0(param_1 + 0xf0);
  FUN_0021b574(param_1 + 0xf8);
  FUN_0021b618(param_1 + 0x100);
  FUN_0021b6bc(param_1 + 0x108);
  FUN_0021b760(param_1 + 0x110);
  FUN_0021b804(param_1 + 0x118);
  FUN_0021b8a8(param_1 + 0x120);
  FUN_0021b94c(param_1 + 0x128);
  FUN_0021b9f0(param_1 + 0x130);
  FUN_0021ba94(param_1 + 0x138);
  FUN_0021b240(param_1 + 0x140);
  FUN_0021bb38(param_1 + 0x148);
  FUN_0021bbdc(param_1 + 0x150);
  FUN_0021bc80(param_1 + 0x158);
  FUN_0021bd24(param_1 + 0x160);
  FUN_0021bdc8(param_1 + 0x168);
  FUN_0021be6c(param_1 + 0x170);
  FUN_0021bf10(param_1 + 0x178);
  FUN_0021bfb4(param_1 + 0x180);
  FUN_0021c058(param_1 + 0x188);
  FUN_0021c0fc(param_1 + 400);
  FUN_0021c1a0(param_1 + 0x198);
  FUN_0021c244(param_1 + 0x1a0);
  FUN_0021c2e8(param_1 + 0x1a8);
  FUN_0021c38c(param_1 + 0x1b0);
  FUN_0021c430(param_1 + 0x1b8);
  FUN_0021c4d4(param_1 + 0x1c0);
  FUN_0021c578(param_1 + 0x1c8);
  FUN_0021c61c(param_1 + 0x1d0);
  FUN_0021c6c0(param_1 + 0x1d8);
  FUN_0021c764(param_1 + 0x1e0);
  FUN_0021c808(param_1 + 0x1e8);
  FUN_0021c8ac(param_1 + 0x1f0);
  FUN_0021c950(param_1 + 0x1f8);
  FUN_0021c9f4(param_1 + 0x200);
  FUN_0021ca98(param_1 + 0x208);
  FUN_0021cb3c(param_1 + 0x210);
  FUN_0021cbe0(param_1 + 0x218);
  FUN_0021cc84(param_1 + 0x220);
  FUN_0021cd28(param_1 + 0x228);
  FUN_0021cdcc(param_1 + 0x230);
  FUN_0021ce70(param_1 + 0x238);
  FUN_0021cf14(param_1 + 0x240);
  FUN_0021cfb8(param_1 + 0x248);
  FUN_0021d05c(param_1 + 0x250);
  FUN_0021d100(param_1 + 600);
  FUN_0021d1a4(param_1 + 0x260);
  FUN_0021d248(param_1 + 0x268);
  FUN_0021d2ec(param_1 + 0x270);
  FUN_0021d390(param_1 + 0x278);
  FUN_0021d434(param_1 + 0x280);
  FUN_0021d4d8(param_1 + 0x288);
  FUN_0021d57c(param_1 + 0x290);
  FUN_0021d620(param_1 + 0x298);
  FUN_0021d6c4(param_1 + 0x2a0);
  FUN_0021d768(param_1 + 0x2a8);
  FUN_0021d80c(param_1 + 0x2b0);
  FUN_0021d8b0(param_1 + 0x2b8);
  FUN_0021d954(param_1 + 0x2c0);
  FUN_0021d9f8(param_1 + 0x2c8);
  FUN_0021da9c(param_1 + 0x2d0);
  FUN_0021db40(param_1 + 0x2d8);
  FUN_0021dbe4(param_1 + 0x2e0);
  FUN_0021dc88(param_1 + 0x2e8);
  FUN_0021dd2c(param_1 + 0x2f0);
  FUN_0021ddd0(param_1 + 0x2f8);
  FUN_0021de74(param_1 + 0x300);
  FUN_0021df18(param_1 + 0x308);
  FUN_0021dfbc(param_1 + 0x310);
  FUN_0021e060(param_1 + 0x318);
  FUN_0021e104(param_1 + 800);
  FUN_0021e1a8(param_1 + 0x328);
  FUN_0021e24c(param_1 + 0x330);
  FUN_0021e2f0(param_1 + 0x338);
  FUN_0021e394(param_1 + 0x340);
  FUN_0021e438(param_1 + 0x348);
  FUN_0021e4dc(param_1 + 0x350);
  FUN_0021e580(param_1 + 0x358);
  FUN_0021e624(param_1 + 0x360);
  FUN_0021e6c8(param_1 + 0x368);
  FUN_0021e76c(param_1 + 0x370);
  FUN_0021e810(param_1 + 0x378);
  FUN_0021e8b4(param_1 + 0x380);
  FUN_0021e958(param_1 + 0x388);
  FUN_0021e9fc(param_1 + 0x390);
  FUN_0021eaa0(param_1 + 0x398);
  FUN_0021eb44(param_1 + 0x3a0);
  FUN_0021ebe8(param_1 + 0x3a8);
  FUN_0021ec8c(param_1 + 0x3b0);
  FUN_0021ed30(param_1 + 0x3b8);
  FUN_0021edd4(param_1 + 0x3c0);
  FUN_0021ee78(param_1 + 0x3c8);
  FUN_0021ef1c(param_1 + 0x3d0);
  return param_1;
}
```

### `focus_00205924` at `00205924`

```c
void focus_00205924(undefined4 param_1,undefined4 param_2,int param_3,undefined4 param_4)

{
  undefined4 unaff_r4;
  uint unaff_r5;
  undefined4 *unaff_r6;
  
  unaff_r6[0xf0] = param_4;
  *(undefined4 *)(param_3 + 4) = unaff_r4;
  FUN_005cc994(param_3,2);
  unaff_r6[0xee] = PTR_DAT_00206670;
  unaff_r6[0xef] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xee,2);
  unaff_r6[0xec] = PTR_DAT_00206674;
  unaff_r6[0xed] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xec,2);
  unaff_r6[0xea] = DAT_00206678;
  unaff_r6[0xeb] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xea,2);
  unaff_r6[0xe8] = DAT_0020667c;
  unaff_r6[0xe9] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xe8,2);
  unaff_r6[0xe6] = DAT_00206680;
  unaff_r6[0xe7] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xe6,2);
  unaff_r6[0xe4] = DAT_00206684;
  unaff_r6[0xe5] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xe4,2);
  unaff_r6[0xe2] = DAT_00206688;
  unaff_r6[0xe3] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xe2,2);
  unaff_r6[0xe0] = DAT_0020668c;
  unaff_r6[0xe1] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xe0,2);
  unaff_r6[0xde] = DAT_00206690;
  unaff_r6[0xdf] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xde,2);
  unaff_r6[0xdc] = DAT_00206694;
  unaff_r6[0xdd] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xdc,2);
  unaff_r6[0xda] = DAT_00206698;
  unaff_r6[0xdb] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xda,2);
  unaff_r6[0xd8] = DAT_0020669c;
  unaff_r6[0xd9] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xd8,2);
  unaff_r6[0xd6] = DAT_002066a0;
  unaff_r6[0xd7] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xd6,2);
  unaff_r6[0xd4] = DAT_002066a4;
  unaff_r6[0xd5] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xd4,2);
  unaff_r6[0xd2] = DAT_002066a8;
  unaff_r6[0xd3] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xd2,2);
  unaff_r6[0xd0] = DAT_002066ac;
  unaff_r6[0xd1] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xd0,2);
  unaff_r6[0xce] = DAT_002066b0;
  unaff_r6[0xcf] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xce,2);
  unaff_r6[0xcc] = DAT_002066b4;
  unaff_r6[0xcd] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xcc,2);
  unaff_r6[0xca] = DAT_002066b8;
  unaff_r6[0xcb] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xca,2);
  unaff_r6[200] = DAT_002066bc;
  unaff_r6[0xc9] = unaff_r4;
  FUN_005cc994(unaff_r6 + 200,2);
  unaff_r6[0xc6] = DAT_002066c0;
  unaff_r6[199] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xc6,2);
  unaff_r6[0xc4] = DAT_002066c4;
  unaff_r6[0xc5] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xc4,2);
  unaff_r6[0xc2] = DAT_002066c8;
  unaff_r6[0xc3] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xc2,2);
  unaff_r6[0xc0] = DAT_002066cc;
  unaff_r6[0xc1] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xc0,2);
  unaff_r6[0xbe] = DAT_002066d0;
  unaff_r6[0xbf] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xbe,2);
  unaff_r6[0xbc] = DAT_002066d4;
  unaff_r6[0xbd] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xbc,2);
  unaff_r6[0xba] = DAT_002066d8;
  unaff_r6[0xbb] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xba,2);
  unaff_r6[0xb8] = DAT_002066dc;
  unaff_r6[0xb9] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xb8,2);
  unaff_r6[0xb6] = DAT_002066e0;
  unaff_r6[0xb7] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xb6,2);
  unaff_r6[0xb4] = DAT_002066e4;
  unaff_r6[0xb5] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xb4,2);
  unaff_r6[0xb2] = DAT_002066e8;
  unaff_r6[0xb3] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xb2,2);
  unaff_r6[0xb0] = DAT_002066ec;
  unaff_r6[0xb1] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xb0,2);
  unaff_r6[0xae] = DAT_002066f0;
  unaff_r6[0xaf] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xae,2);
  unaff_r6[0xac] = DAT_002066f4;
  unaff_r6[0xad] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xac,2);
  unaff_r6[0xaa] = DAT_002066f8;
  unaff_r6[0xab] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xaa,2);
  unaff_r6[0xa8] = DAT_002066fc;
  unaff_r6[0xa9] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xa8,2);
  unaff_r6[0xa6] = DAT_00206700;
  unaff_r6[0xa7] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xa6,2);
  unaff_r6[0xa4] = DAT_00206704;
  unaff_r6[0xa5] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xa4,2);
  unaff_r6[0xa2] = DAT_00206708;
  unaff_r6[0xa3] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xa2,2);
  unaff_r6[0xa0] = DAT_0020670c;
  unaff_r6[0xa1] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xa0,2);
  unaff_r6[0x9e] = DAT_00206710;
  unaff_r6[0x9f] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x9e,2);
  unaff_r6[0x9c] = DAT_00206714;
  unaff_r6[0x9d] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x9c,2);
  unaff_r6[0x9a] = DAT_00206718;
  unaff_r6[0x9b] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x9a,2);
  unaff_r6[0x98] = DAT_0020671c;
  unaff_r6[0x99] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x98,2);
  unaff_r6[0x96] = DAT_00206720;
  unaff_r6[0x97] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x96,2);
  unaff_r6[0x94] = DAT_00206724;
  unaff_r6[0x95] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x94,2);
  unaff_r6[0x92] = DAT_00206728;
  unaff_r6[0x93] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x92,2);
  unaff_r6[0x90] = DAT_0020672c;
  unaff_r6[0x91] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x90,2);
  unaff_r6[0x8e] = DAT_00206730;
  unaff_r6[0x8f] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x8e,2);
  unaff_r6[0x8c] = DAT_00206734;
  unaff_r6[0x8d] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x8c,2);
  unaff_r6[0x8a] = DAT_00206738;
  unaff_r6[0x8b] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x8a,2);
  unaff_r6[0x88] = DAT_0020673c;
  unaff_r6[0x89] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x88,2);
  unaff_r6[0x86] = DAT_00206740;
  unaff_r6[0x87] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x86,2);
  unaff_r6[0x84] = DAT_00206744;
  unaff_r6[0x85] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x84,2);
  unaff_r6[0x82] = DAT_00206748;
  unaff_r6[0x83] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x82,2);
  unaff_r6[0x80] = DAT_0020674c;
  unaff_r6[0x81] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x80,2);
  unaff_r6[0x7e] = DAT_00206750;
  unaff_r6[0x7f] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x7e,2);
  unaff_r6[0x7c] = DAT_00206754;
  unaff_r6[0x7d] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x7c,2);
  unaff_r6[0x7a] = DAT_00206758;
  unaff_r6[0x7b] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x7a,2);
  unaff_r6[0x78] = DAT_0020675c;
  unaff_r6[0x79] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x78,2);
  unaff_r6[0x76] = DAT_00206760;
  unaff_r6[0x77] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x76,2);
  unaff_r6[0x74] = DAT_00206764;
  unaff_r6[0x75] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x74,2);
  unaff_r6[0x72] = DAT_00206768;
  unaff_r6[0x73] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x72,2);
  unaff_r6[0x70] = DAT_0020676c;
  unaff_r6[0x71] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x70,2);
  unaff_r6[0x6e] = DAT_00206770;
  unaff_r6[0x6f] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x6e,2);
  unaff_r6[0x6c] = DAT_00206774;
  unaff_r6[0x6d] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x6c,2);
  unaff_r6[0x6a] = DAT_00206778;
  unaff_r6[0x6b] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x6a,2);
  unaff_r6[0x68] = DAT_0020677c;
  unaff_r6[0x69] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x68,2);
  unaff_r6[0x66] = DAT_00206780;
  unaff_r6[0x67] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x66,2);
  unaff_r6[100] = DAT_00206784;
  unaff_r6[0x65] = unaff_r4;
  FUN_005cc994(unaff_r6 + 100,2);
  unaff_r6[0x62] = DAT_00206788;
  unaff_r6[99] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x62,2);
  unaff_r6[0x60] = DAT_0020678c;
  unaff_r6[0x61] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x60,2);
  unaff_r6[0x5e] = DAT_00206790;
  unaff_r6[0x5f] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x5e,2);
  unaff_r6[0x5c] = DAT_00206794;
  unaff_r6[0x5d] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x5c,2);
  unaff_r6[0x5a] = DAT_00206798;
  unaff_r6[0x5b] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x5a,2);
  unaff_r6[0x58] = DAT_0020679c;
  unaff_r6[0x59] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x58,2);
  unaff_r6[0x56] = DAT_002067a0;
  unaff_r6[0x57] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x56,2);
  unaff_r6[0x54] = DAT_002067a4;
  unaff_r6[0x55] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x54,2);
  unaff_r6[0x52] = DAT_002067a8;
  unaff_r6[0x53] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x52,2);
  unaff_r6[0x50] = DAT_002067ac;
  unaff_r6[0x51] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x50,2);
  unaff_r6[0x4e] = DAT_002067b0;
  unaff_r6[0x4f] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x4e,2);
  unaff_r6[0x4c] = DAT_002067b4;
  unaff_r6[0x4d] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x4c,2);
  unaff_r6[0x4a] = DAT_002067b8;
  unaff_r6[0x4b] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x4a,2);
  unaff_r6[0x48] = DAT_002067bc;
  unaff_r6[0x49] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x48,2);
  unaff_r6[0x46] = DAT_002067c0;
  unaff_r6[0x47] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x46,2);
  unaff_r6[0x44] = DAT_002067c4;
  unaff_r6[0x45] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x44,2);
  unaff_r6[0x42] = DAT_002067c8;
  unaff_r6[0x43] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x42,2);
  unaff_r6[0x40] = DAT_002067cc;
  unaff_r6[0x41] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x40,2);
  unaff_r6[0x3e] = DAT_002067d0;
  unaff_r6[0x3f] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x3e,2);
  unaff_r6[0x3c] = DAT_002067d4;
  unaff_r6[0x3d] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x3c,2);
  unaff_r6[0x3a] = DAT_002067d8;
  unaff_r6[0x3b] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x3a,2);
  unaff_r6[0x38] = DAT_002067dc;
  unaff_r6[0x39] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x38,2);
  unaff_r6[0x36] = DAT_002067e0;
  unaff_r6[0x37] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x36,2);
  unaff_r6[0x34] = DAT_002067e4;
  unaff_r6[0x35] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x34,2);
  unaff_r6[0x32] = DAT_002067e8;
  unaff_r6[0x33] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x32,2);
  unaff_r6[0x30] = DAT_002067ec;
  unaff_r6[0x31] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x30,2);
  unaff_r6[0x2e] = DAT_002067f0;
  unaff_r6[0x2f] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x2e,2);
  unaff_r6[0x2c] = DAT_002067f4;
  unaff_r6[0x2d] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x2c,2);
  unaff_r6[0x2a] = DAT_002067f8;
  unaff_r6[0x2b] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x2a,2);
  unaff_r6[0x28] = DAT_002067fc;
  unaff_r6[0x29] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x28,2);
  unaff_r6[0x26] = DAT_00206800;
  unaff_r6[0x27] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x26,2);
  unaff_r6[0x24] = DAT_00206804;
  unaff_r6[0x25] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x24,2);
  unaff_r6[0x22] = DAT_00206808;
  unaff_r6[0x23] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x22,2);
  unaff_r6[0x20] = DAT_0020680c;
  unaff_r6[0x21] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x20,2);
  unaff_r6[0x1e] = DAT_00206810;
  unaff_r6[0x1f] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x1e,2);
  unaff_r6[0x1c] = DAT_00206814;
  unaff_r6[0x1d] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x1c,2);
  unaff_r6[0x1a] = DAT_00206818;
  unaff_r6[0x1b] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x1a,2);
  unaff_r6[0x18] = DAT_0020681c;
  unaff_r6[0x19] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x18,2);
  unaff_r6[0x16] = DAT_00206820;
  unaff_r6[0x17] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x16,2);
  unaff_r6[0x14] = DAT_00206824;
  unaff_r6[0x15] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x14,2);
  unaff_r6[0x12] = DAT_00206828;
  unaff_r6[0x13] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x12,2);
  unaff_r6[0x10] = DAT_0020682c;
  unaff_r6[0x11] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0x10,2);
  unaff_r6[0xe] = DAT_00206830;
  unaff_r6[0xf] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xe,2);
  unaff_r6[0xc] = DAT_00206834;
  unaff_r6[0xd] = unaff_r4;
  FUN_005cc994(unaff_r6 + 0xc,2);
  unaff_r6[10] = DAT_00206838;
  unaff_r6[0xb] = unaff_r4;
  FUN_005cc994(unaff_r6 + 10,2);
  unaff_r6[8] = DAT_0020683c;
  unaff_r6[9] = unaff_r4;
  FUN_005cc994(unaff_r6 + 8,2);
  unaff_r6[6] = DAT_00206840;
  unaff_r6[7] = unaff_r4;
  FUN_005cc994(unaff_r6 + 6,2);
  unaff_r6[4] = DAT_00206844;
  unaff_r6[5] = unaff_r4;
  FUN_005cc994(unaff_r6 + 4,2);
  unaff_r6[2] = DAT_00206848;
  unaff_r6[3] = unaff_r4;
  FUN_005cc994(unaff_r6 + 2,2);
  *unaff_r6 = DAT_0020684c;
  unaff_r6[1] = unaff_r4;
  FUN_005cc994();
  if ((unaff_r5 & 1) == 0) {
    return;
  }
  FUN_006ec18c();
  return;
}
```

### `FUN_00206c88` at `00206c88`

```c
int * FUN_00206c88(void)

{
  int *piVar1;
  
  piVar1 = DAT_00206cb8;
  if (*DAT_00206cb8 == 0) {
    FUN_005cc9b4();
    FUN_006e840c(piVar1,DAT_00206cbc,DAT_00206cc0);
  }
  return piVar1;
}
```

### `focus_00206d60` at `00206d60`

```c
undefined4 focus_00206d60(void)

{
  return 0x4b;
}
```

### `focus_00206fb4` at `00206fb4`

```c
undefined8 focus_00206fb4(int param_1,int param_2)

{
  int unaff_r7;
  uint unaff_lr;
  bool in_ZR;
  
  if (in_ZR) {
    param_2 = unaff_r7 + (param_1 >> (unaff_lr & 0xff));
  }
  return CONCAT44(param_2,0x4b);
}
```

### `focus_002084c8` at `002084c8`

```c
void focus_002084c8(undefined4 *param_1,uint param_2)

{
  *param_1 = DAT_005cc9b0;
  if ((param_2 & 1) == 0) {
    return;
  }
  FUN_006ec18c();
  return;
}
```

### `focus_002086bc` at `002086bc`

```c
void focus_002086bc(void)

{
  return;
}
```

### `focus_00208738` at `00208738`

```c
undefined4 focus_00208738(int param_1)

{
  return *(undefined4 *)(param_1 + 4);
}
```

### `focus_00208804` at `00208804`

```c
void focus_00208804(undefined4 *param_1,uint param_2,undefined4 *param_3,undefined4 param_4)

{
  undefined4 in_r12;
  
  param_3[1] = param_4;
  *param_3 = in_r12;
  *param_1 = DAT_005cc9b0;
  if ((param_2 & 1) == 0) {
    return;
  }
  FUN_006ec18c();
  return;
}
```
