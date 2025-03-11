import os
import argparse
import sys
from pathlib import Path

def generate_tree(root_dir, ignore_dirs=None, ignore_files=None, indent=0, use_ascii=False):
    """Generate a tree-like structure of the directory."""
    if ignore_dirs is None:
        ignore_dirs = ['.git', '__pycache__', 'venv', 'env', '.venv']
    if ignore_files is None:
        ignore_files = ['.gitignore', '.DS_Store']
    
    # Use simple ASCII characters if requested or on Windows
    if use_ascii:
        branch = "|-- "
    else:
        branch = "├── "
    
    items = os.listdir(root_dir)
    items.sort()
    
    structure = ""
    
    for item in items:
        path = os.path.join(root_dir, item)
        
        # Skip ignored directories and files
        if (os.path.isdir(path) and item in ignore_dirs) or (os.path.isfile(path) and item in ignore_files):
            continue
        
        structure += "    " * indent + branch + item + "\n"
        
        if os.path.isdir(path):
            structure += generate_tree(path, ignore_dirs, ignore_files, indent + 1, use_ascii)
    
    return structure

def save_tree_to_file(root_dir, output_file=None, use_ascii=False):
    """Save the directory tree structure to a file."""
    # If no output file is specified, create it in the same directory
    if output_file is None:
        output_file = os.path.join(root_dir, "project_structure.txt")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(root_dir) + "\n")
            f.write(generate_tree(root_dir, use_ascii=use_ascii))
        print(f"Project structure saved to {output_file}")
    except UnicodeEncodeError:
        # If Unicode encoding fails, try again with ASCII
        print("Warning: Unicode encoding failed. Switching to ASCII characters.")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(root_dir) + "\n")
            f.write(generate_tree(root_dir, use_ascii=True))
        print(f"Project structure saved to {output_file} using ASCII characters")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate a project directory structure file')
    parser.add_argument('--path', '-p', default=None, help='Path to the project directory (default: current script directory)')
    parser.add_argument('--output', '-o', default=None, help='Output file path (default: project_structure.txt in the project directory)')
    parser.add_argument('--ignore-dirs', '-id', nargs='+', default=None, help='Directories to ignore')
    parser.add_argument('--ignore-files', '-if', nargs='+', default=None, help='Files to ignore')
    parser.add_argument('--ascii', '-a', action='store_true', help='Use ASCII characters for better compatibility')
    
    args = parser.parse_args()
    
    # Determine if we should use ASCII by default on Windows
    use_ascii = args.ascii or (sys.platform == 'win32')
    
    # Use the script's directory as the default path if none is provided
    if args.path is None:
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_path = script_dir
    else:
        # Use the provided path
        project_path = os.path.abspath(args.path)
    
    # Convert to Path object for better cross-platform compatibility
    project_path = Path(project_path)
    
    # Generate and save the tree structure
    save_tree_to_file(
        project_path, 
        args.output,
        use_ascii
    )

if __name__ == "__main__":
    main()