from pathlib import Path
import argparse
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

from analysis_helper import find_images

def compute_histogram(image_path: Path, min_val: int, max_val: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute histogram for an image.
    """
    image = Image.open(image_path) 
    image_array = np.array(image)
    num_bins = min(256, max_val - min_val + 1)
    histogram, bins = np.histogram(image_array, bins=num_bins, range=(min_val, max_val))
    return histogram, bins[:-1]

def plot_histograms(image_folder: Path, min_val: int, max_val: int) -> None:
    """
    Plot histograms for all images in a folder.
    """
    image_files = find_images(Path(image_folder))
    num_images = len(image_files)
    
    cols = min(3, num_images)  # Limit to 3 columns for better readability
    rows = (num_images + cols - 1) // cols  # Compute number of rows
    
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 5, rows * 4))
    axes = axes.ravel() if num_images > 1 else [axes]
    
    for i, image_path in enumerate(image_files):
        histogram, bins = compute_histogram(image_path, min_val, max_val)
        
        bin_width = bins[1] - bins[0]
        axes[i].bar(bins, histogram, width=bin_width, color='gray', alpha=0.7)
        axes[i].set_title(Path(image_path).name)
        axes[i].set_xlabel("Pixel Intensity")
        axes[i].set_ylabel("Pixel Count")
        axes[i].set_xlim([min_val, max_val])
    
    # Hide any unused subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])
    
    plt.tight_layout()
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Plot histograms of images in a folder.')
    parser.add_argument('folder', type=str, help='Path to the folder containing images')

    parser.add_argument(
        "--min",
        dest="min_intensity",
        type=int,
        default=0,
        help="Minimum pixel intensity to display. Default: 0."
    )

    parser.add_argument(
        "--max",
        dest="max_intensity",
        type=int,
        default=4096,
        help="Maximum pixel intensity to display. Default: 4096."
    )
    args = parser.parse_args()

    plot_histograms(
        args.folder,
        args.min_intensity,
        args.max_intensity,
    )

if __name__ == "__main__":
    main()
