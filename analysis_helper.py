from pathlib import Path
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import PolygonSelector
from matplotlib.path import Path as MplPath

def ask_input_folder():
    while True:
        input_folder = Path(input("Key in input folder:"))
        if input_folder.exists() and input_folder.is_dir():
            return input_folder
        else: 
            print("Directory does not exist")
            continue


def ask_min():
    while True:
        min_value = int(input("Key in min value:"))
        if min_value > 4095 or min_value < 0:
            print("Key in a value in the range from 0-4096")
            continue
        return min_value

def ask_max(min_value):
    while True:
        max_value = int(input("Key in max value:"))
        if max_value > 4096 or max_value < 0:
            print("Key in a value in the range from 0-4096")
            continue
        if max_value <= min_value:
            print(f"Make sure your max value is larger than min {min_value}")
            continue
        return max_value


def find_images(input_folder: Path, supported_extensions='raw') -> list[Path]:

    '''
    Find all image files in the input folder (including subfolders). 
    Returns a list of image file paths.
    '''
    if supported_extensions == 'raw':
        supported_extensions = {'.tiff', '.tif'}
    else:
        supported_extensions = {'.png', '.jpg', '.jpeg'}
    image_files = [f for f in input_folder.rglob("*") if f.is_file() and f.suffix.lower() in supported_extensions]
    
    if not image_files:
        raise FileNotFoundError("No image files found in the specified folder.")
    
    return image_files

def ask_subfolder_choice(input_folder: Path):
    display_folders = sorted(p for p in input_folder.iterdir() if p.is_dir())
    while display_folders:
        candidate = display_folders[-1]
        while True:
            answer = input(
                f"Folder of scaled images for cropping display. Found: {candidate}\n"
                "Is this it? [y/n]: "
            ).strip().lower()
            if answer in {"y", "yes"}:
                return candidate
            if answer not in {"n", "no"}:
                print("Please enter y or n.")
                continue
            break
        display_folders.pop()

    raise NotADirectoryError("Folder that contains scaled images for cropping purpose asked. please move it to the input folder!")

def ask_image_choices(image_files: list[Path]) -> list[int]:
    """
    Ask the user to choose one or more images from a list.

    The user can enter:
        1
        1,3,5
        all

    Returns:
        A list of selected image indices.
    """
    if not image_files:
        raise ValueError("No image files found.")

    print("Available images:")
    for idx, image_file in enumerate(image_files, start=1):
        print(f"{idx}. {image_file}")

    while True:
        user_input = input(
            "\nEnter image number(s) of interest for mean/median calculation, "
            f"(1-{len(image_files)}), separated by commas, or 'all': "
        ).strip()

        if user_input.lower() == "all":
            return list(range(len(image_files)))

        try:
            selected_indices = [
                int(part.strip()) - 1
                for part in user_input.split(",")
                if part.strip()
            ]
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas, e.g. 1,3,5.")
            continue

        if not selected_indices:
            print("No selection entered.")
            continue

        invalid_indices = [
            idx for idx in selected_indices
            if idx < 0 or idx >= len(image_files)
        ]

        if invalid_indices:
            print(f"Each choice must be between 1 and {len(image_files)}.")
            continue

        # Remove duplicates while preserving order
        selected_indices = list(dict.fromkeys(selected_indices))

        return selected_indices


def select_polygon_region(
    image: Image.Image
) -> list[tuple[float, float]] | None:
    """
    Let the user select a polygon region.

    Controls:
        Left click: add polygon point
        Enter: finish polygon
        Esc: cancel selection
        Close window without input: use full image

    Returns:
        List of polygon points, or None if no region was selected.
    """
    selected_points: list[tuple[float, float]] = []

    fig, ax = plt.subplots()
    ax.imshow(image)
    ax.set_title(
        "Click points to select polygon region.\n"
        "Press Enter to finish. Press Esc or close window for full image."
    )

    polygon_selector = None

    def finish_selection(vertices):
        selected_points.clear()
        selected_points.extend(vertices)

        if selected_points:
            print(f"Selected polygon points: {selected_points}")
        else:
            print("No polygon selected. Using full image.")

        plt.close(fig)

    def on_select(vertices):
        finish_selection(vertices)

    polygon_selector = PolygonSelector(
        ax,
        on_select,
        useblit=True
    )

    def on_key(event):
        if event.key == "escape":
            selected_points.clear()
            print("No region selected. Using full image.")
            plt.close(fig)

        elif event.key == "enter":
            vertices = polygon_selector.verts

            if len(vertices) >= 3:
                finish_selection(vertices)
            else:
                selected_points.clear()
                print("Fewer than 3 points selected. Using full image.")
                plt.close(fig)

    fig.canvas.mpl_connect("key_press_event", on_key)

    plt.show()

    if len(selected_points) < 3:
        return None

    return selected_points


def make_polygon_mask(
    image_size: tuple[int, int],
    polygon_points: list[tuple[float, float]] | None
) -> np.ndarray:
    """
    Create a boolean mask for the polygon region.

    Args:
        image_size: PIL image size as (width, height).
        polygon_points: Polygon vertices, or None for full image.

    Returns:
        Boolean mask with shape (height, width).
    """
    width, height = image_size

    if not polygon_points:
        return np.ones((height, width), dtype=bool)

    y_grid, x_grid = np.mgrid[:height, :width]
    points = np.vstack((x_grid.ravel(), y_grid.ravel())).T

    polygon_path = MplPath(polygon_points)
    mask = polygon_path.contains_points(points).reshape(height, width)

    return mask


def crop_polygon_region(
    image: Image.Image,
    polygon_points: list[tuple[float, float]] | None = None
) -> Image.Image:
    """
    Crop image to the polygon's bounding box and make pixels outside
    the polygon transparent.

    If polygon_points is None or empty, return the full image.
    """
    if not polygon_points:
        return image.copy()

    image_rgba = image.convert("RGBA")
    image_array = np.array(image_rgba)

    height, width = image_array.shape[:2]

    polygon_array = np.array(polygon_points)

    x_min = max(int(np.floor(polygon_array[:, 0].min())), 0)
    y_min = max(int(np.floor(polygon_array[:, 1].min())), 0)
    x_max = min(int(np.ceil(polygon_array[:, 0].max())), width)
    y_max = min(int(np.ceil(polygon_array[:, 1].max())), height)

    if x_max <= x_min or y_max <= y_min:
        return image.copy()

    y_grid, x_grid = np.mgrid[y_min:y_max, x_min:x_max]
    points = np.vstack((x_grid.ravel(), y_grid.ravel())).T

    polygon_path = MplPath(polygon_points)
    mask = polygon_path.contains_points(points).reshape(y_max - y_min, x_max - x_min)

    cropped_array = image_array[y_min:y_max, x_min:x_max].copy()

    # Make outside-polygon pixels transparent
    cropped_array[~mask] = [0, 0, 0, 0]

    return Image.fromarray(cropped_array)