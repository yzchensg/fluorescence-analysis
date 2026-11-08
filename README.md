# Image Analysis Helpers

Small Python scripts for basic image processing and analysis.

## Files

* `analysis_helper.py` — finds image files in a folder.
* `display_histograms.py` — displays pixel-intensity histograms for all images in a folder.
* `scale_to_8.py` — rescales images to 8-bit (256) PNGs from 12-bit (4096) TIFs using a chosen min/max intensity range.
* `crop_interactively_mean_median.py` — lets the user select a crop region, then calculates mean and median RGB values for that region across images.

## Usage

Step 1: Display histograms to figure out which are the fluorescent images and what are their ranges; default min 0 max 4096.
```bash
python display_histograms.py ../../database/fluorescamine-0728/raw \
  --min 0 \
  --max 4096 
```
Step 2: Note down the fluorescent and brightfield images, and scale the images separately to the observed range by manually inputting the values. 
```bash
python scale_to_256.py ../../database/fluorescamine-0728/raw \
  --output ../../database/fluorescamine-0728/scale-2000 \
  --min 0 \
  --max 200
```
Step 3: Note down the fluorescent image indices. Select them for median/mean analysis.
```bash
python crop_calc.py <input_folder> <scaled_images_folder> <output_folder>
```

## Requirements

```bash
pip install numpy pillow matplotlib
```

# Updates:
- What's needed?
1. Simplify input/output address documentation
2. Automatically choose the best regions and ignore outliers