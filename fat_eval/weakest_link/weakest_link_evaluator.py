from collections import defaultdict

import numpy as np

from abaqus_python_interface import ABQInterface

from fat_eval.weakest_link.FEM_functions.elements import element_types
from fat_eval.weakest_link.hazard_functions import weibull
from fat_eval.fatigue_materials import materials
from fat_eval.utilities.steel_data import abaqus_fields, SteelData


def setup_weakest_link_evaluator(odb_file, heat_treatment, element_set, instance_name,
                                 symmetry_factor, abaqus):
    abq = ABQInterface(abaqus)
    element_data = abq.get_element_data(odb_file, element_set, instance_name)
    heat_treatment_data = {}
    element_labels = None
    for i, heat_treatment_field in enumerate(abaqus_fields):
        field, _, element_labels = abq.read_data_from_odb(
            odb_file_name=heat_treatment.odb_file_name,
            field_id=heat_treatment_field,
            step_name=heat_treatment.step_name,
            frame_number=heat_treatment.frame_number,
            set_name=heat_treatment.element_set,
            instance_name=heat_treatment.instance,
            get_position_numbers=True
        )
        heat_treatment_data[heat_treatment_field] = field
    elements = {}
    for element_type, element_coordinates in element_data.items():
        for element_label, coords in element_coordinates.items():
            elements[element_label] = element_types[element_type](coords)

    evaluator = WeakestLinkEvaluator(elements, element_labels, SteelData(heat_treatment_data),
                                     symmetry_factor)
    return evaluator


class WeakestLinkEvaluator:
    def __init__(self, elements, element_labels, steel_data, symmetry_factor=1.):
        self.elements = elements
        self.element_labels = element_labels
        self.symmetry_factor = symmetry_factor
        self.steel_data = steel_data

    def evaluate(self, stress_state, material_name, hazard_function=weibull, cycles=2e6):
        material = materials[material_name]
        functional_values = hazard_function(stress_state, self.steel_data, material, cycles=cycles)
        values_dict = defaultdict(list)
        for s, label in zip(functional_values, self.element_labels):
            values_dict[label].append(s)
        integral = 0
        for e_label, values in values_dict.items():
            element = self.elements[e_label]
            for vol, w, val in zip(element.gauss_point_volumes, element.gauss_weights, values):
                integral += val*w*vol

        pf = 1 - np.exp(-integral)
        return 1 - (1 - pf)**self.symmetry_factor
