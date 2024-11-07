import os.path
import re
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfile
from tkinter import messagebox
import xml.etree.ElementTree as ET

gui = tk.Tk()
gui.geometry("710x942")
gui.title(os.path.basename(__file__))

file_selection_frame = tk.LabelFrame(gui, text = "Select files to compare")
node_selection_frame = tk.LabelFrame(gui, text = "Select nodes to compare")
results_frame = tk.Frame(gui)
search_pattern_frame = tk.Frame(node_selection_frame)
file_selection_frame.grid(row=0, column=0, padx=4, pady=4, sticky="WENS")
node_selection_frame.grid(row=1, column=0, padx=4, pady=4, sticky="WENS")
results_frame.grid(row=2, column=0, padx=10, pady=4)
search_pattern_frame.grid(row=0, column=0, columnspan=4, padx=4, pady=10, sticky="WENS")

node_selection_notebook = ttk.Notebook(node_selection_frame)
node_selection_notebook.grid(row=1, column=0, padx=4, pady=4, columnspan=4)

nodes_of_interest_tab = tk.Frame(node_selection_notebook)
compare_by_path_tab = tk.Frame(node_selection_notebook)
node_selection_notebook.add(nodes_of_interest_tab, text=" Nodes w/differences ")
node_selection_notebook.add(compare_by_path_tab, text=" Compare two nodes ")

results_notebook = ttk.Notebook(results_frame)
results_notebook.grid(row=0, column=0)

node_params_tab = tk.Frame(results_notebook)
text_content_tab = tk.Frame(results_notebook)
project_comments_tab = tk.Frame(results_notebook)
results_notebook.add(node_params_tab, text="Node params")
results_notebook.add(text_content_tab, text="Text content")
results_notebook.add(project_comments_tab, text="Project comments")

COLOUR_SEARCH_WITH_VALUE = "#E8D7F2" # light purple
COLOUR_SEARCH_WITHOUT_VALUE = ""
TAG_COLOUR_UNEQUAL = "#e39191" # redish #e36565
TAG_COLOUR_EQUAL = ""

def popup_info(message_title, message_description) -> None:
    '''
    Opens an information window and displays a message.  User needs to click to continue.

    Args:
        message_title (str): Title appears in the window frame.
        message_description (str): Message appears in the body of the window.

    Returns:
        None: This function does not return any value.
    '''
    messagebox.showinfo(title=message_title, message=message_description)

def popup_warning(message_title, message_description) -> None:
    '''
    Opens a warning window and displays a message.  User needs to click to continue.

    Args:
        message_title (str): Title appears in the window frame.
        message_description (str): Message appears in the body of the window.

    Returns:
        None: This function does not return any value.
    '''
    messagebox.showwarning(title=message_title, message=message_description)

def on_select(file_num) -> None:
    '''
    Coordinates selection, loading, parsing of a Terragen file. Constructs 
    nodes of interest dictionary and display when two Terragen files have 
    been selected.

    Args:
        file_num (int): Flag designating which file has been selected.
    
    Returns:
        None: This function does not return any value.
    '''
    global file1_node_paths, file2_node_paths, file1_root, file2_root
    file_path = select_tg_file()
    if file_path:
        file_contents = read_xml_file(file_path)
        if file_num == 1:
            file1_label.set(file_path)
            file1_root = ET.fromstring(file_contents)
            file1_node_paths = sorted(get_paths_of_children(file1_root, prefix="/"))
            update_project_comments(file_num)
        else:
            file2_label.set(file_path)
            file2_root = ET.fromstring(file_contents)
            file2_node_paths = sorted(get_paths_of_children(file2_root, prefix="/"))
            update_project_comments(file_num)

    update_compare_by_path(file_num)
    on_clear()
    update_result_headers()

    # when two Terragen files have been selected
    if file1_node_paths and file2_node_paths:
        set1 = set(file1_node_paths)
        set2 = set(file2_node_paths)
        nodes_in_common = sorted(list(set1.intersection(set2)))
        file1_unique_nodes = sorted(list(set1 - set2))
        file2_unique_nodes = sorted(list(set2 - set1))
        clear_nodes_of_interest_dict() # init dict

    # build nodes of interest dictionary
        for node_path in nodes_in_common:
            element1 = find_child_by_path(file1_root,prefix="/", find_path=node_path)
            element2 = find_child_by_path(file2_root,prefix="/", find_path=node_path)
            union_of_keys = set(element1.keys()) | set(element2.keys())
            if element1 is not None:
                for key in union_of_keys: # attributes ie name, enable, far_colour, input_node, etc
                    if key.startswith("gui_"):
                        continue
                    value1 = element1.get(key)
                    value2 = element2.get(key)
                    if value1 != value2:
                        update_nodes_of_interest_dicts(
                            str(node_path),str(key),
                            str(value1),str(value2)
                            )
                    else:
                        update_nodes_of_interest_dicts(
                            str(node_path), str(key),
                            str(value1), str(value2), dict_flag=2
                            )
            else:
                print (f"could not find {node_path}")

        # include nodes found only in one project file
        if file1_unique_nodes:
            for node_path in file1_unique_nodes:
                update_nodes_of_interest_dicts(
                    str(node_path),
                    "Node is only in file 1", "", ""
                    )

        if file2_unique_nodes:
            for node_path in file2_unique_nodes:
                update_nodes_of_interest_dicts(
                    str(node_path),
                    "Node is only in file 2", "", ""
                    )

        # display nodes of interest
        update_nodes_of_interest()

