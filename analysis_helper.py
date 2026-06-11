from pathlib import Path

def find_images(input_folder: Path) -> list[Path]:
    '''
    Find all image files in the input folder (including subfolders). Returns a list of image file paths.
    '''
    supported_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.tif'}
    image_files = [f for f in input_folder.rglob("*") if f.is_file() and f.suffix.lower() in supported_extensions]
    
    if not image_files:
        raise FileNotFoundError("No image files found in the specified folder.")
    
    return image_files