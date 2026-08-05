import os
import ast
import sys

def check_streamlit_pages(home_file="Home.py"):
    """
    Parses Home.py and ensures all targets of make_page() actually exist in the filesystem.
    """
    print(f"Checking Streamlit routes in {home_file}...")
    if not os.path.exists(home_file):
        print(f"Error: {home_file} not found.")
        sys.exit(1)
        
    with open(home_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax Error in {home_file}: {e}")
        sys.exit(1)
    
    missing_pages = []
    page_count = 0
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "make_page":
                if len(node.args) > 0 and isinstance(node.args[0], ast.Constant):
                    file_path = node.args[0].value
                    page_count += 1
                    if not os.path.exists(file_path):
                        missing_pages.append(file_path)
                        
    if missing_pages:
        print("\nBroken Links Found!")
        print("The following Streamlit pages are referenced in Home.py but do not exist on disk:")
        for p in missing_pages:
            print(f"  - {p}")
        sys.exit(1)
    else:
        print(f"Success: All {page_count} Streamlit pages referenced in {home_file} exist on disk.")

if __name__ == "__main__":
    # Move to the root of the project
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)
    
    check_streamlit_pages()
