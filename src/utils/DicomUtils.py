import pydicom
from PIL import Image
import os
import numpy as np
from src.configuration.config import SampleCTDicomPath,TempDCMseries
import nibabel as nib
import numpy as np
import highdicom as hd
from pydicom.sr.codedict import codes
from scipy.ndimage import zoom

def ImageToDicom(ImagePath, Data):
    ds = pydicom.dcmread(SampleCTDicomPath)
    image = Image.open(ImagePath)
    image = np.array(image, dtype=np.uint16)
    
    ds.SOPClassUID = Data["sopclassuid"]
    ds.SOPInstanceUID = Data["sopinstanceuid"]
    ds.PatientName = Data["patientname"]
    ds.PatientID = Data["patientid"]
    ds.PixelData = image.tobytes()

    return ds
    
    # dicom_file_path = os.path.join("output", "SampelRetinalimage.dcm")
    # os.makedirs(os.path.dirname(dicom_file_path), exist_ok=True)
    
    # # Save the DICOM file
    # ds.save_as(dicom_file_path)
    
    # # Check if the file was saved successfully
    # if os.path.exists(dicom_file_path):
    #     print(f"DICOM file saved at: {dicom_file_path}")
    # else:
    #     print(f"Failed to save DICOM file at: {dicom_file_path}")
    
    # return dicom_file_path



import pydicom
import shutil
import os
from nii2dcm.run import run_nii2dcm

def fun(niftypath, outputDirPath, outputzipPath ):
    os.makedirs(outputDirPath, exist_ok=True)
    shutil.rmtree(outputDirPath)
    os.makedirs(outputDirPath, exist_ok=True)
    run_nii2dcm(niftypath,outputDirPath, 'MR')
    for dcm in os.listdir(outputDirPath):
        os.rename(os.path.join(outputDirPath,dcm),os.path.join(outputDirPath,dcm)+'.dcm')
    new_study_id = "12345"
    # Iterate through each file in the directory
    for filename in os.listdir(outputDirPath):
        # Build the full file path
        file_path = os.path.join(outputDirPath, filename)
        # Check if the file is a valid DICOM file
        if filename.endswith(".dcm"):  # Ensures only .dcm files are processed
            try:
                # Load the DICOM file
                ds = pydicom.dcmread(file_path)
                # Check if the StudyID tag exists
                if 'StudyID' in ds:
                    print(f"Original StudyID in {filename}: {ds.StudyID}")
                else:
                    print(f"StudyID missing in {filename}. Adding it now.")
                # Set or update the StudyID
                ds.StudyID = new_study_id
                # Save the file in place (overwrite the original file)
                ds.save_as(file_path)
                print(f"Updated StudyID for {filename} and saved in place.")
            except Exception as e:
                print(f"Failed to process {filename}: {e}")
    shutil.make_archive(outputzipPath, 'zip', outputDirPath)






# def CreateSegForMRI(DicomSeriesPath, SegmentationNiiPath):
#     print()

#     nii_img = nib.load(SegmentationNiiPath)
#     data = nii_img.get_fdata()

#     current_shape = data.shape
#     affine = nii_img.affine
#     files = os.listdir(DicomSeriesPath)
#     pixeldata = pydicom.dcmread(os.path.join(DicomSeriesPath,files[0]))
#     pixeldata = pixeldata.pixel_array



#     new_shape = (pixeldata.shape[0], pixeldata.shape[1], data.shape[2])  # You can adjust the number of slices (last dimension) as needed

#     # Calculate the zoom factors for resizing
#     zoom_factors = [new_shape[0] / current_shape[0], 
#                     new_shape[1] / current_shape[1], 
#                     1]  # No resizing in the z-axis (slice dimension)

#     # Resize the data
#     resized_data = zoom(data, zoom_factors, order=1)  # 'order=1' for bilinear interpolation

#     # Update the affine matrix: Adjust voxel size for the first two dimensions
#     new_affine = affine

#     # Calculate new voxel size for the resized image (in the x and y dimensions)
#     new_voxel_size = np.array(nii_img.header.get_zooms()) * np.array(zoom_factors)
#     new_affine[0, 0] = new_voxel_size[0]
#     new_affine[1, 1] = new_voxel_size[1]

#     new_img = nib.Nifti1Image(resized_data, new_affine)
#     nib.save(new_img, SegmentationNiiPath)





#     img = nib.load(SegmentationNiiPath)
#     data = img.get_fdata()
#     data = np.array(data)

#     description = hd.seg.SegmentDescription(
#         segment_number=1,
#         segment_label='Tumor',
#         segmented_property_category=codes.SCT.Blood,
#         segmented_property_type=codes.SCT.Blood,
#         algorithm_type=hd.seg.SegmentAlgorithmTypeValues.MANUAL,
#     )
    

#     files = os.listdir(DicomSeriesPath)
#     files = sorted(files)
#     maskDict = {}
#     maskDict['Tumor'] = []
#     source_images = []
#     i = 0
#     for file in files:
#         file_path = os.path.join(DicomSeriesPath, file)
#         source_images.append(pydicom.dcmread(file_path))
#         slice1 = data[:,:,i]
#         maskDict['Tumor'].append(np.array(slice1))
#         i = i + 1
    
