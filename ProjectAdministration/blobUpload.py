from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
#credentials
from decouple import config 

storage_account_key = config('STORAGEACCOUNTKEY')
storage_account_name = config('STORAGEACCOUNTNAME')
connection_string = config('CONNECTIONSTRING')
container_name = config('CONTAINERNAME')

def uploadToBlobStorage(file_path,file_name):
   blob_service_client = BlobServiceClient.from_connection_string(connection_string)
   blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
   with open(file_path,'rb') as data:
      blob_client.upload_blob(data)
      print(f'Uploaded {file_name}.')

list_of_files = [
['Z:/MTGArchived/JOU/Document_20240709_JOU_0009.jpg','Document_20240709_JOU_0009.jpg','Z:/MTGArchived/XXX/Document_20240709_JOU_0009.jpg'],
['Z:/MTGArchived/ORI/Document_20240711_ORI_0002.jpg','Document_20240711_ORI_0002.jpg','Z:/MTGArchived/XXX/Document_20240711_ORI_0002.jpg'],
['Z:/MTGArchived/C20/Document_20240331_0071.jpg','Document_20240331_0071.jpg','Z:/MTGArchived/XXX/Document_20240331_0071.jpg'],
['Z:/MTGArchived/C13/Document_20240331_0145.jpg','Document_20240331_0145.jpg','Z:/MTGArchived/XXX/Document_20240331_0145.jpg'],
['Z:/MTGArchived/ODY/Document_20250129_XXX_0004.jpg','Document_20250129_XXX_0004.jpg','Z:/MTGArchived/XXX/Document_20250129_XXX_0004.jpg'],
['Z:/MTGArchived/INR/Document_20250129_XXX_0003.jpg','Document_20250129_XXX_0003.jpg','Z:/MTGArchived/XXX/Document_20250129_XXX_0003.jpg'],
['Z:/MTGArchived/PRM/Document_20240331_0001.jpg','Document_20240331_0001.jpg','Z:/MTGArchived/XXX/Document_20240331_0001.jpg'],
['Z:/MTGArchived/C19/Document_20240331_0037.jpg','Document_20240331_0037.jpg','Z:/MTGArchived/XXX/Document_20240331_0037.jpg'],
['Z:/MTGArchived/2XM/Document_20240331_0341.jpg','Document_20240331_0341.jpg','Z:/MTGArchived/XXX/Document_20240331_0341.jpg'],
['Z:/MTGArchived/RIX/Document_20240331_0202.jpg','Document_20240331_0202.jpg','Z:/MTGArchived/XXX/Document_20240331_0202.jpg'],
['Z:/MTGArchived/MH2/Document_20240331_0247.jpg','Document_20240331_0247.jpg','Z:/MTGArchived/XXX/Document_20240331_0247.jpg'],
['Z:/MTGArchived/JUD/Document_20240331_0079.jpg','Document_20240331_0079.jpg','Z:/MTGArchived/XXX/Document_20240331_0079.jpg'],
['Z:/MTGArchived/INV/Document_20240713_INV_0134.jpg','Document_20240713_INV_0134.jpg','Z:/MTGArchived/XXX/Document_20240713_INV_0134.jpg'],
['Z:/MTGArchived/MH3/Document_20240703_MH3_0108.jpg','Document_20240703_MH3_0108.jpg','Z:/MTGArchived/XXX/Document_20240703_MH3_0108.jpg'],
['Z:/MTGArchived/DDJ/Document_20240331_0223.jpg','Document_20240331_0223.jpg','Z:/MTGArchived/XXX/Document_20240331_0223.jpg'],
['Z:/MTGArchived/AFR/Document_20240331_0006.jpg','Document_20240331_0006.jpg','Z:/MTGArchived/XXX/Document_20240331_0006.jpg'],
['Z:/MTGArchived/CLB/Document_20240331_0109.jpg','Document_20240331_0109.jpg','Z:/MTGArchived/XXX/Document_20240331_0109.jpg'],
['Z:/MTGArchived/C21/Document_20240331_0009.jpg','Document_20240331_0009.jpg','Z:/MTGArchived/XXX/Document_20240331_0009.jpg'],
['Z:/MTGArchived/C20/Document_20240331_0006.jpg','Document_20240331_0006.jpg','Z:/MTGArchived/XXX/Document_20240331_0006.jpg'],
['Z:/MTGArchived/SOK/Document_20240331_0294.jpg','Document_20240331_0294.jpg','Z:/MTGArchived/XXX/Document_20240331_0294.jpg'],
['Z:/MTGArchived/M21/Document_20240331_0091.jpg','Document_20240331_0091.jpg','Z:/MTGArchived/XXX/Document_20240331_0091.jpg'],
['Z:/MTGArchived/M10/Document_20240709_M10_0012.jpg','Document_20240709_M10_0012.jpg','Z:/MTGArchived/XXX/Document_20240709_M10_0012.jpg'],
['Z:/MTGArchived/M10/Document_20240709_M10_0010.jpg','Document_20240709_M10_0010.jpg','Z:/MTGArchived/XXX/Document_20240709_M10_0010.jpg'],
['Z:/MTGArchived/M10/Document_20240709_M10_0011.jpg','Document_20240709_M10_0011.jpg','Z:/MTGArchived/XXX/Document_20240709_M10_0011.jpg'],
['Z:/MTGArchived/DIS/Document_20240331_0087.jpg','Document_20240331_0087.jpg','Z:/MTGArchived/XXX/Document_20240331_0087.jpg'],
['Z:/MTGArchived/MRD/Document_20240324_0018.jpg','Document_20240324_0018.jpg','Z:/MTGArchived/XXX/Document_20240324_0018.jpg'],
['Z:/MTGArchived/APC/Document_20240710_APC_0001.jpg','Document_20240710_APC_0001.jpg','Z:/MTGArchived/XXX/Document_20240710_APC_0001.jpg'],
['Z:/MTGArchived/APC/Document_20240710_APC_0003.jpg','Document_20240710_APC_0003.jpg','Z:/MTGArchived/XXX/Document_20240710_APC_0003.jpg'],
['Z:/MTGArchived/APC/Document_20240710_APC_0002.jpg','Document_20240710_APC_0002.jpg','Z:/MTGArchived/XXX/Document_20240710_APC_0002.jpg'],
['Z:/MTGArchived/LCC/Document_20240331_0190.jpg','Document_20240331_0190.jpg','Z:/MTGArchived/XXX/Document_20240331_0190.jpg'],
['Z:/MTGArchived/MRD/Document_20240324_0015.jpg','Document_20240324_0015.jpg','Z:/MTGArchived/XXX/Document_20240324_0015.jpg'],
['Z:/MTGArchived/MH3/Document_20240703_MH3_FOIL_0006.jpg','Document_20240703_MH3_FOIL_0006.jpg','Z:/MTGArchived/XXX/Document_20240703_MH3_FOIL_0006.jpg'],
['Z:/MTGArchived/CLB/Document_20240331_0322.jpg','Document_20240331_0322.jpg','Z:/MTGArchived/XXX/Document_20240331_0322.jpg'],
['Z:/MTGArchived/AFR/Document_20240711_AFR_0001.jpg','Document_20240711_AFR_0001.jpg','Z:/MTGArchived/XXX/Document_20240711_AFR_0001.jpg'],
['Z:/MTGArchived/INV/Document_20240713_INV_0119.jpg','Document_20240713_INV_0119.jpg','Z:/MTGArchived/XXX/Document_20240713_INV_0119.jpg'],
['Z:/MTGArchived/CMM/Document_20240331_0155.jpg','Document_20240331_0155.jpg','Z:/MTGArchived/XXX/Document_20240331_0155.jpg'],
['Z:/MTGArchived/FUT/Document_20240324_0024.jpg','Document_20240324_0024.jpg','Z:/MTGArchived/XXX/Document_20240324_0024.jpg']
]

# calling a function to perform upload
# uploadToBlobStorage('Z:/MTGArchived/RAV/Document_20240416_0001.jpg','Document_20240416_0001_RAV.jpg')

"""
This looks at the files above and tries to upload them to the blob, if it exists, skip, if it is in the general XXX directory, then try the XXX mapping
""" 
for r in list_of_files:
   try:
      uploadToBlobStorage(r[0],r[1])
   except FileNotFoundError:
      try:
         uploadToBlobStorage(r[2],r[1])
      except ResourceExistsError:
         pass
   except ResourceExistsError:
      pass