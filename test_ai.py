from dotenv import load_dotenv
import os
import requests

load_dotenv()  # This loads variables from .env into the environment

api_key = os.getenv("OPENROUTER_API_KEY") or "YOUR_OPENROUTER_API_KEY"
model = "google/gemma-2-9b-it:free"  # or any other free model you want to test

prompt = """
Give financial advice based on this bank statement:
STANDARD BANK SOUTH AFRICA
Soweto Plaza Branch | Tel: 0860 123 000
ACCOUNT STATEMENT
Account Holder: Thabo Moloi Statement Period: 01 April 2025 - 30 June 2025
Account Number: 6234 5678 9012 Account Type: Cheque Account
Branch Code: 004805 (Soweto Plaza) Opening Balance: ZAR 8,500.00
Date Description Debit (ZAR) Credit (ZAR) Balance
01/04/2025 Opening Balance-- 8,500.00
01/04/2025 Rent - Diepsloot Prop 6,500.00-2,000.00
01/04/2025 Eskom Electricity 850.00-1,150.00
01/04/2025 Joburg Water 320.00-830.00
01/04/2025 Orlando West Primary School Fees 1,200.00--370.00
02/04/2025 Shoprite Groceries 1,750.00--2,120.00
05/04/2025 Taxi Fare 180.00--2,300.00
08/04/2025 PEP Clothing 420.00--2,720.00
12/04/2025 MTN Airtime 200.00--2,920.00
15/04/2025 Shoprite Groceries 1,680.00--4,600.00
18/04/2025 Petrol - Engen Soweto 500.00--5,100.00
22/04/2025 Clinic Visit 150.00--5,250.00
25/04/2025 Soweto Auto Repair Salary-18,000.00 12,750.00
25/04/2025 Toyota Corolla Instalment 2,200.00-10,550.00
27/04/2025 DStv Subscription 300.00-10,250.00
28/04/2025 Spar Groceries 1,200.00-9,050.00
30/04/2025 ATM Cash Withdrawal 1,000.00-8,050.00
01/05/2025 Rent - Diepsloot Prop 6,500.00-1,550.00
25/05/2025 Soweto Auto Repair Salary-18,000.00 19,550.00
30/05/2025 Closing Balance-- 7,000.00
01/06/2025 Rent - Diepsloot Prop 6,500.00-500.00
25/06/2025 Soweto Auto Repair Salary-18,000.00 18,500.00
30/06/2025 Closing Balance-- 3,200.00
** FICTITIOUS STATEMENT FOR DEMONSTRATION PURPOSES ONLY **
This is not a real bank document. Do not use for any official purpose.
Generated on: 15 July 2025 | Standard Bank South Africa - Soweto Plaza Branch
"""

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

payload = {
    "model": model,
    "messages": [
        {"role": "user", "content": prompt}
    ]
}

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json=payload
)

print("Status:", response.status_code)
print("Response:", response.json()) 