def update_nodes_of_interest() -> None:
    '''
    Refreshes the nodes of interest treeview widget, displaying items that match
    search pattern in the nodes of interest dict.

    Returns:
        None: This function does not return any value.
    '''
    for item in nodes_of_interest.get_children():
        nodes_of_interest.delete(item)
    search_term = search_var.get()
    for key,value in nodes_of_interest_dict.items():
        if search_term in key:
            problems = len(value)
            if value[0][0].startswith("Node is only in file"):
                summary = str(value[0][0])
            else:
                if problems == 1:
                    summary = "1 difference found"
                else:
                    summary = str(problems) + " differences found"
            summary_tuple = ((str(key)), (summary))
            node_of_interest_id = insert_node_of_interest_with_tag(summary_tuple)
            if key == nodes_of_interest_last_known_selection:
                nodes_of_interest.selection_set(node_of_interest_id)

def insert_node_of_interest_with_tag(summary_tuple):
    '''
    Inserts a new item into the nodes of interest listbox widget with an appropriate tag.

    Args:
        summary_tuple (tuple): Contains node path and summary of differences description.

    Returns:
        id (int): Index of item in listbox
    '''
    search_term = search_var.get()
    node_of_interest_id = None
    if len(search_term) > 0:
        node_of_interest_id = nodes_of_interest.insert(
            "", tk.END, values=summary_tuple, tags=('with_value',)
            )
    else:
        node_of_interest_id = nodes_of_interest.insert(
            "", tk.END, values=summary_tuple, tags=('without_value',)
            )
    return node_of_interest_id

def clear_nodes_of_interest_dict() -> None:
    '''
    Initializes the nodes of interest dictionary.

    Returns:
        None: This function does not return any values.
    '''
    global nodes_of_interest_dict, nodes_of_interest_equal_val_dict
    nodes_of_interest_dict.clear()
    nodes_of_interest_equal_val_dict.clear()

def update_nodes_of_interest_dicts(node_path, param, val1, val2, dict_flag=1):
    '''
    Adds items to either the nodes of interest dictionary or the unequal values dict.
    These are nodes common to both both project files selected.  The key is a node path
    and the value is a tuple consisting of the parameter name and values from each file.

    Args:
        node_path (str): Node path
        param (str): Parameter name
        val1 (str): Parameter value from file 1
        val2 (str): Parameter value from file 2
        dict_flag (int): Flag for which dictionary to update. Defaults to 1.

    Returns:
        None: This function does not return any values
    '''
    global nodes_of_interest_dict, nodes_of_interest_equal_val_dict
    if dict_flag == 1:
        node_dict = nodes_of_interest_dict
    else:
        node_dict = nodes_of_interest_equal_val_dict

    new_tuple = (param, val1, val2)
    if node_path in node_dict:
        existing_tuple = node_dict[node_path]
        combined_tuple = existing_tuple + (new_tuple,)
        node_dict[node_path] = combined_tuple
    else:
        node_dict[node_path] = (new_tuple,)

def update_compare_by_path(file_num) -> None:
    '''
    Refreshes the list of node paths in the appropriate compare by path listbox widget.

    Args:
        file_num (int): Flag indicating which listbox to refresh.

    Returns:
        None: This function does not return any value.
    '''
    clear_compare_by_path(file_num)
    if file_num == 1:
        for item in file1_node_paths:
            file1_paths.insert(tk.END, item)
    if file_num == 2:
        for item in file2_node_paths:
            file2_paths.insert(tk.END, item)
    else: # both
        for item in file1_node_paths:
            file1_paths.insert(tk.END, item)
        for item in file2_node_paths:
            file2_paths.insert(tk.END, item)

