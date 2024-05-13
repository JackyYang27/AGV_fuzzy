from enum import Enum

# 模糊系統
class Fuzzy:
    def __init__(self):
        self.max_delta = 40 # 轉彎角度

        self.mf_value = 0

    def get_theta(self, distance, right_distance, left_distance):
        # 取得距離 Set
        distance_set, distance_value = self.get_distance(distance)
        # 取得靠近方向 Set
        right_left_distance = right_distance - left_distance
        close_to_set, close_to_value = self.get_close_to(right_left_distance)
        print("close_to_set" + str(close_to_set) + " close_to_value" + str(close_to_value))
        # 取得轉向的 Set
        turn_set, turn_value = self.fuzzy_rule(distance_set, distance_value, close_to_set, close_to_value)
        print("turn_set" + str(turn_set) + " turn_value" + str(turn_value))
        # 取模糊，取的 delta
        delta = self.un_fuzzy(turn_set, turn_value)
        return delta

    # 模糊規則
    def fuzzy_rule(self, distance_set, distance_value, close_to_set, close_to_value):
        # 當距離為 Far 時，方向 Set 為 Straight
        if (distance_set == Distance.Far):
            return Turn.Straight, close_to_value * distance_value
        else:  # 當距離為 Close 時，方向 Set 為 Left, Right
            if(close_to_set == CloseTo.Right):
                return Turn.Left, close_to_value * distance_value
            else :
                return Turn.Right , close_to_value * distance_value

    # 取得距離
    def get_distance(self, distance):
        if(distance < 15):
            return Distance.Short, 1
        else:
            return Distance.Far, 1

    # 取得靠近哪邊
    def get_close_to(self, right_left_distance):
        if(right_left_distance < 0):
            return CloseTo.Right, self.triangle_function_right(-14, 0, right_left_distance)
        else:
            return CloseTo.Left, self.triangle_function_left(14, 0, right_left_distance)

    # 用來實作三角形函數
    def triangle_function_left(self, up_num, down_num, value):
        if(value > up_num):
            return_value = 1
        elif(value > down_num):
            return_value = (down_num - value) / (down_num - up_num)
        else:
            return_value = 0

        return return_value
    # 用來實作三角形函數
    def triangle_function_right(self, up_num, down_num, value):
        if(value < up_num):
            return_value = 1
        elif(value < down_num):
            return_value = (down_num - value) / (down_num - up_num)
        else:
            return_value = 0

        return return_value
    # def triangle_function_left(self, up_num, down_num, value):
    #     if value < down_num:
    #         return 1
    #     elif down_num <= value <= up_num:
    #         return (up_num - value) / (up_num - down_num)
    #     else:
    #         return 0

    # def triangle_function_right(self, up_num, down_num, value):
    #     if value > up_num:
    #         return 1
    #     elif down_num <= value <= up_num:
    #         return (value - down_num) / (up_num - down_num)
    #     else:
    #         return 0
    # 去模糊
    def un_fuzzy(self, turn_set, turn_value):
        if(turn_set == Turn.Straight):
            return 0
        elif(turn_set == Turn.Left):
            return - turn_value * self.max_delta
        else:
            return turn_value * self.max_delta


# 距離 Set
class Distance(Enum):
    Short = 0
    Far = 1

# 靠近 Set
class CloseTo(Enum):
    Left = 0
    Right = 1

# 轉彎 Set
class Turn(Enum):
    Straight = 0
    Left = 1
    Right = 2

