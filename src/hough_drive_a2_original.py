#!/usr/bin/env python
# -*- coding: utf-8 -*-

####################################################################
# 프로그램명 : hough_drive_a2.py
# 작 성 자 : 자이트론
# 생 성 일 : 2020년 08월 12일
# 본 프로그램은 상업 라이센스에 의해 제공되므로 무단 배포 및 상업적 이용을 금합니다.
####################################################################

import rospy, rospkg
import numpy as np
import cv2, random, math
from cv_bridge import CvBridge
from xycar_motor.msg import xycar_motor
from sensor_msgs.msg import Image

import sys
import os
import signal

def signal_handler(sig, frame):
    os.system('killall -9 python rosout')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

image = np.empty(shape=[0])
bridge = CvBridge()
pub = None
Width = 640
Height = 480
Offset = 340
Gap = 40

def img_callback(data):
    global image
    image = bridge.imgmsg_to_cv2(data, "bgr8")

# publish xycar_motor msg
def drive(Angle, Speed):
    global pub

    msg = xycar_motor()
    msg.angle = Angle
    msg.speed = Speed

    pub.publish(msg)

def region_of_interest(image,width,height1,height2,roiw,roih):
    src=np.array([[width/2-280,height1],[width/2+280,height1],[width/2+300,height2],[width/2-300,height2]],np.float32)
    dst=np.array([[0,0],[roiw,0],[roiw,roih],[0,roih]],np.float32)
    M=cv2.getPerspectiveTransform(src,dst)
    return cv2.warpPerspective(image,M,(roiw,roih))

