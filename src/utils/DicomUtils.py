import pydicom
from PIL import Image
import os
import numpy as np
from src.configuration.config import SampleCTDicomPath,TempDCMseries
import nibabel as nib
import numpy as np
import highdicom as hd
from pydicom.sr.codedict import codes

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




def CreateSegForMRI(DicomSeriesPath, SegmentationNiiPath):
    img = nib.load(SegmentationNiiPath)
    data = img.get_fdata()
    data = np.array(data)

    description = hd.seg.SegmentDescription(
        segment_number=1,
        segment_label='Tumor',
        segmented_property_category=codes.SCT.Blood,
        segmented_property_type=codes.SCT.Blood,
        algorithm_type=hd.seg.SegmentAlgorithmTypeValues.MANUAL,
    )
    

    files = os.listdir(DicomSeriesPath)
    files = sorted(files)
    maskDict = {}
    maskDict['Tumor'] = []
    source_images = []
    i = 0
    for file in files:
        file_path = os.path.join(DicomSeriesPath, file)
        source_images.append(pydicom.dcmread(file_path))
        slice1 = data[:,:,i]
        maskDict['Tumor'].append(np.array(slice1))
        i = i + 1
    
    mask = []
    for key,value in maskDict.items():
        mask.append(np.stack(value, axis=0))
    
    mask = np.stack(mask, axis=3)
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
    SegObjPath = os.path.join(TempDCMseries,'AI.dcm')
    seg_obj.save_as(SegObjPath)

    return SegObjPath

