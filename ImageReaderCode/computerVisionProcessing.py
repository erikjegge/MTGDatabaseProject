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

#implementation of threading
import threading
from threading import Thread
from time import perf_counter

#credentials
from decouple import config 

#globabls
# I can only call the API 10 times a second. So this would be the max
maxthreads = 100
sema = threading.Semaphore(value=maxthreads)

'''
Authenticate
Authenticates your credentials and creates a client.
'''
# <snippet_vars>
subscription_key = config('CVSUBSCRIPTIONKEY')
endpoint = config('CVENDPOINT')

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

'''
    START
    send_and_archive takes the card object created by the rest of processing and imports it to the database
'''
# takes a list called card
def send_and_archive(card):
    #connection string
    server = config('SERVER')
    database = config('DATABASE')
    username = config('DB_USERNAME')
    password = config('DB_PASSWORD')
    driver= '{ODBC Driver 17 for SQL Server}'

    conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = conn.cursor()

    cardName = card[0].replace("'", "''")
    read_image_path = card[2]
    write_image_path = card[3]

    sqlString = (
            "INSERT INTO tbl_MTGCardLibrary ([cardName],[isEnabled],[color],[type],[set],[filepath],[isFoil]) "
            "VALUES "
            "('"+cardName+"',1,NULL,NULL,'"+card[1]+"','"+card[-1]+"',0)"
    )

    if "_FOIL" in card[-1]:
        sqlString = (
                "INSERT INTO tbl_MTGCardLibrary ([cardName],[isEnabled],[color],[type],[set],[filepath],[isFoil]) "
                "VALUES "
                "('"+cardName+"',1,NULL,NULL,'"+card[1]+"','"+card[-1]+"',1)"
        )
    
    cursor.execute(sqlString)
    conn.commit()

    # move the file to the archive
    shutil.move(read_image_path, write_image_path)

    cursor.close()
    conn.close()
'''
    END
'''

'''
    START
    ignore_files is a function that copy tree uses to ignore files when cloning the structure from source to destination
'''
def ignore_files(dir, files):
    return [f for f in files if os.path.isfile(os.path.join(dir, f))]

'''
    END
'''

'''
    START
    call_cv: Threading try
'''
def call_cv(read_image_path, write_image_path, setAbrev):
    sema.acquire()

    print(f'Processing the file {read_image_path}')
    card_results = []
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
        time.sleep(10)

    # Print results, line by line
    if read_result.status == OperationStatusCodes.succeeded:
        for text_result in read_result.analyze_result.read_results:
            for line in text_result.lines:
                card_results.append(line.text)

    #close the image
    read_image.close()

    if card_results:
        head, tail = os.path.split(read_image_path)
        card_results.append(tail)
        card_results.insert(1, setAbrev)
        card_results.insert(2, read_image_path) 
        card_results.insert(3, write_image_path)
        send_and_archive(card_results)

    sema.release()
'''
    END
'''

def main():

    #start_time = time.time()

    source = 'Z:/MTGImages' 
    destination = 'Z:/MTGArchived'

    # copying the directory structure from source into desitination
    shutil.copytree(source,destination,ignore=ignore_files, dirs_exist_ok=True)

    filesToAnalyze = []

    # this grabs the list of files we want to send through computer vision and appends them to our list
    for subdir, dirs, files in os.walk(source):
            if subdir != source:
                    head, tail = os.path.split(subdir)
                    if files:
                            for file in files:
                                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                                        sourceFile = os.path.join(subdir,file)
                                        sourceFile = sourceFile.replace('\\', '/')
                                        destFile = sourceFile.replace(source,destination)
                                        filesToAnalyze.append([sourceFile,destFile,tail])
            

    # threading implementation
    threads = [Thread(target=call_cv, args=(r[0], r[1], r[2]))
        for r in filesToAnalyze]

    theadCount = 1
    # start the threads
    for thread in threads:
        thread.start()

        # solution to limit the number of calls per second? Lets see
        theadCount += 1
        if theadCount >= 9:
            theadCount = 1
            time.sleep(5)

    # wait for the threads to complete
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    start_time = perf_counter()

    main()

    end_time = perf_counter()
    print(f'It took {end_time- start_time :0.2f} second(s) to complete.')