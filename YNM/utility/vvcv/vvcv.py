# -*- coding: utf-8 -*-

import YNM.cv2 as cv2
import pytesseract
import numpy
import math
from PIL import Image


def pil_to_opencv(pil):
    # copy from
    # http://stackoverflow.com/questions/14134892/convert-image-from-pil-to-opencv-format
    opencv = numpy.array(pil)
    opencv = opencv[:, :, ::-1].copy()
    return opencv


def opencv_to_pil(opencv):
    # copy from
    # http://stackoverflow.com/questions/13576161/convert-opencv-image-into-pil-image-in-python-for-use-with-zbar-library
    pil = Image.fromarray(opencv)
    return pil


def text_from_image(snapshot_image):

    s = snapshot_image
#     s.save('orig.jpg')
    s = pil_to_opencv(s)

    s = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY)

    _, s_bin = cv2.threshold(s, 230, 255, cv2.THRESH_BINARY_INV)
    kernel = numpy.ones((2, 2), numpy.uint8)
    s_bin = cv2.morphologyEx(s_bin, cv2.MORPH_OPEN, kernel)
    i_bin = opencv_to_pil(s_bin)
#     i_bin.save('output.jpg')
    text = pytesseract.image_to_string(i_bin)
    return text


def cv_detect_windows(images):
    def contour_to_motion_windows(contours, hierarchy):
        return contours

    def distance(p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    # detect privacy masks through opencv, input objects should be
    img1, img2 = images

    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    _, img1_gray = cv2.threshold(img1_gray, 40, 255, cv2.THRESH_BINARY)
    _, img2_gray = cv2.threshold(img2_gray, 40, 255, cv2.THRESH_BINARY)
#     cv2.imwrite('cv-1.jpg', img1_gray)
#     cv2.imwrite('cv-2.jpg', img2_gray)

    img_diff = cv2.absdiff(img1_gray, img2_gray)
#     cv2.imwrite('cv-diff.jpg', img_diff)
    dst = cv2.cornerHarris(img_diff, 2, 3, 0.04)
    dst = cv2.normalize(dst, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_32FC1, None)
    dst = cv2.convertScaleAbs(dst)

    points = []
    for y in range(0, len(dst) - 1):
        for x in range(0, len(dst[0]) - 1):
            # 70 is a try-and-error threshold, please don't change unless you
            # know what you are doing
            if dst[y][x] > 80:
                cv2.circle(img_diff, (x, y), 2, 100)
                add = True
                for point in points:
                    d = distance(point, (x, y))
                    if d < 5:
                        add = False
                        break

                if add:
                    points.append((x, y))

#     cv2.imwrite('cv-circled.jpg', img_diff)

    contours, hierarchy = cv2.findContours(img_diff, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)

    return len(contours), points
