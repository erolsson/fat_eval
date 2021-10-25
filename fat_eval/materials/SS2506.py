import numpy as np


def sth(steel_data, effective_stress):
    return 0*steel_data.HV


def m(steel_data, effective_stress, N=2e6):
    m = 11.5719e6/steel_data.HV**2
    if N < 1e5:
        b = 5
    else:
        b = 28
    return m*(N/1e5)**(-1/b)


def mean_stress_sensitivity(steel_data):
    return np.array(steel_data.HV)/1000


def findley_k(steel_data):
    return 0.017 + 8.27e-4*steel_data.HV


def critical_findley_stress(steel_data):
    return 197.75 + 0.56833*steel_data.HV


def sw(steel_data, effective_stress, N=2e6):
    if N < 1e5:
        b = 5
    else:
        b = 28
    sw = 158.7 + 0.481538*steel_data.HV
    return sw*(N/1e5)**(-1/b)
