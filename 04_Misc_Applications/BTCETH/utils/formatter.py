from typing import Union
import math

def format_currency(value: float, decimals: int = 2) -> str:
    """Formats a float as a currency string.
    
    Args:
        value (float): The monetary value.
        decimals (int): Number of decimal places.
        
    Returns:
        str: Formatted currency (e.g., "$1,234.56").
    """
    if math.isnan(value) or math.isinf(value):
        return "$0.00"
    return f"${value:,.{decimals}f}"

def format_hashrate(hashrate_h_s: float) -> str:
    """Formats a raw hashrate (H/s) to the most appropriate unit (EH/s, PH/s, TH/s, etc.).
    
    Args:
        hashrate_h_s (float): Hashrate in hashes per second.
        
    Returns:
        str: Formatted hashrate (e.g., "120.45 TH/s").
    """
    if hashrate_h_s <= 0:
        return "0 H/s"
    
    units = ["H/s", "KH/s", "MH/s", "GH/s", "TH/s", "PH/s", "EH/s"]
    i = 0
    while hashrate_h_s >= 1000.0 and i < len(units) - 1:
        hashrate_h_s /= 1000.0
        i += 1
    
    return f"{hashrate_h_s:,.2f} {units[i]}"

def format_probability(prob: float, decimals: int = 12) -> str:
    """Formats a probability, switching to scientific notation for extremely small values.
    
    Args:
        prob (float): Probability between 0 and 1.
        decimals (int): Decimal precision to keep.
        
    Returns:
        str: Formatted percentage string.
    """
    if prob <= 0.0:
        return "0.00%"
    if prob >= 1.0:
        return "100.00%"
    
    # If the probability is very small, use scientific notation
    if prob < 0.0001:
        # Convert to percentage first (prob * 100) and format in scientific
        pct_val = prob * 100.0
        return f"{pct_val:.{decimals}e}%"
    
    return f"{prob * 100.0:.{decimals}f}%"

def format_duration(seconds: float) -> str:
    """Converts a duration in seconds to a human-readable string (Years, Days, Hours, etc.).
    
    Handles astronomical numbers (e.g., billions of years) gracefully.
    
    Args:
        seconds (float): Duration in seconds.
        
    Returns:
        str: Human-readable time duration.
    """
    if math.isinf(seconds) or seconds <= 0:
        return "無限大"
    
    # Define time constants in seconds
    MINUTE = 60
    HOUR = 3600
    DAY = 86400
    YEAR = 31536000  # 365 days
    
    # Check if we are dealing with massive scale
    years = seconds / YEAR
    if years >= 1_000_000:
        if years >= 1_000_000_000:
            return f"{years / 1_000_000_000:,.2f} 十億年"
        return f"{years / 1_000_000:,.2f} 百萬年"
    
    if seconds >= YEAR:
        y = int(years)
        remainder_days = (seconds % YEAR) / DAY
        d = int(remainder_days)
        if y > 10:
            return f"{y:,} 年 {d} 天"
        remainder_hours = ((seconds % YEAR) % DAY) / HOUR
        h = int(remainder_hours)
        return f"{y} 年 {d} 天 {h} 小時"
        
    if seconds >= DAY:
        d = int(seconds / DAY)
        h = int((seconds % DAY) / HOUR)
        m = int(((seconds % DAY) % HOUR) / MINUTE)
        return f"{d} 天 {h} 小時 {m} 分鐘"
        
    if seconds >= HOUR:
        h = int(seconds / HOUR)
        m = int((seconds % HOUR) / MINUTE)
        return f"{h} 小時 {m} 分鐘"
        
    if seconds >= MINUTE:
        m = int(seconds / MINUTE)
        s = int(seconds % MINUTE)
        return f"{m} 分鐘 {s} 秒"
        
    return f"{seconds:.2f} 秒"
