import argparse
import sys

from fat_eval.utilities.input_file_functions import argparse_check_path, FatigueFileReadingError, read_input_file
from fat_eval.utilities.input_file_functions import OdbData

from calculate_pf import calculate_probability_of_failure


def parse_weakest_link_file(input_file):
    keywords = read_input_file(input_file)

    mandatory_single_keywords = ["abaqus", "heat_treatment"]
    for keyword in mandatory_single_keywords:
        if len(keywords[keyword]) != 1:
            raise FatigueFileReadingError(f"The keyword *{keyword} is mandatory and must appear only once "
                                          f"in the file".format(keyword=keyword))
    heat_treatment = OdbData(keywords["heat_treatment"][0])
    abaqus = keywords["abaqus"][0].parameters["abq"]
    for pf_calc in keywords["calculate_probability_of_failure"]:
        pf_calc_data = OdbData(pf_calc)
        calculate_probability_of_failure(
            odb_file=pf_calc_data.odb_file_name,
            material=pf_calc.parameters["material"],
            field=pf_calc_data.field,
            heat_treatment=heat_treatment,
            element_set=pf_calc_data.element_set,
            instance_name=pf_calc_data.instance,
            symmetry_factor=float(pf_calc.parameters["symmetry_factor"]),
            load_cases=pf_calc.data,
            abaqus=abaqus)


def main():
    parser = argparse.ArgumentParser(description="Run effective fatigue stress evaluations based on abaqus simulations")
    parser.add_argument("input_file", type=argparse_check_path,
                        help="Path to the file defining the fatigue evaluation")
    parser.add_argument("--cpus", type=int, help="Number of cpu cores used for the simulations")
    args = parser.parse_args()
    try:
        parse_weakest_link_file(args.input_file)
    except FatigueFileReadingError as e:
        print("Problems when reading the file" + str(args.input_file))
        print(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
