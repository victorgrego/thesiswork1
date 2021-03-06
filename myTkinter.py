#!/usr/bin/env python	

import pyscreenshot as ImageGrab
import tkinter as tk
from Datapoint import *
from tkinter.simpledialog import *
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from KmeansScreen import *
from MyUtils import *
import MyUtils
import time

import numpy as np

root = tk.Tk()

#TODO
#Fix a bug where if you dont press next or prev it wont save the current clustering space
#Save canvas as image
#insert poits with labels
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

	#Create the widgets in the interface and the dynamic vars associated with them
	def create_widgets(self):
		self.canvas = tk.Canvas(self, width=canvas_width, height=canvas_height,bg=BLACK)
		self.canvas.pack(anchor=W)
		#self.canvas.grid()

		self.savebtn = tk.Button(self, text='Save', command=self.on_save_button)
		self.savebtn.pack(side=LEFT)

		self.loadbtn = tk.Button(self, text='Load', command=self.on_load_datapoints)
		self.loadbtn.pack(side=LEFT)

		self.click_state = StringVar(self)
		self.click_state.set("Click")
		self.clickmenu = OptionMenu(self, self.click_state, "Click", "Distribution", "Random", "Interpolate", command=self.clickmenu_controller)
		self.clickmenu.pack(side=LEFT)
		
		self.leftButton = tk.Button(self, text='previous',command=self.prev_button)			
		self.leftButton.pack(side=LEFT)
		
		self.rightButton = tk.Button(self, text='next',command=self.next_button)			
		self.rightButton.pack(side=LEFT)

		self.saveImageButton = tk.Button(self, text='Save Image',command=self.save_image)		
		self.saveImageButton.pack(side=LEFT)

		self.matchAllButton = tk.Button(self, text='Match All',command=self.run_scan_timeline)		
		self.matchAllButton.pack(side=LEFT)

		self.clustering_state = StringVar(self)
		self.clustering_state.set("Kmeans")
		self.clustering_config = self.__current_clustering_window = KmeansScreen(tk.Toplevel(self))
		self.clusteringmenu = OptionMenu(self, self.clustering_state, "Kmeans", "DBSCAN", command=self.clustering_controller)
		self.clusteringmenu.pack(side=LEFT)

		self.clusteringButton = tk.Button(self, text='Run Clustering',command=self.run_clustering)		
		self.clusteringButton.pack(side=LEFT)

		self.monic_config = MONICScreen(tk.Toplevel(self))


	def run_scan_timeline(self):
		overlaps = scan_timeline()
		print(overlaps)

		for i in range(len(overlaps)):
			#print (overlaps[i])
			detect_external_transitions2(overlaps[i], i, float(self.monic_config.match.get()), float(self.monic_config.split.get()))
			'''if overlaps[i][2] > self.monic_config.match.get():
				print("At clusterings {} and {}, clusters {} and {} match!".format(i,i+1, overlaps[i][0], overlaps[i][1]))'''


	def draw_bounding_circle(self, position, radius, c=WHITE):
		self.canvas.create_oval(position[0]-radius, 
			position[1]-radius, 
			position[0]+radius, 
			position[1]+radius, 
			fill=c)


	def draw_boundind_box(self, x0, y0, x1, y1, c=WHITE):
		self.canvas.create_rectangle(x0, y0, x1, y1, fill=c)


	def run_clustering(self):
		st = self.clustering_state.get()
		self.canvas.delete('all')
		if st == "Kmeans": self.run_Kmeans()
		elif st == "DBSCAN": self.run_DBSCAN()


	def run_DBSCAN(self):
		dbscan = DBSCAN(eps=float(self.clustering_config.eps.get()), 
			min_samples=int(self.clustering_config.min_samples.get()),
			n_jobs=int(self.clustering_config.n_jobs.get())).fit(self.get_clustering_data())
		for i in np.unique(dbscan.labels_):
			shape = self.monic_config.shape_state.get()
			if shape == 'Circle':
				c = min_bound_circle(datapoints, dbscan.labels_, i)
				self.draw_bounding_circle(c[0], c[1])
			elif shape == 'Box':
				c = min_bound_box(datapoints, dbscan.labels_, i)
				self.draw_boundind_box(c[0], c[1], c[2], c[3])
			elif shape == 'Grid':
				c = grid_shape(datapoints, dbscan.labels_, i, [int(self.monic_config.grid_res_x.get()),int(self.monic_config.grid_res_y .get())])
				for cell in c:
					self.draw_boundind_box(cell[0], cell[1], cell[2], cell[3])
			elif shape == 'Quadtree':
				bb = min_bound_box(datapoints, dbscan.labels_, i)
				c = quadtree(datapoints, bb, int(self.monic_config.qt_depth.get()))
				for cell in c:
					self.draw_boundind_box(cell[0], cell[1], cell[2], cell[3])
			

		for i in range(len(dbscan.labels_)):
			datapoints[i].label = dbscan.labels_[i]
			self.draw_datapoint(datapoints[i])


	def run_Kmeans(self):
		kmeans = KMeans(n_clusters=int(self.clustering_config.num_clusters.get()), random_state=0, n_jobs=int(self.clustering_config.num_jobs.get())).fit(self.get_clustering_data())
		for i in np.unique(kmeans.labels_):
			shape = self.monic_config.shape_state.get()
			if shape == 'Circle':
				c = min_bound_circle(datapoints, kmeans.labels_, i)
				self.draw_bounding_circle(c[0], c[1])
			elif shape == 'Box':
				c = min_bound_box(datapoints, kmeans.labels_, i)
				self.draw_boundind_box(c[0], c[1], c[2], c[3])
		
		for i in range(len(kmeans.labels_)):
			datapoints[i].label = kmeans.labels_[i]
			self.draw_datapoint(datapoints[i])


	def save_image(self):
		self.getter(self.canvas)


	def get_clustering_data(self):
		return [i.position for i in datapoints]


	def clustering_controller(self, value):
		self.__clustering_state = value

		if self.__current_clustering_window != None:
			self.__current_clustering_window.close_windows()

		if self.__clustering_state == 'DBSCAN':
			self.__current_clustering_window = self.clustering_config = DBSCANScreen(tk.Toplevel(self))
		elif self.__clustering_state == 'Kmeans':
			self.__current_clustering_window = self.clustering_config = KmeansScreen(tk.Toplevel(self))


	def clickmenu_controller(self, value):
		
		self.__click_state = value
		
		if self.__current_click_window != None:
			self.__current_click_window.close_windows()
		
		if self.__click_state == "Distribution":
			self.__current_click_window = DistributionScreen(tk.Toplevel(self))

		if self.__click_state == "Interpolate":
			self.__current_click_window = InterpolationtionScreen(tk.Toplevel(self))			


	def on_save_button(self):
		a = askstring("File name", "Insert the name of the file without extension" )
		if a != None: 
			save(a, timeline)


	def on_load_datapoints(self):
		global datapoints, timeline

		a = askstring("File name", "Insert the name of the DATAPOINTS file without extension" )
		#a = 'dualall'
		if a != None: 
			MyUtils.timeline = timeline = load(a)
			#print(timeline == MyUtils.timeline)
			#print(len(MyUtils.timeline))
			self.timeline_position = 0
			datapoints = timeline[0]
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
			for i in range(int(self.__current_click_window.size.get())): 
				datapoints.append(Datapoint([event.x + dx[i] , event.y + dy[i]], 
											None if self.__current_click_window.label.get() == 'None' else int(self.__current_click_window.label.get())))

			if self.timeline_position == len(timeline):
				timeline.append(datapoints)
			else:
				timeline[self.timeline_position] = datapoints

			self.update_screen()

		elif st == "Click":
			datapoints.append(Datapoint([event.x,event.y]))
			self.draw_datapoint(datapoints[-1])
		elif st == "Random":
			datapoints.append(Datapoint([np.random.randint(0,canvas_width),
				np.random.randint(0,canvas_height)]))
			self.draw_datapoint(datapoints[-1])
		elif st == "Interpolate":
			if len(timeline) > 0:# and self.timeline_position > 0:
				prev_datapoints = timeline[self.timeline_position]
				center_x = np.mean([i.position[0] for i in prev_datapoints])
				center_y = np.mean([i.position[1] for i in prev_datapoints])
				delta_x, delta_y = event.x - center_x, event.y - center_y
				#print(center_x, center_y)
				#print(delta_x, delta_y)
				#print(event.x, event.y)

				num_steps = int(self.__current_click_window.num_steps.get())
				newpos = []
				xspeed = delta_x / num_steps
				yspeed = delta_y / num_steps
				#print("Xspeed {}, Yspeed {}".format(xspeed, yspeed))
				#print("***")
				
				to_insert = []

				for step in range(1, num_steps+1):
					#print("Xoffset{}, Yoffset{}".format(xspeed*step, yspeed*step))
					xoffset, yoffset = (xspeed * step), (yspeed * step)
					newdatapoints = []
					for i in datapoints:
						_nx = i.position[0] + xoffset + np.random.normal(0, float(self.__current_click_window.scale.get()))
						_ny = i.position[1] + yoffset + np.random.normal(0, float(self.__current_click_window.scale.get()))
						newdatapoints.append(Datapoint([_nx, _ny]))
					timeline.append(newdatapoints)
				
				'''for i in to_insert:
					if self.timeline_position > 0: timeline.insert(self.timeline_position+1, i)
					else: timeline.append(i)
					self.timeline_position+=1'''

				self.update_screen()
			else:
				self.clickmenu_controller("Distribution")
				self.click_state.set("Distribution")
				self.on_mouse_click(event)


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
		self.canvas.delete('all')
		labels_ = [i.label for i in datapoints if i.label is not None]
		if len(labels_) > 0:
			for i in np.unique(labels_):
				c = min_bound_circle(datapoints, labels_, i)
				self.draw_bounding_circle(c[0], c[1])

		for i in datapoints:
			self.draw_datapoint(i)


	def create_new_clustering(self):
		global datapoints
		timeline.append(datapoints)
		datapoints = []
		self.timeline_position += 1


	def getter(self, widget):
		global datapoints

		x=root.winfo_rootx()+widget.winfo_x()
		y=root.winfo_rooty()+widget.winfo_y()
		x1=x+widget.winfo_width()
		y1=y+widget.winfo_height()

		arr = []
		ImageGrab.grab().crop((x,y,x1,y1)).save(str(self.timeline_position)+".png")


def main():
	app = Application()					   
	app.master.title('System')
	app.mainloop() 


if __name__ == '__main__':
	main()