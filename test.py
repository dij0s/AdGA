import re
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd

# File path (replace with your file path)
file_path = "resps.out"

# Extract the timestamp and duration from each log line
time_pattern = re.compile(r"\[(.*?)\]")
duration_pattern = re.compile(r"in (\d+\.\d+) seconds")

timestamps = []
durations = []

# Open the file and read lines
with open(file_path, "r") as file:
    for line in file:
        timestamp_match = time_pattern.search(line)
        duration_match = duration_pattern.search(line)
        if timestamp_match and duration_match:
            timestamp = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S.%f")
            duration = float(duration_match.group(1))
            timestamps.append(timestamp)
            durations.append(duration)

# Create a DataFrame for easier grouping and aggregation
data = pd.DataFrame({"timestamp": timestamps, "duration": durations})

# Set the timestamp as the index and resample into 5-minute intervals
data.set_index("timestamp", inplace=True)
grouped_data = data.resample("5T").mean()  # '5T' stands for 5-minute intervals

# Convert timestamps to numeric for trend line fitting
timestamps_numeric = grouped_data.index.astype(np.int64) // 10**9  # Convert to UNIX timestamps

# Fit a linear regression line (y = mx + b)
m, b = np.polyfit(timestamps_numeric, grouped_data["duration"], 1)
trend_line = m * timestamps_numeric + b

# Plotting the average time taken and trend line
plt.figure(figsize=(10, 6))
plt.plot(grouped_data.index, grouped_data["duration"], marker='o', linestyle='-', label='Avg Time Taken (seconds)')
plt.plot(grouped_data.index, trend_line, linestyle='--', color='red', label='Trend Line')
plt.xlabel('Timestamp')
plt.ylabel('Average Response Time (seconds)')
plt.title('Average Response Time Over 5-Minute Intervals with Trend Line')
plt.grid(True)
plt.legend()
plt.show()
