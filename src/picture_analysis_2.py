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
