from threading import Thread
import cv2
import pandas as pd
import numpy as np
import os
import imutils
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import datetime
import csv



def nothing(x):
    pass
    
class WebcamVideoStream:
	def __init__(self, src=0):
		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(src)
		self.grabbed, self.frame = self.stream.read()
		self.windowName = 'Webcam Live video feed'
		self.thresh = 125
		self.max_area = 0.0
		self.stopped = False
		
	def start(self):
		# start the thread to read frames from the video stream
		Thread(target=self.update, args=()).start()
		return self
	def update(self):
		# keep looping infinitely until the thread is stopped
		cv2.namedWindow(self.windowName)
		cv2.createTrackbar("threshold", self.windowName, self.thresh, 255, nothing)
		while True:
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return
			# otherwise, read the next frame from the stream
			(self.grabbed, self.frame) = self.stream.read()
			proc_frame = self.frame.copy()
			self.thresh= cv2.getTrackbarPos("threshold", self.windowName)
			ret,thresh1 = cv2.threshold(proc_frame,self.thresh,255,cv2.THRESH_BINARY_INV)
			closing = cv2.cvtColor(thresh1,cv2.COLOR_BGR2GRAY)
			contours,hierarchy = cv2.findContours(closing,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
			closing = cv2.cvtColor(closing,cv2.COLOR_GRAY2RGB)
			
			areas = []
			for contour in contours:
			    ar = cv2.contourArea(contour)
			    areas.append(ar)
			try:
			    self.max_area = max(areas)
			    max_area_index = areas.index(self.max_area)
			    cnt = contours[max_area_index]
			    cv2.drawContours(proc_frame, [cnt], 0, (0,0,255), 1)
			    cv2.imshow('Thresholded', closing)
			    cv2.imshow(self.windowName, proc_frame)  
			except ValueError:
			    cv2.imshow(self.windowName, proc_frame)
			    if cv2.waitKey(1) == 113:
			        self.stopped = True
			if cv2.waitKey(1) == 113:
			    self.stop()
	def read(self):
		# return the frame most recently read
		return self.frame
	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
	def read_area(self):
	        return self.max_area


class Record:
    def __init__(self):
        self.n_ovocito = None
        self.gen1 = None
        self.gen2 = None
        self.masa1 = None
        self.masa2 = None
        self.pH_interno = None
        self.pH_externo = None
        self.osmolaridad = None
        self.dilucion = None
        self.horas_expresion = None
        self.area = None
        self.snapshot_time = None
        self.tiempo = None
        self.condition = None
        self.header = ['n_ovocito', 'gen1', 'gen2', 'masa1', 'masa2', 'pH_interno', 'pH_externo', 'osmolaridad', 'dilucion', 'horas_expresion', 'area', 'tiempo', 'condition']
        self.row = None
        
    def write_header(self, fname):
        if fname not in os.listdir('./'):
            with open(fname, 'a') as file:
                write = csv.writer(file)
                write.writerows((self.header,))
#            with open(fname,'a') as file:
#                file.write(','.join(self.header))
    
    def update_row(self):
        self.row = [getattr(self, var) for var in self.header]
    
    def write_row(self, fname):
        self.update_row()
        with open(fname, 'a') as file:
            write = csv.writer(file)
            write.writerows((self.row,))
#            file.write(','.join(self.row))
            

def set_record_attr(record, lista, types):
    for parameter in lista:
        param_value = input(f'Asignar valor a {parameter}: ')
        if param_value == 'quit':
            vs.stop()
            quit()
        setattr(record,parameter, types[parameter](param_value))
    record.update_row()
        

def select_variables(all_vars):
    print('\n'*5)
    print('-'*40)
    print('Seleccioná tus variables \ningresando los números separados por coma')
    print('-'*40)
    for i, variable in enumerate(all_vars):
        print(f'{i} - {variable}')
    print('-'*40)
    xp_variables = input()
    if xp_variables == 'quit':
        vs.stop()
        quit()
    xp_variables = xp_variables.split(',')
    xp_variables = [all_vars[int(i)] for i in xp_variables]
    xp_parameters = [parameter for parameter in all_vars if parameter not in xp_variables]
    with open('variables.csv','a') as file:
        write = csv.writer(file)
        write.writerows((xp_variables,))
    return (xp_variables, xp_parameters)
    
def set_timings():
    total_time = float(input('Ingresá el tiempo total de registro (segundos): ')) 
    snapshot_window = float(input('Ingresá el tiempo entre fotos (segundos): '))
    area_window = float(input('Ingresá el tiempo entre registros de area (segundos): '))
    return (total_time, snapshot_window, area_window)    
    
    

		
vs = WebcamVideoStream(src=0).start()
while vs.max_area == 0.0:
    pass

all_variables = ['gen1', 'gen2', 'masa1', 'masa2', 'pH_interno', 'pH_externo', 'osmolaridad', 'dilucion', 'horas_expresion']
all_variables_types = {
    'gen1':str,
    'gen2':str,
    'masa1':float,
    'masa2':float,
    'pH_interno':float,
    'pH_externo':float,
    'osmolaridad':float,
    'dilucion':eval,
    'horas_expresion':float} 

record = Record()
xp_vars, xp_parms = select_variables(all_variables)
set_record_attr(record, xp_parms, all_variables_types)


total_time, snapshot_window, area_window = set_timings()
record.n_ovocito = int(input('Número de ovocito inicial: '))

print(record.row)
print('-'*40)
print('\n'*5)

registro_fname = 'registro_areas.csv'
record.write_header(registro_fname)
        
program_started = True
run_record = False
condition = 'Arosoro'

while program_started:
          
    if program_started and not run_record:
        print(f'Condición actual: {condition}')
        ask_set_vars = int(input('¿Querés asignar nueva condición o salir?\n0 - No\n1 - Si\n'))
        if ask_set_vars:
            set_record_attr(record, xp_vars, all_variables_types)          
            condition = '-'.join([str(getattr(record,var)) for var in xp_vars])
        os.mkdir(f'./{record.n_ovocito}')
        initial_time_record = datetime.datetime.now().timestamp()
        initial_time_snap = datetime.datetime.now().timestamp()
        record.area, frame = vs.max_area, vs.frame
        record.tiempo = 0.0
        record.snapshot_time = 0.0
        n_record = 1
        n_snap = 1
        record.condition = condition
        record.update_row()
        record.write_row(registro_fname)
        cv2.imwrite(f'./{record.n_ovocito}/{condition}-{record.snapshot_time:02.0f}.pgm', cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))        
        run_record = True
    
    if run_record:
        now = datetime.datetime.now().timestamp()
        record.tiempo = (now-initial_time_record)
        area_time_window_passed =  record.tiempo > (n_record * area_window)
        
          
        if area_time_window_passed:
            n_record += 1
            record.area = vs.max_area
            record.update_row()
            record.write_row(registro_fname)
            print(f'{record.tiempo:5.2f} {record.area}')

            
        record.snapshot_time = (now-initial_time_record)
        snapshot_time_window_passed = record.snapshot_time > n_snap * snapshot_window 
        
        if snapshot_time_window_passed:
            n_snap += 1
            frame = vs.frame
            cv2.imwrite(f'./{record.n_ovocito}/{condition}-{record.snapshot_time:02.0f}.pgm', cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
            
    
        if record.tiempo >= total_time:
            run_record = False
            record.n_ovocito += 1    
    

        
        
        
        
        
