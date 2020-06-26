# CPU Usage

This basic example uses `psutil` to collect a simple time-series of per-CPU usage percent. It then prints out some aggregate statistics based on the collected data.

## Running the code

Create a virtualenv and install the required libraries:
```
virtualenv -p python3.6 env
source env/bin/activate
pip install -r requirements.txt
```

Run the `collect` script to populate the database with the CPU statistics. Let it run for a bit before pressing CTRL+C.
```
python collect.py
```

Run the `results` script to display the CPU statistics:
```
python results.py
```
