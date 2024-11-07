# tg-compare-files
A fully functionally Python script, which can be run from the command line or using a GUI.

The script provides two modes of operation. <br> 

The first analyzes and summarizes any "nodes of interest" it finds.  These are nodes which are unique to one file or another, or nodes that are common to both but have different values for a given parameter. <br>

To see the differences between two Terragen files, simply select a node path in the "Nodes with differences" tab.  The differences are highlighted in red in the "Node params" tab below.<br>


![tg_compare_files GUI](/images/tg_compare_files_gui_nodes_with_differences.jpg)

The second mode allows you to compare any node from File 1 with any node from File 2.  This can be very helpful when nodes are renamed between different project files.<br>

![tg_compare_two_nodes_GUI](/images/tg_compare_files_gui_compare_two_nodes.jpg)

### Requirements:
Python 3.x <br>
Two Terragen project files saved to disk.

### Installation:
In this repository you'll find two Python scripts.<br>
tg_compare_files.py <br>
tg_compare_files_cli.py <br>

*Note: The CLI version does not allow comparing any node from File 1 with any node from File 2.* 

### Usage
From the GUI <br>
* Select two Terragen project files. <br> 
* To display parameter names and values in the "Node params" tab click on a node in the "Nodes with differences" tab, or click on any two nodes in the "Compare two nodes" tab. <br>

From the command line <br>
* The tg_compare_files_cli.py script requires two arguments to be passed to it.  These are the full path and filenames of the two Terragen project files to be compared.
* Example: tg_compare_files_cli.py MyTerragenProject.tgd MyOtherTerragenProject.tgd
* The output from the script will be diplayed on the terminal. 
<br><br>
![tg_compare_files_cli output example](/images/tg_compare_files_cli_output.jpg)

## Changelog:
### 2024-11-07
- Compare any node from File 1 with any node from File 2 via the "Compare two nodes" tab.  Especially useful when the name of a node changes between two projects.
- Moved and renamed "Nodes of interest" to "Nodes with differences" tab. Functionally remains the same.
- Moved comparison results from the "Attribute values" pane to the "Node params" tab.  All results or only parameters with differences can be displayed.
- Comments from the Terragen project settings are displayed in the "Project comments" tab.
- XML elements with text content is displayed in the "Text content" tab. Primarily useful for Terrgen Sky, and in future versions of Terragen.
- Support for .tgc and .tgv file formats.
- The GUI version of the script no longer requires the CLI version to operate.
- Deprecated Compare button.
- Deprecated alphanumeric sorting in "Nodes with differences" tab.

### Known Issues:
* Group nodes are not displayed.
