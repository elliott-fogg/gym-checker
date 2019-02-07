import tkinter as tk

class MinimalTestCase(tk.Frame):

    def __init__(self, master, *args, **kwargs):

        tk.Frame.__init__(self, master)

        self.f1 = tk.Frame(self)
        self.f2 = tk.Frame(self)
        self.f2.rowconfigure(0, weight=1) # <-- row 0 will be resized

        self.f1.grid(row=0, column=0)
        self.f2.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))

        ### Fill left frame with dummy elements to demonstrate the problem
        for i in range(15):
            tk.Label(self.f1, text="Label{}".format(i)).grid(row=i)

        ### Put listbox on right frame
        self.lbox = tk.Listbox(self.f2)
        self.lbox.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        self.grid()

if __name__ == "__main__":

    root=tk.Tk()
    MinimalTestCase(root)
    root.mainloop()
