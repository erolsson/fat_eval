import numpy as np


def weibull(stress, hv, material, effective_stress="Findley"):
    stress = np.array(stress)
    hv = np.array(hv)
    m = material.m(hv, effective_stress)
    sw = material.sw(hv, effective_stress)
    sth = material.sth(hv, effective_stress)
    stress[stress < sth] = 0
    return (stress/sw)**m
