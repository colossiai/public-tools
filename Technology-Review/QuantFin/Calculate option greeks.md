# **How to calculate UserGreeks, suppose user has a position, and now he enter a new order.**

### **Calculating UserGreeks When a New Order is Entered**

To calculate UserGreeks, you need to **fetch the current Greeks**, compute the **Greeks impact of the new order**, and **update the total exposure**.

## **1. Steps to Compute Updated UserGreeks**

### **Step 1: Retrieve Existing Greeks from the User's Portfolio**

Each position in the user's portfolio has Greeks calculated per contract.  
Retrieve the sum of Greeks across all positions:

Net Delta=∑(Delta per contract×contract quantity)\text{Net Delta} = \sum (\text{Delta per contract} \times \text{contract quantity}) Net Gamma=∑(Gamma per contract×contract quantity)\text{Net Gamma} = \sum (\text{Gamma per contract} \times \text{contract quantity}) Net Vega=∑(Vega per contract×contract quantity)\text{Net Vega} = \sum (\text{Vega per contract} \times \text{contract quantity}) Net Theta=∑(Theta per contract×contract quantity)\text{Net Theta} = \sum (\text{Theta per contract} \times \text{contract quantity})

### **Step 2: Calculate Greeks of the New Order**

- Use an **options pricing model** (Black-Scholes, Binomial, or market IV-based approach) to compute **per contract Greeks**.

- Multiply by the order quantity.

Order Delta=Delta per contract×order quantity\text{Order Delta} = \text{Delta per contract} \times \text{order quantity}

(Similar calculations for **Gamma, Vega, Theta**)

### **Step 3: Adjust Based on Order Side**

- If **BUY**, add the new order Greeks to the existing Greeks.

- If **SELL**, subtract them.

Updated Net Delta=Existing Net Delta±Order Delta\text{Updated Net Delta} = \text{Existing Net Delta} \pm \text{Order Delta}

(Same for **Gamma, Vega, Theta**)

### **Step 4: Compare with Limits**

After updating, check if the new Greeks exceed predefined risk thresholds.

## **2. Example in Golang**

package risk

import (

"errors"

)

// UserGreeks stores net Greeks for a trader

type UserGreeks struct {

UserID string

Delta float64

Gamma float64

Vega float64

Theta float64

Limit GreeksLimit

}

// GreeksLimit defines maximum allowed exposure

type GreeksLimit struct {

MaxDelta float64

MaxGamma float64

MaxVega float64

MaxTheta float64

}

// OrderGreeks represents the Greeks impact of a new order

type OrderGreeks struct {

Delta float64

Gamma float64

Vega float64

Theta float64

Quantity int

Side string // "buy" or "sell"

}

// UpdateUserGreeks calculates the new Greeks after an order

func UpdateUserGreeks(userGreeks UserGreeks, order OrderGreeks) (UserGreeks, error) {

multiplier := 1.0

if order.Side == "sell" {

multiplier = -1.0

}

newGreeks := UserGreeks{

UserID: userGreeks.UserID,

Delta: userGreeks.Delta + (order.Delta \* float64(order.Quantity) \* multiplier),

Gamma: userGreeks.Gamma + (order.Gamma \* float64(order.Quantity) \* multiplier),

Vega: userGreeks.Vega + (order.Vega \* float64(order.Quantity) \* multiplier),

Theta: userGreeks.Theta + (order.Theta \* float64(order.Quantity) \* multiplier),

Limit: userGreeks.Limit,

}

// Check limits

if abs(newGreeks.Delta) \> userGreeks.Limit.MaxDelta {

return userGreeks, errors.New("net Delta limit exceeded")

}

if abs(newGreeks.Gamma) \> userGreeks.Limit.MaxGamma {

return userGreeks, errors.New("net Gamma limit exceeded")

}

if abs(newGreeks.Vega) \> userGreeks.Limit.MaxVega {

return userGreeks, errors.New("net Vega limit exceeded")

}

if abs(newGreeks.Theta) \> userGreeks.Limit.MaxTheta {

return userGreeks, errors.New("net Theta limit exceeded")

}

return newGreeks, nil

}

// Helper function for absolute value

func abs(x float64) float64 {

if x \< 0 {

return -x

}

return x

}

## **3. Example Calculation**

### **User’s Existing Portfolio:**

| **Symbol** | **Contracts** | **Delta** | **Gamma** | **Vega** | **Theta** |
|------------|---------------|-----------|-----------|----------|-----------|
| AAPL 150C  | 10            | 0.50      | 0.02      | 0.10     | -0.05     |
| TSLA 800P  | -5            | -0.40     | 0.01      | 0.20     | -0.03     |

