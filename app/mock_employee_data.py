import pandas as pd

# Create a DataFrame with sample employee(s)
df = pd.DataFrame([
    {
        "name": "Ahmad Bin Ali",
        "role": "Software Engineer",
        "start_date": "2022-01-01",
        "salary": 5000,
        "unused_leave": 5,
        "contract_type": "permanent",
        "probation_status": "completed"
    },
    {
        "name": "Siti Binti Omar",
        "role": "HR Executive",
        "start_date": "2023-03-15",
        "salary": 4000,
        "unused_leave": 2,
        "contract_type": "contract",
        "probation_status": "completed"
    }
])

# Save as CSV
df.to_csv("mock_employees.csv", index=False)
