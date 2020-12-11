from analysis.traj_analyzer import do_energy_analysis, calc_phys_values_from_traj
from trajopt.direct_collocation import *
from dynamics.zhukovskii_glider import *
from plot.plot import *
from trajopt.fourier_collocation import *
import json
import logging as log


def calc_and_plot_trajectory(
    phys_params,
    phys_constraints,
    travel_angle=0,
    period_guess=8,
    avg_vel_scale_guess=1,
    plot_axis="",
):

    (m, c_Dp, A, b, rho, g, AR) = phys_params
    (
        max_bank_angle,
        max_lift_coeff,
        min_lift_coeff,
        max_load_factor,
        min_height,
        max_height,
        h0,
    ) = phys_constraints

    zhukovskii_glider = RelativeZhukovskiiGlider(
        m,
        c_Dp,
        A,
        b,
        rho,
        g,
        max_bank_angle,
        max_lift_coeff,
        min_lift_coeff,
        max_load_factor,
        min_height,
        max_height,
        h0,
    )

    # Print performance params
    Lam = zhukovskii_glider.calc_opt_glide_ratio(AR, c_Dp)
    Th = zhukovskii_glider.calc_opt_glide_angle(AR, c_Dp)
    V_opt = zhukovskii_glider.calc_opt_glide_speed(AR, c_Dp, m, A, b, rho, g)
    V_l = zhukovskii_glider.calc_opt_level_glide_speed(AR, c_Dp, m, A, b, rho, g)
    T = zhukovskii_glider.get_char_time()

    log.info(
        " ### Running dircol with:"
        + "\n"
        + "\tLam: {0}\n\tTh: {1}\n\tV_opt: {2}\n\tV_l: {3}\n\tT: {4}".format(
            Lam, Th, V_opt, V_l, T
        )
    )

    (
        found_solution,
        solution_details,
        solution_trajectory,
        _,
    ) = direct_collocation_relative(
        zhukovskii_glider,
        travel_angle,
        period_guess=period_guess,
        avg_vel_scale_guess=avg_vel_scale_guess,
    )

    avg_speed, period = solution_details
    # Solution in ENU frame
    times, x_knots_ENU, u_knots_ENU = solution_trajectory

    # Calc NED frame trajectory for physical calcs
    x_knots_NED = np.zeros(x_knots_ENU.shape)
    u_knots_NED = np.zeros(u_knots_ENU.shape)

    x_knots_NED[:, 0] = x_knots_ENU[:, 1]
    x_knots_NED[:, 1] = x_knots_ENU[:, 0]
    x_knots_NED[:, 2] = -x_knots_ENU[:, 2]
    x_knots_NED[:, 3] = x_knots_ENU[:, 4]
    x_knots_NED[:, 4] = x_knots_ENU[:, 3]
    x_knots_NED[:, 5] = -x_knots_ENU[:, 5]

    u_knots_NED[:, 0] = u_knots_ENU[:, 1]
    u_knots_NED[:, 1] = u_knots_ENU[:, 0]
    u_knots_NED[:, 2] = -u_knots_ENU[:, 2]

    # Calculate physical quantities in trajectory
    (
        phi_knots,
        gamma_knots,
        psi_knots,
        c_l_knots,
        n_knots,
    ) = calc_phys_values_from_traj(
        zhukovskii_glider, phys_params, x_knots_NED, u_knots_NED
    )
    # Unpack trajectory constraints
    (
        max_bank_angle,
        max_lift_coeff,
        min_lift_coeff,
        max_load_factor,
        min_height,
        max_height,
        h0,
        min_travelled_distance,
    ) = zhukovskii_glider.get_constraints()

    # Energy analysis
    soaring_power, vel_knots = do_energy_analysis(
        times, x_knots_NED, u_knots_NED, phys_params
    )
    height_knots = x_knots_ENU[:, 2]
    abs_vel_knots = np.sqrt(np.diag(vel_knots.dot(vel_knots.T)))

    # Plotting
    plot_glider_pos(
        x_knots_ENU,
        u_knots_ENU,
        period,
        travel_angle,
        draw_soaring_power=False,
        soaring_power=soaring_power,
        plot_axis=plot_axis,
    )
    plot_glider_angles(
        times,
        gamma_knots,
        psi_knots,
        phi_knots,
        max_bank_angle,
    )
    plot_glider_height_and_vel(
        times, abs_vel_knots, height_knots, min_height, max_height
    )
    plot_glider_phys_quantities(
        times,
        u_knots_ENU,
        c_l_knots,
        n_knots,
        height_knots,
        max_lift_coeff,
        min_lift_coeff,
        max_load_factor,
        min_height,
        max_height,
    )
    plt.show()
    return


