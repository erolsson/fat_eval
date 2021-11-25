import numpy as np

from abaqus_python_interface import ABQInterface

from multiprocesser import multi_processer

from fat_eval.weakest_link.weakest_link_evaluator import setup_weakest_link_evaluator, WeakestLinkEvaluator


def probabilistic_sn_curve(odb_data, material, heat_treatment,
                           pf_levels, load_cases, symmetry_factor, span, abaqus, cpus=None):
    print("Setting up weakest-link evaluation")
    evaluator = setup_weakest_link_evaluator(odb_data.odb_file_name, heat_treatment, odb_data.element_set,
                                             odb_data.instance, symmetry_factor, abaqus)
    if cpus is None:
        cpus = 1
    abq = ABQInterface(abaqus)
    read_jobs = []
    for load_case in load_cases:
        kw_args = {
            "odb_file_name": odb_data.odb_file_name,
            "field_id": "SF",
            "step_name": load_case.step,
            "frame_number": load_case.frame,
            "set_name": odb_data.element_set,
            "instance_name": odb_data.instance
        }
        read_jobs.append((abq.read_data_from_odb, [], kw_args))
    print("Reading stress states")
    stress_states = multi_processer(read_jobs, timeout=1e9, delay=0., cpus=min(cpus, len(read_jobs)))

    output = ["Probabilistic SN-curve"]
    heading = ["Load"]
    heading.extend(["N at pf = " + str(int(pf*100)) + " %" for pf in pf_levels])
    output.append(", ".join(heading))

    life_jobs = []

    for stress_state in stress_states:
        for pf in pf_levels:
            kw_args = {
                "stress_state": stress_state,
                "evaluator": evaluator,
                "pf": pf,
                "span": span,
                "material": material
            }
            life_jobs.append([calculate_life, [], kw_args])
    print("Evaluating SN-curve")
    lives = multi_processer(life_jobs, timeout=1e9, delay=0., cpus=min(cpus, len(life_jobs)))

    job = 0
    for stress_state, load_case in zip(stress_states, load_cases):
        output_data = [str(load_case.load)]
        for _ in pf_levels:
            output_data.append(str(int(lives[job])))
            job += 1
        output.append(", ".join(output_data))

    for output_string in output:
        print(output_string)
    return output


def calculate_life(stress_state, evaluator, pf, span, material):
    def calculate_pf(cycles):
        return evaluator.evaluate(stress_state, material, cycles=np.exp(cycles)) - pf

    n1 = np.log(span[0])
    n2 = np.log(span[1])
    n = (n1 + n2)/2
    while abs(n2 - n1) > 1e-3:
        f = calculate_pf(n)
        if f == 0:
            return np.exp(n)
        elif calculate_pf(n1)*f < 0:
            n2 = n
        else:
            n1 = n
        n = (n1 + n2) / 2
    return np.exp(n)





