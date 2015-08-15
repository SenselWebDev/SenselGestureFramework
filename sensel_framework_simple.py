#
# This Python library abstracts Sensel contact data into specific gesture events.
# 

from math import *
from enum import Enum
import sensel
import time

# Delay for events before triggering start call (s)
START_DELAY = 0.2

# Margin of error for identifying a stationary point (mm)
MOE_STATIONARY = 1.5

# Required movement distance to be classified as a pan rather than a tap
PAN_DIST = 3

# Weight class maxiumums
LIGHT_CLASS_MIN = 0
MEDIUM_CLASS_MIN = 2500
HEAVY_CLASS_MIN = 6000

class WeightClass(Enum):
	LIGHT = 0
	MEDIUM = 1
	HEAVY = 2

class GestureState(Enum):
	INITED = 0
	STARTED = 1
	MOVED = 2
	ENDED = 3

class GestureType(Enum):
	TAP = 0
	PAN = 1

class Direction(Enum):
	UP = 0
	RIGHT = 1
	DOWN = 2
	LEFT = 3

#########

def isActiveGesture(gesture):
	return not gesture == None and not gesture.state == GestureState.ENDED

class SenselGesture(object):
	"""docstring for SenselGesture"""
	def __init__(self, contact_points, weight_class, down_x, down_y):
		super(SenselGesture, self).__init__()
		self.contact_points = contact_points
		self.weight_class = weight_class
		self.down_x = down_x
		self.down_y = down_y
		self.down_start_time = time.time()
		self.gesture_type = None
		#self.movement_dist = None
		self.has_started = False
		self.state = GestureState.INITED
		self.tracked_locations = []
		self.addLocation((down_x, down_y))
		self.ydirection = None
		self.xdirection = None
		self.angle = None # Radians

	def addLocation(self, location):
		self.tracked_locations.append(location)
		if(len(self.tracked_locations) > 1):
			delta_y = self.tracked_locations[0][1] - location[1]
			delta_x = self.tracked_locations[0][0] - location[0]
			self.angle = atan2(delta_y, -delta_x)
			if(delta_y > 0):
				self.ydirection = Direction.UP
			else:
				self.ydirection = Direction.DOWN

			if(delta_x > 0):
				self.xdirection = Direction.LEFT
			else:
				self.xdirection = Direction.RIGHT

	def __str__(self):
		return str(self.gesture_type) + ": " + str(self.contact_points) + " fingers, " + str(self.weight_class) + ", state: " + str(self.state) + ", started @ (" + str(self.down_x) + ", " + str(self.down_y) + ", " + str(len(self.tracked_locations)) + " locations, " + str(self.xdirection) + " and " + str(self.ydirection) + " at " + str(self.angle) + " radians"

#########