def clear_compare_by_path(file_num) -> None:
    '''
    Clears the selected file path listbox. Both listboxes can be cleared
    at once by passing a value other than 1 or 2.

    Args:
        file_num (int): A value of 0 clears both listboxes.

    Returns:
        None: This function does not return any value.
    '''
    if file_num == 1:
        file1_paths.delete(0, tk.END)
    elif file_num == 2:
        file2_paths.delete(0, tk.END)
    else:
        file1_paths.delete(0, tk.END)
        file2_paths.delete(0, tk.END)

def select_tg_file():
    """
    Opens file requestor window to select Terragen file.

    Returns:
        file_obj.name (str): Terragen file name or None if invalid file type.
    """
    file_types = (("All Terragen project files", "*.tgd;*.tgv;*.tgc"),
                  ("Terragen 4 project files", "*.tgd"),
                  ("Terragen 4 clip files", "*.tgc"),
                  ("Terragen V project files", "*.tgv"),
                  ("All files", "*.*")
                  )
    file_obj = askopenfile(title="Select a file", filetypes=file_types)
    if file_obj:
        if not file_obj.name.endswith(('.tgd', '.tgv', '.tgc')):
            popup_warning("Terragen warning", "Invalid file type selected.")
            return None
        return file_obj.name

def read_xml_file(file_path):
    ''' Read the selected Terragen file and replace double colons. Return file contents as string.

    Args:
        file_path (): Selected Terragen file, .tgd or .tgv

    Returns:
        xml_data_validated (str): Terragen file contents
    '''
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_data_raw = file.read()
        xml_data_validated = re.sub(r'<([^>]*?)::([^>]*?)>', r'<\1_\2>', xml_data_raw)
    return xml_data_validated

def get_paths_of_children(node, prefix:str):
    '''
    Given a node, returns all child paths recursively

    Args:
        node (obj): A parent node id
        prefix (str): Typically a slash / character

    Return:
        node_paths (list): List of child node paths
    '''
    node_paths = []
    for child in node:
        if child.tag not in EXCLUDE_TAGS:
            child_path = generate_path(child=child, prefix=prefix)
            node_paths.append(child_path)
            deeper_names = get_paths_of_children(child, prefix=child_path+"/")
            node_paths.extend(deeper_names)
    return node_paths

def generate_path(child, prefix:str):
    '''
    Creates the full file path for the child node.

    Args:
        child (obj): A child node id ... I think
        prefix (str): Typically a slash / character

    Returns:
        string: a full path
    '''
    if 'name' in child.attrib: # some nodes don't have a name attribute e.g. animationdata
        return prefix + child.attrib['name']
    else:
        return prefix + "unnamed_node_" + child.tag

def update_project_comments(file_num) -> None:
    '''
    Updates the project comments display with comments from the project file.

    Args:
        file_num (int): Flag indicating which text widget to update.
    
    Returns:
        None: This function does not return any value.
    '''
    if file_num == 1:
        file1_comments.delete('1.0', tk.END)
        root1_comments = file1_root.get("comments")
        if root1_comments:
            file1_comments.insert(tk.END, root1_comments)
    elif file_num == 2:
        file2_comments.delete('1.0', tk.END)
        root2_comments = file2_root.get("comments")
        if root2_comments:
            file2_comments.insert(tk.END, root2_comments)
    else:
        file1_comments.delete('1.0', tk.END)
        file2_comments.delete('1.0', tk.END)

def on_search(event) -> None:
    '''
    Coordinates clearing and refreshing of compare by path and nodes of interest listboxes.

    Returns:
        None: This function does not return any value.
    '''
    clear_compare_by_path(0)
    search_for = search_var.get() # i.e. R n d r
    if len(search_for) > 0:
        item_colour = COLOUR_SEARCH_WITH_VALUE
    else:
        item_colour = COLOUR_SEARCH_WITHOUT_VALUE
    for item in file1_node_paths:
        if search_for in item:
            file1_paths.insert(tk.END, item)
            file1_paths.itemconfig(file1_paths.size() - 1, {'bg': item_colour})
    for item in file2_node_paths:
        if search_for in item:
            file2_paths.insert(tk.END, item)
            file2_paths.itemconfig(file2_paths.size() - 1, {'bg': item_colour})
    filter_nodes_of_interest()

