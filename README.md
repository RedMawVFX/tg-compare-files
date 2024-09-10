# tg-compare-files
A fully functionally Python script, which can be run from the command line or using a GUI.

Given two Terragen project files as input, the script will return any "nodes of interest" it finds.  <br>
These are nodes which are unique to one project or the other, or nodes that are common to both but have different values for a given parameter. <br>
Selecting a node of interest, will diplay the parameter values from each file. <br>


![tg_compare_files GUI](/images/tg_compare_files_gui.jpg)

### Requirements:
Python 3.x <br>
Two Terragen project files saved to disk.

### Installation:
In this repository you'll find two Python scripts.  You need both scripts for the GUI version to work. <br>
tg_compare_files.py <br>
tg_compare_files_cli.py <br>

### Usage
From the GUI <br>
* Select two Terragen project files and click the Compare button.  The nodes of interest window will update. <br> 
* You can sort the window alphanumerically and in reverse. <br> 
* You can filter the displayed results as well. <br>  
* Clicking on a node in the nodes of interest window will display the attribute name and values from each file.

From the command line <br>
* The tg_compare_files_cli.py script requires two arguments to be passed to it.  These are the full path and filenames of the two Terragen project files to be compared.
* Example: tg_compare_files_cli.py MyTerragenProject.tgd MyOtherTerragenProject.tgd
* The output from the script will be diplayed on the terminal. 
<br><br>
![tg_compare_files_cli output example](/images/tg_compare_files_cli_output.jpg)

### Known Issues:
* Currently the animation data block and group nodes are not displayed.