# Create a new SenselGestureHandler and call the start method to start listening for events
class SenselGestureHandler(object):
	"""docstring for SenselGestureHandler"""
	def __init__(self, arg):
		super(SenselGestureHandler, self).__init__()
		self.arg = arg
		
	def getWeightClass(self, weight):
		if(weight >= HEAVY_CLASS_MIN):
			return WeightClass.HEAVY
		elif(weight >= MEDIUM_CLASS_MIN):
			return WeightClass.MEDIUM
		else:
			return WeightClass.LIGHT

	def euclideanDist(self, a, b):
		# print(a)
		# print(b)
		# print(sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2))
		return sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

	def gestureEvent(self, gesture, arg):
		#print("You must implement this to recieve events")
		if(gesture.state == GestureState.STARTED):
			print("Started gesture: " + str(gesture) + " @ " + str(time.time()))
		#elif(gesture.state == GestureState.MOVED):
			#print("Gesture moved")
		elif(gesture.state == GestureState.ENDED):
			print("Gesture ended: " + str(gesture) + " @ " + str(time.time()))
		#else:
		#	print("Gesture Inited")

	def start(self):
		sensel_device = sensel.SenselDevice()

		if not sensel_device.openConnection():
			print("Unable to open Sensel sensor!")
			exit()

		#Enable contact sending
		sensel_device.setFrameContentControl(sensel.SENSEL_FRAME_CONTACTS_FLAG)
	  
		#Enable scanning
		sensel_device.startScanning(0)

		startGestureTimer = None
		curr_gesture = None

		while True: 
			contacts = sensel_device.readContacts()
	  		#if(startGestureTimer): print(str(time.time()))
			if contacts == None:
				print("NO CONTACTS")
				continue
	   
			# Calculate the average of the locations and weights
			avg_x = None
			avg_y = None
			avg_weight = None
			delta_dist = None
			if(len(contacts) > 0):
				sum_x = 0
				sum_y = 0
				sum_weight = 0
				for c in contacts:
					sum_x += c.x_pos_mm
					sum_y += c.y_pos_mm
					sum_weight += c.total_force
				avg_x = sum_x / len(contacts)
				avg_y = sum_y / len(contacts)
				avg_weight = sum_weight / len(contacts)
				weight_class = self.getWeightClass(avg_weight)
				#print(str(weight_class) + " " + str(avg_x) + " " + str(avg_y) + " " + str(avg_weight))
				if(isActiveGesture(curr_gesture)):
					#print(str(curr_gesture.gesture_type) + " " + str(curr_gesture.state) + " " + str(isActiveGesture(curr_gesture)))

					delta_dist = self.euclideanDist((avg_x, avg_y), (curr_gesture.down_x, curr_gesture.down_y))
					#print(delta_dist)
					if(not curr_gesture.has_started):
						#print("checking start delay: " + str(time.time()) + " - " + str(startGestureTimer) + " >=? " + str(START_DELAY) + " ... " + str(time.time() - startGestureTimer))
						# If the elapsed time is greater than the delay time than start the gesture
						if(time.time() - startGestureTimer >= START_DELAY):
							# Set the type
							#print("inside!!! " + str(delta_dist))
							if(delta_dist >= PAN_DIST):
								curr_gesture.gesture_type = GestureType.PAN
								#print(curr_gesture.gesture_type)
							else:
								curr_gesture.gesture_type = GestureType.TAP
							#curr_gesture.movement_dist = delta_dist
							curr_gesture.contact_points = len(contacts)
							curr_gesture.weight_class = weight_class
							# EVENT: On start
							curr_gesture.state = GestureState.STARTED
							self.gestureEvent(curr_gesture, self.arg)
							curr_gesture.has_started = True
					# Modify to determine swipes vs taps by start call
					if(curr_gesture.state == GestureState.MOVED or (delta_dist and delta_dist > MOE_STATIONARY)):
						# EVENT: On Move
						curr_gesture.state = GestureState.MOVED
						curr_gesture.addLocation((avg_x, avg_y))
						self.gestureEvent(curr_gesture, self.arg)
						#print("Gesture has moved: " + str(delta_dist))


				else:
					# Init the new gesture
					curr_gesture = SenselGesture(len(contacts), weight_class, avg_x, avg_y)
					startGestureTimer = time.time()
					#print("Inited gesture")
			# No contacts remain, so end the gesture
			else:
				if(isActiveGesture(curr_gesture)):
					if(not curr_gesture.has_started):
						# Default to taps here since the touch was so quick it triggered before the start
						curr_gesture.gesture_type = GestureType.TAP
						# Trigger a quick start call before the end call
						# This can happen with quick taps
						# EVENT: On Start
						curr_gesture.state = GestureState.STARTED
						self.gestureEvent(curr_gesture, self.arg)
					curr_gesture.state = GestureState.ENDED
					# EVENT: On End
					self.gestureEvent(curr_gesture, self.arg)

		sensel_device.stopScanning();
		sensel_device.closeConnection();

if __name__ == '__main__':
	sgh = SenselGestureHandler(None)
	sgh.start()