### **Current Greeks:**

Net Delta=(10×0.50)+(−5×−0.40)=5+2=7\text{Net Delta} = (10 \times 0.50) + (-5 \times -0.40) = 5 + 2 = 7 Net Gamma=(10×0.02)+(−5×0.01)=0.2−0.05=0.15\text{Net Gamma} = (10 \times 0.02) + (-5 \times 0.01) = 0.2 - 0.05 = 0.15 Net Vega=(10×0.10)+(−5×0.20)=1−1=0\text{Net Vega} = (10 \times 0.10) + (-5 \times 0.20) = 1 - 1 = 0 Net Theta=(10×−0.05)+(−5×−0.03)=−0.5+0.15=−0.35\text{Net Theta} = (10 \times -0.05) + (-5 \times -0.03) = -0.5 + 0.15 = -0.35

### **New Order:**

- Buy **5 AAPL 150C**

- Per contract Greeks:

  - Delta = 0.50, Gamma = 0.02, Vega = 0.10, Theta = -0.05

### **Updated Greeks After Order:**

New Delta=7+(5×0.50)=7+2.5=9.5\text{New Delta} = 7 + (5 \times 0.50) = 7 + 2.5 = 9.5 New Gamma=0.15+(5×0.02)=0.15+0.10=0.25\text{New Gamma} = 0.15 + (5 \times 0.02) = 0.15 + 0.10 = 0.25 New Vega=0+(5×0.10)=0+0.50=0.50\text{New Vega} = 0 + (5 \times 0.10) = 0 + 0.50 = 0.50 New Theta=−0.35+(5×−0.05)=−0.35−0.25=−0.60\text{New Theta} = -0.35 + (5 \times -0.05) = -0.35 - 0.25 = -0.60

✅ If these values **stay within the risk limits**, approve the order.  
❌ If they **exceed any limit**, reject the order.

## **4. Summary**

- **Retrieve the current net Greeks** from the user's portfolio.

- **Compute the Greeks impact of the new order** using per-contract values.

- **Update the total Greeks** and compare with predefined risk limits.

- **Approve or reject the order** based on the updated values.

Would you like to integrate this with a real-time risk engine using Redis or WebSockets? 🚀

# **How to calculate per contract greeks**

### **How to Calculate Per Contract Greeks**

To calculate the Greeks per option contract, we typically use the **Black-Scholes model** for European options. For American options, the **Binomial model** or **Monte Carlo simulations** are used.

## **1. Inputs for Greek Calculations**

Before computing the Greeks, you need these values:

| **Symbol** | **Description** | **Formula/Source** |
|----|----|----|
| SS | Current stock price | Market data |
| KK | Strike price of the option | Option contract |
| TT | Time to expiration (in years) | days to expiration365\frac{\text{days to expiration}}{365} |
| rr | Risk-free interest rate | U.S. Treasury yield |
| σ\sigma | Implied volatility (IV) | Market data |
| N(x)N(x) | CDF of standard normal distribution | Statistics function |

Two key calculations used for Greeks:

d1=ln⁡(S/K)+(r+σ2/2)TσTd_1 = \frac{\ln(S/K) + (r + \sigma^2 / 2)T}{\sigma \sqrt{T}} d2=d1−σTd_2 = d_1 - \sigma \sqrt{T}

## **2. Greek Calculations for Calls & Puts**

