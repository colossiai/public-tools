# gcam: git add & push

```bash
alias gaa  
gaa='git add --all'

alias gcmsg 
gcmsg='git commit -m'


alias gcam        
gcam='gaa && gcmsg'
```


## sample:

```bash
gcam "update api-doc"
gp # git push
```