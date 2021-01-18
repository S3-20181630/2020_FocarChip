import cv2
import numpy as np
import time

class Crosswalk_Counter:
    def __init__(self):
        self.cnt = 0
        # self.previous_time = time.time() + 5
        # self.lower_yellow = (20, 100, 100)
        # self.upper_yellow = (40, 255, 255)

    def check_crosswalk(self, img):
        # if time.time() < self.previous_time + 10:
        #     return False
        #cv2.imshow('img', img)
        #cv2.waitKey(-1)
        img_copy = img.copy() #240
        img_copy = img_copy[375:410, 90:610]
        gray = cv2.cvtColor(img_copy, cv2.COLOR_BGR2GRAY)
        img_mask, dst = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        # img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # img_mask = cv2.inRange(img_hsv, self.lower_yellow, self.upper_yellow)

        # IMSHOW FOR DEBUG
        # print(np.count_nonzero(img_mask))
        # cv2.putText(img_mask, 'NONZERO %d'%np.count_nonzero(img_mask), (0,15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        cv2.imshow('img_mask', dst)
        #cv2.waitKey(-1)
        print("np.count_nonzero(img_mask) : {}".format(np.count_nonzero(dst)))
        if np.count_nonzero(dst) > 5000:
            self.cw_on_detected()
            return True

        return False

    def cw_on_detected(self):
        print('CROSSWALK LINE DETECTED!!!')
        # self.previous_time = time.time()
        self.cnt += 1

if __name__ == '__main__':
    crosswalk_counter = Crosswalk_Counter()

    cap = cv2.VideoCapture('video/original.avi')
    while cap.isOpened():
        ret, frame = cap.read()
        crosswalk_counter.check_crosswalk(frame)

        cv2.imshow('frame', frame)
        if cv2.waitKey(1) == ord('q'):
            break
