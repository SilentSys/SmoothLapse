import cv2

def Diff(A, B, threshold):
    diff = cv2.absdiff(A, B)
    ret, thresh = cv2.threshold(diff, threshold, 1, cv2.THRESH_BINARY)
    sum = cv2.sumElems(thresh)[0]
    return sum