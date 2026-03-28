You can wrap it as a Bash function so it always mounts the **current directory** into `/workspace` inside the container.

Add this to your `~/.bashrc` or `~/.zshrc`:

```bash
dlinux() {
  docker run -it --rm -v "$(pwd):/workspace" -w /workspace lowlatency-dev bash
}
```

Then reload your shell:

```bash
source ~/.bashrc
# or
source ~/.zshrc
```

Now you can run:

```bash
dlinux
```

It will:

* start the `lowlatency-dev` container
* mount the **current directory** to `/workspace`
* set the working directory inside the container to `/workspace`
* open an interactive `bash` shell
* remove the container automatically on exit (`--rm`)

### Optional (more powerful version)

If you want to **pass extra docker args or commands**:

```bash
dlinux() {
  docker run -it --rm \
    -v "$(pwd):/workspace" \
    -w /workspace \
    lowlatency-dev \
    "$@"
}
```

Examples:

```bash
dlinux bash
dlinux make
dlinux gcc main.c
```

### Pro tip

Many developers also mount the home cache for tools:

```bash
-v "$HOME/.cache:/root/.cache"
```

This avoids rebuilding dependencies every run.

If you want, I can also show a **"pro developer" version** that automatically:

* mounts `~/.ssh`
* mounts `~/.gitconfig`
* keeps build cache
* uses host UID/GID (avoids root-owned files).