def on_clear() -> None:
    '''
    Resets search pattern. Coordinates clearing of the results and text content widgets, and
    refreshes listboxes for the compare by path and nodes of interest. Resets global dicts
    file1_node_params_dict and file2_node_params_dict and nodes_of_interest_last_known_selection.

    Returns:
        None: This function does not return any value.
    '''
    global file1_node_params_dict, file2_node_params_dict, nodes_of_interest_last_known_selection
    search_var.set("")
    clear_results()
    update_text_content(file_num=0, text="")
    update_compare_by_path(0)
    update_nodes_of_interest()
    file1_node_params_dict.clear()
    file2_node_params_dict.clear()
    nodes_of_interest_last_known_selection = None

def clear_results():
    '''
    Initializes the results window.

    Returns:
        None
    '''
    for item in results.get_children():
        results.delete(item)

def update_text_content(file_num, text):
    '''
    Initializes or updates the text content pane.

    Args:
        file_num (int): Flag for which file's text content to update.
        text (str): Some text maybe

    Returns:
        None
    '''
    file1_content.config(state=tk.NORMAL) # so text can be updated by program
    file2_content.config(state=tk.NORMAL)
    if file_num == 1:
        file1_content.delete('1.0', tk.END)
        if text:
            file1_content.insert(tk.END, text)
    elif file_num == 2:
        file2_content.delete('1.0', tk.END)
        if text:
            file2_content.insert(tk.END, text)
    else:
        file1_content.delete('1.0', tk.END)
        file2_content.delete('1.0', tk.END)
    file1_content.config(state=tk.DISABLED) # so user can't type stuff in text box
    file2_content.config(state=tk.DISABLED)

def filter_nodes_of_interest() -> None:
    '''
    Filters the items displayed in the nodes of interest treeview widget,
    based on the radio button selected: All, Attributes, File1 or File2.

    Returns:
        None: This function does not return any values.
    '''
    last_known_selection = get_nodes_of_interest_last_known_selection()
    search_term = search_var.get()
    sifted = filter_by_var.get()
    for item in nodes_of_interest.get_children():
        nodes_of_interest.delete(item)
    for key,value in nodes_of_interest_dict.items():
        if search_term in key:
            problems = len(value) # number of attributes with dissimilar values
            if value[0][0].startswith("Node is only in file"):
                summary = str(value[0][0])
            else:
                if problems == 1:
                    summary = str(problems) + " difference found"
                else:
                    summary = str(problems) + " differences found"

            summary_tuple = ((str(key)), (summary))

            # insert by selected filter type
            node_of_interest_id = None # init
            if sifted == 1 and "difference" in summary_tuple[1]: # attributes
                node_of_interest_id = insert_node_of_interest_with_tag(summary_tuple)
            elif sifted == 2 and "only in file 1" in summary_tuple[1]: # file 1
                node_of_interest_id = insert_node_of_interest_with_tag(summary_tuple)
            elif sifted == 3 and "only in file 2" in summary_tuple[1]: # file 2
                node_of_interest_id = insert_node_of_interest_with_tag(summary_tuple)
            elif sifted == 0:
                node_of_interest_id = insert_node_of_interest_with_tag(summary_tuple)

            if key == last_known_selection and node_of_interest_id is not None:
                nodes_of_interest.selection_set(node_of_interest_id)

def clear_result_params() -> None:
    '''
    Initializes the results pane.

    Returns:
        None: This function does not return any values.
    '''
    for item in results.get_children():
        results.delete(item)

def update_result_params(params) -> None:
    '''
    Refreshes the results pane with node params found in the two files.

    Args:
        params (list): Parameter attributes in common for the selected paths in 
        the compare by path listboxes

    Returns:
        None: This function does not return any values.
    '''
    clear_result_params()
    compare_by_path_unequal_values_dict = {}
    compare_by_path_equal_values_dict = {}

    for param in params:
        try:
            value1 = file1_node_params_dict[param]
        except KeyError:
            value1 = None
        try:
            value2 = file2_node_params_dict[param]
        except KeyError:
            value2 = None

        # sort the params into equal and unequal value dicts
        if value1 != value2:
            compare_by_path_unequal_values_dict[param] = (value1, value2)
        else:
            compare_by_path_equal_values_dict[param] = (value1, value2)

    if show_differences_only_var.get(): # display differences only
        for key, value in compare_by_path_unequal_values_dict.items():
            results.insert("", tk.END, values=(key, value[0], value[1]), tags=('unequal_value',))
    else:
        for key, value in compare_by_path_unequal_values_dict.items():
            results.insert("", tk.END, values=(key, value[0], value[1]), tags=('unequal_value',))
        for key, value in compare_by_path_equal_values_dict.items():
            results.insert("", tk.END, values=(key, value[0], value[1]), tags=('equal_value',))

