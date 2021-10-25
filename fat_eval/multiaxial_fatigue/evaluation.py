import numpy as np

from multiprocesser import multi_processer

from fat_eval.utilities.steel_data import SteelData


def evaluate_effective_stress(stress_history, material, criterion, cpus=1, search_grid=None, **steel_data):
    """
    Function for evaluating different effective fatigue stresses using multiple cpus
    :param stress_history:  3d - numpy_array with the stress history, first index represent the time, second index the
                            points and the third index the stress components
    :param steel_data:      keyword arguments for providing needed data of the steel to determine material properties
    :param material:        name of the material, used for looking up a material object to get material data from
    :param criterion        the criterion to be evaluated, current implemented criteria can be imported from
                            fat_eval.multiaxial_fatigue.criteria
    :param cpus             The number of cpus used for the evaluation
    :param search_grid      Parameter controlling the angle increment when evaluating critical plane criteria
                            Default is none which sets to a suitable value in each criterion
    :returns                A numpy array with effective fatigue stress values
    """

    if cpus > 1:
        steel_data_list = [dict() for _ in range(cpus)]
        stress_history_chuncks = np.array_split(stress_history, cpus, axis=1)
        for field_name, data in steel_data.items():
            field_data = np.array_split(data, cpus)
            for i in range(cpus):
                steel_data_list[i][field_name] = field_data[i]
        steel_data = []
        for data in steel_data_list:
            steel_data.append(SteelData(data))
        job_list = [(criterion,
                     [stress, data, material],
                     {"search_grid": search_grid}) for stress, data in zip(stress_history_chuncks, steel_data)]
        results = multi_processer(job_list, cpus=cpus, delay=0, timeout=1e9)

        return np.vstack(results)
    else:
        return criterion(stress_history, SteelData(steel_data), material)


def main():
    """
    Function for testing the functionality in-place
    :return nothing:
    """
    from fat_eval.materials.fatigue_materials import SS2506
    from fat_eval.multiaxial_fatigue.criteria import haigh
    num_points = 3000

    stress_history = np.zeros((4, num_points, 6))
    hv = np.zeros(num_points) + 750
    austenite = np.zeros(num_points)
    s = evaluate_effective_stress(stress_history, SS2506, haigh, hv=hv, austenite=austenite, cpus=1)


if __name__ == '__main__':
    main()
