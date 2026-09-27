Most popular market making algorithms with pseudo code.

Market making algorithms are designed to provide liquidity by continuously quoting bid and ask prices. Here are the most popular approaches with their core logic:

## 1. Simple Spread-Based Market Making

This is the foundational approach where the algorithm maintains symmetric spreads around a reference price.

ALGORITHM: Simple Spread Market Making

INPUT: reference_price, spread_width, quantity

OUTPUT: bid_price, ask_price, bid_qty, ask_qty

BEGIN

half_spread = spread_width / 2

bid_price = reference_price - half_spread

ask_price = reference_price + half_spread

bid_qty = quantity

ask_qty = quantity

PLACE_ORDER(BUY, bid_price, bid_qty)

PLACE_ORDER(SELL, ask_price, ask_qty)

WHILE market_open DO

IF order_filled THEN

UPDATE_INVENTORY()

RECALCULATE_PRICES()

REPLACE_ORDERS()

END IF

IF market_data_updated THEN

reference_price = GET_MID_PRICE()

ADJUST_QUOTES()

END IF

END WHILE

END

## 2. Inventory-Aware Market Making (Avellaneda-Stoikov)

This sophisticated model adjusts quotes based on current inventory to manage risk and target zero inventory over time.

ALGORITHM: Avellaneda-Stoikov Market Making

INPUT: mid_price, volatility, risk_aversion, inventory, time_horizon

OUTPUT: optimal_bid, optimal_ask

BEGIN

gamma = risk_aversion

sigma = volatility

T = time_horizon

q = current_inventory

// Calculate reservation price

reservation_price = mid_price - (gamma \* sigma^2 \* T \* q)

// Calculate optimal spread

optimal_spread = (gamma \* sigma^2 \* T) + (2 \* ln(1 + gamma/k))

// where k is market depth parameter

// Set quotes around reservation price

half_spread = optimal_spread / 2

optimal_bid = reservation_price - half_spread

optimal_ask = reservation_price + half_spread

// Inventory skewing

IF q \> 0 THEN // long inventory

optimal_bid = optimal_bid - inventory_penalty(q)

optimal_ask = optimal_ask - inventory_penalty(q)

ELSE IF q \< 0 THEN // short inventory

optimal_bid = optimal_bid + inventory_penalty(\|q\|)

optimal_ask = optimal_ask + inventory_penalty(\|q\|)

END IF

RETURN optimal_bid, optimal_ask

END

FUNCTION inventory_penalty(inventory_size)

RETURN alpha \* inventory_size^2 // quadratic penalty

END

## 3. Mean Reversion Market Making

This algorithm assumes prices will revert to a long-term mean and adjusts quotes accordingly.

ALGORITHM: Mean Reversion Market Making

INPUT: current_price, moving_average, reversion_speed, confidence

OUTPUT: bid_quote, ask_quote

BEGIN

mean_price = CALCULATE_MOVING_AVERAGE(price_history, window)

deviation = current_price - mean_price

// Calculate reversion probability

reversion_prob = SIGMOID(reversion_speed \* deviation)

// Adjust spread based on mean reversion expectation

base_spread = minimum_spread

IF current_price \> mean_price THEN // price above mean

// Expect downward reversion - wider ask, tighter bid

bid_adjustment = -deviation \* reversion_prob \* 0.5

ask_adjustment = deviation \* reversion_prob \* 0.3

ELSE // price below mean

// Expect upward reversion - wider bid, tighter ask

bid_adjustment = deviation \* reversion_prob \* 0.3

ask_adjustment = -deviation \* reversion_prob \* 0.5

END IF

bid_quote = current_price - (base_spread/2) + bid_adjustment

ask_quote = current_price + (base_spread/2) + ask_adjustment

RETURN bid_quote, ask_quote

END

FUNCTION SIGMOID(x)

RETURN 1 / (1 + EXP(-x))

END

## 4. Order Flow Imbalance Market Making

This algorithm adjusts quotes based on order book imbalances and recent trade flow.

ALGORITHM: Order Flow Market Making

INPUT: order_book, recent_trades, imbalance_threshold

OUTPUT: adjusted_bid, adjusted_ask

BEGIN

// Calculate order book imbalance

total_bid_volume = SUM(order_book.bids.volume)

total_ask_volume = SUM(order_book.asks.volume)

imbalance = (total_bid_volume - total_ask_volume) /

(total_bid_volume + total_ask_volume)

// Calculate trade flow imbalance

recent_buy_volume = SUM(recent_trades WHERE side = BUY)

recent_sell_volume = SUM(recent_trades WHERE side = SELL)

trade_imbalance = (recent_buy_volume - recent_sell_volume) /

