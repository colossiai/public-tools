# **CDF on market returns**

Let's consider an example of **market returns** using the **Cumulative Distribution Function (CDF)**.

### **Example: Stock Market Returns**

Suppose the **daily returns** of a stock follow a **normal distribution** with:

- **Mean (μ)** = 0.5% (0.005 in decimal form)

- **Standard Deviation (σ)** = 2% (0.02 in decimal form)

We want to determine:

1.  **Probability that the daily return is less than -1% (-0.01).**

2.  **Probability that the daily return is less than 3% (0.03).**

Using the CDF of a normal distribution:

P(X≤x)=CDF(x,μ,σ)P(X \leq x) = \text{CDF}(x, \mu, \sigma)

where XX is the daily return.

Now, let's calculate these probabilities.

### 

import scipy.stats as stats

\# Given parameters

mu = 0.005 \# Mean return (0.5%)

sigma = 0.02 \# Standard deviation (2%)

\# Values to check

x1 = -0.01 \# -1% return

x2 = 0.03 \# 3% return

\# Compute cumulative probabilities

prob_x1 = stats.norm.cdf(x1, mu, sigma)

prob_x2 = stats.norm.cdf(x2, mu, sigma)

prob_x1, prob_x2

Result

(0.2266273523768682, 0.8943502263331446)

### 

### **Results:**

1.  **Probability that the daily return is less than -1%**: ≈ **22.66%**

2.  **Probability that the daily return is less than 3%**: ≈ **89.44%**

### **Interpretation:**

- There is a **22.66% chance** that the stock loses more than 1% in a day.

- There is an **89.44% chance** that the stock gains less than 3% in a day.

This helps traders understand **risk and potential losses/gains** based on historical return distributions. Let me know if you want a visualization!
