# Show storage devices

```bash
lsblk
```

# top

run `top` command and check %wa (IO wait time)

if %wa is > 0.1/0.2, then it indicate some heavy IO operation. 

# iostat

use `iostat` to check %utilization of hard disk to identiy which device has issue.

# iotop

use `iotop` to identify what process/cmd occupy the CPU