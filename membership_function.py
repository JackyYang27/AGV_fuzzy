import matplotlib.pyplot as plt
import numpy as np

class FuzzyController:
    def __init__(self, max_delta=40):
        self.max_delta = max_delta

    def turn_left(self, z):
        return np.where(z <= -self.max_delta, 1, np.where(z < 0, -z / self.max_delta, 0))

    def turn_straight(self, z):
        return np.where(abs(z) <= 10, (10 - abs(z)) / 10, 0)

    def turn_right(self, z):
        return np.where(z >= self.max_delta, 1, np.where(z > 0, z / self.max_delta, 0))

# Define the membership functions for front distance
def front_near(x):
    if x <= 4:
        return 1
    elif 4 < x <= 5:
        return (5 - x)
    else:
        return 0

def front_medium(x):
    if 6 < x < 9:
        return 1
    elif 4 <= x <= 6:
        return (x - 4) / 2
    elif 9 <= x <= 11:
        return (11 - x) / 2
    else:
        return 0

def front_far(x):
    if x >= 12:
        return 1
    elif 10 <= x < 12:
        return (x - 10) / 2
    else:
        return 0

# Define the membership functions for right-left distance difference
def right_left_diff_left(y):
    if y <= -4:
        return 1
    elif -4 < y <= 0:
        return (-y) / 4
    else:
        return 0

def right_left_diff_straight(y):
    if -2 <= y <= 2:
        return 1
    elif -4 < y < -2:
        return (y + 4) / 2
    elif 2 < y <= 4:
        return (4 - y) / 2
    else:
        return 0

def right_left_diff_right(y):
    if y >= 4:
        return 1
    elif 0 <= y < 4:
        return y / 4
    else:
        return 0

# Initialize the fuzzy controller with default max_delta
fuzzy_controller = FuzzyController()

# Plot the membership functions for front distance
x = np.arange(0, 16, 1)
plt.figure(figsize=(10, 5))
plt.plot(x, [front_near(i) for i in x], label='Near')
plt.plot(x, [front_medium(i) for i in x], label='Medium')
plt.plot(x, [front_far(i) for i in x], label='Far')
plt.xticks(np.arange(0, 16, 1))
plt.xlabel('Front Distance')
plt.ylabel('Membership Degree')
plt.title('Membership Functions for Front Distance')
plt.legend()
plt.grid(True)
plt.show()

# Plot the membership functions for right-left distance difference
y = np.arange(-10, 11, 1)
plt.figure(figsize=(10, 5))
plt.plot(y, [right_left_diff_right(i) for i in y], label='Turn Right')
plt.plot(y, [right_left_diff_straight(i) for i in y], label='Go Straight')
plt.plot(y, [right_left_diff_left(i) for i in y], label='Turn Left')
plt.xticks(np.arange(-10, 11, 1))
plt.xlabel('Right-Left Distance Difference')
plt.ylabel('Membership Degree')
plt.title('Membership Functions for Right-Left Distance Difference')
plt.legend()
plt.grid(True)
plt.show()

# Plot the membership functions for steering behaviors
z = np.linspace(-50, 50, 400)
plt.figure(figsize=(10, 5))
plt.plot(z, [fuzzy_controller.turn_left(i) for i in z], label='Turn Left')
plt.plot(z, [fuzzy_controller.turn_straight(i) for i in z], label='Go Straight')
plt.plot(z, [fuzzy_controller.turn_right(i) for i in z], label='Turn Right')
plt.xticks(np.arange(-50, 51, 10))
plt.xlabel('Steering Angle Difference')
plt.ylabel('Membership Degree')
plt.title('Steering Behaviors')
plt.legend()
plt.grid(True)
plt.show()
