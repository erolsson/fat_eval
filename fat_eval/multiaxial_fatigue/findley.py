from math import cos, sin, pi

import numpy as np

from fat_eval.materials.fatigue_materials import materials


class Findley:
    name = 'Findley'
    variables = ["SF", "SFI"]
    field_descriptions = ["Findley effective stress",
                          "Normalized effective Findley stress, SFI > 1 means fatigue failures"]

    @staticmethod
    def evaluate(stress_history, steel_data, material_name, search_grid=None):
        material = materials[material_name]
        try:
            k = material.findley_k(steel_data)
        except AttributeError:
            raise ValueError("The Findley effective stress criterion is not implemented for material " + material.name
                             + " as it does not have any attribute findley_k")
        if search_grid is None:
            search_grid = 10
        s = findley(stress_history, k, search_grid)
        try:
            sf = material.critical_findley_stress(steel_data)
        except AttributeError:
            return s
        data = np.zeros((s.shape[0], 2))
        data[:, 0] = s[:, 0]
        data[:, 1] = s[:, 0]/sf
        return data


def smallest_enclosing_circle(xp, yp, xo=None, yo=None):
    # [xc, yc, R] = smallest_enclosing_circle(X, Y)
    #
    # Purpose:
    # Calculate the Smallest Enclosing Circle of a set of points
    #
    # Input:
    # xp                       np array with X coordinates of the points, size: 1 x nr_points
    # yp                       np array with Y coordinates of the points, size: 1 x nr_points
    #
    # Input used for recursive use only:
    # xo                  array with 1, 2 or 3 X coordinates of outermost points, size: 1 x nr_outer_points
    # yo                  array with 1, 2 or 3 Y coordinates of outermost points, size: 1 x nr_outer_points
    #
    # Output:
    # xc                 X coordinate of smallest enclosing circle
    # yc                 Y coordinate of smallest enclosing circle
    # radius             radius of smallest enclosing circle
    #
    # History:
    # 14-Dec-2006 creation by FSta
    #             based on an example by Yazan Ahed (yash78@gmail.com),
    #             who based his code on a Java applet by Shripad Thite (http://heyoka.cs.uiuc.edu/~thite/mincircle/)

    # Initialize xo, yo, nr_outer_points
    if xo is None or yo is None:
        xo = []
        yo = []
        nr_outer_points = 0
    else:
        nr_outer_points = np.size(xo)

    # Compute new center point coordinates and radius
    if nr_outer_points == 0:
        xc = np.mean(xp)
        yc = np.mean(yp)
        radius = 0
    elif nr_outer_points == 1:
        xc = xo[0]
        yc = yo[0]
        radius = 0
    elif nr_outer_points == 2:
        xc = (xo[0] + xo[1])/2
        yc = (yo[0] + yo[1])/2
        radius = np.sqrt((xo[0] - xc)**2 + (yo[0] - yc)**2)

    elif nr_outer_points == 3:
        a = xo[2]**2*(yo[0] - yo[1])
        b = (xo[0]**2 + (yo[0] - yo[1])*(yo[0] - yo[2]))*(yo[1] - yo[2])
        c = xo[1]**2*(-yo[0] + yo[2])
        d = (2*(xo[2]*(yo[0] - yo[1]) + xo[0]*(yo[1] - yo[2]) + xo[1]*(-yo[0] + yo[2])))
        xc = (a + b + c)/d
        yc = (yo[1] + yo[2])/2 - (xo[2] - xo[1])/(yo[2] - yo[1])*(xc - (xo[1] + xo[2])/2)
        radius = np.sqrt((xo[0] - xc)**2 + (yo[0] - yc)**2)
        return xc, yc, radius
    else:
        print("warning... caught an unexpected mode... in elif 1")
        raise RuntimeError

    # Check if points are within the circle
    for i, _ in enumerate(xp):
        if (xp[i] - xc)**2 + (yp[i] - yc)**2 > radius**2:
            if xo is not None or yo is not None:
                if not xp[i] in xo or not yp[i] in yo:
                    if nr_outer_points == 0:
                        xo = [xp[i]]
                        yo = [yp[i]]
                    elif nr_outer_points == 1:
                        xo = [xo[0], xp[i]]
                        yo = [yo[0], yp[i]]
                    elif nr_outer_points == 2:
                        xo = [xo[0], xo[1], xp[i]]
                        yo = [yo[0], yo[1], yp[i]]
                    else:
                        print("warning... caught an unexpected mode... in elif 2")
                        raise RuntimeError

                    [xc, yc, radius] = smallest_enclosing_circle(xp[0:i + 1], yp[0:i + 1], xo, yo)

    return xc, yc, radius


def get_transform_matrix(theta_deg, phi_deg):
    # Radians
    theta_r = pi*theta_deg/180.0
    phi_r = pi*phi_deg/180.0

    # Multiaxial fatigue, Marquis, Eq 1.3 & 1.5
    a11 = cos(theta_r) * sin(phi_r)
    a12 = sin(theta_r) * sin(phi_r)
    a13 = cos(phi_r)
    a21 = -sin(theta_r)
    a22 = cos(theta_r)
    a23 = 0
    a31 = -cos(theta_r) * cos(phi_r)
    a32 = -sin(theta_r) * cos(phi_r)
    a33 = sin(phi_r)

    # Compose transformation matrix
    trans_matrix = np.array([[a11**2, a12**2, a13**2, 2*a11*a12, 2*a11*a13, 2*a13*a12],
                             [a21**2, a22**2, a23**2, 2*a21*a22, 2*a21*a23, 2*a23*a22],
                             [a31**2, a32**2, a33**2, 2*a31*a32, 2*a31*a33, 2*a33*a32],
                             [a11*a21, a12*a22, a13*a23, a11*a22 + a12*a21, a13*a21 + a11*a23, a12*a23 + a13*a22],
                             [a11*a31, a12*a32, a13*a33, a11*a32 + a12*a31, a13*a31 + a11*a33, a13*a32 + a12*a33],
                             [a21*a31, a22*a32, a23*a33, a21*a32 + a22*a31, a23*a31 + a21*a33, a22*a33 + a23*a32]])
    return trans_matrix


def findley(stress_history, k, search_grid):
    phi_space = 90
    theta_space = 180

    #     Get shape of stress matrix
    load_steps, points, no_stress_components = stress_history.shape

    # Result array [theta, phi, max_sigma_n, max_tau_amplitude, F]
    findley_vec = np.zeros((points, 1)) - 1e6

    for theta in np.arange(0, theta_space + search_grid, search_grid):
        for phi in np.arange(-phi_space, phi_space + search_grid, search_grid):

            # Compute the transformation matrix for the considered plane
            q = get_transform_matrix(theta, phi)

            # For the currently considered planed, evaluate sigma_n, tau_1, tau_2,
            # Delta_tau, F for every node for the load history (time domain)
            for j, node_s_hist_vector in enumerate(np.rollaxis(stress_history, 1)):

                # Compute shear stress and normal stresses for the load history
                s_prim = np.dot(node_s_hist_vector, q.T)
                # Evaluate the smallest enclosing circle to get the shear stress amplitude
                # (i.e. the radius of the circle)
                x, y, max_tau_amplitude = smallest_enclosing_circle(s_prim[:, 3], s_prim[:, 4])

                # Evaluate the largest normal stress on the plane for the load history
                max_sigma_n = s_prim[:, 0].max()

                # Store result if the are larger than the current value (except for first plane, then just store data)
                sf = max_tau_amplitude + k[j]*max_sigma_n
                if sf > findley_vec[j, 0]:
                    findley_vec[j, 0] = sf

    return findley_vec
