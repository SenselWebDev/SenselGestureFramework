# #!/usr/bin/python

# from Tkinter import *

# root = Tk()

# root.title("Simple Graph")

# root.resizable(0,0)

# points = []

# spline = 0

# tag1 = "theline"

# def point(event):
# 	c.create_oval(event.x, event.y, event.x+1, event.y+1, fill="black")
# 	points.append(event.x)
# 	points.append(event.y)
# 	return points

# def canxy(event):
# 	print event.x, event.y

# def graph(event):
# 	global theline
# 	c.create_line(points, tags="theline")
	

# def toggle(event):
# 	global spline
# 	if spline == 0:
# 		c.itemconfigure(tag1, smooth=1)
# 		spline = 1
# 	elif spline == 1:
# 		c.itemconfigure(tag1, smooth=0)
# 		spline = 0
# 	return spline


# c = Canvas(root, bg="white", width=300, height= 300)

# c.configure(cursor="crosshair")

# c.pack()

# c.bind("<Button-1>", point)

# c.bind("<Button-3>", graph)

# c.bind("<Button-2>", toggle)

# root.mainloop()


import Tkinter as tk

class Example(tk.Frame):
  def __init__(self, parent):
      tk.Frame.__init__(self, parent)
      self.text = CustomText(self, wrap="word")
      self.text.pack(side="top", fill="both", expand=True)
      self.label = tk.Label(self, anchor="w")
      self.label.pack(side="bottom", fill="x")

      # this is where we tell the custom widget what to call
      self.text.set_callback(self.callback)

  def callback(self, result, *args):
      '''Updates the label with the current cursor position'''
      index = self.text.index("insert")
      self.label.configure(text="index: %s" % index)

class CustomText(tk.Text):
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)

        # Danger Will Robinson!
        # Heavy voodoo here. All widget changes happen via
        # an internal Tcl command with the same name as the 
        # widget:  all inserts, deletes, cursor changes, etc
        #
        # The beauty of Tcl is that we can replace that command
        # with our own command. The following code does just
        # that: replace the code with a proxy that calls the
        # original command and then calls a callback. We
        # can then do whatever we want in the callback. 
        private_callback = self.register(self._callback)
        self.tk.eval('''
            proc widget_proxy {actual_widget callback args} {

                # this prevents recursion if the widget is called
                # during the callback
                set flag ::dont_recurse(actual_widget)

                # call the real tk widget with the real args
                set result [uplevel [linsert $args 0 $actual_widget]]

                # call the callback and ignore errors, but only
                # do so on inserts, deletes, and changes in the 
                # mark. Otherwise we'll call the callback way too 
                # often.
                if {! [info exists $flag]} {
                    if {([lindex $args 0] in {insert replace delete}) ||
                        ([lrange $args 0 2] == {mark set insert})} {
                        # the flag makes sure that whatever happens in the
                        # callback doesn't cause the callbacks to be called again.
                        set $flag 1
                        catch {$callback $result {*}$args } callback_result
                        unset -nocomplain $flag
                    }
                }

                # return the result from the real widget command
                return $result
            }
            ''')
        self.tk.eval('''
            rename {widget} _{widget}
            interp alias {{}} ::{widget} {{}} widget_proxy _{widget} {callback}
        '''.format(widget=str(self), callback=private_callback))

    def _callback(self, result, *args):
        self.callback(result, *args)

    def set_callback(self, callable):
        self.callback = callable


if __name__ == "__main__":
  root = tk.Tk()
  frame = Example(root)
  frame.pack(side="top", fill="both", expand=True)
  root.mainloop()