def update_results_from_node_of_interest() -> None:
    '''
    Refreshes result pane when item is selected from nodes of interest pane.

    Returns:
        None: This function does not return any value.
    '''
    clear_result_params()
    selected_item_id = nodes_of_interest.selection()
    if len(selected_item_id) > 0:
        selected_values = nodes_of_interest.item(selected_item_id[0], 'values')
        path = selected_values[0]
        param_values = nodes_of_interest_dict[path]
        try:
            param_equal_values = nodes_of_interest_equal_val_dict[path]
        except KeyError:
            param_equal_values = ()

        if show_differences_only_var.get():
            for p in param_values: # this dict only has attribute values that are unequal
                results.insert("", tk.END, values=(p[0], p[1], p[2]), tags=('unequal_value',))
        else:
            for p in param_values:
                results.insert("", tk.END, values=(p[0], p[1], p[2]), tags=('unequal_value',))
            for pe in param_equal_values:
                results.insert("", tk.END, values=(pe[0], pe[1], pe[2]), tags=('equal_value',))

        element1 = find_child_by_path(file1_root, "/", find_path=path)
        element2 = find_child_by_path(file2_root, "/", find_path=path)
        if element1 is not None:
            update_text_content(1, element1.text)
        else:
            update_text_content(1, "")
        if element2 is not None:
            update_text_content(2, element2.text)
        else:
            update_text_content(2, "")

def update_results_from_node_of_interest_with_event(event) -> None:
    '''
    Refreshes result pane when item in params of interest is selected, 
    or show differences checkbox is clicked.

    Returns:
        None: This function does not return any values.
    '''
    update_results_from_node_of_interest()

def update_results_from_compare_two_nodes() -> None:
    '''
    Creates a list of all unique elements (union) from the two dictionaries of parameters.
    Updates the result and text content panes.

    Returns:
        None: This function does not return any value.
    '''
    # deterine which keys, node's parameters, are common to both dictionaries
    clear_results()
    params = list(set(file1_node_params_dict) | set(file2_node_params_dict)) # union of two sets
    if params:
        update_result_params(params)
    update_text_content(1,file1_node_text_content)
    update_text_content(2,file2_node_text_content)

def update_results_for_current_mode() -> None:
    '''
    Updates the results pane depending on which tab is selected. 

    Returns:
        None: This function does not return any value.
    '''
    nb = node_selection_notebook
    tab_index = nb.index(nb.select()) # 0 or 1
    if tab_index == 0:
        update_results_from_node_of_interest()
    else:
        update_results_from_compare_two_nodes()

def on_node_selection_tab_selected(event) -> None:
    '''
    Accepts a binded event argument, then calls a function without passing the event argument.

    Results:
        None: This function does not return any value.
    '''
    update_results_for_current_mode()

def on_node_path_select(event, file_num) -> None:
    '''
    Coordinates dynamic building of dictionaries for selected nodes in compare by path,
    then displays results.

    Returns:
        None: This function does not return any values.
    '''
    try:
        if file_num == 1:
            current_selection = file1_paths.curselection() # returns a tuple
            current_index = current_selection[0]
            current_item = file1_paths.get(current_index)
        else:
            current_selection = file2_paths.curselection()
            current_index = current_selection[0]
            current_item = file2_paths.get(current_index)
        # build dict of params for selected node
        build_param_dict(current_item, file_num)
        update_results_from_compare_two_nodes()
    except IndexError: # if user clicks in empty listbox
        pass

def build_param_dict(current_item, file_num) -> None:
    '''
    Modifies the global variables file1_node_params_dict or file2_node_params_dict
    for the node parameter dictionaries for each Terragen file. Dict key is the 
    parameter attribute and the value is its value, i.e. 'enable': '0'.  Also 
    modifies the global variables file1_node_text_content and file2_node_text_content.

    Args:
        current_item (str): Selected node path in compare by path listbox
        file_num (int): Flag indicating which file is selected.

    Returns:
        None: This function does not return any values.
    '''
    global file1_node_params_dict, file2_node_params_dict, file1_node_text_content, file2_node_text_content
    if file_num == 1:
        file1_node_text_content = ""
        file1_node_params_dict.clear()
        element = find_child_by_path(file1_root, "/", find_path=current_item)
        if element is not None:
            file1_node_text_content = element.text
            for key in element.keys():
                if key.startswith("gui_"):
                    continue
                value = element.get(key)
                file1_node_params_dict[key] = value
    else:
        file2_node_text_content = ""
        file2_node_params_dict.clear()
        element = find_child_by_path(file2_root, "/", find_path=current_item)
        if element is not None:
            file2_node_text_content = element.text
            for key in element.keys():
                if key.startswith("gui_"):
                    continue
                value = element.get(key)
                file2_node_params_dict[key] = value

