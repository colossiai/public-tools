## 1. Generate keys

```bash
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/mykey
```

## 2. Copy key to  GitHub Account `Settings → SSH and GPG keys`

`cat ~/.ssh/id_ed25519.pub` then manually copy


## 3. Add Key to SSH Agent

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

## 4. Now you can use git clone

```bash
git clone git@github.com:username/repository-name.git
```

## Test SSH connection

```bash
ssh -T git@github.com
```