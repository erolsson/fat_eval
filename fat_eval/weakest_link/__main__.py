import argparse
import sys

from fat_eval.utilities.input_file_functions import argparse_check_path, FatigueFileReadingError, read_input_file


def parse_weakest_link_file(input_file):
    keywords = read_input_file(input_file)
    print(keywords)

    mandatory_single_keywords = ['abaqus']
    for keyword in mandatory_single_keywords:
        if len(keywords[keyword]) != 1:
            raise FatigueFileReadingError(f"The keyword *{keyword} is mandatory and must appear only once "
                                          f"in the file".format(keyword=keyword))
    pass


def main():
    parser = argparse.ArgumentParser(description="Run effective fatigue stress evaluations based on abaqus simulations")
    parser.add_argument("input_file", type=argparse_check_path,
                        help="Path to the file defining the fatigue evaluation")
    parser.add_argument("--cpus", type=int, help="Number of cpu cores used for the simulations")
    args = parser.parse_args()
    try:
        fatigue_analysis_data = parse_weakest_link_file(args.input_file)
    except FatigueFileReadingError as e:
        print("Problems when reading the file" + str(args.input_file))
        print(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
