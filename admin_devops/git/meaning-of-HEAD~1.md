# what is HEAD~1, HEAD^1 etc


两个符号解决的是不同问题：`~` 是**往上走几代**，`^` 是**选第几个父节点**。

## `~n` — 沿第一父链向上 n 步

```
HEAD      当前 commit
HEAD~1    上一个（= HEAD~）
HEAD~2    上上一个
HEAD~3    再往上一个
```

遇到 merge commit 时，`~` 永远走第一个父节点（也就是你 merge 时所在的那条分支）。

## `^n` — 取当前 commit 的第 n 个父节点

```
HEAD^1    第一个父节点（= HEAD^）
HEAD^2    第二个父节点 —— 只有 merge commit 才有
HEAD^3    第三个父节点 —— 章鱼式 merge 才有
```

普通 commit 只有一个父节点，所以 `HEAD^2` 会报错。

## 两者的重叠与区别

对**普通（非 merge）commit**，下面这些完全等价：

```
HEAD^  ==  HEAD^1  ==  HEAD~  ==  HEAD~1
```

区别只在 merge commit 上。假设 `M` 是一个 merge commit：

```
        A---B---C        feature
       /         \
  o---1---2---3---M      main   (M = HEAD)
```

- `HEAD^1` → `3`（main 那边，merge 时所在分支）
- `HEAD^2` → `C`（feature 那边，被并进来的分支）
- `HEAD~1` → `3`（等于 `^1`）
- `HEAD~2` → `2`（继续沿第一父链，**不会**拐到 feature 上）

要走到 feature 那条线，必须先用 `^2` 拐过去：`HEAD^2~1` → `B`。

## 可以链式组合

从左到右依次求值：

```
HEAD~2^2     先上两代，再取那个 commit 的第二父节点
HEAD^^       = HEAD~2（连续两次取第一父节点）
HEAD^^^      = HEAD~3
94f6d22~1    也能用在任意 commit hash / 分支名 / tag 上
main~3       main 分支往上三代
```

几个实用点：

- 记忆法：`~` 是竖着往上爬（linear），`^` 是横着选分叉（which parent）。
- 你用的是 zsh，如果开了 `EXTENDED_GLOB`，`^` 是 glob 字符，`git show HEAD^` 可能报 `no matches found`。加引号即可：`git show 'HEAD^'`，或者干脆用 `HEAD~1`。
- 验证自己理解对不对，随时可以查：

```bash
git --no-optional-locks log --oneline -1 'HEAD~2'
```

- 相关但不同的还有 `HEAD@{2}`（reflog，第 2 次 HEAD 移动之前的位置）和 `main@{yesterday}`，那是按**时间/操作历史**定位，不是按**提交祖先**定位。

# "git reset HEAD~1" 含义是恢复到 HEAD~1 这个commit的状态，并且保留更改吗？


是的，但说得更精确一点：**`git reset HEAD~1` 只把 HEAD（准确说是当前分支指针）和暂存区恢复到 HEAD~1 的状态，工作区磁盘上的文件一个字都不动。**

`reset` 同时作用于三棵"树"，三种模式的区别就在于它动到哪一层：

| 模式 | 分支指针 | 暂存区 (index) | 工作区 (磁盘文件) |
|---|---|---|---|
| `--soft` | 移到 HEAD~1 | 不动 | 不动 |
| `--mixed`（默认） | 移到 HEAD~1 | 重置为 HEAD~1 | 不动 |
| `--hard` | 移到 HEAD~1 | 重置为 HEAD~1 | 重置为 HEAD~1 ⚠️ |

`git reset HEAD~1` 没写模式，就是 `--mixed`。

## 具体过程

假设你刚提交了一个改了 `a.txt` 的 commit：

```
1---2---3   (HEAD -> main)   commit 3 修改了 a.txt
```

执行 `git reset HEAD~1` 之后：

```
1---2       (HEAD -> main)   commit 3 从分支上脱离了
         \
          3  （还在 .git 里，被 reflog 引用着）
```

- **分支指针**：`main` 从 3 退回到 2
- **暂存区**：内容变成 commit 2 的样子
- **工作区**：`a.txt` 磁盘上仍然是 commit 3 里的内容，没被碰过

于是 `git status` 会显示：

```
Changes not staged for commit:
        modified:   a.txt
```

改动还在，只是从"已提交"退回到了"已修改但未暂存"。想重新提交就 `git add` 再 `git commit`。

## 几个容易踩的点

- **和 `--soft` 的区别只在暂存区**。`--soft` 之后改动是**已暂存**状态（`Changes to be committed`），可以直接 `git commit`；`--mixed` 之后要先 `git add`。想改 commit message 或补文件，`--soft` 更顺手。

- **`--mixed` 会把你原本已经 `git add` 过、但还没提交的改动一起退回未暂存状态**。改动不丢，但暂存状态没了。

- **未跟踪文件（untracked）永远不受影响**，三种模式都一样。`--hard` 也不会删未跟踪文件，要删得用 `git clean`。

- **只有 `--hard` 会真的丢东西**：它会用 HEAD~1 的内容覆盖工作区，未提交的改动直接消失且不进 reflog，基本找不回来。

- **被甩掉的 commit 3 并没有立刻被删**，`git reflog` 里还能查到它的 hash，`git reset --hard <hash>` 就能回去（默认保留约 30 天后才被 gc 清理）。