# TODO this is unfinished and currently not working
def do_collocation_w_fourier():
    zhukovskii_glider = ZhukovskiiGlider()
    prog = FourierCollocationProblem(
        zhukovskii_glider.continuous_dynamics_dimless,
        zhukovskii_glider.get_constraints_dimless(),
    )
    prog.get_solution()
    return


def show_sweep_result():
    # Load data from files

    solution_avg_speeds = dict()
    solution_periods = dict()
    with open("./results/plots/sweep_results_speeds", "r") as f:
        solution_avg_speeds = json.load(f)
        f.close()
    with open("./results/plots/sweep_results_periods", "r") as f:
        solution_periods = json.load(f)
        f.close()

    plot_sweep_polar(solution_avg_speeds, solution_periods)
    plt.show()


def sweep_calculation_for_period(
    phys_params, start_angle, period_guess, avg_vel_scale_guess=1, n_angles=9
):
    (m, c_Dp, A, b, rho, g, AR) = phys_params
    zhukovskii_glider = RelativeZhukovskiiGlider(m, c_Dp, A, b, rho, g)

    # Print performance params
    Lam = zhukovskii_glider.calc_opt_glide_ratio(AR, c_Dp)
    Th = zhukovskii_glider.calc_opt_glide_angle(AR, c_Dp)
    V_opt = zhukovskii_glider.calc_opt_glide_speed(AR, c_Dp, m, A, b, rho, g)
    V_l = zhukovskii_glider.calc_opt_level_glide_speed(AR, c_Dp, m, A, b, rho, g)
    T = zhukovskii_glider.get_char_time()

    log.info(
        " ### Running dircol sweep with:\n"
        + "\tLam: {0}\n\tTh: {1}\n\tV_opt: {2}\n\tV_l: {3}\n\tT: {4}".format(
            Lam, Th, V_opt, V_l, T
        )
    )

    angle_increment = 2 * np.pi / n_angles

    travel_angles = np.hstack(
        [
            np.arange(start_angle, 2 * np.pi, angle_increment),
            np.arange(0, start_angle, angle_increment),
        ]
    )

    solution_avg_speeds = dict()
    solution_periods = dict()

    # Initial guess
    period_initial_guess = period_guess
    avg_speed_initial_guess = avg_vel_scale_guess * V_l
    next_initial_guess = None

    # Run a sweep search
    for travel_angle in travel_angles[0:]:
        found_solution = False
        reduced_period = period_initial_guess
        reduced_avg_vel = avg_speed_initial_guess

        # Decrease the avg vel every iteration until a solution is found
        while not found_solution:
            # Obtain solution with straight line as initial guess
            (
                found_solution,
                solution_details,
                solution_trajectory,
                potential_initial_guess,
            ) = direct_collocation_relative(
                zhukovskii_glider,
                travel_angle,
                period_guess=reduced_period,
                avg_vel_guess=reduced_avg_vel,
                initial_guess=next_initial_guess,
            )

            # Solution not found
            if not found_solution:
                #    # Reduce avg_vel
                #    reduced_avg_vel *= 0.95
                #    log.warning(" No solution found, decreasing avg_vel")
                #    next_initial_guess = None

                # Reduce period
                reduced_period *= 0.95
                log.warning(" No solution found, decreasing period")

                # Start using straight line if initial guess fails too many times
                if reduced_period < 4.0:
                    next_initial_guess = None
                    reduced_period = period_initial_guess
                continue

                # Stop searching and give up
                if reduced_avg_vel <= 0.3:
                    solution_avg_speeds[travel_angle] = -1
                    solution_periods[travel_angle] = -1
                    log.error(" Could not find a solution with avg_vel reduction")
                    break

            # Found a solution
            avg_speed, period, limited_by_time_step = solution_details
            next_initial_guess = potential_initial_guess

            # Check if it was limited by step size
            if not limited_by_time_step == "false":
                reduced_avg_vel = avg_speed_initial_guess
                # Increase or decrease period if limited by step size
                if limited_by_time_step == "upper":
                    log.warning(" Time step at max, increasing period")
                    reduced_period *= 1.1
                elif limited_by_time_step == "lower":
                    log.warning(" Time step at min, decreasing period")
                    reduced_period *= 0.9
                # Do a rerun
                found_solution = False
                continue

        # Found solution and it is not limited by step size
        # then save values
        initial_guess = next_initial_guess
        avg_speed, period, _ = solution_details
        solution_avg_speeds[travel_angle] = avg_speed
        solution_periods[travel_angle] = period

        with open("./results/plots/sweep_results_speeds", "w") as f:
            f.write(json.dumps(solution_avg_speeds))
            f.close()

        with open("./results/plots/sweep_results_periods", "w") as f:
            f.write(json.dumps(solution_periods))
            f.close()

    return


