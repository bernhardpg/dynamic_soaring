import numpy as np
from pydrake.all import (
    eq,
    MathematicalProgram,
    Solve,
    Variable,
    Expression,
    BasicVector_,
    TemplateSystem,
    LeafSystem_,
)

from dynamics.wind_models import (
    wind_model,
    ddt_wind_model,
    get_wind_vector,
    get_dimless_wind_vector,
)

# From Mortens notes
@TemplateSystem.define("ZhukovskiiGliderDimless_")
def ZhukovskiiGliderDimless_(T):
    class Impl(LeafSystem_[T]):
        def _construct(self, converter=None):
            LeafSystem_[T].__init__(self, converter)

            # Three inputs
            self.DeclareVectorInputPort("u", BasicVector_[T](3))
            # Six outputs (full state)
            self.DeclareVectorOutputPort("x", BasicVector_[T](6), self.CopyStateOut)
            # Three positions, three velocities
            self.DeclareContinuousState(3, 3, 0)
            # State = [x, y, z, xdot, ydot, zdot]

            # Constants
            self.e_z = np.array([0, 0, 1])  # Unit vector along z axis
            self.Gamma = 40  # Optimal lift to drag ratio
            self.efficiency = 1 / self.Gamma  # Small efficiency number
            self.V_l = 20
            self.G = 9.81  # Gravitational constant
            self.L = self.V_l ** 2 / self.G  # Characteristic length
            self.T = self.V_l / self.G  # Characteristic time

        def _construct_copy(self, other, converter=None):
            Impl._construct(self, converter=converter)

        def DoCalcTimeDerivatives(self, context, derivatives):
            # NOTE all variabled dimless here
            # x, y, z, xdot, ydot, zdot
            x = context.get_continuous_state_vector().CopyToVector()
            u = self.EvalVectorInput(context, 0).CopyToVector()

            c = u
            pos = x[0:3]
            vel = x[3:6]

            dimless_wind = get_dimless_wind_vector(pos[2], self.L, self.V_l)
            vel_rel = vel - dimless_wind

            # NOTE necessary to add a small epsilon to deal
            # with gradients of vector norms being horrible
            epsilon = 0.001
            l_term = (vel_rel.T.dot(vel_rel) + c.T.dot(c)) / (
                2 * np.sqrt(vel_rel.T.dot(vel_rel) + epsilon)
            )

            vel_dot = -self.e_z - (
                self.efficiency * l_term * np.eye(3) + skew_matrix(c)
            ).dot(vel_rel)

            derivatives.get_mutable_vector().SetFromVector(
                np.concatenate((vel, vel_dot))
            )

        # y = x
        def CopyStateOut(self, context, output):
            x = context.get_continuous_state_vector().CopyToVector()
            output.SetFromVector(x)

    return Impl


ZhukovskiiGliderDimless = ZhukovskiiGliderDimless_[None]


@TemplateSystem.define("ZhukovskiiGlider_")
def ZhukovskiiGlider_(T):
    class Impl(LeafSystem_[T]):
        def _construct(self, converter=None):
            LeafSystem_[T].__init__(self, converter)

            # two inputs (thrust)
            self.DeclareVectorInputPort("u", BasicVector_[T](3))
            # six outputs (full state)
            self.DeclareVectorOutputPort("x", BasicVector_[T](6), self.CopyStateOut)
            # three positions, three velocities
            self.DeclareContinuousState(3, 3, 0)
            # state = [x, y, z, xdot, ydot, zdot]

            # Constants
            # Values taken from Deittert et al.
            self.rho = 1.255  # g/m**3 air_density
            self.S = 0.473  # m**2 wing_area
            self.c_d0 = 0.0173  # parasitic drag
            self.c_d2 = 0.0517  # lift induced drag constant
            self.wingspan = 3  # m
            self.m = 4.5  # kg
            self.g = 9.81  # gravity
            self.g_vec = np.array([0, 0, -self.g])
            self.Gamma = 45  # Optimal lift to drag ratio
            self.V_l = 20  # Level flight speed that achieves LDR

        def _construct_copy(self, other, converter=None):
            Impl._construct(self, converter=converter)

        def DoCalcTimeDerivatives(self, context, derivatives):
            # x, y, z, xdot, ydot, zdot
            x = context.get_continuous_state_vector().CopyToVector()
            u = self.EvalVectorInput(context, 0).CopyToVector()

            c = u
            pos = x[0:3]
            vel = x[3:6]

            wind = get_wind_vector(pos[2])
            vel_rel = vel - wind

            # NOTE Original expression which is numerically bad
            # d = ((self.m * self.g) / (self.rho * self.Gamma * self.V_l)) * l(
            #    np.linalg.norm(vel_rel) / self.V_l,
            #    (self.rho * self.V_l * np.linalg.norm(c)) / (self.m * self.g),
            # )

            # NOTE necessary rewrite to deal with gradients of vector norms being horrible
            epsilon = 0.001
            l_term = (
                (vel_rel.T.dot(vel_rel)) / (self.V_l ** 2)
                + (self.rho ** 2 * self.V_l ** 2 * c.T.dot(c)) / (self.m * self.g) ** 2
            ) / (2 * (np.sqrt(vel_rel.T.dot(vel_rel) + epsilon) / self.V_l))

            d = ((self.m * self.g) / (self.rho * self.Gamma * self.V_l)) * l_term

            vel_dot = (1 / self.m) * (
                self.m * self.g_vec
                - self.rho * (d * np.eye(3) + skew_matrix(c)).dot(vel_rel)
            )

            derivatives.get_mutable_vector().SetFromVector(
                np.concatenate((vel, vel_dot))
            )

        # y = x
        def CopyStateOut(self, context, output):
            x = context.get_continuous_state_vector().CopyToVector()
            output.SetFromVector(x)

    return Impl


ZhukovskiiGlider = ZhukovskiiGlider_[None]


def l(w, c):
    return (w ** 2 + c ** 2) / (2 * w)


def skew_matrix(v):
    S = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return S


# TODO old?
def continuous_dynamics(x, u):
    # Constants
    air_density = 1.255
    wing_area = 1.5
    parasitic_drag = 1
    wingspan = 2
    mass = 2

    # Dynamics
    x_dot = np.empty(6, dtype=Expression)

    circulation = u
    pos = x[0:3]
    height = pos[2]
    vel = x[3:6]

    wind = np.array([get_wind(height), 0, 0])
    #     if height <= 0: # No wind below ground
    #         wind = np.array([0,0,0])
    rel_vel = vel - wind

    circ_squared_norm = (
        pow(circulation[0], 2) + pow(circulation[1], 2) + pow(circulation[2], 2)
    )

    x_dot[0:3] = vel
    x_dot[3:6] = (1 / mass) * (
        air_density * np.cross(circulation, rel_vel)
        - 0.5
        * air_density
        * wing_area
        * parasitic_drag
        * np.sqrt(rel_vel.T.dot(rel_vel) + 0.001)
        * rel_vel
        - (2 * air_density / np.pi)
        * (circ_squared_norm / wingspan ** 2)
        * rel_vel
        / np.sqrt(rel_vel.T.dot(rel_vel) + 0.001)
        + mass * np.array([0, 0, -9.81])
    )

    return x_dot


def get_wind(height):
    # TODO set parameters here
    ref_height = 10
    alpha = 2

    # TODO replace u0
    u0 = 5

    return u0 * (height / ref_height) ** alpha


def get_wind_field(x, y, z):
    u = get_wind(z)
    v = np.zeros(y.shape)
    w = np.zeros(z.shape)

    return u, v, w