def update_result_headers() -> None:
    '''
    Sets the description, width, and number of columns of the results widget.

    Returns:
        None: This function does not return any value.
    '''
    results["columns"] = ("Column 1", "Column 2", "Column 3")
    results.column("#0", width=0, stretch=False) # hide first empty column
    results.column("Column 1", anchor="w", width=210, stretch=False)
    results.column("Column 2", anchor="w", width=210, stretch=False)
    results.column("Column 3", anchor="w", width=210, stretch=False)
    results.heading("#0", text="", anchor="w")
    results.heading("Column 1", text="Parameters:", anchor="w")
    results.heading("Column 2", text=os.path.basename(file1_label.get()), anchor="w")
    results.heading("Column 3", text=os.path.basename(file2_label.get()), anchor="w")

def update_nodes_of_interest_headers() -> None:
    '''
    Sets the description, width, and number of colums or the nodes of interest widget.

    Returns: 
        None: This function does not return any values.
    '''
    nodes_of_interest["columns"] = ("Column 1", "Column 2")
    nodes_of_interest.column("#0", width=0, stretch="no") # hide first empty column
    nodes_of_interest.column("Column 1", anchor="w", width=300)
    nodes_of_interest.column("Column 2", anchor="w", width=300)
    nodes_of_interest.heading("#0", text="", anchor="w")
    nodes_of_interest.heading("Column 1", text="==NODE PATHS==", anchor="w")
    nodes_of_interest.heading("Column 2", text="==SUMMARY==", anchor="w")

def find_child_by_path(node, prefix:str, find_path):
    '''
    Recursively finds child nodes and generates file paths.

    Args:
        node (Element): Root id
        prefix (str): Typically a slash / character.
        find_path (obj): Node id

    Returns:
        child (obj): Element object id, i.e. <Element 'null 01' at 0x000...>
    '''
    for child in node:
        if child.tag not in EXCLUDE_TAGS:
            child_path = generate_path(child=child, prefix=prefix)
            if child_path == find_path:
                return child
            recursion_result = find_child_by_path(child, prefix=child_path+"/", find_path=find_path)
            if recursion_result is not None:
                return recursion_result
    return None

def get_nodes_of_interest_last_known_selection():
    '''
    Gets and/or sets the current selected item in the nodes of interest pane. 
    If nothing is selected returns the last known selection.

    Returns:
        nodes_of_interest_last_known_selection (int): Index
    '''
    global nodes_of_interest_last_known_selection
    selection = get_nodes_of_interest_selection()
    if selection is None:
        return nodes_of_interest_last_known_selection
    else:
        nodes_of_interest_last_known_selection = selection
        return nodes_of_interest_last_known_selection

def get_nodes_of_interest_selection():
    '''
    Gets the selected item if any in the nodes of interest pane.

    Returns:
        selected_values (): Value or None
    '''
    selected_item_id = nodes_of_interest.selection()
    if len(selected_item_id) > 0:
        selected_values = nodes_of_interest.item(selected_item_id[0], 'values')
        return selected_values[0]
    else:
        return None

# variables
file1_label = tk.StringVar()
file1_label.set("File 1")
file1_node_paths = []
file1_root = None # Element object for parsed file
file1_node_params_dict = {}
file1_node_text_content = ""
file2_label = tk.StringVar()
file2_label.set("File 2")
file2_node_paths = []
file2_root = None
file2_node_params_dict = {}
file2_node_text_content = ""
search_var = tk.StringVar()
search_var.set("")
filter_by_var = tk.IntVar()
EXCLUDE_TAGS = ["group"]
nodes_of_interest_dict = {}
nodes_of_interest_equal_val_dict = {}
nodes_of_interest_last_known_selection = None
show_differences_only_var = tk.BooleanVar()
show_differences_only_var.set(False)

