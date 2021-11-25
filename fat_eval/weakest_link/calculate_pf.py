from abaqus_python_interface import ABQInterface

from fat_eval.weakest_link.weakest_link_evaluator import setup_weakest_link_evaluator


def calculate_probability_of_failure(odb_file, material, field, heat_treatment, element_set, instance_name,
                                     load_cases, symmetry_factor, abaqus):
    abq = ABQInterface(abaqus)

    evaluator = None
    output = []
    for load_case in load_cases:
        load_case_parameters = load_case.split(',')
        step = load_case_parameters[0]
        frame = int(load_case_parameters[1])
        load_cycles = [float(n) for n in load_case_parameters[2:]]
        stress, _, element_labels = abq.read_data_from_odb(field, odb_file, step, frame, element_set, instance_name,
                                                           get_position_numbers=True)
        if evaluator is None:
            print("Setting up weakest-link evaluation")
            evaluator = setup_weakest_link_evaluator(odb_file, heat_treatment, element_set,
                                                     instance_name, symmetry_factor, abaqus)
        data_string = [
            f"The probability of failure for the step {step} frame {frame} field {field} "
            f"at".format(step=step, frame=frame, field=field)
        ]
        print("Calculating probability of failure for {step} step frame {frame} field {field} in odb "
              "file {odb_file}".format(step=step, frame=frame, field=field, odb_file=odb_file))

        for cycles in load_cycles:
            pf = evaluator.evaluate(stress, material, cycles=cycles)
            data_string.append("N={cycles}: {pf}".format(cycles=int(cycles), pf=round(pf, 3)))
        output.append(" ".join(data_string))

    for output_string in output:
        print(output_string)
    return output
