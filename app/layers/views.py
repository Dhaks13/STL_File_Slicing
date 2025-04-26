from django.shortcuts import render
import os

# Create your views here.
def layer_index():
    # Get the path to the current file
    current_file_path = os.path.abspath(__file__)

    # Get the directory name of the current file
    directory_name = os.path.dirname(current_file_path)

    # Get the parent directory name
    parent_directory_name = os.path.dirname(directory_name)

    # Construct the path to the "templates" folder
    layers_folder_path = os.path.join(parent_directory_name, "layers")
    files = os.listdir(layers_folder_path)
    # Filter the list to include only files with the ".png" extension
    png_files = [f for f in files if f.endswith(".png")]
    # Create a list of dictionaries with file names and paths
    png_files_list = []
    for file in png_files:
        file_path = os.path.join(layers_folder_path, file)
        png_files_list.append({"name": file, "path": file_path})
    return {"png_files": png_files_list}


def layer_view(request):
    png_files_list = layer_index()
    return render(request, "layers.html", {"png_files": png_files_list})