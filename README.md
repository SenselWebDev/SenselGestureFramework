# SenselGestureFramework
Gesture framework for abstracting Sensel contact data.

This framework currently supports TAP and PAN events with varying weight classes (pressure-based) and contact counts.

To use this framework, extend the SenselGestureHandler class and override the gestureEvent method. This method is called on every gesture event. From there, switch on the GestureState (STARTED, MOVED, ENDED) and trigger custom events based on the number of fingers, weight classes, etc. See the SenselGesture class to see which fields are available.

The default implementation will simply print out information on the gestures based on the gesture state.

```python
def gestureEvent(self, gesture):
		if(gesture.state == GestureState.STARTED):
			print("Started gesture: " + str(gesture) + " @ " + str(time.time()))
		elif(gesture.state == GestureState.MOVED):
			#print("Gesture moved")
		elif(gesture.state == GestureState.ENDED):
			print("Gesture ended: " + str(gesture) + " @ " + str(time.time()))
```
