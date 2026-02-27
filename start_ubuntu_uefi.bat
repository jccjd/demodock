@echo off
echo Starting Ubuntu (UEFI Mode) from Virtual Disk...
echo.
echo Virtual Disk: uefi_disk.qcow2
echo Boot Mode: UEFI (enter setup first)
echo VNC: 0.0.0.0:5901 (multi-client)
echo.

D:\apps\qemu\qemu-system-x86_64.exe -m 4G -smp 2 -drive if=pflash,format=raw,readonly=on,file=D:\apps\qemu\share\edk2-x86_64-code.fd -drive if=pflash,format=raw,file=D:\apps\qemu\share\edk2-i386-vars.fd -drive file=D:\apps\qemu\uefi_disk.qcow2,format=qcow2,if=virtio -boot menu=on,splash-time=65535 -net nic,model=virtio -net user -display sdl -vnc 127.0.0.1:1,connections=10

pause