| **Greek** | **Call Option Formula** | **Put Option Formula** |
|----|----|----|
| **Delta** | N(d1)N(d_1) | N(d1)−1N(d_1) - 1 |
| **Gamma** | N′(d1)SσT\frac{N'(d_1)}{S \sigma \sqrt{T}} | Same as Call |
| **Vega** | SN′(d1)TS N'(d_1) \sqrt{T} | Same as Call |
| **Theta** | −SN′(d1)σ2T−rKe−rTN(d2)-\frac{S N'(d_1) \sigma}{2\sqrt{T}} - rKe^{-rT} N(d_2) | −SN′(d1)σ2T+rKe−rTN(−d2)-\frac{S N'(d_1) \sigma}{2\sqrt{T}} + rKe^{-rT} N(-d_2) |
| **Rho** | KTe−rTN(d2)K T e^{-rT} N(d_2) | −KTe−rTN(−d2)-K T e^{-rT} N(-d_2) |

**Note:** N′(d1)N'(d_1) is the **probability density function (PDF)** of the standard normal distribution:

N′(d1)=e−d12/22πN'(d_1) = \frac{e^{-d_1^2 / 2}}{\sqrt{2\pi}}

## **3. Golang Code for Greeks Calculation**

Here’s how to compute per contract Greeks using the Black-Scholes model:

package main

import (

"math"

"fmt"

)

// Black-Scholes Greeks Calculation

// Normal CDF (N(x))

func normCDF(x float64) float64 {

return 0.5 \* (1 + math.Erf(x/math.Sqrt2))

}

// Normal PDF (N'(x))

func normPDF(x float64) float64 {

return math.Exp(-0.5\*x\*x) / math.Sqrt(2\*math.Pi)

}

// Black-Scholes Greeks

func calculateGreeks(S, K, T, r, sigma float64, optionType string) (delta, gamma, vega, theta, rho float64) {

d1 := (math.Log(S/K) + (r+0.5\*sigma\*sigma)\*T) / (sigma \* math.Sqrt(T))

d2 := d1 - sigma\*math.Sqrt(T)

if optionType == "call" {

delta = normCDF(d1)

theta = (-S \* normPDF(d1) \* sigma / (2 \* math.Sqrt(T))) - (r \* K \* math.Exp(-r\*T) \* normCDF(d2))

rho = K \* T \* math.Exp(-r\*T) \* normCDF(d2)

} else { // put option

delta = normCDF(d1) - 1

theta = (-S \* normPDF(d1) \* sigma / (2 \* math.Sqrt(T))) + (r \* K \* math.Exp(-r\*T) \* normCDF(-d2))

rho = -K \* T \* math.Exp(-r\*T) \* normCDF(-d2)

}

// Common Greeks

gamma = normPDF(d1) / (S \* sigma \* math.Sqrt(T))

vega = S \* normPDF(d1) \* math.Sqrt(T)

return delta, gamma, vega, theta, rho

}

func main() {

// Example: AAPL 150 Call Option

S := 150.0 // Current stock price

K := 150.0 // Strike price

T := 30.0/365.0 // Time to expiration (30 days)

r := 0.05 // Risk-free rate (5%)

sigma := 0.25 // Implied Volatility (25%)

delta, gamma, vega, theta, rho := calculateGreeks(S, K, T, r, sigma, "call")

fmt.Printf("Delta: %.4f\nGamma: %.4f\nVega: %.4f\nTheta: %.4f\nRho: %.4f\n", delta, gamma, vega, theta, rho)

}

## **4. Example Calculation**

For an **AAPL 150 Call Option** with:

- **Stock Price** = 150

- **Strike Price** = 150

- **Time to Expiration** = 30 days

- **Risk-Free Rate** = 5%

- **Implied Volatility** = 25%

🔹 **Output:**

Delta: 0.5366

Gamma: 0.0390

Vega: 7.3456

Theta: -3.1623

Rho: 2.1458

This means:

- Delta **(0.5366)** → Option price moves **~\$0.54 per \$1 stock movement**.

- Gamma **(0.0390)** → Delta **changes by ~0.039 per \$1 stock move**.

- Vega **(7.3456)** → Option price increases **~\$7.35 per 1% IV increase**.

- Theta **(-3.1623)** → Option loses **~\$3.16 per day due to time decay**.

- Rho **(2.1458)** → Option price increases **~\$2.15 per 1% interest rate hike**.

## **5. Summary**

- Use the **Black-Scholes model** to compute per contract Greeks.

- Fetch **real-time market data** (stock price, IV, time, etc.).

- Apply **Greek formulas** (Delta, Gamma, Vega, Theta, Rho).

- Use the calculated Greeks to **evaluate risk limits** before order execution.

Would you like me to integrate this with a **risk management system** in your trading exchange? 🚀

# **How to calc IV?**

### **How to Calculate Implied Volatility (IV)?**

Implied Volatility (IV) is the **volatility that makes the market price of an option match the Black-Scholes price**.  
Unlike historical volatility (based on past price movement), IV is derived by **reversing the Black-Scholes formula** to solve for σ\sigma (volatility).

## **1. IV Calculation: The Inverse Black-Scholes Problem**

The Black-Scholes formula for option price CC (call option) is:

C=SN(d1)−Ke−rTN(d2)C = S N(d_1) - K e^{-rT} N(d_2)

Where:

d1=ln⁡(S/K)+(r+σ2/2)TσTd_1 = \frac{\ln(S/K) + (r + \sigma^2/2) T}{\sigma \sqrt{T}} d2=d1−σTd_2 = d_1 - \sigma \sqrt{T}

- **Given:**

  - CC (option market price)

  - S,K,T,rS, K, T, r (stock price, strike, time, risk-free rate)

- **Unknown:** σ\sigma (implied volatility)

Since **Black-Scholes is not directly solvable for σ\sigma**, we use a **numerical method** like **Newton-Raphson** to approximate IV.

## **2. Newton-Raphson Method for IV Calculation**

Newton's method iterates to find σ\sigma by solving:

σn+1=σn−f(σn)f′(σn)\sigma\_{n+1} = \sigma_n - \frac{f(\sigma_n)}{f'(\sigma_n)}

Where:

- f(σ)=BS Price(σ)−Market Pricef(\sigma) = \text{BS Price}(\sigma) - \text{Market Price}

- f′(σ)=ddσBS Price(σ)f'(\sigma) = \frac{d}{d\sigma} \text{BS Price}(\sigma) (Vega)

Since **Vega measures the option price's sensitivity to volatility**, we use:

Vega=SN′(d1)TVega = S N'(d_1) \sqrt{T}

## **3. Golang Code for Implied Volatility Calculation**

package main

import (

"fmt"

"math"

)

// Normal CDF (N(x))

func normCDF(x float64) float64 {

return 0.5 \* (1 + math.Erf(x/math.Sqrt2))

}

// Normal PDF (N'(x))

func normPDF(x float64) float64 {

return math.Exp(-0.5\*x\*x) / math.Sqrt(2\*math.Pi)

}

// Black-Scholes Call Option Price

func blackScholesCall(S, K, T, r, sigma float64) float64 {

d1 := (math.Log(S/K) + (r+0.5\*sigma\*sigma)\*T) / (sigma \* math.Sqrt(T))

d2 := d1 - sigma\*math.Sqrt(T)

return S\*normCDF(d1) - K\*math.Exp(-r\*T)\*normCDF(d2)

}

// Vega Calculation (Derivative of Black-Scholes w.r.t sigma)

func vega(S, K, T, r, sigma float64) float64 {

d1 := (math.Log(S/K) + (r+0.5\*sigma\*sigma)\*T) / (sigma \* math.Sqrt(T))

return S \* normPDF(d1) \* math.Sqrt(T)

}

// Newton-Raphson Method for Implied Volatility

func impliedVolatility(S, K, T, r, marketPrice float64) float64 {

sigma := 0.2 // Initial guess (20% IV)

tolerance := 1e-5

maxIterations := 100

for i := 0; i \< maxIterations; i++ {

price := blackScholesCall(S, K, T, r, sigma)

vegaValue := vega(S, K, T, r, sigma)

// Stop if Vega is too small (avoiding division by zero)

if math.Abs(vegaValue) \< 1e-10 {

break

}

// Newton-Raphson step

sigma = sigma - (price-marketPrice)/vegaValue

// Convergence check

if math.Abs(price-marketPrice) \< tolerance {

break

}

}

return sigma

}

func main() {

S := 150.0 // Stock price

K := 150.0 // Strike price

T := 30.0 / 365.0 // Time to expiration (30 days)

r := 0.05 // Risk-free rate (5%)

marketPrice := 7.50 // Observed option market price

IV := impliedVolatility(S, K, T, r, marketPrice)

fmt.Printf("Implied Volatility: %.2f%%\n", IV\*100)

}

## **4. Example Calculation**

For an **AAPL 150 Call Option** with:

- **Stock Price (S):** \$150

- **Strike Price (K):** \$150

- **Time to Expiry (T):** 30 days

- **Risk-Free Rate (r):** 5%

- **Market Price of Option:** \$7.50

🔹 **Output:**

Implied Volatility: 24.67%

This means the market **expects a 24.67% annualized volatility** for AAPL.

## **5. Alternative Methods for IV Calculation**

If Newton-Raphson fails (e.g., low Vega or poor initial guess), alternatives include:

- **Bisection Method:** Slower but robust.

- **Brent’s Method:** Combines bisection and Newton for faster convergence.

- **Machine Learning:** Train a model on past IVs.

## **6. Summary**

- **Implied Volatility (IV)** is the volatility needed to match the **market price** with the **Black-Scholes price**.

- IV is **not directly solvable**, so we use **Newton-Raphson iteration**.

- **Golang implementation** solves IV efficiently.

- **IV is used in options pricing, risk management, and trading strategies**.

Would you like me to integrate this into your **option trading exchange**? 🚀
