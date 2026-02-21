# In claude.code, why we need Skill.md besides CLAUDE.md ?

## `summary`: CLAUDE.md 定义边界， SKILL.md 其实相当于task.sh(不消耗token)

In `Claude Code`, CLAUDE.md and SKILL.md serve distinct roles in managing how Claude interacts with your project. While CLAUDE.md provides global context, SKILL.md enables modular, on-demand capabilities. 


## Key Differences

* CLAUDE.md (Always-On Context): This file is loaded at the start of every session. It contains project-wide "rules of the road" such as build commands, test frameworks, and general coding styles.

* SKILL.md (On-Demand Intelligence): A skill is a modular set of instructions that only loads when relevant to a task or when explicitly invoked via a slash command (e.g., /deploy). 


## Why You Need Both

1. **Token Efficiency**: CLAUDE.md uses up context tokens constantly. By moving specialized tasks (like "how to handle PDF extraction" or "deployment workflows") into a SKILL.md, you keep the base context window lean, as the full skill content only loads when needed.

2. **Explicit Tooling**: Skills can be invoked directly as commands. If you have a complex sequence of steps for a code review or a database migration, a skill allows you to trigger that exact workflow intentionally rather than hoping Claude infers it from general project rules.

3. **Executable Logic**: Unlike CLAUDE.md, which is strictly text instructions, a skill directory can include supporting files and scripts (Python, Bash, etc.). This allows Claude to execute proven code for precise tasks instead of just generating new code from scratch.

4. **Reusability & Portability**: Skills follow the Agent Skills open standard, meaning they can be shared across projects or even different AI tools, whereas CLAUDE.md is typically tied to a specific local codebase. 


Feature| 	CLAUDE.md|	SKILL.md|
-------|--------|------------------
Loading |	Always (at session start)|	On-demand (when relevant/invoked)|
Primary | Use	Project conventions, build/test commands |	Specific workflows, task automation
Trigger|	Automatic (Context)	| Slash command or Contextual trigger|
Complexity| 	Pure text/instructions |	Can include executable scripts|

# Skill.md is like individual run-task.sh command that can be invoke manually and doesn't consume token?


That is an excellent way to think about it! You’ve hit on the core "performance" benefit of the architecture.

Comparing `SKILL.md` to a `run-task.sh` command is very accurate, but there is one nuance regarding how tokens are consumed.


## The Token "On-Demand" Model
You are correct that skills help save tokens, but it works more like "Just-in-Time" loading rather than being completely free:

* CLAUDE.md (The "System Prompt"): These tokens are charged on every single message you send because they stay in the active context window.

* SKILL.md (The "Library"): These tokens are only charged once you (or the task) invoke the skill.
    - If you never run the skill during a session, you pay 
 tokens for it.
    - Once invoked, the skill's instructions are "injected" into the conversation to guide Claude through that specific task.

## Why it’s like an "AI-Powered" .sh Script
While a standard .sh script is rigid, a `SKILL.md` is an **intelligent script**. Here is why they are better for certain tasks:

1. **Context-Aware Execution**: Unlike a shell script that just runs code, a skill tells Claude why it is running it and what to look for in the output (e.g., "Run this migration, but if you see a 'Foreign Key' error, check the orders table first").

2. **Interactive Logic**: A skill can include steps that require Claude to stop and think, ask you a question, or analyze a file before proceeding to the next command.

3. **Discovery**: Claude Code can "see" that a skill exists. If you say "Fix the database," Claude can look at your skills and say, "I see a db-repair skill, I'll use that," rather than guessing.


## Comparison: Script vs. Skill

Feature|	run-task.sh |	SKILL.md|
------|-----------------|------------|
Logic |	Rigid, predefined code.|	Natural language + code.|
Error Handling|	Hardcoded if/else. |	Claude interprets the error and fixes it.
Token Cost | 0|	Only when activated. |
Invoke |	Manual only. |	Manual (slash command) or Automatic.|

