# Ghidra Integrity Focus

Program: `system_miniboot_region_0x21d5d8_armle.bin`

## String Hits And Xrefs

- `Upgrade CRC Failure` at `038245bc`: `ter Display Init....mini-boot Done\n.BSP Assert..Upgrade CRC Failure..reboot.Upgrade/bootloader image invalid, using primary.\n...Primary image invalid, using upgrade/bootloader.\n...`
  - no Ghidra xrefs
- `Upgrade/bootloader image invalid` at `038245d8`: `t Done\n.BSP Assert..Upgrade CRC Failure..reboot.Upgrade/bootloader image invalid, using primary.\n...Primary image invalid, using upgrade/bootloader.\n...QRY.Battery.Power Supply....`
  - no Ghidra xrefs
- `Primary image invalid` at `0382460c`: `ade/bootloader image invalid, using primary.\n...Primary image invalid, using upgrade/bootloader.\n...QRY.Battery.Power Supply....UNKNOWN I2C Device..I2C Write to %s A/D config reg...`
  - no Ghidra xrefs
- `BBootImageHeaderPtr` at `038244cc`: `ss (%02x)\n..BImageHeaderPtr            (%08x)\n..BBootImageHeaderPtr        (%08x)\n..On/Off downKey             (%02x)\n..Battery Voltage            (%d)\n....FpgaBootOK         ...`
  - no Ghidra xrefs
- `FpgaBootOK` at `03824538`: `   (%02x)\n..Battery Voltage            (%d)\n....FpgaBootOK                 (%d)\n....FlashSize                  (%08x)\n..Mini-boot after Display Init....mini-boot Done\n.BSP Ass...`
  - no Ghidra xrefs

## Focus Function Decompilation

- none