# widgets - file selection frame
select_file1 = tk.Button(file_selection_frame, text="Select file 1", command=lambda:on_select(1))
select_file1.grid(row=0, column=0, padx=4, pady=4, sticky="w")
tk.Label(file_selection_frame, textvariable=file1_label).grid(row=0, column=1, padx=10, pady=4, sticky='w')

select_file2 = tk.Button(file_selection_frame, text="Select file 2", command=lambda:on_select(2))
select_file2.grid(row=1, column=0, padx=4, pady=4, sticky="w" )
tk.Label(file_selection_frame, textvariable=file2_label).grid(row=1, column=1, padx=10, pady=4, sticky='w')

# widgets - node selection frame
tk.Label(node_selection_frame, text="Search pattern: ").grid(row=0, column=0, padx=4, sticky='w')
search_pattern = tk.Entry(node_selection_frame, textvariable=search_var, bg=COLOUR_SEARCH_WITH_VALUE)
search_pattern.grid(row=0, column=1, padx=4, pady=2, sticky='w')
search_pattern.bind("<KeyRelease>", on_search)
search_clear = tk.Button(node_selection_frame, text="Clear", command=on_clear)
search_clear.grid(row=0, column=2, padx=4, sticky='w')

filter_all = tk.Radiobutton(nodes_of_interest_tab, text="All differences", variable=filter_by_var, value=0, command=filter_nodes_of_interest)
filter_attribute = tk.Radiobutton(nodes_of_interest_tab, text="Attributes", variable=filter_by_var, value=1, command=filter_nodes_of_interest)
filter_file1 = tk.Radiobutton(nodes_of_interest_tab, text="Only in file 1", variable=filter_by_var, value=2, command=filter_nodes_of_interest)
filter_file2 = tk.Radiobutton(nodes_of_interest_tab, text="Only in file 2", variable=filter_by_var, value=3, command=filter_nodes_of_interest)
filter_all.grid(row=0,column=0, padx=4, pady=4, sticky="w")
filter_attribute.grid(row=0, column=1, padx=4, pady=4, sticky="w")
filter_file1.grid(row=0, column=2, padx=4, pady=4, sticky="w")
filter_file2.grid(row=0, column=3, padx=4, pady=4, sticky="w")

# widgets - nodes of interest tab
nodes_of_interest = ttk.Treeview(nodes_of_interest_tab, height=15)
nodes_of_interest.grid(row=1, column=0, padx=4, pady=4, columnspan=5, sticky="nsew")
nodes_of_interest_vscroll = tk.Scrollbar(nodes_of_interest_tab, orient="vertical", command=nodes_of_interest.yview)
nodes_of_interest_hscroll = tk.Scrollbar(nodes_of_interest_tab, orient="horizontal", command=nodes_of_interest.xview)
nodes_of_interest.configure(yscrollcommand=nodes_of_interest_vscroll.set, xscrollcommand=nodes_of_interest_hscroll.set)
nodes_of_interest_vscroll.grid(row=1, column=5, sticky='ns')
nodes_of_interest_hscroll.grid(row=2, column=0, columnspan=4, sticky='ew')
nodes_of_interest.bind("<<TreeviewSelect>>", update_results_from_node_of_interest_with_event)
nodes_of_interest.tag_configure('with_value', background=COLOUR_SEARCH_WITH_VALUE)
nodes_of_interest.tag_configure('without_value', background=COLOUR_SEARCH_WITHOUT_VALUE)

update_nodes_of_interest_headers()

# widgets - compare by path tab
file1_paths = tk.Listbox(compare_by_path_tab, height=10, width=100, selectmode=tk.SINGLE, exportselection=0)
file1_paths_vscroll = tk.Scrollbar(compare_by_path_tab, orient=tk.VERTICAL, command=file1_paths.yview, bg="blue")
file1_paths_hscroll = tk.Scrollbar(compare_by_path_tab, orient=tk.HORIZONTAL, command=file1_paths.xview)
file1_paths.config(yscrollcommand=file1_paths_vscroll.set, xscrollcommand=file1_paths_hscroll.set)
file1_paths.grid(row=0, column=0, padx=10, pady=4, sticky="nsew")
file1_paths_vscroll.grid(row=0, column=1, padx=5, sticky="ns")
file1_paths_hscroll.grid(row=1, column=0, sticky='ew')
file1_paths.bind("<ButtonRelease-1>", lambda event: on_node_path_select(event, 1))

