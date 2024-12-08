"""
    Alot of these come from the quickstart tutorial

    This script will upload everything to the ML instance and tag it accordlingly.

    https://docs.microsoft.com/en-us/azure/cognitive-services/Custom-Vision-Service/quickstarts/image-classification?tabs=visual-studio&pivots=programming-language-python 
"""

#imports
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from azure.cognitiveservices.vision.customvision.training.models import ImageFileCreateBatch, ImageFileCreateEntry, Region
from msrest.authentication import ApiKeyCredentials
import os, time, uuid

ENDPOINT = "https://eecustomvisiontesting-prediction.cognitiveservices.azure.com/"
training_key = "4bde06b2e58741a991204b3a34a65044"
credentials = ApiKeyCredentials(in_headers={"Training-key": training_key})
trainer = CustomVisionTrainingClient(ENDPOINT, credentials)
prediction_key = "90c26acaa9414c23ac56131c90733ebb"
prediction_resource_id = "/subscriptions/988cdd22-02c4-4fb6-b952-00cac1cab1ae/resourceGroups/CustomVisionProject/providers/Microsoft.CognitiveServices/accounts/EECustomVisionTesting-Prediction"

# Now there is a trained endpoint that can be used to make a prediction
#prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": prediction_key})
#predictor = CustomVisionPredictionClient(ENDPOINT, prediction_credentials)

base_image_location = 'Z:/MTGArchived'
project_id = "b19edd6d-880d-4d24-9bca-1f44baaa93c2"
publish_iteration_name = "Iteration2"

filesToAnalyze = []
sets = []

# this grabs the list of files we want to send through computer vision and appends them to our list
for subdir, dirs, files in os.walk(base_image_location):
        if subdir != base_image_location:
                head, tail = os.path.split(subdir)
                if files:
                        for file in files:
                                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    sourceFile = os.path.join(subdir,file)
                                    sourceFile = sourceFile.replace('\\', '/')

                                    # stupid windows
                                    if tail == "_CON":
                                        tail = "CON"
                                    
                                    filesToAnalyze.append([sourceFile,tail])
                                    sets.append(tail)

finalSets = set(sets)
image_list = []

for r in finalSets:
    trainer.create_tag(project_id, r)
    
for r in filesToAnalyze:
    with open(r[0], "rb") as image_contents:
        image_list.append(ImageFileCreateEntry(name=r, contents=image_contents.read(), tag_ids=, t))










"""


print("Adding images...")

image_list = []

for image_num in range(1, 11):
    file_name = "hemlock_{}.jpg".format(image_num)
    with open(os.path.join (base_image_location, "Hemlock", file_name), "rb") as image_contents:
        image_list.append(ImageFileCreateEntry(name=file_name, contents=image_contents.read(), tag_ids=[hemlock_tag.id]))

for image_num in range(1, 11):
    file_name = "japanese_cherry_{}.jpg".format(image_num)
    with open(os.path.join (base_image_location, "Japanese_Cherry", file_name), "rb") as image_contents:
        image_list.append(ImageFileCreateEntry(name=file_name, contents=image_contents.read(), tag_ids=[cherry_tag.id]))

upload_result = trainer.create_images_from_files(project.id, ImageFileCreateBatch(images=image_list))
if not upload_result.is_batch_successful:
    print("Image batch upload failed.")
    for image in upload_result.images:
        print("Image status: ", image.status)
    exit(-1)


"""