from fastapi import FastAPI, File, Form, UploadFile, HTTPException, APIRouter
import shutil
import os
import uuid
from src.utils.ImageUtils import ModifyImageForDicom,reshape_to_HW_slices
from src.utils.DicomUtils import ImageToDicom,fun, CreateSegForMRI
from src.utils.FileHandlingUtils import FindAllDCMSeries
from src.configuration.config import TempDCMseries, OutputFolder, OutputMRDir, VSmodelURL,CorrectNfityPath
from fastapi.responses import FileResponse
import tempfile
import pydicom
import zipfile
import dicom2nifti
import nibabel as nib
import numpy as np
import requests
from scipy.ndimage import zoom


router = APIRouter()

TEMP_DIRECTORY = "temp_files"
OUTPUT_DIRECTORY = "output"


os.makedirs(TEMP_DIRECTORY, exist_ok=True)
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

@router.post("/upload/")
async def upload_image(
    image: UploadFile = File(...),
    sopclassuid: str = Form(...),
    sopinstanceuid: str = Form(...),
    patientname: str = Form(...),
    patientid: str = Form(...),
):
    """
    Endpoint to upload an image, modify it, and convert it into a DICOM file.
    """
    # Generate unique file names for temporary files
    file_extension = os.path.splitext(image.filename)[1]
    temp_image_path = os.path.join(TEMP_DIRECTORY, f"{uuid.uuid4()}{file_extension}")
    modified_image_path = os.path.join(TEMP_DIRECTORY, f"{uuid.uuid4()}.png")
    dicom_file_path = os.path.join(OUTPUT_DIRECTORY, "SampleRetinalImage.dcm")

    try:
        # Save uploaded file to a temporary location
        with open(temp_image_path, 'wb') as tmp_file:
            data = await image.read()
            tmp_file.write(data)

        # Modify the image for DICOM compatibility
        modified_image = ModifyImageForDicom(temp_image_path)
        modified_image.save(modified_image_path, quality=100)

        # Convert the modified image to a DICOM file
        dicom_data = {
            "sopclassuid": sopclassuid,
            "sopinstanceuid": sopinstanceuid,
            "patientname": patientname,
            "patientid": patientid,
        }
        ds = ImageToDicom(modified_image_path, dicom_data)
        ds.save_as(dicom_file_path)

        # Ensure the DICOM file was created successfully
        if not os.path.exists(dicom_file_path):
            raise HTTPException(status_code=500, detail="Failed to create DICOM file.")

        return FileResponse(
            path=dicom_file_path,
            media_type="application/dicom",
            filename=os.path.basename(dicom_file_path),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    finally:
        # Cleanup temporary files
        for path in [temp_image_path, modified_image_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError as cleanup_error:
                    print(f"Failed to delete {path}: {cleanup_error}")



@router.post("/dcmtonii/")
async def dcmtonii(
    file: UploadFile = File(...),
):
    file_extension = os.path.splitext(file.filename)[1]
    temp_zip_path = os.path.join(TEMP_DIRECTORY, f"{uuid.uuid4()}{file_extension}")
    try:
        with open(temp_zip_path, 'wb') as tmp_file:
            data = await file.read()
            tmp_file.write(data)
        
        os.makedirs(TempDCMseries, exist_ok=True)
        shutil.rmtree(TempDCMseries)
        os.makedirs(TempDCMseries, exist_ok=True)

        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(TempDCMseries)
        
        AllMRSeries = FindAllDCMSeries(TempDCMseries)

        OutputFilesPath = []
        id = 0
        Correctnii = nib.load(CorrectNfityPath)

        for Path in AllMRSeries:
            output_file = os.path.join(OutputFolder, f'vs_gk_000{id}.nii.gz')
            dicom2nifti.dicom_series_to_nifti(Path, output_file, reorient_nifti=True)

            nii_img = nib.load(output_file)
            data = nii_img.get_fdata()

            current_shape = data.shape
            affine = nii_img.affine

            new_shape = (416, 488, data.shape[2])  # You can adjust the number of slices (last dimension) as needed

            # Calculate the zoom factors for resizing
            zoom_factors = [new_shape[0] / current_shape[0], 
                            new_shape[1] / current_shape[1], 
                            1]  # No resizing in the z-axis (slice dimension)

            # Resize the data
            resized_data = zoom(data, zoom_factors, order=1)  # 'order=1' for bilinear interpolation

            # Update the affine matrix: Adjust voxel size for the first two dimensions
            new_affine = affine

            # Calculate new voxel size for the resized image (in the x and y dimensions)
            new_voxel_size = np.array(nii_img.header.get_zooms()) * np.array(zoom_factors)
            new_affine[0, 0] = new_voxel_size[0]
            new_affine[1, 1] = new_voxel_size[1]

            new_img = nib.Nifti1Image(resized_data, new_affine)
            nib.save(new_img, output_file)

            nii_img = nib.load(output_file)
            data = nii_img.get_fdata()
            data = np.array(data, dtype=np.uint16)
            nii_img = nib.Nifti1Image(data, Correctnii.affine)
            nib.save(nii_img, output_file)
            OutputFilesPath.append(output_file)



        return FileResponse(
            path=OutputFilesPath[0],
            media_type="application/gzip",  # or use "application/nii" if that's more suitable
            filename=os.path.basename(OutputFilesPath[0]),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/niitodcm/")
async def niitodcm(
    file: UploadFile = File(...),
):
    file_extension = '.nii.gz'
    temp_nii_path = os.path.join(TEMP_DIRECTORY, f"{uuid.uuid4()}{file_extension}")
    try:
        with open(temp_nii_path, 'wb') as tmp_file:
            data = await file.read()
            tmp_file.write(data)
        
        outputzipPath = os.path.join(OutputFolder, f"{uuid.uuid4()}")
        fun(temp_nii_path, OutputMRDir, outputzipPath)
        outputzipPath = outputzipPath + '.zip'


        return FileResponse(
            path=outputzipPath,
            media_type="application/zip",  # or use "application/nii" if that's more suitable
            filename=os.path.basename(outputzipPath),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
        





@router.post("/NiiToSeg/")
async def niitodcm(
    Nii: UploadFile = File(...),
    MRI: UploadFile = File(...),
):
    Nii_file_extension = '.nii.gz'
    temp_nii_path = os.path.join(TEMP_DIRECTORY, f"{uuid.uuid4()}{Nii_file_extension}")
    MRI_file_extension = os.path.splitext(MRI.filename)[1]
    temp_zip_path = os.path.join(TEMP_DIRECTORY, f"{uuid.uuid4()}{MRI_file_extension}")
    try:
        with open(temp_nii_path, 'wb') as tmp_file:
            data = await Nii.read()
            tmp_file.write(data)
        
        with open(temp_zip_path, 'wb') as tmp_file:
            data = await MRI.read()
            tmp_file.write(data)
        

        os.makedirs(TempDCMseries, exist_ok=True)
        shutil.rmtree(TempDCMseries)
        os.makedirs(TempDCMseries, exist_ok=True)

        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(TempDCMseries)
        
        AllMRSeries = FindAllDCMSeries(TempDCMseries)

        SegObjPath = CreateSegForMRI(AllMRSeries[0],temp_nii_path)


        return FileResponse(
            path=SegObjPath,
            media_type="application/dicom",  # or use "application/nii" if that's more suitable
            filename=os.path.basename(SegObjPath),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    


    


    
    

@router.post("/Predictv1/")
async def niitodcm(
    MRI: UploadFile = File(...),
):
    MRI_file_extension = os.path.splitext(MRI.filename)[1]
    temp_zip_path = os.path.join(TEMP_DIRECTORY, f"{uuid.uuid4()}{MRI_file_extension}")
    try:
        with open(temp_zip_path, 'wb') as tmp_file:
            data = await MRI.read()
            tmp_file.write(data)

        os.makedirs(TempDCMseries, exist_ok=True)
        shutil.rmtree(TempDCMseries)
        os.makedirs(TempDCMseries, exist_ok=True)

        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(TempDCMseries)
        
        AllMRSeries = FindAllDCMSeries(TempDCMseries)

        os.makedirs(OutputFolder, exist_ok=True)
        shutil.rmtree(OutputFolder)
        os.makedirs(OutputFolder, exist_ok=True)

        OutputFilesPath = []
        id = 0
        Correctnii = nib.load(CorrectNfityPath)

        dicom2nifti.settings.disable_validate_slice_increment()
        dicom2nifti.settings.disable_validate_slicecount()

        for Path in AllMRSeries:
            output_file = os.path.join(OutputFolder, f'vs_gk_000{id}.nii.gz')
            dicom2nifti.dicom_series_to_nifti(Path, output_file, reorient_nifti=True)
            file1 = os.listdir(Path)
            file1 = file1[0]
            pixelarray = pydicom.dcmread(os.path.join(Path,file1))
            pixelarray = pixelarray.pixel_array

        



            # nii_img = nib.load(output_file)
            # data = nii_img.get_fdata()

            # current_shape = data.shape
            # affine = nii_img.affine

            # new_shape = (416, 488, data.shape[2])  # You can adjust the number of slices (last dimension) as needed

            # # Calculate the zoom factors for resizing
            # zoom_factors = [new_shape[0] / current_shape[0], 
            #                 new_shape[1] / current_shape[1], 
            #                 1]  # No resizing in the z-axis (slice dimension)

            # # Resize the data
            # resized_data = zoom(data, zoom_factors, order=1)  # 'order=1' for bilinear interpolation

            # # Update the affine matrix: Adjust voxel size for the first two dimensions
            # new_affine = affine

            # # Calculate new voxel size for the resized image (in the x and y dimensions)
            # new_voxel_size = np.array(nii_img.header.get_zooms()) * np.array(zoom_factors)
            # new_affine[0, 0] = new_voxel_size[0]
            # new_affine[1, 1] = new_voxel_size[1]

            # new_img = nib.Nifti1Image(resized_data, new_affine)
            # nib.save(new_img, output_file)

            nii_img = nib.load(output_file)
            data = nii_img.get_fdata()
            data = reshape_to_HW_slices(pixelarray,data)
            print("resahape:-",data.shape)


            data = np.array(data, dtype=np.uint16)
            

            nii_img = nib.Nifti1Image(data, Correctnii.affine)
            nib.save(nii_img, output_file)
            OutputFilesPath.append((Path,output_file))
            id = id+ 1
        

        file_path = OutputFilesPath[0][1]  # File to upload
        nii_img = nib.load(file_path)
        data = nii_img.get_fdata()
        print("sendinf nii.gz:-",data.shape)


        output_path = os.path.join(OutputFolder,"downloaded_file.nii.gz")

        with open(file_path, "rb") as file:
            # Send the file to the API
            response = requests.post(VSmodelURL, files={"file": file})

            # Check if the request was successful
            if response.status_code == 200:
                # Save the returned file
                with open(output_path, "wb") as output_file:
                    output_file.write(response.content)
                print(f"File saved as {output_path}")
            else:
                print(f"Failed to fetch the file. Status code: {response.status_code}")
                print(response.json())  # If the API sends error details
        
        nii_img = nib.load(output_file)
        data = nii_img.get_fdata()

        nii_img = nib.Nifti1Image(data, Correctnii.affine)
        nib.save(nii_img, output_file)

        SegObjPath = CreateSegForMRI(OutputFilesPath[0][0],output_path)

        return FileResponse(
            path=SegObjPath,
            media_type="application/dicom",  # or use "application/nii" if that's more suitable
            filename=os.path.basename(SegObjPath),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
                