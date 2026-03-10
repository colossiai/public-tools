#! /bin/bash

# linux-dev contains nasm,gcc,gdb
# enter linux vm and map current folder to vm /workspace
docker run -it --rm -v $(pwd):/workspace linux-dev bash