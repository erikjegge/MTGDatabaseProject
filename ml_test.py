"""
    Alot of these come from the quickstart tutorial

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
prediction_key = "90c26acaa9414c23ac56131c90733ebb"
prediction_resource_id = "/subscriptions/988cdd22-02c4-4fb6-b952-00cac1cab1ae/resourceGroups/CustomVisionProject/providers/Microsoft.CognitiveServices/accounts/EECustomVisionTesting-Prediction"

# Now there is a trained endpoint that can be used to make a prediction
prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": prediction_key})
predictor = CustomVisionPredictionClient(ENDPOINT, prediction_credentials)

base_image_location = "images/testImages/"
project_id = "b19edd6d-880d-4d24-9bca-1f44baaa93c2"
publish_iteration_name = "Iteration3"

source = 'Z:/MTGImages' 
destination = 'Z:/MTGArchived'

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
                                    filesToAnalyze.append(sourceFile)
                                    
for r in filesToAnalyze:
    with open(r, "rb") as image_contents:
        results = predictor.classify_image(project_id, publish_iteration_name, image_contents.read())

    # Display the results.
    for prediction in results.predictions:
        print("\t" + prediction.tag_name +
              ": {0:.2f}%".format(prediction.probability * 100))

"""
with open(os.path.join (base_image_location, "image20220317190547.jpg"), "rb") as image_contents:
    results = predictor.classify_image(
        project_id, publish_iteration_name, image_contents.read())

    # Display the results.
    for prediction in results.predictions:
        print("\t" + prediction.tag_name +
              ": {0:.2f}%".format(prediction.probability * 100))
"""
