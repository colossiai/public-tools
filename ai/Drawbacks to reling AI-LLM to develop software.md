# What is the drawbacks to reling AI/LLM to develop softwares?

Relying on AI / LLMs to develop software can be powerful—but there are real drawbacks to keep in mind. Here are the big ones, without the hype gloss:

---

### 1. **Hallucinations & subtle bugs**

LLMs can confidently generate **incorrect or non-existent APIs**, flawed logic, or code that *looks* right but fails in edge cases. These bugs are often subtle and hard to detect in reviews.

---

### 2. **Shallow understanding of context**

AI doesn’t truly understand:

* Your business domain
* Long-term architectural goals
* Historical design tradeoffs

It optimizes for *local correctness*, not *system-level intent*.

---

### 3. **Technical debt acceleration**

AI often:

* Duplicates logic instead of refactoring
* Overuses patterns/frameworks
* Produces verbose or inconsistent styles

If unchecked, this quietly **increases tech debt faster than humans do**.

---

### 4. **Security risks**

LLMs may:

* Introduce insecure defaults
* Miss threat models
* Reproduce vulnerable patterns from training data

They don’t *reason like an attacker* unless explicitly guided.

---

### 5. **License & IP uncertainty**

Generated code can unintentionally:

* Mirror licensed code patterns
* Violate corporate IP policies

This is especially risky in regulated or enterprise environments.

---

### 6. **Over-reliance erodes developer skill**

Teams that rely too heavily on AI may see:

* Weaker debugging skills
* Reduced architectural thinking
* Less code ownership

This hurts long-term team resilience.

---

### 7. **Poor fit for novel or hard problems**

LLMs excel at:

* Known patterns
* Common libraries
* Boilerplate

They struggle with:

* New algorithms
* Deep performance tuning
* Complex concurrency or distributed systems

---

### 8. **False sense of productivity**

You get **more code faster**, but not necessarily:

* Better code
* More maintainable systems
* Fewer bugs

Velocity without judgment can backfire.

---

### The healthy framing

AI is best used as:

* A **junior pair programmer**
* A **code sketcher**
* A **documentation and test assistant**

Not as:

* The system architect
* The final reviewer
* The source of truth

If you want, I can also break this down by **startup vs enterprise**, or **junior vs senior dev impact**, or give **rules of thumb for safe AI-assisted coding**.



# Give senior dev impact.

Alright—**senior dev impact**, specifically, warts and all 👇

---

## How AI/LLMs impact **senior developers**

### 1. **Architectural authority gets diluted**

LLMs can generate *plausible* architectures quickly, which can:

* Confuse less-experienced teammates about what’s “correct”
* Undermine a senior’s role as the system-level decision maker
* Create bikeshedding around AI-suggested designs

Seniors end up spending more time **unwinding bad architectural momentum**.

---

### 2. **Review load increases, not decreases**

Instead of reviewing *handwritten* code, seniors now review:

* Larger diffs
* Inconsistent styles
* Over-engineered abstractions

AI code often passes lint but fails **design judgment**, so review becomes *mentally heavier*.

---

### 3. **Loss of signal in problem-solving**

Traditionally, how a dev solved a problem showed:

* Their reasoning
* Their tradeoffs
* Their growth

With AI in the loop, seniors lose that signal—making it harder to:

* Mentor effectively
* Evaluate performance
* Spot skill gaps

---

### 4. **Senior devs become “AI whisperers”**

Time shifts from building to:

* Prompt engineering
* Correcting hallucinations
* Teaching AI constraints repeatedly

This is valuable—but often **not why seniors became engineers**.

---

### 5. **Higher accountability, same ownership**

When AI-generated code fails:

* The senior is still responsible
* The AI isn’t on-call
* The blame doesn’t distribute

This increases **cognitive and emotional load**.

---

### 6. **Risk of skill atrophy (yes, even for seniors)**

Seniors who lean too hard on AI may:

* Think less in code
* Skip deep dives
* Accept “good enough” solutions too often

Over time, this weakens intuition—especially in:

* Debugging
* Performance tuning
* Systems design

---

### 7. **But—real upsides when used correctly**

For seniors who stay intentional, AI:

* Offloads boilerplate
* Speeds up exploration
* Helps sanity-check edge cases
* Acts as a rubber duck with infinite patience

Used well, it **amplifies judgment** rather than replacing it.

---

## Senior-safe rules of thumb

Most strong seniors I see follow these:

* **Design first, prompt second**
* Never merge AI code you can’t explain line-by-line
* Use AI to explore *options*, not pick winners
* Keep humans responsible for:

  * Architecture
  * Security
  * Performance
  * Final review

---

If you want, I can also:

* Compare **senior devs with vs without AI**
* Give **team policies that protect senior leverage**
* Show **how seniors should mentor juniors using AI**

Just tell me the angle you want.
