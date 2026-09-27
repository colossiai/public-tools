# **Difference between Initial Margin and maintenance margin**

# 

The **initial margin** and **maintenance margin** are two key concepts in margin trading (e.g., stocks, futures, crypto). Here's the difference:

### **🟢 Initial Margin**

- **Definition**: The **amount you must deposit upfront** to open a leveraged position.

- **Purpose**: Acts as a down payment when you first buy or short an asset using borrowed funds.

- **Example**: If you want to buy \$10,000 worth of stock with 2x leverage, you'd need to put up **\$5,000** (50% initial margin).

### **🟡 Maintenance Margin**

- **Definition**: The **minimum amount of equity** you must maintain in your margin account **after opening a position**.

- **Purpose**: Ensures you have enough skin in the game to cover losses.

- **Example**: If the maintenance margin is 25%, and the value of your position drops such that your equity falls below 25%, you'll get a **margin call**.

### **🔁 Summary Table:**

||
||
||
||

Would you like an example using real numbers to make this more clear?

# **Show me crypto perpetual example.**

Sure! Let's walk through a **crypto perpetual futures** example using **real numbers**, with **initial margin**, **maintenance margin**, and leverage explained clearly.

### **📘 Scenario:**

You’re trading **BTC/USDT perpetual futures** on an exchange like Binance or Bybit.

- **Leverage**: 10x

- **Initial Margin Requirement**: 10%

- **Maintenance Margin Requirement**: 0.5%

- **Your capital (equity)**: \$1,000

- **BTC price**: \$50,000

- You want to go **long** on BTC.

### **✅ Step 1: Open the Position (Initial Margin)**

With 10x leverage:

- You can control a position of: \$1,000 × 10 = **\$10,000  **

- That means: **0.2 BTC** at \$50,000

- **Initial margin used**: \$1,000

- You’ve met the **initial margin** of 10%

### **⚠️ Step 2: Price Drops — Checking Maintenance Margin**

Let’s say BTC drops from **\$50,000 to \$48,000**:

- Your position value: 0.2 BTC × \$48,000 = **\$9,600  **

- Unrealized loss: \$10,000 - \$9,600 = **\$400  **

- Your remaining equity: \$1,000 - \$400 = **\$600  **

#### **➤ Maintenance margin check:**

- 0.5% of \$10,000 = **\$50  **

- Your equity = \$600 \> \$50 → ✅ You’re safe.

### **❌ Step 3: Price Drops More — Margin Call / Liquidation**

Now BTC drops further to **\$44,750**:

- Position value: 0.2 BTC × \$44,750 = **\$8,950  **

- Unrealized loss: \$10,000 - \$8,950 = **\$1,050  **

- Your equity: \$1,000 - \$1,050 = **- \$50  **

You're now below **maintenance margin** → ❌ **Liquidation Triggered!**

The exchange will **liquidate your position** to protect the borrowed funds.

### **🔁 Summary Table**

| **Term** | **Value** | **Meaning** |
|----|----|----|
| Position Size | \$10,000 | With 10x leverage on \$1,000 capital |
| Initial Margin (10%) | \$1,000 | Required to open the trade |
| Maintenance Margin | \$50 | 0.5% of \$10,000, required to avoid liquidation |
| Liquidation Price | ~\$44,750 | Where your equity hits \$0 (approx.) |

Want a calculator or formula to estimate **liquidation price** for your leverage?
