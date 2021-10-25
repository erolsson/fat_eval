from abaqus_python_interface import ABQInterface

from fat_eval.weakest_link.FEM_functions.elements import element_types
from fat_eval.utilities.steel_data import abaqus_fields, SteelData
from weakest_link_evaluator import WeakestLinkEvaluator


def calculate_probability_of_failure(odb_file, material, field, heat_treatment, element_set, instance_name,
                                     load_cases, symmetry_factor, abaqus):
    abq = ABQInterface(abaqus)
    element_data = abq.get_element_data(odb_file, element_set, instance_name)
    heat_treatment_data = {}
    for heat_treatment_field in abaqus_fields:
        heat_treatment_data[heat_treatment_field] = abq.read_data_from_odb(
            odb_file_name=heat_treatment.odb_file_name,
            field_id=heat_treatment_field,
            step_name=heat_treatment.step_name,
            frame_number=heat_treatment.frame_number,
            set_name=heat_treatment.element_set,
            instance_name=heat_treatment.instance
        )

    evaluator = None
    for load_case in load_cases:
        load_case_parameters = load_case.split(',')
        step = load_case_parameters[0]
        frame = int(load_case_parameters[1])
        load_cycles = [float(n) for n in load_case_parameters[2:]]
        stress, _, element_labels = abq.read_data_from_odb(field, odb_file, step, frame, element_set, instance_name,
                                                           get_position_numbers=True)

        elements = {}
        if evaluator is None:
            for element_type, element_coordinates in element_data.items():
                for element_label, coords in element_coordinates.items():
                    elements[element_label] = element_types[element_type](coords)

            evaluator = WeakestLinkEvaluator(elements, element_labels, SteelData(heat_treatment_data), material,
                                             symmetry_factor)
        print("The probability of failure for the stress state in step " + step + " frame " + str(frame) + " is ")
        for cycles in load_cycles:
            print("\tAt " + str(cycles) + " pf = " + str(evaluator.evaluate(stress, cycles=cycles)))
