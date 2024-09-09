import argparse
import xml.etree.ElementTree as ET
import re

exclude_tags = ['animationData','group']

def preprocess_xml(xml_string):
    # Replace invalid characters (e.g., "::") in tag names
    return re.sub(r'<([^>]*?)::([^>]*?)>', r'<\1_\2>', xml_string)

def preprocess_file(file):
    with open(file,'r',encoding='utf-8') as file:
        xml_data = file.read()
        xml_data_preprocessed = preprocess_xml(xml_data)
    return xml_data_preprocessed

def get_paths_of_children(node,prefix:str):
    node_names = []
    for child in node:
        if child.tag not in exclude_tags:
            child_path = generate_path(child=child, prefix = prefix)
            node_names.append(child_path)
            deeper_names = get_paths_of_children(child,prefix=child_path+"/")
            node_names.extend(deeper_names)
    return node_names

def generate_path(child,prefix:str):
    if 'name' in child.attrib: # some nodes don't have a name attribute e.g. animationdata
        return prefix + child.attrib['name']
    else:
        return prefix + "unnamed_node_" + child.tag

def find_child_by_path(node,prefix:str,find_path):
    for child in node:
        if child.tag == "custom":
            pass
        if child.tag not in exclude_tags:
            child_path = generate_path(child=child, prefix = prefix)
            if child_path == find_path:
                return child
            recursion_result = find_child_by_path(child,prefix=child_path+"/",find_path=find_path)
            if recursion_result != None:
                return recursion_result
    return None

def parse_tgd(file):
    parsed = ET.fromstring(file)
    return parsed

def main():
    # create argument parser
    parser = argparse.ArgumentParser(description="Process two files")
    
    # add arguments for file paths
    parser.add_argument("file1",type=str,help="Path to the first file")
    parser.add_argument("file2",type=str,help="Path to the second file")
    
    # parse the arguments
    args = parser.parse_args()

    # remove double colons from tags before parsing
    file1_preprocessed = preprocess_file(args.file1)
    file2_preprocessed = preprocess_file(args.file2)

    # parse terragen project file
    root1 = parse_tgd(file1_preprocessed)
    root2 = parse_tgd(file2_preprocessed)
    
    # build a list of node names for each file
    file1_node_names = get_paths_of_children(root1,prefix="/")
    file2_node_names = get_paths_of_children(root2,prefix="/")
    
    # build a list of node names common to both files, as well as unique nodes
    set1 = set(file1_node_names)
    set2 = set(file2_node_names)
    common_nodes = list(set1.intersection(set2))
    unique_nodes = list(set1.symmetric_difference(set2))

    # output results
    different_value_summary = "Summary of different parameter values in the following files: \n" + args.file1 + "\n" + args.file2 + "\n\n"
    for node_name in common_nodes:
        previous_node_of_interest = ""
        display_string = ""
        element1 = find_child_by_path(root1, "/", find_path=node_name)
        element2 = find_child_by_path(root2, "/", find_path=node_name)
        if element1 != None:
            for key in element1.keys():
                value1 = element1.get(key)
                value2 = element2.get(key)
                if key.startswith("gui_"):
                    continue
                if value1 != value2:
                    node_of_interest = node_name.split("/")[1] # e.g. /parent/child/grandchild returns parent
                    if node_of_interest != previous_node_of_interest:
                        different_value_summary = different_value_summary + node_of_interest + "\n"
                        previous_node_of_interest = node_of_interest
                    different_value_summary = different_value_summary + "    " + str(key) + ": \n        " + value1 + " \n        " + value2 + "\n"
        else:
            print(f"could not find {node_name} ")
        
    print (different_value_summary)

if __name__ == "__main__":
    main()