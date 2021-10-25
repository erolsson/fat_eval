from collections import defaultdict

import numpy as np

from fat_eval.weakest_link.hazard_functions import weibull
from fat_eval.materials import materials


class WeakestLinkEvaluator:
    def __init__(self, elements, element_labels, steel_data, material, symmetry_factor=1.):
        self.elements = elements
        self.element_labels = element_labels
        self.symmetry_factor = symmetry_factor
        self.steel_data = steel_data
        self.material = materials[material]

    def evaluate(self, stress_state, hazard_function=weibull, cycles=2e6):
        functional_values = hazard_function(stress_state, self.steel_data, self.material, cycles=cycles)
        values_dict = defaultdict(list)
        for s, label in zip(functional_values, self.element_labels):
            values_dict[label].append(s)
        integral = 0
        for e_label, values in values_dict.items():
            element = self.elements[e_label]
            for gp, w, val in zip(element.gauss_points, element.gauss_weights, values):
                integral += val*w*np.linalg.det(element.J(*gp))

        pf = 1 - np.exp(-integral)
        return 1 - (1 - pf)**self.symmetry_factor
