# Fluorescence Image Analysis

Inspect TIFF intensities, create 8-bit previews, and measure fluorescence within manually selected regions.

## Setup

Use Python 3.10+ with a graphical display:

```bash
pip install numpy pillow matplotlib scipy
```

## Workflow

Run these commands from the project folder. Each script prompts for its inputs; no command-line arguments are required. Enter folder paths without surrounding quotes.

### 1. Inspect intensities

```bash
python display_histograms.py
```

Enter the raw-image folder and histogram minimum/maximum. The script searches subfolders for `.tif` and `.tiff` images and displays their histograms.

### 2. Create previews

```bash
python scale_to_256.py
```

Enter the same folder and a scaling range. Values are clipped to that range and mapped to 0–255. For 12-bit images, intensities run from 0 to 4095.

PNGs are saved inside the input folder:

```text
<input_folder>/<folder_name>_scaled_<min>-<max>/
    <image_stem>_scaled_<min>-<max>.png
```

### 3. Select regions and measure

```bash
python crop_calc.py
```

- Enter the raw-image folder.
- Select image numbers, such as `1,3,5`, or enter `all`.
- Confirm the preview subfolder with `y`; enter `n` to try the next candidate.
- Click polygon vertices around the deposition region. Close the polygon or press Enter after at least three points to finish. Press Esc or close the window before completing a polygon to use the full image.

Measurements use original TIFF intensities, not preview values. The reported `mean` is a trimmed mean that removes 20% of pixels from each intensity tail; `median` is the region median.

Outputs in the raw-image folder (overwritten on reruns):

- `means_medians.json` — mean and median by filename.
- `means_medians.txt` — statistics and polygon coordinates.
- `cropped_regions/region_overlay_<image_stem>.png` — previews with region outlines.

## Notes

- Use single-channel TIFFs for measurement.
- Raw and preview images are paired by list position. Verify matching order, count, dimensions, and alignment before measuring.
- Keep raw filenames unique across subfolders to avoid output collisions.
- `analysis_helper.py` provides file discovery, prompts, and polygon masks.
