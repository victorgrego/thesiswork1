#!/usr/bin/env python	  
import tkinter as tk
from tkinter.simpledialog import *
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from KmeansScreen import *

import numpy as np

#colors
WHITE = '#fff'
BLACK = '#000'

RED = '#f00'
GREEN = '#0f0'
BLUE = '#00f'

YELLOW = '#ff0'
CYAN = '#0ff'
MAGENTA = '#f0f'

GRAY = '#aaa'


datapoint_radius = 3

#canvas declaration
canvas_width = 800
canvas_height = 800

#stores a timeline of clustering spaces
timeline = []

#array of datapoints
datapoints = []

root = tk.Tk()

class Datapoint:
	def __init__(self, position, label=None):
		self.position = position
		self.label = label

	@property
	def position(self):
		return self.__position

	@position.setter
	def position(self, position):
		self.__position = position

		if self.__position[0] < 0:
			self.__position[0] = 0
		elif self.__position[0] > canvas_width:
			self.__position[0] = canvas_width
		
		if self.__position[1] < 0:
			self.__position[1] = 0
		elif self.__position[1] > canvas_height:
			self.__position[1] = canvas_height
	
	def get_fill(self):
		colors = [GREEN,BLUE,YELLOW, WHITE, CYAN, MAGENTA, GRAY]
		try:
			return colors[self.label]
		except:
			return RED

	def draw(self, canvas):
		#print(self.position)
		canvas.create_oval(int(self.position[0])-datapoint_radius, 
			self.position[1]-datapoint_radius, 
			self.position[0]+datapoint_radius, 
			self.position[1]+datapoint_radius, 
			fill=self.get_fill())

