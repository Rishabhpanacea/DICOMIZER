import requests
import os

# Replace with your API endpoint URL
url = "http://127.0.0.1:8000/upload/"

# Path to the image to upload
image_path = os.path.join("SampleData", "0abf0c485f66.png")

# Verify the file exists
if not os.path.exists(image_path):
    print(f"Error: File not found at {image_path}")
    exit(1)

# Prepare the file and form data
with open(image_path, "rb") as image_file:
    files = {"image": image_file}
    data = {
        "sopclassuid": "1.2.840.10008.5.1.4.1.1.2",
        "sopinstanceuid": "1.2.840.113619.2.55.3.604688326.455.1586502025",
        "patientname": "John Doe",
        "patientid": "12345",
    }

    try:
        # Send the POST request
        response = requests.post(url, files=files, data=data)

        # Handle the response
        if response.status_code == 200:
            # Save the DICOM file locally
            output_file = "output.dcm"
            with open(output_file, "wb") as f:
                f.write(response.content)
            print("Upload successful!")
            print(f"DICOM file saved as {output_file}")
        else:
            # Print detailed error information
            print(f"Failed to upload. Status code: {response.status_code}")
            try:
                print("Error response:", response.json())
            except ValueError:
                print("Error response:", response.text)
    except requests.RequestException as e:
        print(f"An error occurred while making the request: {e}")
