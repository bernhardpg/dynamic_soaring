import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation

from dynamics.wind_models import *

plot_location = "./results/plots/"


def plot_energies(times, E_tot, E_kin, E_pot):
    max_energy = max(max(E_tot), max(E_kin), max(E_pot))
    fig, axes = plt.subplots(3, 1)
    axes[0].plot(times, E_tot)
    axes[0].set_title("Total energy")
    axes[0].set_ylim(0, max_energy)

    axes[1].plot(times, E_kin)
    axes[1].set_title("Kinetic energy")
    axes[1].set_ylim(0, max_energy)

    axes[2].plot(times, E_pot)
    axes[2].set_title("Potential energy")
    axes[2].set_ylim(0, max_energy)
    return


def _plot_wind_profile(ax, wind_function, h_max=20):
    dh_arrows = 2.5

    h = np.arange(0.03, h_max, 0.05)
    ax.plot(wind_function(h), h, color="black")

    arrow_start = np.arange(dh_arrows, h_max, dh_arrows)
    wind_strengths = wind_function(arrow_start)
    zeros = np.zeros(arrow_start.shape[0])
    ax.quiver(
        zeros, arrow_start, wind_strengths, zeros, units="xy", scale=1, color="tab:blue"
    )
    ax.set_aspect("equal")
    ax.set_xlim(0, 20)
    ax.set_ylim(0, h_max)
    # ax.grid()


def plot_wind_profiles():
    fig, axs = plt.subplots(1, 4, constrained_layout=True)
    fig.set_size_inches(10, 3)
    wind_profiles = [
        linear_wind_model,
        log_wind_model,
        exp_wind_model,
        logistic_wind_model,
    ]
    wind_profile_names = [
        "Linear",
        "Logarithmic",
        "Exponential",
        "Logistic",
    ]
    for i in range(len(wind_profiles)):
        ax = axs[i]
        _plot_wind_profile(ax, wind_profiles[i])
        ax.set_title(wind_profile_names[i])
        if i == 0:
            ax.set_xlabel("Wind strength [m/s]")
            ax.set_ylabel("Height [m]")

    plt.savefig(plot_location + "wind_models.eps", bbox_inches="tight")
    return


def plot_glider_angles(t, gamma_trj, phi_trj, psi_trj):
    plt.subplots(figsize=(5, 4))

    plt.subplot(3, 1, 1)
    plt.plot(t, gamma_trj * 180 / np.pi)
    plt.xlabel("time [s]")
    plt.ylabel("deg")
    plt.title("Rel flight path angle")

    plt.subplot(3, 1, 2)
    plt.plot(t, phi_trj * 180 / np.pi)
    plt.xlabel("time [s]")
    plt.title("Bank angle")
    plt.ylabel("deg")

    plt.subplot(3, 1, 3)
    plt.plot(t, psi_trj * 180 / np.pi)
    plt.xlabel("time [s]")
    plt.title("Heading angle")
    plt.ylabel("deg")

    plt.savefig(plot_location + "attitude.pdf", bbox_inches="tight", pad_inches=0)

    return


def plot_glider_input(t, u_trj, c_l_trj, phi_trj, n_trj):
    plt.subplots(figsize=(5, 4))

    plt.subplot(3, 1, 1)
    plt.plot(t, c_l_trj)
    plt.xlabel("time [s]")
    plt.title("Lift coeff")
    plt.ylabel("c_L")

    plt.subplot(3, 1, 2)
    plt.plot(t, phi_trj * 180 / np.pi)
    plt.xlabel("time [s]")
    plt.title("Bank angle")
    plt.ylabel("deg")

    plt.subplot(3, 1, 3)
    plt.plot(t, n_trj)
    plt.xlabel("time [s]")
    plt.title("Load factor")
    plt.ylabel("")

    plt.savefig(plot_location + "input.pdf", bbox_inches="tight", pad_inches=0)
    return


