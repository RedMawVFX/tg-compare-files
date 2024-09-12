import os.path
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfile
from tkinter import messagebox
import tg_compare_files_cli as cli

gui = Tk()
gui.geometry("600x800")
gui.title(os.path.basename(__file__))

frame0 = LabelFrame(gui,text="Select files to compare")
frame3 = LabelFrame(gui,text="Sort options")
frame4 = LabelFrame(gui,text="Filter options")
frame1 = LabelFrame(gui,text="Nodes of interest")
frame2 = LabelFrame(gui,text="Attribute values")

frame0.grid(row=0,column=0,padx=4,pady=4,sticky="WENS")
frame1.grid(row=3,column=0,padx=4,pady=4,sticky="WENS")
frame2.grid(row=4,column=0,padx=4,pady=4,sticky="WENS")
frame3.grid(row=1,column=0,padx=4,pady=4,sticky="WENS")
frame4.grid(row=2,column=0,padx=4,pady=4,sticky="WENS")

frame1.columnconfigure(0,weight=1)
frame2.columnconfigure(0,weight=1)

colour_search_with_value = "#E8D7F2" # light purple
colour_search_without_value = ""

def popup_info(message_title,message_description):
    messagebox.showinfo(title=message_title,message=message_description)

def popup_warning(message_title,message_description):
    messagebox.showwarning(title = message_title,message = message_description)

def select_tg_file(x):
    file_obj = askopenfile(title="Select a file",filetypes = [("Terragen 4 project files",".tgd"),("All files","*.*")])
    if file_obj:
        file_path = file_obj.name
        # update entry widget
        if x == 1:
            file1_var.set(file_path)
        else:
            file2_var.set(file_path)
    else:
        if x == 1:
            file1_var.set("")
        else:
            file2_var.set("")

def update_differences_dict(node_name,param,val1,val2):
    global difference_dict_unsorted
    new_tuple = (param,val1,val2)
    if node_name in difference_dict_unsorted:
        existing_tuple = difference_dict_unsorted[node_name]
        combined_tuple = existing_tuple + (new_tuple,)
        difference_dict_unsorted[node_name] = combined_tuple
    else:
        difference_dict_unsorted[node_name] = (new_tuple,)

def format_tuples(tuples): # given (('posiiton','1 1 1','99 99 99'),('rotation','4 5 6','7 8 9'), etc)
    global current_dict
    formatted_str = ""
    for item in tuples:
        name, value1, value2 = item
        formatted_str = formatted_str + f"{name}\n" f"    {value1}\n" f"    {value2}\n" 
    return formatted_str

def treeview_display_node_params(event):
    selected_item_id = treeview.selection()
    if len(selected_item_id) == 0:
        attributes_of_interest_tb.delete(1.0,END)
        return
    selected_values = treeview.item(selected_item_id[0],'values')
    selected_index = selected_values[0]
    default_value = ('Unknown key','N/A','N/A')
    selected_value = current_dict.get(selected_index,default_value) # providing a default value tuple in case the key doesn't exist
    formatted_output = format_tuples(selected_value)
    attributes_of_interest_tb.delete(1.0,END) # delete previous entries
    attributes_of_interest_tb.insert(END,formatted_output)

def build_current_dict(reselect_last_known = True):
    global difference_dict_unsorted, current_dict
    current_dict = difference_dict_unsorted # default
    sort_by = sort_by_var.get()
    if sort_by == 1:
        current_dict = dict(sorted(difference_dict_unsorted.items())) # sort alphabetically
    elif sort_by == 2:
        current_dict = dict(sorted(difference_dict_unsorted.items(),reverse=True)) # reverse sorted alphabetically
    populate_treeview(reselect_last_known=reselect_last_known)

def get_treeview_selection():
    selected_item_id = treeview.selection()
    if len(selected_item_id) > 0:
        selected_values = treeview.item(selected_item_id[0],'values')
        return selected_values[0]
    else:
        return None
    
def get_last_known_selection():
    global last_known_selection
    selection = get_treeview_selection()
    if selection == None:
        return last_known_selection
    else:
        last_known_selection = selection
        return last_known_selection