class Application(tk.Frame):
	def __init__(self, master=None):
		tk.Frame.__init__(self, master)
		self.grid()					   
		self.create_widgets()
		self.bind_events()
		
		#TODO:
		#Migrate to a initialize_vars routine -> has to run before widgets and events
		self.timeline_position = 0
		self.__current_click_window = None

	def clickmenu_controller(self, value):
		
		self.__click_state = value
		
		if self.__current_click_window != None:
			self.__current_click_window.close_windows()
		
		if self.__click_state == "Distribution":
			self.__current_click_window = DistributionScreen(tk.Toplevel(self))

	def create_widgets(self):
		self.canvas = tk.Canvas(self, width=canvas_width, height=canvas_height,bg=BLACK)
		self.canvas.pack(anchor=W)
		#self.canvas.grid()

		'''self.savebtn = tk.Button(self, text='Save', command=self.on_save_button)
		self.savebtn.pack(side=LEFT)

		self.loadbtn = tk.Button(self, text='Load Datapoints', command=self.on_load_datapoints)
		self.loadbtn.pack(side=LEFT)'''			

		self.click_state = StringVar(self)
		self.click_state.set("Click")
		self.clickmenu = OptionMenu(self, self.click_state, "Click", "Distribution", "Random", command=self.clickmenu_controller)
		self.clickmenu.pack(side=LEFT)
		
		self.leftButton = tk.Button(self, text='previous',command=self.prev_button)			
		self.leftButton.pack(side=LEFT)
		
		self.rightButton = tk.Button(self, text='next',command=self.next_button)			
		self.rightButton.pack(side=LEFT)

		self.clusteringButton = tk.Button(self, text='Run Clustering',command=self.run_clustering)		
		self.clusteringButton.pack(side=LEFT)

		self.matchButton = tk.Button(self, text='Match to Next',command=self.match_next)		
		self.matchButton.pack(side=LEFT)

		self.clustering_state = StringVar(self)
		self.clustering_state.set("Kmeans")
		self.kmeans_config = self.new_window()
		self.clusteringmenu = OptionMenu(self, self.clustering_state, "Kmeans", "DBSCAN")
		self.clusteringmenu.pack(side=LEFT)

	def new_window(self):
		return KmeansScreen(tk.Toplevel(self))

	def min_bound_circle(self, labels, target):
		xpos = [datapoints[j].position[0] for j in range(len(labels)) if labels[j] == target]
		ypos = [datapoints[j].position[1] for j in range(len(labels)) if labels[j] == target]

		xavg = np.mean(xpos)
		yavg = np.mean(ypos)

		radius = np.max([np.linalg.norm(np.array([xavg, yavg])-np.array([xpos[i], ypos[i]])) for i in range(len(xpos))])
		return [[xavg, yavg], radius]

	def draw_bounding_circle(self, position, radius, c=WHITE):
		self.canvas.create_oval(position[0]-radius, 
			position[1]-radius, 
			position[0]+radius, 
			position[1]+radius, 
			fill=c)

	def run_clustering(self):
		st = self.clustering_state.get()
		self.canvas.delete('all')
		if st == "Kmeans": self.run_Kmeans()
		elif st == "DBSCAN": self.run_DBSCAN()

	def run_DBSCAN(self):
		dbscan = DBSCAN(eps=50, n_jobs=-1).fit(self.get_clustering_data())
		for i in np.unique(dbscan.labels_):
			c = self.min_bound_circle(dbscan.labels_, i)
			self.draw_bounding_circle(c[0], c[1])

		for i in range(len(dbscan.labels_)):
			datapoints[i].label = dbscan.labels_[i]
			self.draw_datapoint(datapoints[i])

	def run_Kmeans(self):
		kmeans = KMeans(n_clusters=int(self.kmeans_config.num_clusters.get()), random_state=0, n_jobs=int(self.kmeans_config.num_jobs.get())).fit(self.get_clustering_data())
		for i in np.unique(kmeans.labels_):
			c = self.min_bound_circle(kmeans.labels_, i)
			self.draw_bounding_circle(c[0], c[1])
		
		for i in range(len(kmeans.labels_)):
			datapoints[i].label = kmeans.labels_[i]
			self.draw_datapoint(datapoints[i])


	#Based on this: https://stackoverflow.com/questions/4247889/area-of-intersection-between-two-circles
	#and this: http://mathworld.wolfram.com/Circle-CircleIntersection.html
	#this just calculates between circles!
	def intersection_area(self, c0, r0, c1, r1):
		x0, y0 = c0[0], c0[1]
		x1, y1 = c1[0], c1[1]

		rr0 = r0 * r0
		rr1 = r1 * r1
		d = np.linalg.norm(np.array([x0,y0]) - np.array([x1,y1]))
		#np.sqrt((x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0))
		#print(r0, np.pi * rr0, r1, np.pi * rr1)

		#Circles do not overlap
		if d > r1 + r0: return 0
		#Circle1 is completely inside circle0
		elif d <= np.absolute(r0 - r1) and r0 >= r1: 
			#print('r0')
			return np.pi * rr0 / (np.pi * rr0)
		#Circle0 is completely inside circle1
		elif d <= np.absolute(r0 - r1) and r0 < r1: 
			#print('r1')
			return np.pi * rr0 / (np.pi * rr1)
		else:
			#print('else')
			phi = (np.arccos((rr0 + (d * d) - rr1) / (2 * r0 * d))) * 2
			theta = (np.arccos((rr1 + (d * d) - rr0) / (2 * r1 * d))) * 2
			area1 = 0.5 * theta * rr1 - 0.5 * rr1 * np.sin(theta)
			area2 = 0.5 * phi * rr0 - 0.5 * rr0 * np.sin(phi)
			overlap = area1 + area2
			total = (np.pi * rr0 + np.pi * rr1) - overlap
			return overlap/total

	def match_next(self):
		self.get_matches(timeline[self.timeline_position], timeline[self.timeline_position+1])

	#Given two sets of clusterings, prints the matches between a pair A,B
	def get_matches(self, set1, set2):
		labels_a = [i.label for i in set1]
		labels_b = [i.label for i in set2]
		get_clusters = lambda x: [self.min_bound_circle(x, i) for i in np.unique(x)]
		clusters_a = get_clusters(labels_a)
		clusters_b = get_clusters(labels_b)

		for i in clusters_a:
			for j in clusters_b:
				print (self.intersection_area(i[0], i[1], j[0], j[1]))

	def get_clustering_data(self):
		return [i.position for i in datapoints]

	def on_save_button(self):
		a = askstring("File name", "Insert the name of the file without extension" )
		if a != None: 
			for i in range(len(timeline)):
				np.save(a + str(i), np.array(a))

	def on_load_datapoints(self):
		global datapoints
		a = askstring("File name", "Insert the name of the DATAPOINTS file without extension" )
		if a != None: 
			datapoints = np.load(a+".npy")
			self.update_screen()

	def bind_events(self):
		#Mouse left button click
		self.canvas.bind("<Button 1>",self.on_mouse_click)

	def draw_datapoint(self, d):
		d.draw(self.canvas)

	def on_mouse_click(self, event):
		st = self.click_state.get()
		if st == "Distribution":
			dx = np.random.normal(0, float(self.__current_click_window.scale.get()), int(self.__current_click_window.size.get()))
			dy = np.random.normal(0, float(self.__current_click_window.scale.get()), int(self.__current_click_window.size.get()))
			for i in range(int(self.__current_click_window.size.get())): datapoints.append(Datapoint([event.x + dx[i] , event.y + dy[i]]))
			self.update_screen()

		elif st == "Click":
			datapoints.append(Datapoint([event.x,event.y]))
			self.draw_datapoint(datapoints[-1])
		elif st == "Random":
			datapoints.append(Datapoint([np.random.randint(0,canvas_width),
				np.random.randint(0,canvas_height)]))
			self.draw_datapoint(datapoints[-1])

	def next_button(self):
		global datapoints, timeline
		if len(datapoints) > 0:
			#self.timeline_position == len(timeline) or 
			if self.timeline_position == len(timeline):
				timeline.append(datapoints)
				datapoints = []
				self.timeline_position += 1
			else:
				timeline[self.timeline_position] = datapoints
				self.timeline_position += 1
				datapoints = (timeline[self.timeline_position] if self.timeline_position < len(timeline) else [])
			
			self.canvas.delete('all')
			self.update_screen()
			#print(datapoints, self.timeline_position, len(timeline))
			#print("ta",timeline)

	def prev_button(self):
		global datapoints, timeline
		
		if not (self.timeline_position > 0): return
		if self.timeline_position == len(timeline) and len(datapoints) > 0:
			timeline.append(datapoints)

		self.canvas.delete('all')
		self.timeline_position -= 1
		datapoints = timeline[self.timeline_position]
		self.update_screen()

	#TODO
	#Fix error where it does not update after clustering and adding more points
	def update_screen(self):
		labels_ = [i.label for i in datapoints]
		if len(labels_) > 0 and labels_[0] != None:
			for i in np.unique(labels_):
				
				c = self.min_bound_circle(labels_, i)
				self.draw_bounding_circle(c[0], c[1])

		for i in datapoints:
			self.draw_datapoint(i)

	def create_new_clustering(self):
		global datapoints
		timeline.append(datapoints)
		datapoints = []
		self.timeline_position += 1

def main():
	app = Application()					   
	app.master.title('System')	
	app.mainloop() 

if __name__ == '__main__':
	main()

