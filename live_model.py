# live_model.py
import numpy as np
import time
from collections import deque
from arch import arch_model
from Sol_Price_Tracker import get_current_price  # your existing function

# Rolling window for most recent prices
price_window = deque(maxlen=3600)  # store last hour (3600 seconds)
last_update = 0
S0 = None

# Price range targets (customize)
TARGET_RANGES = {
    "1h": (200, 220),
    "6h": (190, 240),
    "24h": (170, 260)
}

def fit_garch(prices):
    returns = np.log(prices[1:] / prices[:-1]) * 100
    garch = arch_model(returns, vol='Garch', p=1, q=1)
    res = garch.fit(disp='off')
    forecast = res.forecast(horizon=1)
    sigma = np.sqrt(forecast.variance.values[-1][0]) / 100
    mu = returns.mean()
    return mu, sigma

def simulate_probability(S0, mu, sigma, a, b, hours=1, n=10000):
    Z = np.random.normal(0, 1, (n, hours))
    paths = S0 * np.exp((mu - 0.5*sigma**2)*hours + sigma * np.sqrt(hours) * Z[:, -1])
    return np.mean((paths >= a) & (paths <= b))

def update_model():
    if len(price_window) < 100:
        print("Waiting for more data...")
        return

    prices = np.array(price_window)
    mu, sigma = fit_garch(prices)

    print(f"\n[MODEL UPDATE] μ={mu:.4f}, σ={sigma:.4f}, Current Price={S0:.2f}")
    for label, (a, b) in TARGET_RANGES.items():
        hours = int(label.replace("h", ""))
        prob = simulate_probability(S0, mu, sigma, a, b, hours)
        print(f"→ P(SOL in [{a}, {b}] in {label}): {prob:.2%}")

def main():
    global S0, last_update

    while True:
        S0 = get_current_price()
        price_window.append(S0)
        now = time.time()

        # Update model every 5 minutes (300 seconds)
        if now - last_update > 300:
            update_model()
            last_update = now

        time.sleep(1)

if __name__ == "__main__":
    main()

