
import random as r
import os
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from simple_geometry import *
from fuzzy import *
import numpy as np
import matplotlib.patches
from PyQt5 import QtWidgets, QtCore
matplotlib.use('Qt5Agg')


class Car():
    def __init__(self) -> None:
        self.diameter = 6
        self.angle_min = -90
        self.angle_max = 270
        self.wheel_min = -40
        self.wheel_max = 40
        self.xini_max = 4.5
        self.xini_min = -4.5

        self.reset()

    @property
    def radius(self):
        return self.diameter/2

    # reset the car to the beginning line
    def reset(self):
        self.angle = 90
        self.wheel_angle = 0
        xini_range = (self.xini_max - self.xini_min - self.diameter)
        left_xpos = self.xini_min + self.diameter//2
        # self.xpos = r.random()*xini_range + left_xpos  # random x pos [-3, 3]
        self.xpos = 0
        self.ypos = 0

    def setWheelAngle(self, angle):
        self.wheel_angle = angle if self.wheel_min <= angle <= self.wheel_max else (
            self.wheel_min if angle < self.wheel_min else self.wheel_max)

    def setPosition(self, newPosition: Point2D):
        self.xpos = newPosition.x
        self.ypos = newPosition.y

    # this is the function returning the coordinate on the right, left, front or center points
    def getPosition(self, point='center') -> Point2D:
        if point == 'right':
            right_angle = self.angle - 45
            right_point = Point2D(self.diameter/2, 0).rotate(right_angle)
            return Point2D(self.xpos, self.ypos) + right_point

        elif point == 'left':
            left_angle = self.angle + 45
            left_point = Point2D(self.diameter/2, 0).rotate(left_angle)
            return Point2D(self.xpos, self.ypos) + left_point

        elif point == 'front':
            fx = m.cos(self.angle/180*m.pi)*self.diameter/2+self.xpos
            fy = m.sin(self.angle/180*m.pi)*self.diameter/2+self.ypos
            return Point2D(fx, fy)
        else:
            return Point2D(self.xpos, self.ypos)

    def setAngle(self, new_angle):
        new_angle %= 360
        if new_angle > self.angle_max:
            new_angle -= self.angle_max - self.angle_min
        self.angle = new_angle

    # set the car state from t to t+1
    def tick(self):
        car_angle = self.angle/180*m.pi
        wheel_angle = self.wheel_angle/180*m.pi
        new_x = self.xpos + m.cos(car_angle+wheel_angle) + \
            m.sin(wheel_angle)*m.sin(car_angle)

        new_y = self.ypos + m.sin(car_angle+wheel_angle) - \
            m.sin(wheel_angle)*m.cos(car_angle)
        new_angle = (car_angle - m.asin(2*m.sin(wheel_angle) / self.diameter)) / m.pi * 180

        new_angle %= 360
        if new_angle > self.angle_max:
            new_angle -= self.angle_max - self.angle_min

        self.xpos = new_x
        self.ypos = new_y
        self.setAngle(new_angle)

