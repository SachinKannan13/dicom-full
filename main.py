from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import shutil
import os
from utils import extract_zip, extract_metadata_to_file, dicom_to_png, zip_folder

app = FastAPI()

BASE_DIR = "storage"
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
METADATA_DIR = os.path.join(BASE_DIR, "metadata")
PNGS_DIR = os.path.join(BASE_DIR, "pngs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)
os.makedirs(PNGS_DIR, exist_ok=True)

@app.post("/process-folder/")
async def process_folder(zip_file: UploadFile = File(...)):
    # Clear previous results (optional, or keep separate per upload)
    shutil.rmtree(METADATA_DIR, ignore_errors=True)
    shutil.rmtree(PNGS_DIR, ignore_errors=True)
    os.makedirs(METADATA_DIR, exist_ok=True)
    os.makedirs(PNGS_DIR, exist_ok=True)

    # Save uploaded ZIP
    zip_path = os.path.join(UPLOAD_DIR, zip_file.filename)
    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(zip_file.file, buffer)

    # Extract ZIP to temp folder
    extract_to = os.path.join(UPLOAD_DIR, "extracted")
    shutil.rmtree(extract_to, ignore_errors=True)
    os.makedirs(extract_to, exist_ok=True)
    extract_zip(zip_path, extract_to)

    # Process each DICOM in extracted folder
    for root, _, files in os.walk(extract_to):
        for file in files:
            if file.lower().endswith(".dcm"):
                dicom_path = os.path.join(root, file)
                filename_wo_ext = os.path.splitext(file)[0]

                # Save metadata JSON
                metadata_file = os.path.join(METADATA_DIR, f"{filename_wo_ext}.json")
                extract_metadata_to_file(dicom_path, metadata_file)

                # Save PNG
                png_file = os.path.join(PNGS_DIR, f"{filename_wo_ext}.png")
                dicom_to_png(dicom_path, png_file)

    # Zip metadata and PNGs folders
    metadata_zip = os.path.join(BASE_DIR, "metadata.zip")
    pngs_zip = os.path.join(BASE_DIR, "pngs.zip")
    zip_folder(METADATA_DIR, metadata_zip)
    zip_folder(PNGS_DIR, pngs_zip)

    return {
        "metadata_zip": "/download/metadata.zip",
        "pngs_zip": "/download/pngs.zip"
    }

@app.get("/download/{zip_name}")
async def download_zip(zip_name: str):
    zip_path = os.path.join(BASE_DIR, zip_name)
    if os.path.exists(zip_path):
        return FileResponse(zip_path, media_type='application/zip', filename=zip_name)
    else:
        return JSONResponse(status_code=404, content={"message": "File not found"})
