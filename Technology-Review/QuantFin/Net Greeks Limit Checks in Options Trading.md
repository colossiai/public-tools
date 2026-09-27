### **Net Greeks Limit Checks in Options Trading**

Net Greeks limit checks ensure that a trader’s overall exposure to risk factors (Delta, Gamma, Vega, Theta, Rho) remains within predefined thresholds. This prevents excessive directional risk, volatility exposure, and time decay sensitivity.

### **1. Key Greeks and Their Risk Implications**

- **Delta (Δ):** Measures sensitivity to the underlying asset price.

  - A high positive Delta means the trader is exposed to a price increase.

  - A high negative Delta means the trader benefits from a price drop.

  - **Limit Check:** Ensure the total Delta stays within a range to prevent excessive directional exposure.

- **Gamma (Γ):** Measures how Delta changes with price movements.

  - High Gamma positions are sensitive to price swings.

  - **Limit Check:** Restrict traders from holding excessively large Gamma positions that could lead to uncontrolled Delta swings.

- **Vega (ν):** Measures sensitivity to implied volatility.

  - Large Vega means the trader is highly affected by volatility shifts.

  - **Limit Check:** Cap Vega exposure to prevent losses from unexpected volatility spikes.

- **Theta (Θ):** Measures time decay of option value.

  - High negative Theta means a trader is losing money over time due to option decay.

  - **Limit Check:** Limit Theta risk, especially for naked short options.

- **Rho (ρ):** Measures sensitivity to interest rate changes.

  - Less relevant for short-term trading but useful for long-term risk management.

  - **Limit Check:** Ensure exposure remains within tolerance levels.

### **2. How to Perform Net Greeks Limit Checks**

1.  **Fetch User's Portfolio Greeks  **

    - Sum the Greeks across all positions (e.g., net Delta = sum of all position Deltas).

2.  **Apply Predefined Risk Limits  **

    - Example limits:

      - Max \|Net Delta\| ≤ 1000

      - Max \|Net Gamma\| ≤ 500

      - Max \|Net Vega\| ≤ 200

      - Max \|Net Theta\| ≤ 100

    - If the new order causes a limit breach, **reject the order**.

### **3. Example Check in Golang**

package risk

import "errors"

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

// CheckGreeksLimits verifies if a new order breaches risk limits

func CheckGreeksLimits(userGreeks UserGreeks, orderDelta, orderGamma, orderVega, orderTheta float64) error {

newDelta := userGreeks.Delta + orderDelta

newGamma := userGreeks.Gamma + orderGamma

newVega := userGreeks.Vega + orderVega

newTheta := userGreeks.Theta + orderTheta

if abs(newDelta) \> userGreeks.Limit.MaxDelta {

return errors.New("net Delta limit exceeded")

}

if abs(newGamma) \> userGreeks.Limit.MaxGamma {

return errors.New("net Gamma limit exceeded")

}

if abs(newVega) \> userGreeks.Limit.MaxVega {

return errors.New("net Vega limit exceeded")

}

if abs(newTheta) \> userGreeks.Limit.MaxTheta {

return errors.New("net Theta limit exceeded")

}

return nil // Order is within risk limits

}

// Helper function to get absolute value

func abs(x float64) float64 {

if x \< 0 {

return -x

}

return x

}

### **4. Why is This Important?**

- Prevents users from accumulating excessive risk.

- Avoids forced liquidation due to extreme market movements.

- Ensures overall exchange stability by capping exposure.

Would you like to integrate this into a real-time risk engine using Redis or another approach?
