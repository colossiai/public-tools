# Add multiple GitHub SSH keys to your `.ssh` directory:

Here's how to add multiple GitHub SSH keys to your `.ssh` directory:

## 1. Generate Multiple SSH Keys

Create separate keys for different accounts/purposes:

```bash
# Personal account
ssh-keygen -t ed25519 -C "personal@email.com" -f ~/.ssh/id_ed25519_personal

# Work account  
ssh-keygen -t ed25519 -C "work@email.com" -f ~/.ssh/id_ed25519_work

# Another account (if needed)
ssh-keygen -t rsa -b 4096 -C "other@email.com" -f ~/.ssh/id_rsa_other
```

## 2. Create/Edit SSH Config File

Create `~/.ssh/config` and configure host aliases:

```bash
# Personal GitHub
Host github-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_personal
    IdentitiesOnly yes

# Work GitHub  
Host github-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_work
    IdentitiesOnly yes

# Other GitHub
Host github-other
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_other
    IdentitiesOnly yes
```

## 3. Add Keys to SSH Agent

```bash
# Start SSH agent
eval "$(ssh-agent -s)"

# Add all keys
ssh-add ~/.ssh/id_ed25519_personal
ssh-add ~/.ssh/id_ed25519_work
ssh-add ~/.ssh/id_rsa_other

# List added keys
ssh-add -l
```

## 4. Add Public Keys to GitHub

Copy each public key to respective GitHub accounts:

```bash
# Copy public keys
cat ~/.ssh/id_ed25519_personal.pub
cat ~/.ssh/id_ed25519_work.pub
cat ~/.ssh/id_rsa_other.pub
```

Add each to:
- GitHub Settings → SSH and GPG keys → New SSH key

## 5. Test Connections

```bash
# Test each connection
ssh -T git@github-personal
ssh -T git@github-work  
ssh -T git@github-other
```

## 6. Clone/Use Repositories

Use the appropriate host alias when cloning:

```bash
# Personal repo
git clone git@github-personal:username/personal-repo.git

# Work repo
git clone git@github-work:company/work-repo.git
```

For existing repos, update remote URL:
```bash
git remote set-url origin git@github-personal:username/repo.git
```

## Key Points:

- **File Permissions**: Ensure proper permissions:
  ```bash
  chmod 700 ~/.ssh
  chmod 600 ~/.ssh/*
  chmod 644 ~/.ssh/*.pub
  chmod 644 ~/.ssh/config
  ```

- **IdentitiesOnly yes**: Ensures SSH only uses the specified identity file

- **Host aliases**: Let you easily switch between accounts

This setup allows you to manage multiple GitHub accounts seamlessly!