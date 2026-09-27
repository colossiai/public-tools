# **What is the difficulty to run market making strategy?**

1\) some users filled your order, and you create positions then you need to hedge?

Great question — yes, you're getting to the heart of what makes **market making** challenging. Let's break it down.

## **🎯 What Is the Core Difficulty in Running a Market Making Strategy?**

### **✅ The simple idea:**

> You quote both **bid** and **ask** prices. If you're lucky, you **buy low and sell high**.

But in practice, it's **not that easy**, because you have to constantly manage **inventory**, **risk**, **latency**, and **adverse selection**.

## **🔍 Key Challenges in Market Making**

### **1. Inventory Risk & Hedging**

> ❗ When someone fills your order, you now hold a position.

- If someone hits your **ask**, you’re **short**.

- If someone lifts your **bid**, you’re **long**.

You now carry **inventory risk**: if price moves against you, you lose money.

#### **⚠️ Hedging Considerations:**

- **Do you hedge immediately?** (using a market order = slippage)

- **Do you wait and hope the other side fills?** (risky, may not happen)

- **Do you adjust quotes?** (e.g., skew your quotes to attract the opposite side)

This is **dynamic inventory management** and it’s at the heart of a good MM strategy.

### **2. Adverse Selection**

> ❗ The market knows more than you.

- If your quote is filled, it might be because someone has **better information**.

- For example, you're quoting a buy at 100. Someone sells to you, and the price drops to 95 soon after.

You just bought into a **losing position**.

**Mitigation**:

- Use **shorter time windows**.

- Cancel stale orders.

- Use **predictive models** (e.g., quote only if expected value is favorable).

### **3. Latency & Fill Probability**

> ❗ Market makers must act **fast** to stay competitive.

- Quote updates must be fast.

- You may quote at the top of book — but your orders are **behind** other market participants in queue.

- If you're slow, you get **picked off** (last to be filled, first to be hurt).

This is why **co-location, low latency code, and queue management** matter in high-frequency MM.

### **4. Quote Placement & Spread Management**

> ❗ Quoting too wide = no fills. Too tight = higher fill risk & losses.

- Market makers constantly balance:

  - Profit per trade (wider spread)

  - Fill probability (narrower spread)

- Good MMs dynamically adjust spreads based on:

  - Volatility

  - Order book imbalance

  - Inventory

  - Market trends

### **5. Market Conditions Change**

> ❗ What works in quiet times might blow up in volatility.

- In normal times, spreads are stable.

- In fast markets (news, liquidation cascades), spreads widen, volatility spikes, and your inventory can explode.

You must adapt your:

- Quote frequency

- Hedge rules

- Exposure limits

## **💡 Summary: What Makes MM Hard?**

| **Challenge** | **Description** |
|----|----|
| 🎯 Inventory risk | Managing exposure after fills |
| 🧠 Adverse selection | Others may trade only when it's profitable *for them*, not you |
| 🚀 Latency | You must be faster to be competitive |
| ⚖️ Quote placement | Balance fill rate vs profitability |
| 🌪 Market regimes | Strategies must handle stable and volatile conditions |

If you want, I can help you simulate:

- Inventory evolution over time

- Impact of spread width

- Quote skewing based on position

Would you like to see a code snippet that models this in Python?
