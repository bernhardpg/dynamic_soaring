clear all; close all; clc;

x0 = [5;0;10;0;0;0];
u0 = [5;-1;0];

tf = 3;
tspan = [0 tf];
%[t,x] = ode45(@(t,x) continuous_dynamics(x,u0), tspan, x0);

% Forward Euler
dt = 0.001;
N = tf / dt + 1;
x = zeros(N, 6);
x(1,:) = x0';
for i = 1:N
    x(i + 1, :) = x(i,:) + dt * continuous_dynamics(x(i,:)', u0)';
end

plot3(x(:,1), x(:,2), x(:,3)); hold on
scatter3(x(1,1), x(1,2), x(1,3))

function x_dot = continuous_dynamics(x, u)
    % Constants
    air_density = 1.255;
    wing_area = 1.5;
    parasitic_drag = 1;
    wingspan = 2;
    mass = 2;

    vel = x(4:6);
    height = x(3);
    wind = [5 * (height / 10)^2; 0; 0]; % u0 * (height / ref_height) ** alpha
    if (height < 0)
        wind = [0;0;0];
    end

    rel_vel = vel - wind;

    x_dot = zeros(6,1);
    x_dot(1:3) = x(4:6);
    x_dot(4:6) = (1 / mass) * (air_density * cross(u, rel_vel) ...
        - 0.5 * air_density * wing_area * parasitic_drag * norm(rel_vel) * rel_vel ...
        - (2 * air_density / pi) * (norm(u)^2 / wingspan^2) * rel_vel / norm(rel_vel) ...
        + mass * [0; 0; -9.81]);
end

