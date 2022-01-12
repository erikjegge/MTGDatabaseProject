'''
Computer Vision Quickstart for Microsoft Azure Cognitive Services. 
Uses local and remote images in each example.

Prerequisites:
    - Install the Computer Vision SDK:
      pip install --upgrade azure-cognitiveservices-vision-computervision
    - Install PIL:
      pip install --upgrade pillow
    - Create folder and collect images: 
      Create a folder called "images" in the same folder as this script.
      Go to this website to download images:
        https://github.com/Azure-Samples/cognitive-services-sample-data-files/tree/master/ComputerVision/Images
      Add the following 7 images (or use your own) to your "images" folder: 
        faces.jpg, gray-shirt-logo.jpg, handwritten_text.jpg, landmark.jpg, 
        objects.jpg, printed_text.jpg and type-image.jpg

Run the entire file to demonstrate the following examples:
    - OCR: Read File using the Read API, extract text - remote
    - OCR: Read File using the Read API, extract text - local

References:
    - SDK: https://docs.microsoft.com/en-us/python/api/azure-cognitiveservices-vision-computervision/azure.cognitiveservices.vision.computervision?view=azure-python
    - Documentaion: https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/index
    - API: https://westus.dev.cognitive.microsoft.com/docs/services/computer-vision-v3-2/operations/5d986960601faab4bf452005
'''

# <snippet_imports_and_vars>
# <snippet_imports>
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

from array import array
import os
from PIL import Image
import sys
import time
# </snippet_imports>

# import into SQL server
import pyodbc

# copying files later to the archive
import shutil

# will try to time how long this takes
import time

start_time = time.time()


'''
Authenticate
Authenticates your credentials and creates a client.
'''
# <snippet_vars>
subscription_key = "f134ce90ca1042189a58c629af33466e"
endpoint = "https://eecomputervisiontesting.cognitiveservices.azure.com/"

# </snippet_vars>
# </snippet_imports_and_vars>

# <snippet_client>
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))
# </snippet_client>
'''
END - Authenticate
'''

'''
Quickstart variables
These variables are shared by several examples
'''
# Images used for the examples: Describe an image, Categorize an image, Tag an image, 
# Detect faces, Detect adult or racy content, Detect the color scheme, 
# Detect domain-specific content, Detect image types, Detect objects
images_folder = os.path.join (os.path.dirname(os.path.abspath(__file__)), "images")
# <snippet_remoteimage>
remote_image_url = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-sample-data-files/master/ComputerVision/Images/landmark.jpg"
# </snippet_remoteimage>
'''
END - Quickstart variables
'''

# <snippet_read_call>
'''
OCR: Read File using the Read API, extract text - remote
This example will extract text in an image, then print results, line by line.
This API call can also extract handwriting style text (not shown).
'''
""" print("===== Read File - remote =====")
# Get an image with text
read_image_url = "https://raw.githubusercontent.com/MicrosoftDocs/azure-docs/master/articles/cognitive-services/Computer-vision/Images/readsample.jpg"

# Call API with URL and raw response (allows you to get the operation location)
read_response = computervision_client.read(read_image_url,  raw=True)
# </snippet_read_call>

# <snippet_read_response>
# Get the operation location (URL with an ID at the end) from the response
read_operation_location = read_response.headers["Operation-Location"]
# Grab the ID from the URL
operation_id = read_operation_location.split("/")[-1]

# Call the "GET" API and wait for it to retrieve the results 
while True:
    read_result = computervision_client.get_read_result(operation_id)
    if read_result.status not in ['notStarted', 'running']:
        break
    time.sleep(1)

# Print the detected text, line by line
if read_result.status == OperationStatusCodes.succeeded:
    for text_result in read_result.analyze_result.read_results:
        for line in text_result.lines:
            print(line.text)
            print(line.bounding_box)
print()
# </snippet_read_response>
'''
END - Read File - remote
''' """

'''
OCR: Read File using the Read API, extract text - local
This example extracts text from a local image, then prints results.
This API call can also recognize remote image text (shown in next example, Read File - remote).
'''
print("===== Read File - local =====")