def sweep_calculation_naive(phys_params):
    (m, c_Dp, A, b, rho, g, AR) = phys_params
    zhukovskii_glider = RelativeZhukovskiiGlider(m, c_Dp, A, b, rho, g)
    V_l = zhukovskii_glider.calc_opt_level_glide_speed(AR, c_Dp, m, A, b, rho, g)

    n_angles = 9
    angle_increment = 2 * np.pi / n_angles
    psi_start = np.pi / 2

    travel_angles = np.hstack(
        [
            np.arange(psi_start, 2 * np.pi, angle_increment),
            np.arange(0, psi_start, angle_increment),
        ]
    )

    solution_avg_speeds = dict()
    solution_periods = dict()

    # Obtain an initial guess
    period_initial_guess = 8  # NOTE can be tuned
    avg_speed_initial_guess = 2 * V_l  # NOTE can be tuned

    (
        found_solution,
        solution_details,
        solution_trajectory,
        next_initial_guess,
    ) = direct_collocation_relative(
        zhukovskii_glider,
        travel_angles[0],
        period_guess=period_initial_guess,
        avg_vel_guess=avg_speed_initial_guess,
    )
    if not found_solution:
        solution_avg_speeds[travel_angles[0]] = -1
        solution_periods[travel_angles[0]] = -1
    else:
        avg_speed, period = solution_details
        solution_avg_speeds[travel_angles[0]] = avg_speed
        solution_periods[travel_angles[0]] = period
        initial_guess = next_initial_guess

    # Run a sweep search
    for travel_angle in travel_angles[1:]:
        # Obtain solution with previous solution as initial guess
        (
            found_solution_from_prev,
            solution_details_from_prev,
            solution_trajectory_from_prev,
            next_initial_guess_from_prev,
        ) = direct_collocation_relative(
            zhukovskii_glider,
            travel_angle,
            initial_guess=initial_guess,
        )

        # Obtain solution with straight line as initial guess
        (
            found_solution_from_line,
            solution_details_from_line,
            solution_trajectory_from_line,
            next_initial_guess_from_line,
        ) = direct_collocation_relative(
            zhukovskii_glider,
            travel_angle,
            period_guess=period_initial_guess,
            avg_vel_guess=avg_speed_initial_guess,
        )

        # Use the max solution
        avg_speed_from_prev = solution_details_from_prev
        avg_speed_from_line = solution_details_from_line
        if avg_speed_from_prev > avg_speed_from_line:
            found_solution = found_solution_from_prev
            solution_details = solution_details_from_prev
            solution_trajectory = solution_trajectory_from_prev
            next_initial_guess = next_initial_guess_from_prev
        else:
            found_solution = found_solution_from_line
            solution_details = solution_details_from_line
            solution_trajectory = solution_trajectory_from_line
            next_initial_guess = next_initial_guess_from_line

        # Reduce the period and avg_speed every time until solution is found
        if not found_solution:
            reduced_period = period_initial_guess
            reduced_avg_vel = avg_speed_initial_guess

            while not found_solution:
                # TODO cleanup
                # Do a line search over period and avg velocity
                if not found_solution:
                    reduced_period *= 1
                    reduced_avg_vel *= 0.8

                (
                    found_solution,
                    solution_details,
                    solution_trajectory,
                    next_initial_guess,
                ) = direct_collocation_relative(
                    zhukovskii_glider,
                    travel_angle,
                    period_guess=reduced_period,
                    avg_vel_guess=reduced_avg_vel,
                )

                # Stop searching and give up
                tol = 0.5
                if reduced_avg_vel <= tol:
                    solution_avg_speeds[travel_angle] = -1
                    solution_periods[travel_angle] = -1
                    break

        # Save trajectory and values as initial guess for next travel_angle

        # initial_guess = next_initial_guess # NOTE currently not using previous trajectory as initial guess
        # TODO, first check previous trajectory!
        avg_speed, period = solution_details
        solution_avg_speeds[travel_angle] = avg_speed
        solution_periods[travel_angle] = period

        with open("./results/sweep_results_speeds", "w+") as f:
            f.write(json.dumps(solution_avg_speeds))
            f.close()

        with open("./results/sweep_results_periods", "w+") as f:
            f.write(json.dumps(solution_periods))
            f.close()

    return
