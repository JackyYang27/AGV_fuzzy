from enum import Enum
import numpy as np

class Fuzzy:
    def __init__(self):
        self.max_delta = 40 # 轉彎角度

    def get_theta(self, front_distance, right_distance, left_distance):
        # 定義輸入的模糊集合
        def front_near(x):
            if x <= 4:
                return 1
            elif 4 < x <= 5:
                return (5 - x) / 1
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
            if x > 12:
                return 1
            elif 10 <= x < 12:
                return (x - 10) / 2
            else:
                return 0

        def right_left_diff_left(y):
            if y <= -4:
                return 1
            elif -4 < y <= 0:
                return (-y) / 4
            else:
                return 0


        def right_left_diff_straight(y):
            if -1 <= y <= 1:
                return 1 - abs(y)
            else:
                return 0

        def right_left_diff_right(y):
            if y >= 4:
                return 1
            elif 0 <= y < 4:
                return y / 4
            else:
                return 0

        # 定義輸出的模糊集合
        def turn_left(z):
            return np.where(z <= -self.max_delta, 1, np.where(z < 0, -z / self.max_delta, 0))

        def turn_straight(z):
            return np.where(abs(z) <= 10, (10 - abs(z)) / 10, 0)

        def turn_right(z):
            return np.where(z >= self.max_delta, 1, np.where(z > 0, z / self.max_delta, 0))

        # 模糊化輸入
        front_near_val = front_near(front_distance)
        front_medium_val = front_medium(front_distance)
        front_far_val = front_far(front_distance)

        diff = right_distance - left_distance
        diff_left_val = right_left_diff_left(diff)
        diff_straight_val = right_left_diff_straight(diff)
        diff_right_val = right_left_diff_right(diff)

        # 模糊推理規則
        rule1 = min(front_near_val, diff_left_val)
        rule2 = min(front_near_val, diff_straight_val)
        rule3 = min(front_near_val, diff_right_val)
        rule4 = min(front_medium_val, diff_left_val)
        rule5 = min(front_medium_val, diff_straight_val)
        rule6 = min(front_medium_val, diff_right_val)
        rule7 = min(front_far_val, diff_left_val)
        rule8 = min(front_far_val, diff_straight_val)
        rule9 = min(front_far_val, diff_right_val)

        # 構建輸出樣本點
        samples = np.linspace(-self.max_delta, self.max_delta, 81)

        # 計算每個規則的激活強度
        output_left = np.maximum.reduce([
            turn_left(samples) * rule1,
            turn_left(samples) * rule4,
            turn_left(samples) * rule7
        ])

        output_straight = np.maximum.reduce([
            turn_straight(samples) * rule2,
            turn_straight(samples) * rule5,
            turn_straight(samples) * rule8
        ])

        output_right = np.maximum.reduce([
            turn_right(samples) * rule3,
            turn_right(samples) * rule6,
            turn_right(samples) * rule9
        ])

        # 合併所有規則的輸出
        combined_output = output_left + output_straight + output_right

        # 確保總和不為零以避免除零錯誤
        sum_membership = np.sum(combined_output)
        if sum_membership == 0:
            return 0

        # 計算質心（離散重心）
        centroid = np.sum(samples * combined_output) / sum_membership
        return centroid


# 距離 Set
class Distance(Enum):
    Short = 0
    Medium = 1
    Far = 2

# 轉彎 Set
class Turn(Enum):
    Straight = 0
    Left = 1
    Right = 2
