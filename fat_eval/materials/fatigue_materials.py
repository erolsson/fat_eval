import numpy as np


class Material:
    def __init__(self, name=''):
        self.sw1 = 0
        self.sw2 = 0
        self.b = 0
        self.name = name
        self.mean_stress_sensitivity_k = 0
        self.heat_sim_fields = ['SDV_HARDNESS']

    @staticmethod
    def sth(hv, effective_stress):
        return 0*hv

    def sw(self, hv, effective_stress):
        return self.sw1 + hv*self.sw2

    def m(self, hv, effective_stress):
        return self.b/hv**2

    def mean_stress_sensitivity(self, steel_data):
        hv = np.array(steel_data.hv)
        return hv/self.mean_stress_sensitivity_k

    @staticmethod
    def findley_k(steel_data):
        return 0.017 + 8.27e-4*steel_data.hv

    @staticmethod
    def critical_findley_stress(steel_data):
        return 197.75 + 0.56833*steel_data.hv


SS2506 = Material(name='SS2506')
SS2506.mean_stress_sensitivity_k = 1000

materials = {'SS2506': SS2506}
