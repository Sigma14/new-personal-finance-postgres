import math

import numpy as np
import numpy_financial as npf
import pandas as pd


def calculate_tenure(loan_amount, monthly_payment, annual_interest_rate):
    # Convert annual interest rate to a monthly interest rate
    monthly_interest_rate = annual_interest_rate / 12 / 100

    # Check if the monthly payment is sufficient to cover the interest and principal
    if loan_amount * monthly_interest_rate >= monthly_payment:
        return False

    # Calculate the number of payments (tenure) using the annuity formula
    numerator = math.log(
        1 - ((loan_amount * monthly_interest_rate) / monthly_payment))
    denominator = math.log(1 + monthly_interest_rate)
    tenure = -1 * (numerator / denominator)

    return math.ceil(tenure)  # Round up to the nearest month


def balance(pv, rate, nper, pmt) -> np.ndarray:
    d = (1 + rate) ** nper  # Discount factor
    return pv * d - pmt * (d - 1) / rate


def calculator(amount, interest, tenure, month=None):
    freq = 12  # 12 months per year
    rate = interest / 100  # 6.75% annualized
    nper = tenure  # 30 years
    pv = amount  # Loan face value
    rate /= freq  # Monthly basis
    if not month:
        nper *= freq  # 360 months
    else:
        nper = month

    periods = np.arange(1, nper + 1, dtype=int)
    principal = npf.ppmt(rate, periods, nper, pv)
    interest = npf.ipmt(rate, periods, nper, pv)
    pmt = principal + interest  # Or: pmt = np.pmt(rate, nper, pv)

    cols = ["initial_balance", "payment",
            "interest", "principle", "ending_balance"]
    data = [
        balance(pv, rate, periods - 1, -pmt),
        abs(principal + interest),
        abs(interest),
        abs(principal),
        balance(pv, rate, periods, -pmt),
    ]

    table = pd.DataFrame(data, columns=periods, index=cols).T
    table.index.name = "month"
    return table.round(2)
