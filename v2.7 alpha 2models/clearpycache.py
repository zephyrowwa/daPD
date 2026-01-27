import os
import shutil

def remove_pycache(root_dir):
    """
    Recursively removes all __pycache__ directories within the given root_dir.
    """
    # Get the absolute path for clarity in output
    abs_path = os.path.abspath(root_dir)
    
    if not os.path.exists(abs_path):
        print(f"Error: The directory '{abs_path}' does not exist.")
        return

    pycache_count = 0
    print(f"Scanning '{abs_path}' for __pycache__ folders...\n")

    # Walk through the directory tree
    # topdown=True allows us to modify 'dirs' in-place to avoid recursion into deleted folders
    for current_root, dirs, files in os.walk(root_dir, topdown=True):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(current_root, "__pycache__")
            
            try:
                # Remove the directory and all its contents
                shutil.rmtree(pycache_path)
                print(f"Deleted: {pycache_path}")
                pycache_count += 1
                
                # Remove from 'dirs' list to prevent os.walk from trying to recurse into it
                dirs.remove("__pycache__")
                
            except PermissionError:
                print(f"Skipped (Permission Denied): {pycache_path}")
            except Exception as e:
                print(f"Failed to delete {pycache_path}. Reason: {e}")

    print(f"\nCleanup complete. Removed {pycache_count} '__pycache__' folders.")

if __name__ == "__main__":
    # '.' targets the current directory where the script is run
    target_directory = '.' 
    
    # Safety confirmation
    confirm = input(f"Are you sure you want to delete all __pycache__ folders in '{os.path.abspath(target_directory)}'? (y/n): ")
    
    if confirm.lower() == 'y':
        remove_pycache(target_directory)
    else:
        print("Operation cancelled.")