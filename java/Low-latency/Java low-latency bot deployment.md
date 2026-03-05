# Java low-latency bot deployment


For a **Java low-latency bot** (trading bot / market-making / arbitrage), the “best” deployment depends on whether you optimize for:

* 🔥 **Ultra-low latency (µs–sub-ms)**
* ⚖️ **Balanced latency + operability**
* ☁️ **Cloud scalability**
* 🏦 **Colocated exchange deployment**

Since you’ve been exploring low-latency topics (FIX, Chronicle, off-heap, etc.), I’ll assume you care about performance first.

---

# 🥇 1. Best for Ultra-Low Latency (HFT-style)

## ✅ Bare-metal Linux server (no container)

**Why:**

* No container overhead
* Full control of CPU pinning
* NUMA tuning
* Kernel tuning
* NIC optimization
* Deterministic GC behavior

### Recommended stack

* OS: **Minimal Linux (Ubuntu Server / Rocky Linux)**
* JVM: **OpenJDK 17/21 (LTS)**
* GC:

  * ZGC (balanced low latency)
  * Or tuned G1
* CPU pinning:

  * `taskset`
  * `isolcpus`
* Disable power saving (performance governor)
* Disable hyperthreading (optional)
* Tune:

  * `ulimit`
  * `vm.swappiness=1`
  * hugepages (if needed)

### Network

* Direct FIX or binary protocol
* Kernel bypass (if extreme):

  * DPDK
  * Solarflare Onload

### When to choose this

* Colocated with exchange
* Latency matters more than DevOps convenience
* < 100µs goals

---

# 🥈 2. Best Practical Production Setup (Most Teams)

## ✅ Docker on dedicated VM (not Kubernetes)

You get:

* Easy deployment
* Reproducibility
* Still good latency

**Avoid Kubernetes for hot trading path.**

### Why not Kubernetes?

* Scheduling jitter
* Noisy neighbors
* CPU throttling
* Harder to guarantee core isolation

If you use K8s:

* Only use it for:

  * monitoring
  * risk service
  * analytics
  * dashboards

Keep the bot itself outside.

---

# 🥉 3. Cloud Deployment (If Not HFT)

If latency to exchange isn't microsecond critical:

* AWS c7i / c7gn
* Dedicated instance
* Placement group
* Disable CPU credit burst (no t-series)

Still:

* Pin cores
* Disable C-states
* Monitor GC pause

---

# 🏦 Colocation Setup (Serious Trading)

If deploying near:

* SGX (Singapore Exchange)
* CME
* Binance institutional colo

Typical setup:

* 1U bare metal
* Dual NIC
* 10G/25G fiber
* Cross connect to exchange
* No hypervisor

---

# 🔧 JVM Tuning Template (Good Starting Point)

```bash
-XX:+AlwaysPreTouch
-XX:+UseNUMA
-XX:+UnlockExperimentalVMOptions
-XX:+UseZGC
-Xms4g
-Xmx4g
-XX:MaxGCPauseMillis=1
```

Also:

* Fixed heap size (Xms = Xmx)
* Avoid dynamic resizing
* Avoid large object allocation
* Use off-heap where possible

---

# 🧠 Architecture Best Practice

Separate:

| Component           | Deployment       |
| ------------------- | ---------------- |
| Market Data Handler | Core pinned      |
| Strategy Engine     | Core pinned      |
| Order Sender        | Core pinned      |
| Risk                | Separate process |
| Logging             | Async queue      |

Never block in:

* Market data thread
* Order thread

---

# ⚠️ What NOT To Do

❌ Shared cloud instance
❌ Auto-scaling for trading core
❌ Kubernetes for hot path
❌ Logging synchronously
❌ Default JVM settings

---

# 🎯 My Recommendation For You

If you're serious about low-latency Java:

> 🔥 Bare-metal Linux + Docker (only for packaging) + CPU pinning + tuned JVM

That gives:

* Clean DevOps workflow
* Near-bare-metal performance
* Deterministic latency

---

If you want, I can next show:

* A production-ready Linux tuning checklist
* A real low-latency deployment architecture diagram
* Or a minimal bot deployment template (systemd + JVM tuned)

Which direction are you optimizing for — **µs latency or practical production stability?**

# A production-ready Linux tuning checklist

Here’s a **production-ready Linux tuning checklist** specifically for a **Java low-latency trading bot** (FIX / binary protocol / event-driven engine).

This assumes:

* Dedicated server (bare metal or dedicated VM)
* You care about **deterministic latency**, not just throughput
* Java 17/21 on **OpenJDK**

---

# 🧱 1. BIOS Settings (Before OS Boots)

These matter more than most JVM tuning.

### ✅ CPU

* Disable C-states (or set to C0/C1 only)
* Disable Intel SpeedStep / P-state scaling
* Disable Turbo Boost (optional; improves determinism)
* Disable Hyper-Threading (if extreme low latency)
* NUMA enabled (if multi-socket)

### ✅ Memory

* Disable memory power saving
* Enable performance profile

---

