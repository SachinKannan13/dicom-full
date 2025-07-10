import os
import zipfile
import pydicom
from PIL import Image
import numpy as np
import json

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def extract_metadata_to_file(dicom_path, output_file):
    ds = pydicom.dcmread(dicom_path)
    metadata = {}
    for elem in ds:
        if elem.VR != 'SQ':
            metadata[elem.keyword or str(elem.tag)] = str(elem.value)
    with open(output_file, 'w') as f:
        json.dump(metadata, f, indent=2)

def dicom_to_png(dicom_path, png_path):
    ds = pydicom.dcmread(dicom_path)
    pixel_array = ds.pixel_array
    image_2d = pixel_array.astype(float)
    image_2d_scaled = (np.maximum(image_2d, 0) / image_2d.max()) * 255.0
    image_2d_scaled = np.uint8(image_2d_scaled)
    img = Image.fromarray(image_2d_scaled)
    img.save(png_path)

def zip_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, folder_path)
                zipf.write(abs_path, rel_path)
