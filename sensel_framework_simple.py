#
# This Python library abstracts Sensel contact data into specific gesture events.
# 

from math import sqrt
from enum import Enum
import sensel
import time

# Delay for events before triggering start call (s)
START_DELAY = 0.02

# Margin of error for identifying a stationary point (mm)
MOE_STATIONARY = 1.5

# Weight class maxiumums
LIGHT_CLASS_MIN = 0
MEDIUM_CLASS_MIN = 2500
HEAVY_CLASS_MIN = 8000

class WeightClass(Enum):
	LIGHT = 0
	MEDIUM = 1
	HEAVY = 2

class GestureState(Enum):
	INITED = 0
	STARTED = 1
	ENDED = 2

class GestureType(Enum):
	TAP = 0
	PAN = 1

#########

def isActiveGesture(gesture):
	return not (gesture == None or gesture.state == GestureState.ENDED)

class SenselGesture(object):
	"""docstring for SenselGesture"""
	def __init__(self, contact_points, weight_class, down_x, down_y):
		super(SenselGesture, self).__init__()
		self.contact_points = contact_points
		self.weight_class = weight_class
		self.down_x = down_x
		self.down_y = down_y
		self.down_start_time = time.clock()
		self.gesture_type = None
		self.state = GestureState.INITED

	def __str__(self):
		return str(self.contact_points) + " fingers, " + str(self.weight_class) + ", state: " + str(self.state) + ", started @ (" + str(self.down_x) + ", " + str(self.down_y) + ")"

#########

# Create a new SenselGestureHandler and call the start method to start listening for events
class SenselGestureHandler(object):
	"""docstring for SenselGestureHandler"""
	def __init__(self):
		super(SenselGestureHandler, self).__init__()
		
	def getWeightClass(self, weight):
		if(weight >= HEAVY_CLASS_MIN):
			return WeightClass.HEAVY
		elif(weight >= MEDIUM_CLASS_MIN):
			return WeightClass.MEDIUM
		else:
			return WeightClass.LIGHT

	def gestureEvent(self, gesture):
		#print("You must implement this to recieve events")
		if(gesture.state == GestureState.STARTED):
			print("Started gesture: " + str(gesture) + " @ " + str(time.clock()))
		elif(gesture.state == GestureState.ENDED):
			print("Gesture ended")
		else:
			print("Gesture Inited")

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
	  		#if(startGestureTimer): print(str(time.clock()))
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
					if(curr_gesture.state == GestureState.INITED):
						# If the elapsed time is greater than the delay time than start the gesture
						if(time.clock() - startGestureTimer >= START_DELAY):
							curr_gesture.state = GestureState.STARTED
							curr_gesture.contact_points = len(contacts)
							curr_gesture.weight_class = weight_class
							# EVENT: On start
							self.gestureEvent(curr_gesture)
					delta_dist = sqrt((avg_x-curr_gesture.down_x)**2 + (avg_y-curr_gesture.down_y)**2)
					# Modify to determine swipes vs taps by start call
					#if(delta_dist and delta_dist > MOE_STATIONARY):
						#print("Gesture has moved: " + str(delta_dist))

						# EVENT: On Move
				else:
					# Init the new gesture
					curr_gesture = SenselGesture(len(contacts), weight_class, avg_x, avg_y)
					startGestureTimer = time.clock()
					print("Inited gesture")
			# No contacts remain, so end the gesture
			else:
				if(isActiveGesture(curr_gesture)):
					if(curr_gesture.state == GestureState.INITED):
						# Trigger a quick start call before the end call
						# This can happen with quick taps
						# EVENT: On Start
						curr_gesture.state = GestureState.STARTED
						self.gestureEvent(curr_gesture)
					curr_gesture.state = GestureState.ENDED
					# EVENT: On End
					self.gestureEvent(curr_gesture)

		sensel_device.stopScanning();
		sensel_device.closeConnection();

if __name__ == '__main__':
	sgh = SenselGestureHandler()
	sgh.start()