def populate_treeview(reselect_last_known):
    last_known_selection = get_last_known_selection()
    # populate the treeview table with the summary information
    treeview["columns"] = ("Column 1","Column 2")
    # format columns
    treeview.column("#0",width=0,stretch="no") # hide first empty column
    treeview.column("Column 1",anchor="w",width=150)
    treeview.column("Column 2",anchor="w",width=150)
    # column headings
    treeview.heading("#0",text="",anchor="w")
    treeview.heading("Column 1", text="==NODE PATHS==",anchor="w")
    treeview.heading("Column 2",text="==SUMMARY==",anchor="w")
    for item in treeview.get_children():
        treeview.delete(item) # init the treeview contents first
    # insert data into treeview table
    search_term = search_var.get()
    for key,value in current_dict.items():
        if search_term in key:
            problems = len(value) # number of attributes with dissimilar values
            if value[0][0].startswith("Node is unique to file"):
                summary = str(value[0][0])
            else:
                if problems == 1:
                    summary = str(problems) + " difference found"
                else:
                    summary = str(problems) + " differences found"
            summary_tuple = ((str(key)),(summary))
            id = insert_with_tag(summary_tuple)
            if key == last_known_selection and reselect_last_known:
                treeview.selection_set(id)

def insert_with_tag(summary_tuple):
    search_term = search_var.get()
    id = None
    if len(search_term) > 0:
        id = treeview.insert("",END,values=summary_tuple,tags=('with_value',))
    else:
        id = treeview.insert("",END,values=summary_tuple,tags=('without_value'))
    return id

def filter_current_dict(event=None):
    last_known_selection = get_last_known_selection()
    search_term = search_var.get()
    sifted = filter_by_var.get()
    for item in treeview.get_children():
        treeview.delete(item) # init the treeview contents first
    for key,value in current_dict.items():
            if search_term in key:
                problems = len(value) # number of attributes with dissimilar values
                if value[0][0].startswith("Node is unique to file"):
                    summary = str(value[0][0])
                else:
                    if problems == 1:
                        summary = str(problems) + " difference found"
                    else:
                        summary = str(problems) + " differences found"
                summary_tuple = ((str(key)),(summary))
                # insert by selected filter type
                id = None # init
                if sifted == 1 and "difference" in summary_tuple[1]: # attributes
                    id = insert_with_tag(summary_tuple)
                elif sifted == 2 and "unique to file 1" in summary_tuple[1]: # file 1
                    id = insert_with_tag(summary_tuple)
                elif sifted == 3 and "unique to file 2" in summary_tuple[1]: # file 2
                    id = insert_with_tag(summary_tuple)
                elif sifted == 0:
                    id = insert_with_tag(summary_tuple)

                if key == last_known_selection and id != None:
                    treeview.selection_set(id)

def on_clear(): # clears the search pattern entry
    search_term = search_var.set("")
    filter_current_dict()

def on_compare():
    global difference_dict_unsorted, current_dict, last_known_selection
    last_known_selection = None
    if file1_var.get() and file2_var.get():
        # remove double colons from tags before parsing
        file1_preprocessed = cli.preprocess_file(file1_var.get())
        file2_preprocessed = cli.preprocess_file(file2_var.get())
        # parse tg file
        root1 = cli.parse_tgd(file1_preprocessed)
        root2 = cli.parse_tgd(file2_preprocessed)
        # build a list of node names for each file
        file1_node_names = cli.get_paths_of_children(root1,prefix="/")
        file2_node_names = cli.get_paths_of_children(root2,prefix="/")
        # build a list of node names common to both files, as well as unique nodes
        set1 = set(file1_node_names)
        set2 = set(file2_node_names)
        common_nodes = list(set1.intersection(set2))
        unique_nodes = list(set1.symmetric_difference(set2))
        file1_unique_nodes = list(set1 - set2)
        file2_unique_nodes = list(set2 - set1)
        
        # initialize unsorted dictionary and delete any nodes displayed in the 'attributes of interest' frame
        difference_dict_unsorted.clear()
        current_dict.clear()
        attributes_of_interest_tb.delete(1.0,END)

        # build unsorted dictionary of nodes with different attribute values
        for node_name in common_nodes:
            element1 = cli.find_child_by_path(root1, "/", find_path=node_name)
            element2 = cli.find_child_by_path(root2, "/", find_path=node_name)
            if element1 != None:
                for key in element1.keys():
                    if key.startswith("gui_"):
                        continue
                    value1 = element1.get(key)
                    value2 = element2.get(key)
                    if value1 != value2:
                        update_differences_dict(str(node_name),str(key),str(value1),str(value2))
            else:
                print(f"could not find {node_name}")

        # include nodes unique to only one of the projects, in the unsorted dictionary
        if file1_unique_nodes:
            for node_name in file1_unique_nodes:
                update_differences_dict(str(node_name),"Node is unique to file 1","","")

        if file2_unique_nodes:
            for node_name in file2_unique_nodes:
                update_differences_dict(str(node_name),"Node is unique to file 2","","")
        
        # unsorted dictionary complete, now build sorted dictionary
        build_current_dict(reselect_last_known=False)

    else:
        # abort no file assinged 
        popup_warning("Terragen warning!","Please choose two Terragen projects to compare")

