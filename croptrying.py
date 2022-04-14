import cv2
import numpy as np

# load image
img = cv2.imread('images/cropping/image20220108145025.jpg') 
#rsz_img = cv2.resize(img, None, fx=0.25, fy=0.25) # resize since image is huge
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # convert to grayscale

y=50
x=200
h=2000
w=1000
gray = img[y:y+h, x:x+w]

cv2.imshow("greyed image", gray) 
cv2.waitKey(0)

## find the non-zero min-max coords of canny
canny = cv2.Canny(gray, 300, 200)
pts = np.argwhere(canny>0)

cv2.imshow("canny image", canny) 
cv2.waitKey(0)

y1,x1 = pts.min(axis=0)
y2,x2 = pts.max(axis=0)

## crop the region
cropped = img[y1:y2, x1:x2]
cv2.imwrite("cropped.png", cropped)

cv2.imshow("cropped image", cropped) 
cv2.waitKey(0)

tagged = cv2.rectangle(img.copy(), (x1,y1), (x2,y2), (0,255,0), 3, cv2.LINE_AA)
cv2.imshow("tagged", tagged)
cv2.waitKey()
