import os
import cv2 as cv
import csv
import pandas as pd

def read_img(fname):
    img = cv.imread(fname,0)
    return img

def process_img(img):
    img_color = cv.cvtColor(img, cv.COLOR_GRAY2BGR)
    blur = cv.GaussianBlur(img,(5,5),0)
    ret,thresh = cv.threshold(blur,0,255,cv.THRESH_BINARY_INV+cv.THRESH_OTSU)
    contours, hierarchy = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    areas = []
    for contour in contours:
        ar = cv.contourArea(contour)
        areas.append(ar)    
    max_area = max(areas)
    max_area_index = areas.index(max_area)
    long_cont = contours[max_area_index]
    cv.drawContours(img_color, [long_cont], -1, (0,255,0), 2)
    return(max_area, img_color)

def read_vars(fname):
    with open(fname) as file:
        variables = eval(next(file))
        parms = eval(next(file))
        return (variables, parms)


#os.chdir('/mnt/storage/home/geraz/experimentos_ovocitos/20220211')
root = '.'
thresh_dir_name = 'thresholded'
vars_fname = 'variables.csv'
variables, parms_dict = read_vars(vars_fname)
variables = variables + ['tiempo', 'area', 'condition','n_ovocito']
df = pd.DataFrame(columns = variables + list(parms_dict.keys()))
root,dirs,files=next(os.walk(root))
for directory in dirs:
    thresh_path = os.path.join(root,directory,thresh_dir_name)
    file_list = os.listdir(directory)
    os.mkdir(thresh_path)
    for file in file_list:
        if '.pgm' in file:
            #calcular_circularidad_perimetro() #TODO
            name = file.rsplit('.', 1)[0]
            fname = os.path.join(root,directory,file)
            img = read_img(fname)
            area, img_thresh = process_img(img)
            vars_values = name.split('-')[0:-1]
            tiempo = float(name.rsplit('-',1)[1])
            condition = name.rsplit('-', 1)[0]
            n_ovocito = int(directory)
            vars_values = vars_values + [tiempo]+[area] + [condition] + [n_ovocito]
            vars_dict = dict(zip(variables,vars_values))
            parms_dict.update(vars_dict)
            df_row = pd.DataFrame(parms_dict, index =[0])
            df = pd.concat([df, df_row], ignore_index = True)
            cv.imwrite(f'{thresh_path}/{name}.jpg', img_thresh)

df_mod = df.sort_values(by=['n_ovocito', 'tiempo'])
df.to_csv('registro_fotos.csv')

        
#%%
# in a terminal
# python -m pip install --user opencv-contrib-python numpy scipy matplotlib ipython jupyter pandas sympy nose

import cv2 as cv
import pandas as pd
import numpy as np
import os
import imutils
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import matplotlib.pyplot as plt



img_fname = './1/NI-7.0-04.pgm'
img = cv.imread(img_fname,0)

img_color = cv.cvtColor(img, cv.COLOR_GRAY2BGR)
ret,th1 = cv.threshold(img,125,255,cv.THRESH_BINARY_INV)

blur = cv.GaussianBlur(img,(5,5),0)
ret4,thresh = cv.threshold(blur,0,255,cv.THRESH_BINARY_INV+cv.THRESH_OTSU)


contours, hierarchy = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

areas = []
for contour in contours:
    ar = cv.contourArea(contour)
    areas.append(ar)

long_cont = max(contours, key = len)
print(max(areas))
cv.drawContours(img_color, [long_cont], -1, (0,255,0), 3)

plt.imshow(img_color)
plt.show()
#%%

# using cam built-in to computer
videocapture=cv2.VideoCapture(0)

# using IP camera address from my mobile phone, with Android 'IP Webcam' app over WiFi
# videocapture=cv2.VideoCapture("http://xxx.xxx.xxx.xxx:8080/video")

def safe_div(x,y): # so we don't crash so often
    if y==0: return 0
    return x/y

def nothing(x): # for trackbar
    pass

def rescale_frame(frame, percent=50):  # make the video windows a bit smaller
    width = int(frame.shape[1] * percent/ 100)
    height = int(frame.shape[0] * percent/ 100)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

if not videocapture.isOpened():
    print("can't open camera")
    exit()
    
windowName="Webcam Live video feed"

cv2.namedWindow(windowName)

# Sliders to adjust image
# https://medium.com/@manivannan_data/set-trackbar-on-image-using-opencv-python-58c57fbee1ee
cv2.createTrackbar("threshold", windowName, 125, 255, nothing)
cv2.createTrackbar("kernel", windowName, 5, 30, nothing)
cv2.createTrackbar("iterations", windowName, 1, 10, nothing)
cv2.createTrackbar("empezar", windowName, 0, 1, nothing)

record_time_window = 1.0 # tiempo entre registro de areas (en segundos)
snapshot_time_window = 10.0 # tiempo entre registro de fotos (en segundos)
max_time = 240.0 # tiempo total de registro de fotos y areas (en segundos)