# tkinter variables
file1_var = StringVar()
file1_var.set("")
file2_var = StringVar()
file2_var.set("")
filter_by_var = IntVar()
search_var = StringVar()
sort_by_var = IntVar()
difference_dict_unsorted = {}
current_dict = {}
last_known_selection = None

# frame 0
Label(frame0,text="File 1:").grid(row=0,column=0,padx=4,pady=4,sticky='e')
Label(frame0,text="File 2:").grid(row=1,column=0,padx=4,pady=4,sticky='e')
file1_e = Entry(frame0,textvariable=file1_var,width=75)
file2_e = Entry(frame0,textvariable=file2_var,width=75)
file1_e.grid(row=0,column=1,padx=4,pady=4,sticky='w')
file2_e.grid(row=1,column=1,padx=4,pady=4,sticky='w')
file1_b = Button(frame0,text="   Select   ",command=lambda:select_tg_file(1))
file2_b = Button(frame0,text="   Select   ",command=lambda:select_tg_file(2))
file1_b.grid(row=0,column=2,padx=4,pady=4)
file2_b.grid(row=1,column=2,padx=4,pady=4)
compare_b = Button(frame0,text="Compare",command=on_compare,bg="yellow")
compare_b.grid(row=2,column=2,padx=4,pady=6,sticky='w')

# frame 3 - sort options
sort_by0_rb = Radiobutton(frame3,text="Unsorted",variable=sort_by_var,value=0,command=build_current_dict)
sort_by0_rb.grid(row=0,column=0,padx=4,pady=4,sticky="w")
sort_by1_rb = Radiobutton(frame3,text="Alphanumeric",variable=sort_by_var,value=1,command=build_current_dict)
sort_by1_rb.grid(row=0,column=1,padx=4,pady=4,sticky='w')
sort_by2_rb = Radiobutton(frame3,text="Descending",variable=sort_by_var,value=2,command=build_current_dict)
sort_by2_rb.grid(row=0,column=2,padx=4,pady=4,sticky='w')

# frame 1 filter options
filter_by1_rb = Radiobutton(frame4,text="All",variable=filter_by_var,value=0,command=filter_current_dict)
filter_by2_rb = Radiobutton(frame4,text="Attribute",variable=filter_by_var,value=1,command=filter_current_dict)
filter_by3_rb = Radiobutton(frame4,text="File 1",variable=filter_by_var,value=2,command=filter_current_dict)
filter_by4_rb = Radiobutton(frame4,text="File 2",variable=filter_by_var,value=3,command=filter_current_dict)
filter_by1_rb.grid(row=0,column=0,padx=4,pady=4,sticky="w")
filter_by2_rb.grid(row=0,column=1,padx=4,pady=4,sticky="w")
filter_by3_rb.grid(row=0,column=2,padx=4,pady=4,sticky="w")
filter_by4_rb.grid(row=0,column=3,padx=4,pady=4,sticky="w")

Label(frame4,text="Search pattern: ").grid(row=1,column=0,padx=4,pady=4,sticky='w')
search_e = Entry(frame4,textvariable=search_var,bg=colour_search_with_value)
search_e.grid(row=1,column=1,padx=4,pady=4,sticky='w')
search_e.bind("<KeyRelease>", filter_current_dict)
clear_b = Button(frame4,text="Clear",command=on_clear)
clear_b.grid(row=1,column=2,padx=4,pady=4,sticky='w')

# frame 1 - treeview table for nodes of interest
treeview = ttk.Treeview(frame1)
treeview.grid(row=0,column=0,sticky="nsew")
treeview_vsb = Scrollbar(frame1,orient="vertical",command=treeview.yview)
treeview_hsb = Scrollbar(frame1,orient="horizontal",command=treeview.xview)
treeview.configure(yscrollcommand=treeview_vsb.set,xscrollcommand=treeview_hsb.set)
treeview_vsb.grid(row=0,column=1,sticky='ns')
treeview_hsb.grid(row=1,column=0,sticky='ew')
treeview.bind("<<TreeviewSelect>>", treeview_display_node_params)
treeview.tag_configure('with_value',background=colour_search_with_value)
treeview.tag_configure('without_value',background=colour_search_without_value)

# frame 2 - text widget for attribute values
attributes_of_interest_tb = Text(frame2,width=60,height=12)
attributes_of_interest_tb.grid(row=0,column=0,padx=4,pady=4,sticky="WENS")
attributes_of_interest_sb = Scrollbar(frame2,orient="vertical",command=attributes_of_interest_tb.yview)
attributes_of_interest_sb.grid(row=0,column=1,sticky='ns')
attributes_of_interest_tb.configure(yscrollcommand=attributes_of_interest_sb.set)

gui.mainloop()