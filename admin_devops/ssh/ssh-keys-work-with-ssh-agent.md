# How GitHub SSH keys work with ssh-agent

Here’s a concise, practical guide to how GitHub SSH keys work with ssh-agent and how to set them up.

What ssh-agent does
- ssh-agent is a background process that holds your private SSH keys securely in memory.
- When a client (like git) needs to authenticate to a server (like GitHub), ssh-agent provides the necessary private-key operations without exposing your private key to the client or requiring you to re-enter your passphrase each time.

How GitHub uses SSH keys
- GitHub associates your public key (the .pub file) with your account.
- When you connect to git@github.com over SSH, GitHub challenges your client.
- Your client asks ssh-agent to sign the challenge with the matching private key.
- If the signature verifies against a public key on your GitHub account, you’re authenticated.

Quick setup steps

1) Check for existing keys
- macOS/Linux:
  - ls -al ~/.ssh
  - Typical key names: id_ed25519 and id_ed25519.pub (recommended), or id_rsa and id_rsa.pub
- Windows (PowerShell):
  - ls $env:USERPROFILE\.ssh

2) Generate a new key (if needed)
- Ed25519 (recommended):
  - ssh-keygen -t ed25519 -C "your_email@example.com"
- RSA (if Ed25519 unsupported):
  - ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
- When prompted:
  - File: accept default (~/.ssh/id_ed25519) unless you need multiple keys.
  - Passphrase: set one for security.

3) Start ssh-agent and add your key
- macOS (launchctl-managed):
  - eval "$(ssh-agent -s)"
  - Add key: ssh-add ~/.ssh/id_ed25519
- Ubuntu/Debian:
  - eval "$(ssh-agent -s)"
  - ssh-add ~/.ssh/id_ed25519
- Windows (OpenSSH in PowerShell):
  - Start-Service ssh-agent
  - Set-Service -Name ssh-agent -StartupType Automatic
  - ssh-add $env:USERPROFILE\.ssh\id_ed25519

Notes:
- If you set a passphrase, ssh-add will ask once per session; the agent caches it.
- On macOS, you can store the passphrase in Keychain so it auto-loads:
  - ssh-add --apple-use-keychain ~/.ssh/id_ed25519
  - And ensure in ~/.ssh/config: UseKeychain yes

4) Add the public key to GitHub
- Copy your public key:
  - macOS/Linux: pbcopy < ~/.ssh/id_ed25519.pub or xclip -sel clip < ~/.ssh/id_ed25519.pub
  - Windows: Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | Set-Clipboard
- GitHub: Settings → SSH and GPG keys → New SSH key → paste → Save.

5) Configure SSH for GitHub (optional but helpful)
Create or edit ~/.ssh/config:

Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519
  AddKeysToAgent yes
  UseKeychain yes

- Windows doesn’t use UseKeychain; omit that line.

6) Test the connection
- ssh -T git@github.com
- First time you’ll be asked to trust GitHub’s host key (ED25519 SHA256: p2QAMXNIC1TJYWeIOttrVc98/R1BUFWu3/LiyKgUfQM). Verify on GitHub’s docs.
- If successful, you’ll see: Hi <username>! You’ve successfully authenticated...

Using multiple keys or accounts
- Generate distinct keys: ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_work -C "work@example.com"
- Add both to agent: ssh-add ~/.ssh/id_ed25519 ~/.ssh/id_ed25519_work
- SSH config:

Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519

Host github-work
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_work

- Use URLs:
  - Personal: git@github.com:user/repo.git
  - Work: git@github-work:org/repo.git

Common pitfalls and fixes
- Permission issues:
  - chmod 700 ~/.ssh
  - chmod 600 ~/.ssh/id_ed25519
  - chmod 644 ~/.ssh/id_ed25519.pub
  - chmod 600 ~/.ssh/config
- Agent not running or key not loaded:
  - ssh-add -l shows loaded keys. If “no identities”, run ssh-add path-to-key.
- Wrong key used:
  - Use verbose: GIT_SSH_COMMAND="ssh -v" git ls-remote git@github.com:user/repo.git
  - Or: ssh -vT git@github.com
  - Check which identities are offered and matched.
- Corporate environments:
  - Proxy/Firewall may block SSH (port 22). Try HTTPS-over-SSH port 443:
    - In ~/.ssh/config:
      Host github.com
        HostName ssh.github.com
        Port 443
        User git
        IdentityFile ~/.ssh/id_ed25519
- WSL + Windows:
  - Option A: Run Linux agent in WSL and add keys there; use Git in WSL.
  - Option B: Use Windows ssh-agent and forward into WSL:
    - In WSL ~/.ssh/config: IdentityAgent /mnt/c/Users/<you>/AppData/Local/ssh/ssh-agent.sock
- Key forwarding (advanced):
  - To use your local key on a remote jump host without copying keys:
    - ssh -A user@host
    - In config: ForwardAgent yes
  - Only enable for hosts you trust.

Security tips
- Always use a passphrase on private keys.
- Prefer Ed25519 over RSA.
- Limit key exposure; don’t copy private keys to multiple machines—generate per machine.
- Periodically rotate keys; remove unused keys from GitHub.
- Keep your system’s OpenSSH up to date.

If you share your OS and current errors, I can provide tailored commands to diagnose and fix issues.