# ⚙️ 2. Linux Kernel Boot Parameters

Edit:

```bash
/etc/default/grub
```

Add:

```bash
GRUB_CMDLINE_LINUX="isolcpus=2-7 nohz_full=2-7 rcu_nocbs=2-7 intel_pstate=disable processor.max_cstate=1 idle=poll"
```

Then:

```bash
update-grub
reboot
```

### What This Does

| Parameter            | Why                    |
| -------------------- | ---------------------- |
| isolcpus             | Reserve cores for bot  |
| nohz_full            | Remove scheduler ticks |
| rcu_nocbs            | Offload RCU callbacks  |
| intel_pstate=disable | Disable CPU scaling    |
| idle=poll            | Avoid deep sleep       |

---

# 🔥 3. CPU Governor

Force performance mode:

```bash
cpupower frequency-set -g performance
```

Verify:

```bash
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

---

# 🧠 4. CPU Pinning Strategy

Never let scheduler move threads.

Use:

```bash
taskset -c 2,3 java ...
```

Or better:

* Market data → core 2
* Strategy → core 3
* Order sender → core 4
* Risk → core 5

If multi-socket:

* Keep everything on same NUMA node

Check NUMA:

```bash
numactl --hardware
```

---

# 🧮 5. Memory Tuning

## Disable swap

```bash
swapoff -a
```

In `/etc/fstab` remove swap.

Or:

```bash
vm.swappiness=1
```

Add to:

```bash
/etc/sysctl.conf
```

---

## HugePages (optional)

If large heap:

```bash
vm.nr_hugepages=1024
```

Only useful if:

* Large fixed heap
* Using off-heap buffers

---

# 🌐 6. Network Stack Tuning

Add to `/etc/sysctl.conf`:

```bash
net.core.rmem_max=134217728
net.core.wmem_max=134217728
net.core.netdev_max_backlog=250000
net.ipv4.tcp_tw_reuse=1
net.ipv4.tcp_low_latency=1
net.ipv4.tcp_fin_timeout=10
```

Apply:

```bash
sysctl -p
```

---

## NIC Interrupt Affinity

Check:

```bash
cat /proc/interrupts
```

Pin NIC IRQ to same CPU as market data thread:

```bash
echo 4 > /proc/irq/<irq_number>/smp_affinity
```

This reduces cross-core latency.

---

# 📁 7. File Descriptor Limits

In:

```bash
/etc/security/limits.conf
```

Add:

```bash
* soft nofile 1000000
* hard nofile 1000000
```

Check:

```bash
ulimit -n
```

---

# 🧵 8. Disable Transparent Huge Pages (Important)

```bash
echo never > /sys/kernel/mm/transparent_hugepage/enabled
```

Add to rc.local.

THP causes latency spikes.

---

# 🛑 9. Disable Unnecessary Services

Remove:

* cron (if unused)
* bluetooth
* cups
* avahi
* cloud-init (if static server)

Check:

```bash
systemctl list-unit-files --state=enabled
```

---

# ☕ 10. JVM Production Flags (Low Latency Baseline)

For **OpenJDK 17+**:

```bash
-XX:+AlwaysPreTouch
-XX:+UseNUMA
-XX:+UnlockExperimentalVMOptions
-XX:+UseZGC
-Xms4g
-Xmx4g
-XX:MaxGCPauseMillis=1
-XX:+DisableExplicitGC
```

Important:

* Xms = Xmx
* Pre-touch memory at startup
* Avoid resizing heap

---

# 📊 11. Monitoring Without Noise

Avoid heavy agents.

Use:

* perf
* sar
* vmstat
* pidstat

Avoid:

* Prometheus scraping every 1s on hot path
* Logging in trading thread

---

# 🚨 12. Latency Validation Checklist

After tuning, verify:

### Check jitter:

```bash
cyclictest -p 99 -t 1
```

### Check scheduling:

```bash
ps -eLo pid,psr,comm | grep java
```

### Check GC pause:

```bash
-Xlog:gc*
```

---

# 🏦 If You Deploy Near Exchange (e.g. SGX / CME)

Additional:

* Disable NIC offloading (if needed)
* Use kernel bypass (Solarflare / DPDK)
* Use hardware timestamping
* Cross-connect fiber

---

# 🎯 Final “Production Ready” Checklist

✅ BIOS tuned
✅ CPU performance governor
✅ Swap disabled
✅ THP disabled
✅ CPU cores isolated
✅ IRQ pinned
✅ Fixed heap size
✅ Pre-touch enabled
✅ Logging async
✅ No noisy neighbors

---

# 🔥 Reality Check

If you're not colocated, 80% of latency is network.

OS tuning matters most when:

* You're already within exchange DC
* You’re chasing microseconds
* Strategy reacts on market data tick

---

If you want, next I can show:

* A **minimal hardened systemd service file** for the bot
* A **NUMA-aware deployment diagram**
* Or a **Java low-latency GC comparison (ZGC vs G1 vs Shenandoah)**

What level are you targeting — sub-millisecond or sub-100µs?