file2_paths = tk.Listbox(compare_by_path_tab, height=10, width=100, selectmode=tk.SINGLE, exportselection=0)
file2_paths_vscroll = tk.Scrollbar(compare_by_path_tab, orient=tk.VERTICAL, command=file2_paths.yview, bg="blue")
file2_paths_hscroll = tk.Scrollbar(compare_by_path_tab, orient=tk.HORIZONTAL, command=file2_paths.xview)
file2_paths.config(yscrollcommand=file2_paths_vscroll.set, xscrollcommand=file2_paths_hscroll.set)
file2_paths.grid(row=2, column=0, padx=10, pady=4, sticky="nsew")
file2_paths_vscroll.grid(row=2, column=1, padx=5, sticky="ns")
file2_paths_hscroll.grid(row=3, column=0, sticky='ew')
file2_paths.bind("<ButtonRelease-1>", lambda event: on_node_path_select(event, 2))

# widgets - results frame - parameter values
show_differences_only = tk.Checkbutton(node_params_tab, text="Differences only", variable=show_differences_only_var, command=update_results_for_current_mode)
show_differences_only.grid(row=0, column=0, padx=4 ,pady=4, sticky="w")

node_selection_notebook.bind("<<NotebookTabChanged>>", on_node_selection_tab_selected)

results = ttk.Treeview(node_params_tab, height=13)
results.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
results_vscroll = tk.Scrollbar(node_params_tab, orient="vertical", command=results.yview)
results_hscroll = tk.Scrollbar(node_params_tab, orient="horizontal", command=results.xview)
results.configure(yscrollcommand=results_vscroll.set, xscrollcommand=results_hscroll.set)
results_vscroll.grid(row=1, column=1, sticky='ns')
results_hscroll.grid(row=2, column=0, sticky='ew')
results.tag_configure("equal_value", background=TAG_COLOUR_EQUAL)
results.tag_configure("unequal_value", background=TAG_COLOUR_UNEQUAL)

update_result_headers() # so that treeview fills frame2 properly at run time

# widgets - results frame - text content
file1_content = tk.Text(text_content_tab, wrap='word', width=80, height=8)
file1_content.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
file1_content_vscroll = tk.Scrollbar(text_content_tab, orient=tk.VERTICAL, command=file1_content.yview)
file1_content_hscroll = tk.Scrollbar(text_content_tab, orient=tk.HORIZONTAL, command=file1_content.xview)
file1_content.configure(yscrollcommand=file1_content_vscroll.set, xscrollcommand=file1_content_hscroll.set)
file1_content_vscroll.grid(row=0, column=1, sticky='ns')
file1_content_hscroll.grid(row=1, column=0, sticky='ew')

file2_content = tk.Text(text_content_tab, wrap='word', width=80, height=8)
file2_content.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
file2_content_vscroll = tk.Scrollbar(text_content_tab, orient=tk.VERTICAL, command=file2_content.yview)
file2_content_hscroll = tk.Scrollbar(text_content_tab, orient=tk.HORIZONTAL, command=file2_content.xview)
file2_content.configure(yscrollcommand=file2_content_vscroll.set, xscrollcommand=file2_content_hscroll.set)
file2_content_vscroll.grid(row=2, column=1, sticky='ns')
file2_content_hscroll.grid(row=3, column=0, sticky='ew')

# widgets - results frame - project comments
file1_comments = tk.Text(project_comments_tab, wrap='word', width=80, height=8)
file1_comments.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
file1_comments_vscroll = tk.Scrollbar(project_comments_tab, orient=tk.VERTICAL, command=file1_comments.yview)
file1_comments_hscroll = tk.Scrollbar(project_comments_tab, orient=tk.HORIZONTAL, command=file1_comments.xview)
file1_comments.configure(yscrollcommand=file1_comments_vscroll.set, xscrollcommand=file1_comments_hscroll.set)
file1_comments_vscroll.grid(row=0, column=1, sticky='ns')
file1_comments_hscroll.grid(row=1, column=0, sticky='ew')

file2_comments = tk.Text(project_comments_tab ,wrap='word', width=80, height=8)
file2_comments.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
file2_comments_vscroll = tk.Scrollbar(project_comments_tab, orient=tk.VERTICAL, command=file2_comments.yview)
file2_comments_hscroll = tk.Scrollbar(project_comments_tab, orient=tk.HORIZONTAL, command=file2_comments.xview)
file2_comments.configure(yscrollcommand=file2_comments_vscroll.set, xscrollcommand=file2_comments_hscroll.set)
file2_comments_vscroll.grid(row=2, column=1, sticky='ns')
file2_comments_hscroll.grid(row=3, column=0, sticky='ew')

gui.mainloop()