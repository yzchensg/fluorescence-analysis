import argparse
from pathlib import Path
import json
import numpy as np
from scipy.stats import trim_mean
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
from matplotlib.widgets import PolygonSelector
from matplotlib.path import Path as MplPath

from analysis_helper import (find_images, ask_image_choices, ask_subfolder_choice, 
                             select_polygon_region, make_polygon_mask,
                             ask_input_folder)


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

    avg_pixel = trim_mean(selected_pixels, proportiontocut=0.2)
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

    input_folder: Path = ask_input_folder()
    image_files = find_images(input_folder, "raw")
    chosen_image_indices = ask_image_choices(image_files)

    # display images for cropping
    display_folder = ask_subfolder_choice(input_folder)
    display_image_files = find_images(display_folder, supported_extensions="not_raw")

    # output text file
    output_txt_file = input_folder / "means_medians.txt"
    output_json_file = input_folder / "means_medians.json"
    output = {}
    overlay_folder = input_folder / "cropped_regions"
    overlay_folder.mkdir(exist_ok=True)

    with open(output_txt_file, "w", encoding="utf-8") as f:
        f.write("Image Name, Region Type, Polygon Points, Average Pixel Value, Median Pixel Value\n")

        for i in chosen_image_indices:
            # assuming they are named similarly
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
            # save in json file
            output[region_source_path.name] = {
                "median": float(median_pixel),
                "mean": float(avg_pixel),
            }

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
            overlay_path = overlay_folder / f"region_overlay_{region_source_path.stem}.png"

            save_region_overlay(
                display_image=display_source_image,
                polygon_points=polygon_points,
                output_path=overlay_path
            )

    with open(output_json_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4)


    print("\nDone.")
    print(f"Image statistics saved to: {output_txt_file}")
    print(f"Region overlay images saved in: {input_folder}")


if __name__ == "__main__":
    main()