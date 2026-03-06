# How to persist ssh-agent added keys in WSL2, so that I need not to run ssh-add when I start new WSL2 sessions, and use a simple solution, add setup-ssh-keys.sh in startup .zshrc

Yes, using a simple `setup-ssh-keys.sh` script sourced from your `.zshrc` is a straightforward approach! Here's how to implement it effectively:

## Simple Setup Script Method

### 1. Create the SSH Keys Setup Script

Create `~/.ssh/setup-ssh-keys.sh`:

```bash
#!/bin/bash

# Start SSH agent if not running
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)" > /dev/null
fi

# Add SSH keys if not already added
add_key_if_not_exists() {
    local key_path=$1
    if [ -f "$key_path" ]; then
        # Check if key is already in agent
        if ! ssh-add -l | grep -q "$(ssh-keygen -lf "$key_path" | cut -d' ' -f2)"; then
            echo "Adding SSH key: $key_path"
            ssh-add "$key_path"
        fi
    else
        echo "Warning: SSH key not found: $key_path"
    fi
}

# Add your SSH keys
add_key_if_not_exists ~/.ssh/id_ed25519_personal
add_key_if_not_exists ~/.ssh/id_ed25519_work
add_key_if_not_exists ~/.ssh/id_rsa_other

# Add any additional keys here
# add_key_if_not_exists ~/.ssh/another_key
```

Make it executable:
```bash
chmod +x ~/.ssh/setup-ssh-keys.sh
```

### 2. Source it in your `.zshrc`

Add to your `~/.zshrc`:
```bash
# Setup SSH keys on shell startup
if [ -f ~/.ssh/setup-ssh-keys.sh ]; then
    source ~/.ssh/setup-ssh-keys.sh
fi
```

## Enhanced Version with Better Error Handling

```bash
#!/bin/bash

setup_ssh_agent() {
    # Check if agent is already running and usable
    if ssh-add -l &>/dev/null; then
        return 0
    fi
    
    # Try to use existing agent socket
    if [ -S "$SSH_AUTH_SOCK" ]; then
        return 0
    fi
    
    # Start new agent
    eval "$(ssh-agent -s)" > /dev/null
}

add_ssh_keys() {
    local keys=("$@")
    for key in "${keys[@]}"; do
        if [[ -f "$key" && ! -f "${key}.pub" ]]; then
            echo "Skipping $key: no public key found"
            continue
        fi
        
        if ssh-add -l | grep -q "$(ssh-keygen -lf "$key" 2>/dev/null | cut -d' ' -f2)"; then
            continue
        fi
        
        if ssh-add "$key" 2>/dev/null; then
            echo "✓ Added: $(basename "$key")"
        else
            echo "✗ Failed: $(basename "$key")"
        fi
    done
}

# Main execution
setup_ssh_agent
add_ssh_keys ~/.ssh/id_ed25519_personal ~/.ssh/id_ed25519_work ~/.ssh/id_rsa_other
```

## Testing Your Setup

1. **Reload your shell:**
   ```bash
   exec zsh
   ```

2. **Verify keys are loaded:**
   ```bash
   ssh-add -l
   ```

3. **Test SSH connections:**
   ```bash
   ssh -T git@github.com
   ```

This simple approach works well for most use cases and gives you full control over the process!