@echo off
echo Starting UEFI Virtual Machine for System Installation...
echo.

D:\apps\qemu\qemu-system-x86_64.exe ^
  -m 4G ^
  -smp 2 ^
  -drive if=pflash,format=raw,readonly=on,file=D:\apps\qemu\share\edk2-x86_64-code.fd ^
  -drive if=virtio,file=uefi_disk.qcow2,format=qcow2 ^
  -drive if=virtio,file=D:\TinyCore-current.iso,media=cdrom ^
  -boot menu=on ^
  -net nic,model=virtio ^
  -net user ^
  -display sdl ^
  -vnc 127.0.0.1:1

pause
