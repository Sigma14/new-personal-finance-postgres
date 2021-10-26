import numpy as np
import pandas as pd


def balance(pv, rate, nper, pmt) -> np.ndarray:
    d = (1 + rate) ** nper  # Discount factor
    return pv * d - pmt * (d - 1) / rate


def calculator(amount, interest, tenure):
    freq = 12  # 12 months per year
    rate = interest / 100  # 6.75% annualized
    nper = tenure  # 30 years
    pv = amount  # Loan face value
    rate /= freq  # Monthly basis
    nper *= freq  # 360 months

    periods = np.arange(1, nper + 1, dtype=int)
    principal = np.ppmt(rate, periods, nper, pv)
    interest = np.ipmt(rate, periods, nper, pv)
    pmt = principal + interest  # Or: pmt = np.pmt(rate, nper, pv)

    cols = ['initial_balance', 'payment', 'interest', 'principle', 'ending_balance']
    data = [balance(pv, rate, periods - 1, -pmt), abs(principal + interest), abs(interest), abs(principal), balance(pv, rate, periods, -pmt)]

    table = pd.DataFrame(data, columns=periods, index=cols).T
    table.index.name = 'month'
    return table.round(2)