(recent_buy_volume + recent_sell_volume)

// Combined signal

total_imbalance = (imbalance + trade_imbalance) / 2

base_mid = (best_bid + best_ask) / 2

base_spread = best_ask - best_bid

// Adjust quotes based on imbalance

IF total_imbalance \> imbalance_threshold THEN

// More buying pressure - shift quotes up

mid_adjustment = base_spread \* total_imbalance \* 0.5

spread_adjustment = base_spread \* abs(total_imbalance) \* 0.2

ELSE IF total_imbalance \< -imbalance_threshold THEN

// More selling pressure - shift quotes down

mid_adjustment = base_spread \* total_imbalance \* 0.5

spread_adjustment = base_spread \* abs(total_imbalance) \* 0.2

ELSE

mid_adjustment = 0

spread_adjustment = 0

END IF

adjusted_mid = base_mid + mid_adjustment

adjusted_spread = base_spread + spread_adjustment

adjusted_bid = adjusted_mid - adjusted_spread/2

adjusted_ask = adjusted_mid + adjusted_spread/2

RETURN adjusted_bid, adjusted_ask

END

## 5. Reinforcement Learning Market Making

Modern ML-based approach that learns optimal quoting strategies through interaction with the market.

ALGORITHM: RL Market Making

INPUT: state_features, action_space, reward_function

OUTPUT: optimal_action

BEGIN

// State representation

state = \[

normalized_inventory,

price_momentum,

volatility_estimate,

order_book_imbalance,

time_to_close,

recent_pnl

\]

// Action space: \[bid_offset, ask_offset, bid_size, ask_size\]

action_space = DISCRETIZE(\[-max_offset:max_offset\], \[min_size:max_size\])

// Neural network policy

action_probabilities = NEURAL_NETWORK(state)

action = SAMPLE(action_probabilities)

// Execute action

bid_price = mid_price + action.bid_offset

ask_price = mid_price + action.ask_offset

PLACE_ORDER(BUY, bid_price, action.bid_size)

PLACE_ORDER(SELL, ask_price, action.ask_size)

// Observe outcome and calculate reward

next_state = OBSERVE_MARKET()

reward = CALCULATE_REWARD(pnl_change, inventory_penalty, spread_reward)

// Update policy

STORE_EXPERIENCE(state, action, reward, next_state)

IF enough_experiences THEN

UPDATE_NEURAL_NETWORK()

END IF

RETURN action

END

FUNCTION CALCULATE_REWARD(pnl, inventory, spread)

inventory_penalty = -lambda1 \* inventory^2

spread_reward = lambda2 \* spread_captured

risk_penalty = -lambda3 \* position_risk

RETURN pnl + inventory_penalty + spread_reward + risk_penalty

END

## 6. Multi-Level Market Making

This algorithm places multiple orders at different price levels to capture more trading opportunities.

ALGORITHM: Multi-Level Market Making

INPUT: n_levels, level_spacing, size_distribution

OUTPUT: multiple_bid_asks

BEGIN

mid_price = GET_MID_PRICE()

base_spread = GET_MIN_SPREAD()

orders = \[\]

FOR level = 1 TO n_levels DO

// Calculate prices for this level

bid_offset = base_spread/2 + (level-1) \* level_spacing

ask_offset = base_spread/2 + (level-1) \* level_spacing

bid_price = mid_price - bid_offset

ask_price = mid_price + ask_offset

// Size decreases with distance from mid

size_multiplier = 1 / level^size_decay_factor

bid_size = base_size \* size_multiplier

ask_size = base_size \* size_multiplier

// Adjust for inventory

inventory_adjustment = CALCULATE_INVENTORY_SKEW(current_inventory)

bid_size = bid_size \* (1 + inventory_adjustment)

ask_size = ask_size \* (1 - inventory_adjustment)

orders.APPEND(\[BUY, bid_price, bid_size\])

orders.APPEND(\[SELL, ask_price, ask_size\])

END FOR

PLACE_ALL_ORDERS(orders)

RETURN orders

END

FUNCTION CALCULATE_INVENTORY_SKEW(inventory)

max_inventory = position_limit

skew = inventory / max_inventory

RETURN CLIP(skew, -0.5, 0.5) // Cap the adjustment

END

Each algorithm has different strengths:

- simple spread-based is robust and easy to implement,

- Avellaneda-Stoikov provides theoretical optimality under certain assumptions,

- mean reversion works well in ranging markets,

- order flow algorithms adapt to market microstructure,

- RL approaches can learn complex patterns, and

- multi-level strategies capture more opportunities across the order book.

> The choice depends on market conditions, available data, computational resources, and risk tolerance.
