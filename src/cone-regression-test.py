import os
import sys
import pandas as pd

# Set current working directory
current_dir = os.getcwd()
data_dir = os.path.join(current_dir, 'data')
base_dir = os.path.join(data_dir, 'base')
cone_dir = os.path.join(data_dir, 'cone')

# Check if correct number of arguments provided
print(len(sys.argv))
if len(sys.argv) != 6:
    print(sys.argv)
    print("Usage: python cone-regression-test.py <base_file> <cone_file> <output_file> <max_pressure> <pressure_interval>")
    sys.exit(1)

# Get the CSV file paths from command line arguments
csv_file1 = sys.argv[1]
csv_file2 = sys.argv[2]
output_file = sys.argv[3]
max_pressure = int(sys.argv[4])
pressure_interval = int(sys.argv[5])
values_list = []
# Get list of values from third argument
for i in range(0, max_pressure, pressure_interval):
    values_list.append(str(i))

# Join paths with current directory
csv_file1 = os.path.join(base_dir, csv_file1)
csv_file2 = os.path.join(cone_dir, csv_file2)

# Verify files exist and are CSV files
for file in [csv_file1, csv_file2]:
    if not os.path.exists(file):
        print(f"Error: File '{file}' does not exist")
        sys.exit(1)
    if not file.lower().endswith('.csv'):
        print(f"Error: File '{file}' is not a CSV file")
        sys.exit(1)

# Read the base CSV file
df1 = pd.read_csv(csv_file1, skiprows=7)
# Get index of max value in column 2 (index 2)
max_idx = df1.iloc[:, 2].idxmax()
# Remove all rows after max_idx
df1 = df1.iloc[:max_idx+1]
# Read the cone CSV file
df2 = pd.read_csv(csv_file2, skiprows=0)

# Convert timestamp column to datetime and then to epoch time in milliseconds
df1.iloc[:, 0] = pd.to_datetime(df1.iloc[:, 0]).astype('int64') // 10**6

# Convert timestamps from seconds to milliseconds since epoch
df2.iloc[:, 0] = df2.iloc[:, 0] * 1000

current_time = None
begin_range = None
end_range = None
for i in range(0, len(df2)):
    if current_time is None:
        current_time = df2.iloc[i, 0]
        begin_range = i
    elif current_time != df2.iloc[i, 0] or i == len(df2) - 1:
        end_range = i
        range_size = end_range - begin_range
        for j in range(begin_range, end_range):
            multiplier = j - begin_range
            df2.iloc[j, 0] = current_time + (multiplier * int(1000 / range_size))
        current_time = df2.iloc[i, 0]
        begin_range = i

# Group df2 by the first column (epoch time) and keep first occurrence
# df2 = df2.drop_duplicates(subset=df2.columns[0])
# Write df2 to test.csv
output_dir = os.path.join(current_dir, 'output')
df2.to_csv(os.path.join(output_dir, 'test.csv'), index=False)


# Find closest rows for each value in values_list
closest_rows = []
closest_df = None
if values_list:
    for target_value in values_list:
        target_value = float(target_value)
        # Find row with closest value in column 2 (index 1)
        closest_idx = (df1.iloc[:, 2] - target_value).abs().idxmin()
        # Drop the first column before appending
        row_to_append = df1.iloc[closest_idx].drop(df1.columns[1])
        closest_rows.append(row_to_append)
    
    # Create DataFrame from closest rows
    closest_df = pd.DataFrame(closest_rows)
    # Remove duplicate timestamps by keeping first occurrence
    closest_df = closest_df.drop_duplicates(subset=closest_df.columns[0])
    print("\nClosest matches found:")
    print(closest_df)

output_dir = os.path.join(current_dir, 'output')
# Open file for writing results
results_file = open(os.path.join(output_dir, output_file), 'w')
# Write header
results_file.write('Sleeve_Pressure,Tip_Pressure,Base_Pressure\n')

# Find matching rows in df2 for each timestamp in closest_df
if closest_df is not None:
    print("\nMatching rows from cone data:")
    for idx, row in closest_df.iterrows():
        timestamp = int(row.iloc[0])  # Get timestamp from first column
        pressure = row.iloc[1]
        closest_timestamp_index = (df2.iloc[:, 0] - timestamp).abs().idxmin()
        if closest_timestamp_index is not None:
            results_file.write(f"{df2.iloc[closest_timestamp_index, 3]},{df2.iloc[closest_timestamp_index, 4]},{pressure}\n")
        else:
            print(f"\nNo match found for timestamp {timestamp}")
results_file.close()
print("Results saved to generated_results.csv")