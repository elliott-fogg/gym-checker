from tkinter import Tk, Canvas


class MouseControl:
    '''  Class for mouse control to establish if there is a 'click',
         'double click' or mouse is being moved '''
    def __init__(self, aw):
        self.double_click_flag = False
        self.button_released_flag = False
        self.aw = aw
        self.aw.bind('<Button-1>', self.clicked)  # bind left mouse click
        self.aw.bind('<Double-1>', self.double_click)  # bind double left clicks
        self.aw.bind('<ButtonRelease-1>', self.button_released)  # bind button release
        self.aw.bind('<B1-Motion>', self.moved)  # bring when mouse is moved

    def clicked(self, event):
        '''  add a little delay before calling action to allow for double click
         and button released to have occurred '''
        self.double_click_flag, self.button_released_flag = False, False
        self.aw.after(300, self.action, event)

    def double_click(self, event):
        '''  set flag when there is a double click '''
        self.double_click_flag = True

    def button_released(self, event):
        '''  set flag when button is released '''
        self.button_released_flag = True

    def moved(self, event):
        '''  define action on when mouse is moved in this case just printing
             the coordinates'''
        print('mouse position is at ({:03}. {:03})'.
              format(event.x, event.y), end='\r')

    def action(self, event):
        '''  define action on click and double click in this case just printing
             the event '''
        if self.button_released_flag:

            if self.double_click_flag:
                print('double mouse click event')

            else:
                print('single mouse click event')


root = Tk()
window = Canvas(root, width=400, height=400, bg='grey')
mouse = MouseControl(window)
window.place(x=0, y=0)
window.mainloop()
