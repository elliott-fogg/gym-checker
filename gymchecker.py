from classes.shared_functions import *
from classes.database_class import *
from classes.gui_class import *

def main():
    dirname = os.path.dirname(os.path.realpath(__file__))
    set_folder_paths(dirname)

    if (any(x in ("--update","-u") for x in sys.argv)):
            update_gymchecker()

    if (any(x in ("--debug","-d") for x in sys.argv)):
        set_quiet(False)

    gc = database(data(db_name), 'gymchecker', gc_params)

    root=tk.Tk()
    gui(root, gc)
    root.mainloop()

if __name__=="__main__":
    main()
