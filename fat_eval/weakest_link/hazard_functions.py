import numpy as np


def weibull(stress, steel_data, material, effective_stress="Findley", cycles=2e6):
    stress = np.array(stress)
    m = material.m(steel_data, effective_stress, cycles)
    sw = material.sw(steel_data, effective_stress, cycles)
    sth = material.sth(steel_data, effective_stress)
    stress[stress < sth] = 0
    return (stress/sw)**m
