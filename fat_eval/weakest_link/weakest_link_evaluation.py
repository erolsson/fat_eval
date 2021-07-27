import numpy as np
from fat_eval.weakest_link.hazard_functions import weibull


class WeakestLinkEvaluator:
    def __init__(self, elements, hv, symmetry_factor=1.):
        self.elements = elements
        self.symmetry_factor = symmetry_factor
        self.hv = hv

    def evaluate(self, stress_state, material, hazard_function=weibull):
        functional_values = hazard_function(stress_state, self.hv, material)
        integral = 0
        for e, values in zip(self.elements, functional_values):
            for gp, w, val in zip(e.gauss_points, e.gauss_weights, values):
                integral += val*w*np.linalg.det(e.J(*gp))

        pf = 1 - np.exp(-integral)
        return 1 - (1 - pf)**self.symmetry_factor