def plot_glider_pos(x_trj, u_trj, travel_angle):
    fig = plt.figure()
    ax = fig.gca(projection="3d")

    pos_trj = x_trj[:, 0:3]
    axis_limits = np.array(
        [
            [min(pos_trj[:, 0]), max(pos_trj[:, 0])],
            [min(pos_trj[:, 1]), max(pos_trj[:, 1])],
            [min(pos_trj[:, 2]), max(pos_trj[:, 2])],
        ]
    )
    # Draw projections on walls
    # _draw_trajectory_projection(pos_trj, axis_limits, ax, axis="x")
    _draw_trajectory_projection(pos_trj, axis_limits, ax, axis="y")
    _draw_trajectory_projection(pos_trj, axis_limits, ax, axis="z")

    # Draw trajectory
    _draw_pos_trajectory(pos_trj, travel_angle, axis_limits, ax)
    _draw_direction_vector(x_trj[0, :], travel_angle, axis_limits, ax)
    _draw_wind_field(axis_limits, ax)
    _draw_gliders(x_trj, u_trj, ax)
    _set_real_aspect_ratio(axis_limits, ax)

    # ax.view_init(30, 50) # TODO change this to rotate plot
    fig.set_size_inches((13, 10))
    plt.savefig(plot_location + "trajectory.pdf", bbox_inches="tight", pad_inches=0)
    return


def _draw_trajectory_projection(pos_trj, axis_limits, ax, axis="x"):
    N = pos_trj.shape[0]
    if axis == "x":
        min_axis_value = axis_limits[0, 0]
        traj_plot = ax.plot(
            np.ones(N) * min_axis_value,
            pos_trj[:, 1],
            pos_trj[:, 2],
            "--k",
            alpha=0.5,
            linewidth=0.7,
        )

    if axis == "y":
        min_axis_value = axis_limits[1, 1]
        traj_plot = ax.plot(
            pos_trj[:, 0],
            np.ones(N) * min_axis_value,
            pos_trj[:, 2],
            "--k",
            alpha=0.5,
            linewidth=0.7,
        )
    if axis == "z":
        min_axis_value = np.zeros(N)
        traj_plot = ax.plot(
            pos_trj[:, 0],
            pos_trj[:, 1],
            np.ones(N) * min_axis_value,
            "--k",
            alpha=0.5,
            linewidth=0.7,
        )


# Params:
# x_trj.shape = (N, 3)
# x_trj = [x, y, z]
# TODO continue with adding figure of glider
# TODO continue with only plotting wind at one point
def _draw_pos_trajectory(pos_trj, travel_angle, axis_limits, ax):
    (x_min, x_max), (y_min, y_max), (z_min, z_max) = axis_limits
    x_diff = np.abs(x_min - x_max)
    y_diff = np.abs(y_min - y_max)
    z_diff = np.abs(z_min - z_max)

    traj_plot = ax.plot(
        pos_trj[:, 0],
        pos_trj[:, 1],
        pos_trj[:, 2],
        color="tab:red",
        linewidth=1,
    )

    # Plot start position
    x0 = pos_trj[0, :]
    ax.scatter(x0[0], x0[1], 0, color="tab:green")

    # Set labels
    ax.set_xlabel(
        "East [m]", labelpad=40
    )  # TODO these padds must be adjusted for each plot
    ax.set_ylabel("North [m]", labelpad=0)
    ax.set_zlabel("Height [m]")

    # Set ticks
    x_ticks_spacing = 20 if x_diff >= 40 else 5
    y_ticks_spacing = 20 if y_diff >= 40 else 5
    z_ticks_spacing = 10 if z_diff >= 10 else 5

    ax.xaxis.set_ticks(
        np.arange(
            np.ceil(x_min / x_ticks_spacing) * x_ticks_spacing, x_max, x_ticks_spacing
        )
    )
    ax.yaxis.set_ticks(
        np.arange(
            np.ceil(y_min / y_ticks_spacing) * y_ticks_spacing, y_max, y_ticks_spacing
        )
    )
    ax.zaxis.set_ticks(np.arange(0, z_max, z_ticks_spacing))


def _draw_direction_vector(x0, travel_angle, axis_limits, ax):
    (x_min, x_max), (y_min, y_max), (z_min, z_max) = axis_limits
    x_diff = np.abs(x_min - x_max)
    y_diff = np.abs(y_min - y_max)

    dir_vector = np.array([np.sin(travel_angle), np.cos(travel_angle)])
    dir_vector_length = np.sqrt(x_diff / 10 ** 2 + y_diff / 10 ** 2) * 15
    ax.quiver(
        x0[0],
        x0[1],
        0,
        dir_vector[0],
        dir_vector[1],
        0,
        color="tab:green",
        label="Desired direction",
        length=dir_vector_length,
        linewidth=1,
        arrow_length_ratio=0.2,
    )