oocyte_n = 60
snapshot_time = 0
record_time = 0
condition = 'arosoro'
program_started = False
run_record = False
showLive=True

while(showLive):
    ret, frame=videocapture.read()
    frame_resize = rescale_frame(frame)
    if not ret:
        print("cannot capture the frame")
        exit()
   
    thresh= cv2.getTrackbarPos("threshold", windowName) 
    ret,thresh1 = cv2.threshold(frame_resize,thresh,255,cv2.THRESH_BINARY_INV) 
    
    #kern=cv2.getTrackbarPos("kernel", windowName) 
    #kernel = np.ones((kern,kern),np.uint8) # square image kernel used for erosion
    
    #itera=cv2.getTrackbarPos("iterations", windowName) 
    #dilation =   cv2.dilate(thresh1, kernel, iterations=itera)
    #erosion = cv2.erode(dilation,kernel,iterations = itera) # refines all edges in the binary image

    #opening = cv2.morphologyEx(erosion, cv2.MORPH_OPEN, kernel)
    #closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)  
    #closing = cv2.cvtColor(closing,cv2.COLOR_BGR2GRAY)
    closing = cv2.cvtColor(thresh1,cv2.COLOR_BGR2GRAY)
    
    contours,hierarchy = cv2.findContours(closing,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE) # find contours with simple approximation cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE

    closing = cv2.cvtColor(closing,cv2.COLOR_GRAY2RGB)
    
    cv2.drawContours(closing, contours, -1, (128,255,0), 1)
    
    # focus on only the largest outline by area
    areas = [] #list to hold all areas

    for contour in contours:
      ar = cv2.contourArea(contour)
      areas.append(ar)
    try:
        max_area = max(areas)
    except ValueError:
        cv2.imshow(windowName, frame_resize)
        cv2.waitKey(1)
        continue
        
    max_area_index = areas.index(max_area)  # index of the list element with largest area

    cnt = contours[max_area_index] # largest area contour is usually the viewing window itself, why?

    cv2.drawContours(closing, [cnt], 0, (0,0,255), 1)
    
    def midpoint(ptA, ptB): 
      return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)

    # compute the rotated bounding box of the contour
    orig = frame_resize.copy()
    box = cv2.minAreaRect(cnt)
    box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
    box = np.array(box, dtype="int")
    
    # order the points in the contour such that they appear
    # in top-left, top-right, bottom-right, and bottom-left
    # order, then draw the outline of the rotated bounding
    # box
    box = perspective.order_points(box)
    cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 1)
 
    # loop over the original points and draw them
    for (x, y) in box:
      cv2.circle(orig, (int(x), int(y)), 5, (0, 0, 255), -1)

    # unpack the ordered bounding box, then compute the midpoint
    # between the top-left and top-right coordinates, followed by
    # the midpoint between bottom-left and bottom-right coordinates
    (tl, tr, br, bl) = box
    (tltrX, tltrY) = midpoint(tl, tr)
    (blbrX, blbrY) = midpoint(bl, br)
     
    # compute the midpoint between the top-left and top-right points,
    # followed by the midpoint between the top-righ and bottom-right
    (tlblX, tlblY) = midpoint(tl, bl)
    (trbrX, trbrY) = midpoint(tr, br)
     
    # draw the midpoints on the image
    cv2.circle(orig, (int(tltrX), int(tltrY)), 5, (255, 0, 0), -1)
    cv2.circle(orig, (int(blbrX), int(blbrY)), 5, (255, 0, 0), -1)
    cv2.circle(orig, (int(tlblX), int(tlblY)), 5, (255, 0, 0), -1)
    cv2.circle(orig, (int(trbrX), int(trbrY)), 5, (255, 0, 0), -1)
     
    # draw lines between the midpoints
    cv2.line(orig, (int(tltrX), int(tltrY)), (int(blbrX), int(blbrY)),(255, 0, 255), 1)
    cv2.line(orig, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)),(255, 0, 255), 1)
    cv2.drawContours(orig, [cnt], 0, (0,0,255), 1)
    
    # compute the Euclidean distance between the midpoints
    dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
    dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))

    # compute the size of the object
    pixelsPerMetric = 1 # more to do here to get actual measurements that have meaning in the real world
    dimA = dA / pixelsPerMetric
    dimB = dB / pixelsPerMetric
 
    # draw the object sizes on the image
    cv2.putText(orig, "{:.1f}mm".format(dimA), (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    cv2.putText(orig, "{:.1f}mm".format(dimB), (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    # compute the center of the contour
    M = cv2.moments(cnt)
    cX = int(safe_div(M["m10"],M["m00"]))
    cY = int(safe_div(M["m01"],M["m00"]))
 
    # draw the contour and center of the shape on the image
    cv2.circle(orig, (cX, cY), 5, (255, 255, 255), -1)
    cv2.putText(orig, "center", (cX - 20, cY - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
 
    cv2.imshow(windowName, orig)
    cv2.imshow('Thresholded', closing)
    if cv2.waitKey(1) == 113:
        showLive=False
        

        
videocapture.release()
cv2.destroyAllWindows()
