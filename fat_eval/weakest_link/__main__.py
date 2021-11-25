import argparse
import pathlib
import sys

from fat_eval.utilities.input_file_functions import argparse_check_path, FatigueFileReadingError, read_input_file
from fat_eval.utilities.input_file_functions import OdbData

from fat_eval.weakest_link.calculate_pf import calculate_probability_of_failure
from fat_eval.weakest_link.probabilistic_sn_curve import probabilistic_sn_curve


class LoadCase:
    def __init__(self, data_string):
        data = data_string.split(",")
        self.load = float(data[0])
        self.step = data[1]
        self.frame = int(data[2])


def parse_weakest_link_file(input_file, cpus):
    valid_keywords = {
        "abaqus",
        "heat_treatment",
        "calculate_probability_of_failure",
        "create_probabilistic_sn_curve",
        "output_file"}

    mandatory_single_keywords = ["abaqus", "heat_treatment"]
    keywords = read_input_file(input_file, valid_keywords, mandatory_single_keywords=mandatory_single_keywords)

    heat_treatment = OdbData(keywords["heat_treatment"][0])
    abaqus = keywords["abaqus"][0].parameters["abq"]
    output_lines = []
    for pf_calc in keywords["calculate_probability_of_failure"]:
        pf_calc_data = OdbData(pf_calc)
        output_lines.extend(calculate_probability_of_failure(
            odb_file=pf_calc_data.odb_file_name,
            material=pf_calc.parameters["material"],
            field=pf_calc_data.field,
            heat_treatment=heat_treatment,
            element_set=pf_calc_data.element_set,
            instance_name=pf_calc_data.instance,
            symmetry_factor=float(pf_calc.parameters["symmetry_factor"]),
            load_cases=pf_calc.data,
            abaqus=abaqus
        ))

    for sn_curve in keywords["create_probabilistic_sn_curve"]:
        pf_levels = [float(pf) for pf in sn_curve.parameters["pf_levels"].split(";")]
        odb_data = OdbData(sn_curve)
        load_cases = [LoadCase(load_case_string) for load_case_string in sn_curve.data]
        span = [float(n) for n in sn_curve.parameters["span"].split(";")]
        output_lines.extend(probabilistic_sn_curve(
            odb_data=odb_data,
            material=sn_curve.parameters["material"],
            heat_treatment=heat_treatment,
            symmetry_factor=float(sn_curve.parameters["symmetry_factor"]),
            pf_levels=pf_levels,
            load_cases=load_cases,
            abaqus=abaqus,
            cpus=cpus,
            span=span
        ))

    for output in keywords["output_file"]:
        with open(pathlib.Path(output.parameters["filename"]).expanduser(), 'w+') as output_file:
            for line in output_lines:
                output_file.write(line + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run weakest-link evaluations based on abaqus odb-files")
    parser.add_argument("input_file", type=argparse_check_path,
                        help="Path to the file defining the weakest-link evaluation")
    parser.add_argument("--cpus", type=int, help="Number of cpu cores used for the simulations")
    args = parser.parse_args()
    try:
        parse_weakest_link_file(args.input_file, args.cpus)
    except FatigueFileReadingError as e:
        print("Problems when reading the file" + str(args.input_file))
        print(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