def _draw_wind_field(axis_limits, ax):
    (x_min, x_max), (y_min, y_max), (z_min, z_max) = axis_limits
    x_diff = np.abs(x_min - x_max)
    y_diff = np.abs(y_min - y_max)
    z_diff = np.abs(z_min - z_max)

    dz = 2.5

    # Plot wind field
    xs = np.arange(np.ceil(x_min / 20) * 20, x_max, 40)  # Arrows every 40 meters
    ys = np.ones(4) * y_max
    zs = np.arange(0, z_max, dz)
    zs[0] = z_min

    X, Y, Z = np.meshgrid(xs, ys, zs)
    u, v, w = get_wind_field(X, Y, Z)
    ax.quiver(
        X,
        Y,
        Z,
        u,
        v,
        w,
        length=1,  # np.sqrt(dx ** 2 + dy ** 2) / 15,
        linewidth=0.3,
        arrow_length_ratio=0.1,
        color="tab:blue",
        alpha=0.7,
    )


def _set_real_aspect_ratio(axis_limits, ax):
    (x_min, x_max), (y_min, y_max), (z_min, z_max) = axis_limits
    x_diff = np.abs(x_min - x_max)
    y_diff = np.abs(y_min - y_max)
    z_diff = np.abs(z_min - z_max)

    origin = np.mean(axis_limits, axis=1)
    radius = 0.5 * np.max(np.abs(axis_limits[:, 1] - axis_limits[:, 0]))

    x, y, z = origin
    ax.set_xlim3d([x - x_diff / 2, x + x_diff / 2])
    ax.set_ylim3d([y - y_diff / 2, y + y_diff / 2])
    ax.set_zlim3d([0, z_diff])

    ax.set_box_aspect([x_diff, y_diff, z_diff])


def _draw_gliders(x_trj, u_trj, ax):
    N = x_trj.shape[0]
    N_gliders = 10
    indices = np.linspace(0, N - 1, N_gliders, dtype=int)

    for i in indices:
        # if i == 0: continue # Do not plot first glider
        x = x_trj[i, :]
        c = u_trj[i, :]
        F, RF, RB, LF, LB = _get_glider_corners(x, c)
        vertices = np.vstack([F, RF, RB, LB, LF, F]).T

        # Draw polygons
        ax.add_collection3d(
            Poly3DCollection(
                [vertices.T.tolist()], linewidths=1, facecolors="orange", alpha=0.8
            )
        )
        ax.add_collection3d(
            Line3DCollection([vertices.T.tolist()], linewidths=1, colors="k")
        )

    return


def _get_glider_corners(x, c):
    sweep = 0.7
    tip_chord = 0.3
    b = 3.03
    dist_cg_front = 0.5
    # TODO chord =

    # Extract values
    p = x[0:3]
    v_r = x[3:6]
    h = p[2]

    # Define glider corners
    scale = 2
    com_to_F = np.array([dist_cg_front, 0, 0]) * scale
    com_to_RF = np.array([dist_cg_front - sweep, b / 2, 0]) * scale
    com_to_RB = np.array([dist_cg_front - sweep - tip_chord, b / 2, 0]) * scale
    com_to_LF = np.array([com_to_RF[0], -com_to_RF[1], com_to_RF[2]])
    com_to_LB = np.array([com_to_RB[0], -com_to_RB[1], com_to_RB[2]])

    # Calculate heading
    # alpha = zhukovskii_glider.calc_rel_flight_path_angle(v_r)  # TODO fix this

    j_body = c / np.linalg.norm(c)  # j unit vector in body frame
    i_body = v_r / np.linalg.norm(v_r)  # i unit vec in stability frame
    # TODO rotate by angle of attack??
    #    i_body = np.array(
    #        [
    #            [np.cos(alpha), 0, np.sin(alpha)],
    #            [0, 1, 0],
    #            [-np.sin(alpha), 0, np.cos(alpha)],
    #        ]
    #    ).dot(
    #        i_stability
    #    )  # Rotate i_stab by alpha around y axis to get i_body
    k_body = np.cross(j_body, i_body)
    R_ned_to_body = np.stack((i_body, j_body, k_body), axis=1)

    # Rotate glider vectors by rotation matrix
    rotated_com_to_F = R_ned_to_body.dot(com_to_F)
    rotated_com_to_RF = R_ned_to_body.dot(com_to_RF)
    rotated_com_to_RB = R_ned_to_body.dot(com_to_RB)
    rotated_com_to_LF = R_ned_to_body.dot(com_to_LF)
    rotated_com_to_LB = R_ned_to_body.dot(com_to_LB)

    # Calculate glider corners
    F = p + rotated_com_to_F  # Front
    RF = p + rotated_com_to_RF  # Right front
    RB = p + rotated_com_to_RB  # Right back
    LF = p + rotated_com_to_LF  # Left front
    LB = p + rotated_com_to_LB  # Left back

    # Plot all corners as vectors without arrowheads
    return F, RF, RB, LF, LB