#     mask = []
#     for key,value in maskDict.items():
#         mask.append(np.stack(value, axis=0))
    
#     mask = np.stack(mask, axis=3)
#     seg_obj = hd.seg.Segmentation(
#         source_images=source_images,
#         pixel_array=mask,
#         segmentation_type=hd.seg.SegmentationTypeValues.BINARY,
#         segment_descriptions=[description],
#         series_instance_uid=hd.UID(),
#         series_number=1,
#         sop_instance_uid=hd.UID(),
#         instance_number=1,
#         manufacturer='Radpretation ai',
#         manufacturer_model_name='Brain structure Segmentation Algorithm',
#         software_versions='0.0.1',
#         device_serial_number='1234567890'
#     )
#     SegObjPath = os.path.join(TempDCMseries,'AI.dcm')
#     seg_obj.save_as(SegObjPath)

#     return SegObjPath


import os
import nibabel as nib
import numpy as np
import pydicom
from scipy.ndimage import zoom
# import hd  # assuming hd is your custom library for segmentation (make sure this is imported correctly)
from pydicom.uid import generate_uid

def CreateSegForMRI(DicomSeriesPath, SegmentationNiiPath):
    print("Test1")
    # Load the NIfTI segmentation image
    nii_img = nib.load(SegmentationNiiPath)
    data = nii_img.get_fdata()

    # current_shape = data.shape
    # affine = nii_img.affine
    files = os.listdir(DicomSeriesPath)
    files = sorted(files)  # Ensure files are sorted by slice order
    pixeldata = pydicom.dcmread(os.path.join(DicomSeriesPath, files[0]))
    pixeldata = pixeldata.pixel_array
    print("pixeldata:-",pixeldata.shape)

    # # Define new shape to match the DICOM image dimensions
    # new_shape = (pixeldata.shape[0], pixeldata.shape[1], data.shape[2])

    # # Calculate the zoom factors to resize the segmentation image
    # zoom_factors = [new_shape[0] / current_shape[0], 
    #                 new_shape[1] / current_shape[1], 
    #                 1]  # No resizing in the z-axis (slice dimension)

    # # Resize the segmentation data
    # resized_data = zoom(data, zoom_factors, order=1)  # 'order=1' for bilinear interpolation

    # # Update affine matrix: Adjust voxel size for the resized image
    # new_affine = affine
    # new_voxel_size = np.array(nii_img.header.get_zooms()) * np.array(zoom_factors)
    # new_affine[0, 0] = new_voxel_size[0]
    # new_affine[1, 1] = new_voxel_size[1]

    # # Save resized segmentation data as a NIfTI file
    # resized_nii_img = nib.Nifti1Image(resized_data, new_affine)
    # nib.save(resized_nii_img, SegmentationNiiPath)
    print("Test2")
    resized_data = data

    # Read and prepare DICOM images and create segmentation mask
    print("no of files:-",len(files))
    print("data shape:-",resized_data.shape)
    source_images = []
    maskDict = {'Tumor': []}
    for i, file in enumerate(files):
        file_path = os.path.join(DicomSeriesPath, file)
        dicom_data = pydicom.dcmread(file_path)

        dicom_data.PatientName = "Doe^John" 
        source_images.append(dicom_data)
        slice_data = resized_data[:, :, i]

        maskDict['Tumor'].append(np.array(slice_data))
    
    print("Test3")

    # Stack all slices to create the final segmentation mask
    mask = []
    for key,value in maskDict.items():
        mask.append(np.stack(value, axis=0))
    
    mask = np.stack(mask, axis=3)
    # mask = np.stack(maskDict['Tumor'], axis=0)
    print("Test4")
    print("source_images",len(source_images))
    print("masks",mask.shape)


    # Create SegmentDescription for the segmentation object
    description = hd.seg.SegmentDescription(
        segment_number=1,
        segment_label='Tumor',
        segmented_property_category=codes.SCT.Blood,
        segmented_property_type=codes.SCT.Blood,
        algorithm_type=hd.seg.SegmentAlgorithmTypeValues.MANUAL,
    )
    mask[mask < 0.5] = 0
    mask[mask >= 0.5] = 1
    mask[mask==0] = False
    mask[mask==1] = True

    print("source_images",len(source_images))
    print("masks",mask.shape)
    print("unique:-",np.unique(mask))


    # Create Segmentation DICOM object

    seg_obj = hd.seg.Segmentation(
        source_images=source_images,
        pixel_array=mask,
        segmentation_type=hd.seg.SegmentationTypeValues.BINARY,
        segment_descriptions=[description],
        series_instance_uid=hd.UID(),
        series_number=1,
        sop_instance_uid=hd.UID(),
        instance_number=1,
        manufacturer='Radpretation ai',
        manufacturer_model_name='Brain structure Segmentation Algorithm',
        software_versions='0.0.1',
        device_serial_number='1234567890'
    )
    print("Test5")

    # Save the segmentation DICOM object
    SegObjPath = os.path.join(TempDCMseries, 'AI.dcm')
    seg_obj.save_as(SegObjPath)

    return SegObjPath

