#!/bin/bash

# macOS

echo "=== CPU Info ==="
sysctl -n machdep.cpu.brand_string
echo "Physical cores: $(sysctl -n hw.physicalcpu)"
echo "Logical cores: $(sysctl -n hw.logicalcpu)"
echo "CPU freq (Hz): $(sysctl -n hw.cpufrequency_max)"
echo "L1 Cache: $(sysctl -n hw.l1dcachesize) bytes"
echo "L2 Cache: $(sysctl -n hw.l2cachesize) bytes"
echo "L3 Cache: $(sysctl -n hw.l3cachesize) bytes"

echo "=== Memory Info ==="
echo "Total RAM (bytes): $(sysctl -n hw.memsize)"
sysctl vm.swapusage
vm_stat | awk -v ps=$(vm_stat | grep "page size" | awk '{print $8}') '
/free/ {free=$3} /active/ {active=$3} /inactive/ {inactive=$3} /wired/ {wired=$3} 
END {
    print "Free MB:", free*ps/1024/1024
    print "Active MB:", active*ps/1024/1024
    print "Inactive MB:", inactive*ps/1024/1024
    print "Wired MB:", wired*ps/1024/1024
}'
