# Why WSL2 perf installation failed?

```bash
sudo apt install linux-tools-$(uname -r)

E: Unable to locate package linux-tools-5.15.153.1-microsoft-standard-WSL2

```

---

Yep — that’s a **common issue on WSL2**, because Microsoft ships its own **custom kernel**, and there’s no matching `linux-tools-<kernel>` package in Ubuntu’s repositories.

Let’s fix it. 👇

---

## 🧩 Why the error happens

Your kernel version in WSL2 (check with `uname -r`) probably looks like this:

```bash
$ uname -r
5.15.153.1-microsoft-standard-WSL2
```

Ubuntu repositories only provide `linux-tools` for *Ubuntu kernels* (e.g. `5.15.0-89-generic`), not Microsoft’s special WSL2 kernel — so `apt` can’t find a matching package.

---

## ✅ Solution 1: Install the “generic” tools (works for most WSL2 users)

Even though the kernel name doesn’t match, you can safely install the generic perf tool:

```bash
sudo apt update
sudo apt install linux-tools-generic linux-tools-common
```

Then check what’s installed:

```bash
ls /usr/lib/linux-tools/
```

You’ll see a folder like `5.15.0-XX-generic/`.

Create a convenient symlink so `perf` runs properly:

```bash
sudo ln -s /usr/lib/linux-tools/*/perf /usr/local/bin/perf
```

Now test:

```bash
perf --version
```

This version should run basic `perf stat` commands fine (software counters, context switches, etc.).

---

## ✅ Solution 2: Use `linux-perf` package (Debian-based fix)

On some distros (Debian 12+, Ubuntu 24.04+):

```bash
sudo apt install linux-perf
```

That installs a standalone `perf` binary not tied to the kernel version.

---

## ✅ Solution 3: Use a compatible perf binary from kernel.org

If you really need the *exact matching version*, you can build or download it manually:

```bash
sudo apt install build-essential flex bison libelf-dev libdw-dev libaudit-dev libperl-dev python3-dev libiberty-dev
git clone https://github.com/torvalds/linux.git
cd linux/tools/perf
make
sudo cp perf /usr/local/bin/
```

That gives you a kernel-version-independent `perf` binary that works in WSL2.

---

## ⚠️ Limitations

Even after installation, hardware events (like CPU cycles, cache misses) usually won’t work in WSL2 because:

* The hypervisor isolates hardware counters.
* The WSL kernel disables `perf_event_open` for security.

But `perf stat` and software metrics will still work.

---

## ✅ Verify working setup

Run:

```bash
sudo perf stat -e task-clock,context-switches,cpu-migrations,instructions,cycles ls
```

If it prints event counts, you’re good to go!