class Playground():
    def __init__(self):
        # read path lines
        self.path_line_filename = "軌道座標點.txt"
        self._setDefaultLine()
        self.decorate_lines = [
            Line2D(-6, 0, 6, 0),  # start line
            Line2D(0, 0, 0, -3),  # middle line
        ]

        self.complete = False
        self.previous_state = [0, 0, 0]
        self.current_state = [0, 0, 0]
        self.previous_angle = 0
        self.current_angle = 0
        self.car = Car()
        self.reset()
        self.cumulated_reward = 0
        self.error_count = 0
        self.fuzzy_controller = Fuzzy()

    def _setDefaultLine(self):
        self.destination_line = Line2D(18, 40, 30, 37)

        self.lines = [
            Line2D(-6, -3, 6, -3),
            Line2D(6, -3, 6, 10),
            Line2D(6, 10, 30, 10),
            Line2D(30, 10, 30, 50),
            Line2D(18, 50, 30, 50),
            Line2D(18, 22, 18, 50),
            Line2D(-6, 22, 18, 22),
            Line2D(-6, -3, -6, 22),
        ]

        self.car_init_pos = None
        self.car_init_angle = None

    def _readPathLines(self):
        try:
            with open(self.path_line_filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # get init pos and angle
                pos_angle = [float(v) for v in lines[0].split(',')]
                self.car_init_pos = Point2D(*pos_angle[:2])
                self.car_init_angle = pos_angle[-1]

                # get destination line
                dp1 = Point2D(*[float(v) for v in lines[1].split(',')])
                dp2 = Point2D(*[float(v) for v in lines[2].split(',')])
                self.destination_line = Line2D(dp1, dp2)

                # get wall lines
                self.lines = []
                inip = Point2D(*[float(v) for v in lines[3].split(',')])
                for strp in lines[4:]:
                    p = Point2D(*[float(v) for v in strp.split(',')])
                    line = Line2D(inip, p)
                    inip = p
                    self.lines.append(line)
        except Exception:
            self._setDefaultLine()

    # @property
    # def n_actions(self):  #7 possible actions
    #     return 7

    @property
    def observation_shape(self):
        return (len(self.state),)

    @ property
    def state(self):
        front_dist = - 1 if len(self.front_intersects) == 0 else self.car.getPosition(
            ).distToPoint2D(self.front_intersects[0])
        right_dist = - 1 if len(self.right_intersects) == 0 else self.car.getPosition(
            ).distToPoint2D(self.right_intersects[0])
        left_dist = - 1 if len(self.left_intersects) == 0 else self.car.getPosition(
            ).distToPoint2D(self.left_intersects[0])

        return [front_dist, right_dist, left_dist]

    def _checkDoneIntersects(self):
        if self.done:
            return self.done

        cpos = self.car.getPosition('center')     # center point of the car
        cfront_pos = self.car.getPosition('front')
        cright_pos = self.car.getPosition('right')
        cleft_pos = self.car.getPosition('left')
        radius = self.car.radius

        isAtDestination = cpos.isInRect(
            self.destination_line.p1, self.destination_line.p2
        )
        # if we finish the tour
        done = False if not isAtDestination else True
        self.complete = False if not isAtDestination else True

        front_intersections, find_front_inter = [], True
        right_intersections, find_right_inter = [], True
        left_intersections, find_left_inter = [], True
        for wall in self.lines:  # check every line in play ground
            dToLine = cpos.distToLine2D(wall)
            p1, p2 = wall.p1, wall.p2
            dp1, dp2 = (cpos-p1).length, (cpos-p2).length
            wall_len = wall.length

            # touch conditions
            p1_touch = (dp1 < radius)
            p2_touch = (dp2 < radius)
            body_touch = (
                dToLine < radius and (dp1 < wall_len and dp2 < wall_len)
            )
            front_touch, front_t, front_u = Line2D(
                cpos, cfront_pos).lineOverlap(wall)
            right_touch, right_t, right_u = Line2D(
                cpos, cright_pos).lineOverlap(wall)
            left_touch, left_t, left_u = Line2D(
                cpos, cleft_pos).lineOverlap(wall)

            if p1_touch or p2_touch or body_touch or front_touch:
                if not done:
                    done = True

            # find all intersections
            if find_front_inter and front_u and 0 <= front_u <= 1:
                front_inter_point = (p2 - p1)*front_u+p1
                if front_t:
                    if front_t > 1:  # select only point in front of the car
                        front_intersections.append(front_inter_point)
                    elif front_touch:  # if overlapped, don't select any point
                        front_intersections = []
                        find_front_inter = False

            if find_right_inter and right_u and 0 <= right_u <= 1:
                right_inter_point = (p2 - p1)*right_u+p1
                if right_t:
                    if right_t > 1:  # select only point in front of the car
                        right_intersections.append(right_inter_point)
                    elif right_touch:  # if overlapped, don't select any point
                        right_intersections = []
                        find_right_inter = False

            if find_left_inter and left_u and 0 <= left_u <= 1:
                left_inter_point = (p2 - p1)*left_u+p1
                if left_t:
                    if left_t > 1:  # select only point in front of the car
                        left_intersections.append(left_inter_point)
                    elif left_touch:  # if overlapped, don't select any point
                        left_intersections = []
                        find_left_inter = False

        self._setIntersections(front_intersections,
                               left_intersections,
                               right_intersections)

        # results
        self.done = done
        return done

    def _setIntersections(self, front_inters, left_inters, right_inters):
        self.front_intersects = sorted(front_inters, key=lambda p: p.distToPoint2D(
            self.car.getPosition('front')))
        self.right_intersects = sorted(right_inters, key=lambda p: p.distToPoint2D(
            self.car.getPosition('right')))
        self.left_intersects = sorted(left_inters, key=lambda p: p.distToPoint2D(
            self.car.getPosition('left')))

    def reset(self):
        self.done = False
        self.complete = False
        self.car.reset()

        if self.car_init_angle and self.car_init_pos:
            self.setCarPosAndAngle(self.car_init_pos, self.car_init_angle)
        
        self._checkDoneIntersects()
        self.cumulative_reward = 0
        return self.state

    def setCarPosAndAngle(self, position: Point2D = None, angle=None):
        if position:
            self.car.setPosition(position)
        if angle:
            self.car.setAngle(angle)
        self._checkDoneIntersects()

    # def calWheelAngleFromAction(self, action):
    #     action_table = [-30, -15, -10, 0, 10, 15, 30]
    #     return action_table[action]


    def step(self, action=None):
        if action is None:
        # 從模糊控制器獲得動作
            distance = self.car.getPosition('front').y  # 獲取前方距離的方法
            right_distance = self.car.getPosition('right').y  # 獲取右方距離的方法
            left_distance = self.car.getPosition('left').y  # 獲取左方距離的方法
            action = self.fuzzy_controller.get_theta(distance, right_distance, left_distance)
    
        # 根據動作設置車輪角度
        self.car.setWheelAngle(action)

        if not self.done:
            self.car.tick()  # 更新車輛位置
            self._checkDoneIntersects()  # 檢查是否達到目的地或碰撞
            return self.state
        else:
            return self.state
 
class Animation(QtWidgets.QMainWindow):
    '''
    state: 當前狀態
    QtCore.QTimer: 控制動畫的執行頻率和狀態
    '''
    def __init__(self, play: Playground):
        super().__init__()
        self.play = play
        self.state = self.play.reset()
        self.now_running = False
        self.timer = QtCore.QTimer(self)
        self.path_points = []

        # 建立主視窗
        self.setWindowTitle("操作介面")
        self.main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.main_widget)

        # 開始動畫按鈕
        self.start_button = QtWidgets.QPushButton("Start")
        self.start_button.clicked.connect(self.start_animation)
        # 停止動畫按鈕
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_animation)

        # 建立動畫畫布
        self.figure = Figure(figsize=(5, 5))
        self.canvas = FigureCanvas(self.figure)

        # 主畫面
        layout = QtWidgets.QVBoxLayout(self.main_widget)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.canvas)
        self.setup_animation()

    def setup_animation(self):
        '''
        start_line: 起點
        finish_line: 終點
        car_path: 明確路徑
        ax: 畫布
        direction_line: 顯示車子所面向的方向
        text: 感測器偵測到的距離    
        '''
        self.ax = self.figure.add_subplot(111)
        self.background = self.play.lines
        self.start_line = self.play.decorate_lines[0]
        self.finish_line = self.play.destination_line
        self.car_radius = self.play.car.radius
        self.direction_line, = self.ax.plot([], [], 'r-')  # 指引方向的線
        self.car_path, = self.ax.plot([], [], 'g-', linewidth=2)
        self.text = self.ax.text(15, 0, '', fontsize=10)

        self.draw_background()

    def draw_background(self):
        for line in self.background:
            self.ax.plot([line.p1.x, line.p2.x], [line.p1.y, line.p2.y], "k-")

        # 起點
        self.ax.plot([self.start_line.p1.x, self.start_line.p2.x],
                     [self.start_line.p1.y, self.start_line.p2.y], "b-")
        # 終點的長方形
        self.ax.plot([self.finish_line.p1.x, self.finish_line.p2.x],
                     [self.finish_line.p1.y, self.finish_line.p1.y], "r-")
        self.ax.plot([self.finish_line.p1.x, self.finish_line.p2.x],
                     [self.finish_line.p2.y, self.finish_line.p2.y], "r-")

        self.ax.axis('equal')

    # 初始化後開始動畫
    def start_animation(self):
        if self.now_running:
            self.timer.stop()

        self.clean()
        self.play.reset()
        self.now_running = True

        # 更新動畫的函數
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)  
    
    # 停止動畫
    def stop_animation(self):
        self.timer.stop()
        self.now_running = False
        self.clean()

    # 畫面
    def update_animation(self):
        car_pos = self.play.car.getPosition("center")
        self.path_points.append((car_pos.x, car_pos.y))
        self.update_path()
        self.draw_car(car_pos)
        #更新感測器所得到的文本
        self.text.set_text(
            f'Front sensor: {self.play.state[0]:.{3}f}\n'
            f'Right sensor: {self.play.state[1]:.{3}f}\n'
            f'Left sensor: {self.play.state[2]:.{3}f}'
        )
        # 使用模糊控制器决定下一步动作
        front_distance = self.play.state[0]  # 前方距离
        right_distance = self.play.state[1]  # 右方距离
        left_distance = self.play.state[2]  # 左方距离
        action = self.play.fuzzy_controller.get_theta(front_distance, right_distance, left_distance)
        
        self.play.step(action)# 成功訊息
        self.canvas.draw()
        if self.play.done:
            if self.play.complete:
                self.show_message("Reach destination!")
            # else:
            #     self.show_message("Crash!")
            self.timer.stop()
            self.now_running = False

    def update_path(self):
        if self.path_points:
            x, y = zip(*self.path_points)
            self.car_path.set_data(x, y)  # 更新路徑數據

    # 秀訊息
    def show_message(self, message):
        msg_box = QtWidgets.QMessageBox()
        msg_box.setText(message)
        msg_box.exec_()

    # 畫出車子
    def draw_car(self, car_pos):
        self.car = plt.Circle((car_pos.x, car_pos.y), self.car_radius, color="green", fill=False)
        self.ax.add_patch(self.car)
        front_sensor = self.play.car.getPosition("front")
        self.direction_line.set_data([car_pos.x, front_sensor.x], [car_pos.y, front_sensor.y])

    # 清理過去車子移動軌跡
    def clean(self):
        for trace in self.ax.patches:
            trace.remove()
        self.path_points.clear()
        self.car_path.set_data([], [])

    # 顯示動畫
    def run(self):
        self.show()

#主程式
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    playground = Playground()
    GUI = Animation(playground)
    GUI.run()
    # 啟動 PyQt5 事件循環。
    app.exec_()