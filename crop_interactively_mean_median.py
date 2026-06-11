import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
from matplotlib.widgets import PolygonSelector
from matplotlib.path import Path as MplPath

from analysis_helper import find_images


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
            return image_files

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


def mean_median_in_region(
    image: Image.Image,
    polygon_points: list[tuple[float, float]] | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculate mean and median pixel values inside the selected polygon.

    If polygon_points is None, use the full image.

    This avoids including transparent/black outside-polygon pixels.
    """
    np_image = np.array(image)

    mask = make_polygon_mask(image.size, polygon_points)

    selected_pixels = np_image[mask]

    if selected_pixels.size == 0:
        raise ValueError("Selected region contains no pixels.")

    avg_pixel = np.mean(selected_pixels, axis=0)
    median_pixel = np.median(selected_pixels, axis=0)

    return avg_pixel, median_pixel


def save_region_overlay(
    display_image: Image.Image,
    polygon_points: list[tuple[float, float]] | None,
    output_path: Path
) -> None:
    """
    Save an image showing the selected polygon overlay.

    If polygon_points is None, save the original image.
    """
    image_with_overlay = display_image.convert("RGBA")
    draw = ImageDraw.Draw(image_with_overlay)

    if polygon_points:
        draw.polygon(polygon_points, outline="red")
        draw.line(
            polygon_points + [polygon_points[0]],
            fill="red",
            width=5
        )

    image_with_overlay.save(output_path)


def format_pixel_value(value: np.ndarray) -> str:
    """
    Format scalar, RGB, RGBA, or multi-channel pixel values cleanly.
    """
    rounded = np.round(value, 2)

    if rounded.ndim == 0:
        return str(float(rounded))

    return "[" + ", ".join(str(x) for x in rounded.tolist()) + "]"


def main() -> None:
    """
    Usage:
        python crop_and_analyze_images.py <input_folder> <output_folder>
    """
    parser = argparse.ArgumentParser(
        description="Select polygon regions from images and compute mean/median pixel values."
    )

    parser.add_argument(
        "input_folder",
        type=Path,
        help="Folder containing original non-adjusted quantitative images, e.g. 0-4096 tif files."
    )

    parser.add_argument(
        "display_folder",
        type=Path,
        help="Folder containing adjusted 0-255 images used for display/region selection."
    )

    parser.add_argument(
        "output_folder",
        type=Path,
        help="Folder where results will be saved."
    )

    args = parser.parse_args()

    input_folder: Path = args.input_folder
    display_folder: Path = args.display_folder
    output_folder: Path = args.output_folder
    output_folder.mkdir(parents=True, exist_ok=True)

    # choose images
    image_files = find_images(input_folder)
    display_image_files = find_images(display_folder)
    chosen_image_indices = ask_image_choices(image_files)

    # output text file
    output_txt_file = output_folder / "means_medians.txt"

    with open(output_txt_file, "w", encoding="utf-8") as f:
        f.write("Image Name, Region Type, Polygon Points, Average Pixel Value, Median Pixel Value\n")

        for i in chosen_image_indices:
            region_source_path = image_files[i]
            display_source_path = display_image_files[i]

            print(f"\nSelected for region selection: {region_source_path}")

            with Image.open(region_source_path) as img:
                region_source_image = img.copy()
            
            with Image.open(display_source_path) as img:
                display_source_image = img.copy()

            # region selection on display image
            print(f"Select region for {region_source_path.name}.")
            polygon_points = select_polygon_region(display_source_image)

            # if nothing selected, use full image
            if polygon_points is None:
                print("Using full image region.")
                region_label = "full_image"
            else:
                region_label = "polygon"

            # calculate on source image
            avg_pixel, median_pixel = mean_median_in_region(
                region_source_image,
                polygon_points
            )

            # save stats on text file
            avg_text = format_pixel_value(avg_pixel)
            median_text = format_pixel_value(median_pixel)

            print(
                f"Image: {region_source_path.name}; "
                f"Average: {avg_text}; "
                f"Median: {median_text}"
            )

            f.write(
                f"{region_source_path.name},\n "
                f"{region_label},\n "
                f"{polygon_points},\n "
                f"{avg_text},\n "
                f"{median_text}\n\n"
            )

            # save overlap images
            overlay_path = output_folder / f"region_overlay_{region_source_path.stem}.png"

            save_region_overlay(
                display_image=display_source_image,
                polygon_points=polygon_points,
                output_path=overlay_path
            )


    print("\nDone.")
    print(f"Image statistics saved to: {output_txt_file}")
    print(f"Region overlay images saved in: {output_folder}")


if __name__ == "__main__":
    main()