# TODO old from here


def polar_plot_avg_velocities(avg_velocities):
    lists = sorted(avg_velocities.items())
    x, y = zip(*lists)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="polar")
    ax.plot(x, y)
    ax.set_title("Achievable speeds")
    fig.savefig("./animations/polar_plot.png")

    return


# TODO OUTDATED with new relative model
def save_trajectory_gif(zhukovskii_glider, traj, travel_angle):
    ## ANIMATION FILE SETTINGS
    filepath = "./animations/"
    filename = "glider_psi_{0}_degs.mp4".format(int(travel_angle * (180 / np.pi)))
    Writer = animation.writers["ffmpeg"]
    writer = Writer(fps=int(1 / dt), metadata=dict(artist="Me"), bitrate=1800)

    # SETUP FIGURE
    fig = plt.figure(figsize=(13, 10))
    ax = fig.gca(projection="3d")

    t, x_trj, u_trj = traj
    N = x_trj.shape[0]
    dt = times[1] - times[0]
    T = 1 / dt

    x0 = x_trj[0, :]

    x_min = min(x_trj[:, 0])
    x_max = max(x_trj[:, 0])
    y_min = min(x_trj[:, 1])
    y_max = max(x_trj[:, 1])
    z_min = 0
    z_max = max(x_trj[:, 2])

    # Spacing for wind field
    dx = np.abs(x_min - x_max)
    dy = np.abs(y_min - y_max)
    dz = np.abs(z_min - z_max)
    max_axis = max([dx, dy, dz])

    x, y, z = np.meshgrid(
        # (-min, max, step_length)
        np.arange(x_min, x_min + max_axis, max_axis / 5 - 1),
        np.arange(y_min, y_min + max_axis, max_axis / 5 - 1),
        np.arange(z_min, z_min + max_axis, max_axis / 5 - 1),
    )
    u, v, w = get_wind_field(x, y, z)

    # Define three points on glider, defined in body frame
    scale = 8
    com_to_wing_vec = np.array([0, zhukovskii_glider.b / 2, 0]) * scale
    com_to_front_vec = np.array([zhukovskii_glider.glider_length, 0, 0]) * scale

    pos = ax.scatter([], [], [])
    w1 = ax.quiver([], [], [], [], [], [])
    w2 = ax.quiver([], [], [], [], [], [])
    w3 = ax.quiver([], [], [], [], [], [])

    def init():
        ax.set_zlim(0, max_axis)
        ax.set_xlim(x_min, x_min + max_axis)
        ax.set_ylim(y_min, y_min + max_axis)
        ax.plot(x_trj[:, 0], x_trj[:, 1], x_trj[:, 2], linewidth=0.7)  # Plot trajectory
        ax.scatter(x0[0], x0[1], x0[2])  # Plot initial position

        # plot wind field
        ax.quiver(
            x,
            y,
            z,
            u,
            v,
            w,
            length=1,
            linewidth=0.5,
            arrow_length_ratio=0.2,
            pivot="middle",
            color="tab:blue",
        )

        # Plot direction vector
        dir_vector = np.array([np.sin(travel_angle), np.cos(travel_angle)])
        ax.quiver(
            x0[0],
            x0[1],
            x0[2],
            dir_vector[0],
            dir_vector[1],
            0,
            color="green",
            label="Desired direction",
            length=10,
            arrow_length_ratio=0.1,
        )

        return (
            pos,
            w1,
            w2,
            w3,
        )

    def update(frame):
        plt.cla()
        init()
        time, x, u = frame

        com = x[0:3]  # Center of mass
        c = u[:]
        pos = ax.scatter(
            com[0], com[1], com[2], color="red", s=0.5
        )  # plot current position

        vel_rel = zhukovskii_glider.get_vel_rel(x[:])
        alpha = zhukovskii_glider.get_angle_of_attack(x[:], u[:])

        j_body = c / np.linalg.norm(c)  # j unit vector in body frame

        i_stability = vel_rel / np.linalg.norm(vel_rel)  # i unit vec in stability frame
        i_body = np.array(
            [
                [np.cos(alpha), 0, np.sin(alpha)],
                [0, 1, 0],
                [-np.sin(alpha), 0, np.cos(alpha)],
            ]
        ).dot(
            i_stability
        )  # Rotate i_stab by alpha around y axis to get i_body
        # TODO which way rotate by alpha here??
        k_body = np.cross(j_body, i_body)

        R_ned_to_body = np.stack((i_body, j_body, k_body), axis=1)
        curr_com_to_wing_vec = R_ned_to_body.dot(com_to_wing_vec)
        curr_com_to_front_vec = R_ned_to_body.dot(com_to_front_vec)

        # Draw glider
        # wing line
        w1 = ax.quiver(
            com[0] - curr_com_to_wing_vec[0],
            com[1] - curr_com_to_wing_vec[1],
            com[2] - curr_com_to_wing_vec[2],
            curr_com_to_wing_vec[0] * 2,
            curr_com_to_wing_vec[1] * 2,
            curr_com_to_wing_vec[2] * 2,
            linewidth=2,
            arrow_length_ratio=0.0,
            color="black",
        )
        # left wing to front
        w2 = ax.quiver(
            com[0] - curr_com_to_wing_vec[0],
            com[1] - curr_com_to_wing_vec[1],
            com[2] - curr_com_to_wing_vec[2],
            curr_com_to_wing_vec[0] + curr_com_to_front_vec[0],
            curr_com_to_wing_vec[1] + curr_com_to_front_vec[1],
            curr_com_to_wing_vec[2] + curr_com_to_front_vec[2],
            linewidth=2,
            arrow_length_ratio=0.0,
            color="black",
        )
        # left wing to front
        w3 = ax.quiver(
            com[0] + curr_com_to_wing_vec[0],
            com[1] + curr_com_to_wing_vec[1],
            com[2] + curr_com_to_wing_vec[2],
            -curr_com_to_wing_vec[0] + curr_com_to_front_vec[0],
            -curr_com_to_wing_vec[1] + curr_com_to_front_vec[1],
            -curr_com_to_wing_vec[2] + curr_com_to_front_vec[2],
            linewidth=2,
            arrow_length_ratio=0.0,
            color="black",
        )

        # Plot x axis
        ax.quiver(
            com[0],
            com[1],
            com[2],
            i_body[0],
            i_body[1],
            i_body[2],
            linewidth=2,
            color="red",
            length=scale * 3,
        )
        # Plot y axis
        ax.quiver(
            com[0],
            com[1],
            com[2],
            j_body[0],
            j_body[1],
            j_body[2],
            linewidth=2,
            color="yellow",
            length=scale * 3,
        )
        # Plot z axis
        ax.quiver(
            com[0],
            com[1],
            com[2],
            -k_body[0],
            -k_body[1],
            -k_body[2],
            linewidth=2,
            color="green",
            length=scale * 3,
        )

        return (
            pos,
            w1,
            w2,
            w3,
        )

    ani = FuncAnimation(
        fig, update, frames=list(zip(times, x_trj, u_trj)), init_func=init, blit=True
    )

    ## SAVE ANIMATION
    ani.save(filepath + filename, writer=writer)
    print("Saved animation as: {0}".format(filename))
    plt.close()

    return