def slidingwindow(img):
    x_location = None

    out_img = np.dstack((img, img, img))
    out_img = np.uint8(out_img)

    height = img.shape[0]
    width = img.shape[1]

    window_height = 10
    window_num = 30

    nonzero = img.nonzero()

    nonzero_y = np.array(nonzero[0])
    nonzero_x = np.array(nonzero[1])

    margin = 20
    minpix = 10
    left_lane = []
    right_lane = []

    # range of draw line
    good_left = ((nonzero_x >= 0) & (nonzero_y >= 380) & (nonzero_x <= width/2 - 70)).nonzero()[0]
    good_right = ((nonzero_x >= width/2 + 20) & (nonzero_y >= 380) & (nonzero_x <= width)).nonzero()[0]

    # draw left square
    square_left = np.array([[0, height], [0, 380], [250, 380], [250, height]], np.int32)
    cv2.polylines(out_img, [square_left], False, (0,255,0), 1)
    # draw left square
    square_right = np.array([[width/2 + 20, height], [width/2 + 20, height - 80], [width, height - 110], [width, height]], np.int32)
    cv2.polylines(out_img, [square_right], False, (255,0,0), 1)
    # draw (0.340)
    draw_line = np.array([[0, 340], [width, 340]], np.int32)
    cv2.polylines(out_img, [draw_line], False, (0,120,120), 1)

    # visualization--> circle valid inds
    for i in range(len(good_left)):
        img = cv2.circle(out_img, (nonzero_x[good_left[i]], nonzero_y[good_left[i]]), 1, (0,255,0), -1)
    for i in range(len(good_right)):
        img = cv2.circle(out_img, (nonzero_x[good_right[i]], nonzero_y[good_right[i]]), 1, (0,0,255), -1)

    #line_exist_flag = None
    y_represent = None
    x_represent = None

    #judge good_left and good_right and then make bigger one to criteria
    if len(good_left) > len(good_right):
        flag = 1
        x_represent = np.int(np.mean(nonzero_x[good_left]))
        y_represent = np.int(np.mean(nonzero_y[good_left]))
    else:
        flag = 2
        x_represent = np.int(np.mean(nonzero_x[good_right]))
        y_represent = np.int(np.mean(nonzero_y[good_right]))

    img = cv2.circle(out_img, (x_represent, y_represent), 15, (0,255,255), -1)

    # window sliding and draw
    for window in range(0, window_num):
        # left lane
        if flag == 1:
            # rectangle x,y range
            win_y_low = y_represent - (window + 1) * window_height
            win_y_high = y_represent - (window) * window_height
            win_x_low = x_represent - margin
            win_x_high = x_represent + margin
            # draw rectangle
            cv2.rectangle(out_img, (win_x_low, win_y_low), (win_x_high, win_y_high), (0, 255, 0), 1)
            cv2.rectangle(out_img, (win_x_low + int(width * 0.54), win_y_low), (win_x_high + int(width * 0.54), win_y_high), (255, 0, 0), 1)

            good_left = ((nonzero_y >= win_y_low) & (nonzero_y < win_y_high) & (nonzero_x >= win_x_low) & (nonzero_x < win_x_high)).nonzero()[0]

            if len(good_left) > minpix:
                x_represent = np.int(np.mean(nonzero_x[good_left]))
            elif nonzero_y[left_lane] != [] and nonzero_x[left_lane] != []:
                p_left = np.polyfit(nonzero_y[left_lane], nonzero_x[left_lane], 3)
                x_represent = np.int(np.polyval(p_left, win_y_high))
            if win_y_low >= 338 and win_y_low < 344:
                x_location = x_represent + int(width//2)
        else: # right lane
            win_y_low = y_represent - (window + 1) * window_height
            win_y_high = y_represent - (window) * window_height
            win_x_low = x_represent - margin
            win_x_high = x_represent + margin
            cv2.rectangle(out_img, (win_x_low - int(width * 0.54), win_y_low), (win_x_high - int(width * 0.54), win_y_high), (0, 255, 0), 1)
            cv2.rectangle(out_img, (win_x_low, win_y_low), (win_x_high, win_y_high), (255, 0, 0), 1)

            good_right = ((nonzero_y >= win_y_low) & (nonzero_y < win_y_high) & (nonzero_x >= win_x_low) & (nonzero_x < win_x_high)).nonzero()[0]

            if len(good_right) > minpix:
                x_represent = np.int(np.mean(nonzero_x[good_right]))
            elif nonzero_y[right_lane] != [] and nonzero_x[right_lane] != []:
                p_right = np.polyfit(nonzero_y[right_lane], nonzero_x[right_lane], 3)
                x_represent = np.int(np.polyval(p_right, win_y_high))
            if win_y_low >= 338 and win_y_low < 344:
                x_location = x_represent - int(width//2)

        left_lane.extend(good_left)
        right_lane.extend(good_right)

    return out_img, x_location
#
# # draw lines
# def draw_lines(img, lines):
#     global Offset
#     for line in lines:
#         x1, y1, x2, y2 = line[0]
#         color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
#         img = cv2.line(img, (x1, y1+Offset), (x2, y2+Offset), color, 2)
#     return img

# # draw rectangle
# def draw_rectangle(img, lpos, rpos, offset=0):
#     center = (lpos + rpos) / 2
#
#     cv2.rectangle(img, (lpos - 5, 15 + offset),
#                        (lpos + 5, 25 + offset),
#                        (0, 255, 0), 2)
#     cv2.rectangle(img, (rpos - 5, 15 + offset),
#                        (rpos + 5, 25 + offset),
#                        (0, 255, 0), 2)
#     cv2.rectangle(img, (center-5, 15 + offset),
#                        (center+5, 25 + offset),
#                        (0, 255, 0), 2)
#     cv2.rectangle(img, (315, 15 + offset),
#                        (325, 25 + offset),
#                        (0, 0, 255), 2)
#     return img

# # left lines, right lines
# def divide_left_right(lines):
#     global Width
#
#     low_slope_threshold = 0
#     high_slope_threshold = 10
#
#     # calculate slope & filtering with threshold
#     slopes = []
#     new_lines = []
#
#     for line in lines:
#         x1, y1, x2, y2 = line[0]
#
#         if x2 - x1 == 0:
#             slope = 0
#         else:
#             slope = float(y2-y1) / float(x2-x1)
#
#         if abs(slope) > low_slope_threshold and abs(slope) < high_slope_threshold:
#             slopes.append(slope)
#             new_lines.append(line[0])
#
#     # divide lines left to right
#     left_lines = []
#     right_lines = []
#
#     for j in range(len(slopes)):
#         Line = new_lines[j]
#         slope = slopes[j]
#
#         x1, y1, x2, y2 = Line
#
#         if (slope < 0) and (x2 < Width/2 - 90):
#             left_lines.append([Line.tolist()])
#         elif (slope > 0) and (x1 > Width/2 + 90):
#             right_lines.append([Line.tolist()])
#
#     return left_lines, right_lines
#
# # get average m, b of lines
# def get_line_params(lines):
#     # sum of x, y, m
#     x_sum = 0.0
#     y_sum = 0.0
#     m_sum = 0.0
#
#     size = len(lines)
#     if size == 0:
#         return 0, 0
#
#     for line in lines:
#         x1, y1, x2, y2 = line[0]
#
#         x_sum += x1 + x2
#         y_sum += y1 + y2
#         m_sum += float(y2 - y1) / float(x2 - x1)
#
#     x_avg = x_sum / (size * 2)
#     y_avg = y_sum / (size * 2)
#     m = m_sum / size
#     b = y_avg - m * x_avg
#
#     return m, b
#
# # get lpos, rpos
# def get_line_pos(img, lines, left=False, right=False):
#     global Width, Height
#     global Offset, Gap
#
#     m, b = get_line_params(lines)
#
#     if m == 0 and b == 0:
#         if left:
#             pos = 0
#         if right:
#             pos = Width
#     else:
#         y = Gap / 2
#         pos = (y - b) / m
#
#         b += Offset
#         x1 = (Height - b) / float(m)
#         x2 = ((Height/2) - b) / float(m)
#
#         cv2.line(img, (int(x1), Height), (int(x2), (Height/2)), (255, 0,0), 3)
#
#     return img, int(pos)

# show image and return lpos, rpos
def process_image(frame):
    global Width
    global Offset, Gap

    # gray
    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

    # blur
    kernel_size = 5
    blur_gray = cv2.GaussianBlur(gray,(kernel_size, kernel_size), 0)

    # canny edge
    low_threshold = 60
    high_threshold = 70
    edge_img = cv2.Canny(np.uint8(blur_gray), low_threshold, high_threshold)

    # # HoughLinesP
    # roi = edge_img[Offset : Offset+Gap, 0 : Width]
    # all_lines = cv2.HoughLinesP(roi,1,math.pi/180,30,30,10)
    #
    # # divide left, right lines
    # if all_lines is None:
    #     return 0, 640
    # left_lines, right_lines = divide_left_right(all_lines)
    #
    # # get center of lines
    # frame, lpos = get_line_pos(frame, left_lines, left=True)
    # frame, rpos = get_line_pos(frame, right_lines, right=True)
    #
    # # draw lines
    # frame = draw_lines(frame, left_lines)
    # frame = draw_lines(frame, right_lines)
    # frame = cv2.line(frame, (230, 235), (410, 235), (255,255,255), 2)

    # # draw rectangle
    # frame = draw_rectangle(frame, lpos, rpos, offset=Offset)
    # #roi2 = cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)
    # #roi2 = draw_rectangle(roi2, lpos, rpos)

    # show image
    cv2.imshow('calibration', edge_img)

    return edge_img

def start():
    global pub
    global image
    global cap
    global Width, Height

    rospy.init_node('auto_drive')
    pub = rospy.Publisher('xycar_motor', xycar_motor, queue_size=1)

    image_sub = rospy.Subscriber("/usb_cam/image_raw", Image, img_callback)
    print "---------- Xycar A2 v1.0 ----------"
    rospy.sleep(2)

    while True:
        while not image.size == (640*480*3):
            continue

        edge_img = process_image(image)

        warp = region_of_interest(edge_img, 640, 350, 380, 640, 480)

        out_img, x_location = slidingwindow(warp)

        if x_location is None:
            Angle = (x_old - 320)*5 // 18
            cv2.circle(out_img, (x_old, 340), 5, (255,0,255),-1)
        else:
            cv2.circle(out_img, (x_location, 340), 5, (255,0,255),-1)
            x_old = x_location
            Angle = (x_location - 320)*5 // 18
            x_loc_list.append(x_location)

        # center = (lpos + rpos) / 2
        # angle = -(Width/2 - center)
        cv2.imshow('result',out_img)
        drive(Angle, 4)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    rospy.spin()

if __name__ == '__main__':

    start()
