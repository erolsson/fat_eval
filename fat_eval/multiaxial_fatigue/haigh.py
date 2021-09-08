import numpy as np

from scipy.linalg import eigh


class Haigh:
    def __init__(self):
        self.name = 'HAIGH'
        self.variable = 'SH'

    @staticmethod
    def evaluate(stress_history, steel_data, material):
        try:
            mean_stress_sensitivities = material.mean_stress_sensitivity(steel_data)
        except AttributeError:
            raise ValueError("The Haigh effective stress criterion is not implemented for material " + material.name
                             + " as it does not have any attribute mean_stress_sensitivity")
        s = haigh(stress_history, mean_stress_sensitivities)
        try:
            su = material.uniaxial_fatigue_limit(steel_data)
        except AttributeError:
            return s
        data = np.zeros((s.shape[0], 2))
        data[:, 0] = s
        data[:, 1] = s/su
        return data


def haigh(stress_history, mean_stress_sensitivities):
    time_points = stress_history.shape[0]
    effective_stress = 0*np.array(mean_stress_sensitivities)
    for i, mean_stress_k in enumerate(mean_stress_sensitivities):

        # Calculating the maximum principal stress at each time step
        s_max = np.zeros(time_points)
        stress_tensors = []
        directions = []
        for j in range(time_points):
            stress_tensor = np.zeros((3, 3))
            np.fill_diagonal(stress_tensor, stress_history[j, i, :3])
            stress_tensor[0, 1] = stress_history[j, i, 3]
            stress_tensor[0, 2] = stress_history[j, i, 4]
            stress_tensor[1, 2] = stress_history[j, i, 5]

            stress_tensor[1, 0] = stress_tensor[0, 1]
            stress_tensor[2, 0] = stress_tensor[0, 2]
            stress_tensor[2, 1] = stress_tensor[1, 2]
            stress_tensors.append(stress_tensor)
            eigen_vals, eigen_dirs = eigh(stress_tensor)

            idx = np.argmax(eigen_vals)
            s_max[j] = eigen_vals[idx]
            directions.append(eigen_dirs[:, idx])
        max_inc = np.argmax(s_max)
        s_max = s_max[max_inc]
        n = directions[max_inc]

        min_stresses = []
        for j in range(time_points):
            if j != max_inc:
                min_stresses.append(np.dot(np.dot(n, stress_tensors[j]), n))
        sa = (s_max - min(min_stresses))/2
        sm = (s_max + min(min_stresses))/2
        effective_stress[i] = sa + mean_stress_k*sm
    return effective_stress


def main():
    from collections import namedtuple

    from fat_eval.materials.fatigue_materials import SS2506

    SteelData = namedtuple('SteelData', ['hv'])
    stress_history = np.array([[[1, 0, 0, 0, 0, 0],
                                [0, 0, 0, 2, 0, 0]],
                               [[0, 0, 0, 0, 0, 0],
                                [0, 0, 0, 1, 0, 0]]])
    steel_data = SteelData(hv=np.array([750, 750]))
    print(haigh(stress_history, steel_data, SS2506))


if __name__ == '__main__':
    main()