# takes a list called card
def send_and_archive(card):
    #connection string
    server = 'computervisioneemtg.database.windows.net'
    database = 'EEComputerVisionDB'
    username = 'eggeej'
    password = 'G$y1(5!hwfUsR4<o}HlK'
    driver= '{ODBC Driver 17 for SQL Server}'

    conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = conn.cursor()

    print("<><><><><><><><><><>")
    print(card[0])
    #for the sql deal
    cardName = card[0].replace("'", "''")
    print(card[1])
    read_image_path = card[2]
    write_image_path = card[3]
    print(read_image_path)
    print(write_image_path)
    print("<><><><><><><><><><>")
    sqlString = (
            "INSERT INTO tbl_MTGCardLibrary ([cardName],[isEnabled],[color],[type],[set],[filepath]) "
            "VALUES "
            "('"+cardName+"',1,NULL,NULL,'"+card[1]+"','"+card[-1]+"')"
    )
    cursor.execute(sqlString)
    conn.commit()

    # move the file to the archive
    shutil.move(read_image_path, write_image_path)

    cursor.close()
    conn.close()


# Get image path
#read_image_path = os.path.join (images_folder, "20211230_110259.jpg")
finalized_List_Cards = []
list_Of_Images = []

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
# this block makes sure that the archive and the images folder have the same directory structure
source = 'Z:/MTGImages' 
destination = 'Z:/MTGArchived'

#shutil.move(source, destination)
# defining the function to ignore the files

# if present in any folder
def ignore_files(dir, files):
    return [f for f in files if os.path.isfile(os.path.join(dir, f))]

# calling the shutil.copytree() method and
# passing the src,dst,and ignore parameters
shutil.copytree(source,destination,ignore=ignore_files, dirs_exist_ok=True)
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

filesToAnalyze = []

for subdir, dirs, files in os.walk(source):
        #print(dirs)
        if subdir != source:
                #print(subdir)
                head, tail = os.path.split(subdir)
                #print(tail)
                #print(files)
                if files:
                        for file in files:
                                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    sourceFile = os.path.join(subdir,file)
                                    sourceFile = sourceFile.replace('\\', '/')
                                    destFile = sourceFile.replace(source,destination)
                                    #print(os.path.join(subdir,file))
                                    filesToAnalyze.append([sourceFile,destFile,tail])

for r in filesToAnalyze:
    #reset the card results
    card_results = []
    #loop through the images

    read_image_path = r[0] # The path to the image we want to send to the API
    print(read_image_path)
    write_image_path = r[1] # The path to the image we want to send the image to after processing
    setAbrev = r[2] # the set folder the image is in

    # Open the image
    read_image = open(read_image_path, "rb")

    # Call API with image and raw response (allows you to get the operation location)
    read_response = computervision_client.read_in_stream(read_image, raw=True)
    # Get the operation location (URL with ID as last appendage)
    read_operation_location = read_response.headers["Operation-Location"]
    # Take the ID off and use to get results
    operation_id = read_operation_location.split("/")[-1]

    # Call the "GET" API and wait for the retrieval of the results
    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status.lower () not in ['notstarted', 'running']:
            break
        #print ('Waiting for result...')
        time.sleep(10)

    # Print results, line by line
    if read_result.status == OperationStatusCodes.succeeded:
        for text_result in read_result.analyze_result.read_results:
            for line in text_result.lines:
                #print(line.text)
                card_results.append(line.text)

    read_image.close()

    if card_results:
        #gets the filename, that's all I care about right now
        head, tail = os.path.split(read_image_path)
        card_results.append(tail)
        #print(tail)
        #print(setAbrev)
        card_results.insert(1, setAbrev)
        # storing these for later, don't want to do the move until we start doing the sql inserts
        card_results.insert(2, read_image_path) 
        card_results.insert(3, write_image_path)

        send_and_archive(card_results)
        # rewrite, instead of sending the card to a list, we will call the send_and_archive function to upload it
        #finalized_List_Cards.append(card_results)
        #shutil.move(read_image_path, write_image_path)

timeInHours = (time.time() - start_time) / 3600

print("--- %s seconds ---" % (time.time() - start_time))
print("--- %s hours ---" % timeInHours)

'''
END - Read File - local
'''
