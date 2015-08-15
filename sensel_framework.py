#
# This Python library abstracts Sensel contact data into specific gesture events.
# 

from math import sqrt
from enum import Enum
import sensel
import time

# Delay for events before triggering start call (s)
START_DELAY = 0.03

# Delay before declaring a change in gesture (s)
CHANGE_DELAY = 0.03

# Margin of error for identifying a stationary point (mm)
MOE_STATIONARY = 1.5

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
	ENDED = 2

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

		self.state = GestureState.INITED

	def __str__(self):
		return str(self.contact_points) + " fingers, " + str(self.weight_class) + ", state: " + str(self.state) + ", started @ (" + str(self.down_x) + ", " + str(self.down_y) + ")"

	def __eq__(self, other):
		if(other == None): return False
		gesture_changed = False
		delta_dist = None # Calculate
		if(isActiveGesture(other)):
			delta_dist = sqrt((self.down_x-other.down_x)**2 + (self.down_y-other.down_y)**2)
		# If number of contacts changed
		if(not self.contact_points == other.contact_points):
			print("Contacts Points changed: " + str(self.contact_points) + " => " + str(other.contact_points))
			gesture_changed = True
		# Check if location changed
		elif(delta_dist and delta_dist > MOE_STATIONARY):
			print("Gesture has moved: " + str(delta_dist))
			gesture_changed = True
		# Check if the weight class has changed
		elif(not self.weight_class == other.weight_class):
			print("Weight class has changed: " + str(self.weight_class) + " => " + str(other.weight_class))
			gesture_changed = True
		return gesture_changed
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

	def gestureEvent(gesture):
		print("You must implement this to recieve events")
		return

	def start(self):
		sensel_device = sensel.SenselDevice()

		if not sensel_device.openConnection():
			print("Unable to open Sensel sensor!")
			exit()

		#Enable contact sending
		sensel_device.setFrameContentControl(sensel.SENSEL_FRAME_CONTACTS_FLAG)
	  
		#Enable scanning
		sensel_device.startScanning(0)

		intraGestureTimer = None
		changeGestureTimer = None
		curr_gesture = None

		while True: 
			contacts = sensel_device.readContacts()
	  		#if(intraGestureTimer): print(str(time.clock()))
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

			# Determine which events to call
			if(isActiveGesture(curr_gesture)):
				next_gesture = SenselGesture(len(contacts), weight_class, avg_x, avg_y)
				if(not curr_gesture.state == GestureState.ENDED):
					if(not curr_gesture == next_gesture): 
						if(changeGestureTimer == None):
							changeGestureTimer = time.clock()
						elif(changeGestureTimer - time.clock() > CHANGE_DELAY):
							changeGestureTimer = None
							# End the current gesture
							curr_gesture.state = GestureState.ENDED
							print("Current Gesture has ended")
							# EVENT: On End
							# If at least one contact is still down, init a new gesture
							if(len(contacts) > 0):
								curr_gesture = SenselGesture(len(contacts), weight_class, avg_x, avg_y)
								intraGestureTimer = time.clock()
								print("inited gesture")
					else:
						# If the gestures are equal, then clear the change gesture timer
						if(not changeGestureTimer == None):
							changeGestureTimer = None
				if(curr_gesture.state == GestureState.INITED):
					# If the elapsed time is greater than the delay time than start the gesture
					if(time.clock() - intraGestureTimer >= START_DELAY):
						curr_gesture.state = GestureState.STARTED
						# EVENT: On start
						print("Started gesture: " + str(curr_gesture) + " @ " + str(time.clock()))
			else:
				# If at least one contact is down, create a new gesture recognizer
				if(len(contacts) > 0):
					curr_gesture = SenselGesture(len(contacts), weight_class, avg_x, avg_y)
					intraGestureTimer = time.clock()
					print("inited gesture @ " + str(intraGestureTimer))

		sensel_device.stopScanning();
		sensel_device.closeConnection();

if __name__ == '__main__':
	sgh = SenselGestureHandler()
	sgh.start()
