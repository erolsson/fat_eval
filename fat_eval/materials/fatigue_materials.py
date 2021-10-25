import types

import numpy as np


class Material:
    def __init__(self, name=''):
        self.b = 0
        self.name = name
        self.mean_stress_sensitivity_k = 0
        self.heat_sim_fields = ['SDV_HARDNESS']
        self.sw = None

    @staticmethod
    def sth(steel_data, effective_stress):
        return 0*steel_data.HV

    def m(self, steel_data, effective_stress):
        return 11.5719e6/steel_data.HV**2

    def mean_stress_sensitivity(self, steel_data):
        return np.array(steel_data.HV)/self.mean_stress_sensitivity_k

    @staticmethod
    def findley_k(steel_data):
        return 0.017 + 8.27e-4*steel_data.HV

    @staticmethod
    def critical_findley_stress(steel_data):
        return 197.75 + 0.56833*steel_data.HV


def sw_SS2506(_, steel_data, effective_stress, N=2e6):
    return 158.7 + 0.481538*steel_data.HV


SS2506 = Material(name='SS2506')
SS2506.mean_stress_sensitivity_k = 1000
SS2506.sw = types.MethodType(sw_SS2506, SS2506)

materials = {'SS2506': SS2506}
