## claude-code explaination

```

########################################################################
❯ I have 2 github accounts A and B, I both setup in ~/.ssh/config, how do I distinguish the account in daily use?
########################################################################

⏺ You configure different SSH hosts in ~/.ssh/config and use the host alias instead of github.com.

  ~/.ssh/config:
  Host github-A
      HostName github.com
      User git
      IdentityFile ~/.ssh/id_ed25519_A

  Host github-B
      HostName github.com
      User git
      IdentityFile ~/.ssh/id_ed25519_B

  Then use the alias wherever you'd use github.com:

  # Clone
  git clone git@github-A:orgA/repo.git
  git clone git@github-B:orgB/repo.git

  # Set remote on an existing repo
  git remote set-url origin git@github-A:orgA/repo.git

  # Test which account a host resolves to
  ssh -T git@github-A   # Hi userA!
  ssh -T git@github-B   # Hi userB!

  The key point: replace github.com with your alias (github-A or github-B) in any git remote URL. Everything else (git push, git pull, etc.) works as normal.

########################################################################
❯ What is orgA part in "github-A:orgA"?
########################################################################

⏺ It's the GitHub username or organization name — the first path segment of any GitHub URL.

  For example, from https://github.com/anthropics/claude-code:
  - anthropics is the org
  - claude-code is the repo

  So the SSH equivalent is:
  git@github.com:anthropics/claude-code.git

  If it's a personal repo under your own account, it's just your GitHub username:
  git@github-A:<myusername>/my-repo.git

※ recap: You're getting the aeron-bank app running locally. The cluster and bank-app are working. Next step is to fix the wrong main class in the runSingleNodeCluster Gradle
  task.

########################################################################
❯ My ./ssh/config
########################################################################

  # github (bbb)
  Host github-bbb
    PreferredAuthentications publickey
    IdentityFile /Users/<myusername>/mykeys/aaa-bbb

  but when I run ssh -T, I got this error

  ssh -T git@github-bbb                                                                                                              255 ✘  11:21:06
  ssh: Could not resolve hostname github-bbb: nodename nor servname provided, or not known

⏺ You're missing HostName github.com in the config entry.

  # github (bbb)
  Host github-bbb
    HostName github.com
    User git
    PreferredAuthentications publickey
    IdentityFile /Users/<myusername>/mykeys/aaa-bbb

  Without HostName, SSH tries to resolve github-bbb as an actual DNS hostname, which fails. HostName tells it the real address to connect to.

########################################################################
❯ My config
########################################################################

  # github (aaa)
  Host github-aaa
    HostName github.com
    PreferredAuthentications publickey
    IdentityFile /Users/<myusername>/mykeys/aaa

  # github (bbb)
  Host github-bbb
    HostName github.com
    PreferredAuthentications publickey
    IdentityFile /Users/<myusername>/mykeys/aaa-bbb

  but now 2 config host return same username, which should be different

   ~/mykeys  ssh -T git@github-bbb                                                                                                              255 ✘ 
  11:21:10
  Hi bbb! You've successfully authenticated, but GitHub does not provide shell access.
   ~/mykeys  ssh -T git@github-aaa                                                                                                                    1 ✘ 
  11:24:16
  Hi bbb! You've successfully authenticated, but GitHub does not provide shell access.

⏺ Both return bbb because User git is missing — without it, SSH falls back to your local system username, and the first matching key in the agent wins regardless of
  IdentityFile.

  Add User git to both entries:

  # github (aaa)
  Host github-aaa
    HostName github.com
    User git
    PreferredAuthentications publickey
    IdentityFile /Users/<myusername>/mykeys/aaa

  # github (bbb)
  Host github-bbb
    HostName github.com
    User git
    PreferredAuthentications publickey
    IdentityFile /Users/<myusername>/mykeys/aaa-bbb

  Also add IdentitiesOnly yes to force SSH to use only the specified key and ignore anything loaded in the agent:

  # github (aaa)
  Host github-aaa
    HostName github.com
    User git
    IdentitiesOnly yes
    PreferredAuthentications publickey
    IdentityFile /Users/<myusername>/mykeys/aaa

  # github (bbb)
  Host github-bbb
    HostName github.com
    User git
    IdentitiesOnly yes
    PreferredAuthentications publickey
    IdentityFile /Users/<myusername>/mykeys/aaa-bbb

  IdentitiesOnly yes is the key fix — without it, SSH tries all keys from the agent first and ignores IdentityFile if any agent key succeeds.

※ recap: Getting the aeron-bank app running locally. SSH config for two GitHub accounts is fixed — next, test both with ssh -T to confirm each returns the correct username.

########################################################################
❯ for the old project I cloned to local, do I need ti change the remote url for all?
########################################################################

⏺ Yes, for any repo where the remote URL still uses github.com you need to update it to use your alias.

  Check the current remote:
  git remote -v

  If it shows github.com, update it:
  # For bbb repos
  git remote set-url origin git@github-bbb:bbb/repo-name.git

  # For aaa repos
  git remote set-url origin git@github-aaa:<myusername>/repo-name.git

  You only need to do this for repos where you push/pull — read-only public repos cloned over HTTPS don't need it.

########################################################################
❯ If I keep this repo urls unchange, what will happen when I push?
########################################################################

⏺ SSH will use whichever key comes first in the agent (or the first matching IdentityFile for github.com), which may authenticate as the wrong account.

  The push itself will likely succeed but it'll be attributed to the wrong GitHub account — commits will show the wrong author identity on GitHub.

  Or if the wrong account doesn't have write access to that repo, it'll fail with:
  ERROR: Permission to orgA/repo.git denied to wronguser.

########################################################################
❯ I also need to change correct user.name in th repos?
########################################################################


⏺ Yes, if the two accounts have different names/emails. Check the current config:

  git config user.name
  git config user.email

  If it's wrong for that repo, set it locally:

  git config user.name "Your Name"
  git config user.email "myusername@gmail.com"

  This sets it per-repo (in .git/config), overriding your global config (~/.gitconfig) just for that repo. Commits made after this will show the correct identity on GitHub.


```