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

['Z:/MTGArchived/DSK/Document_20241130_DSK_02_0021.jpg', 'Document_20241130_DSK_02_0021.jpg', 'Z:/MTGArchived/XXX/Document_20241130_DSK_02_0021.jpg'],
['Z:/MTGArchived/DSK/Document_20241130_DSK_01_0026.jpg', 'Document_20241130_DSK_01_0026.jpg', 'Z:/MTGArchived/XXX/Document_20241130_DSK_01_0026.jpg'],
['Z:/MTGArchived/DSK/Document_20241130_DSK_01_0071.jpg', 'Document_20241130_DSK_01_0071.jpg', 'Z:/MTGArchived/XXX/Document_20241130_DSK_01_0071.jpg'],
['Z:/MTGArchived/DSK/Document_20241130_DSK_02_0072.jpg', 'Document_20241130_DSK_02_0072.jpg', 'Z:/MTGArchived/XXX/Document_20241130_DSK_02_0072.jpg'],
['Z:/MTGArchived/DSK/Document_20241130_DSK_02_0044.jpg', 'Document_20241130_DSK_02_0044.jpg', 'Z:/MTGArchived/XXX/Document_20241130_DSK_02_0044.jpg'],
['Z:/MTGArchived/DSK/Document_20241130_DSK_01_0011.jpg', 'Document_20241130_DSK_01_0011.jpg', 'Z:/MTGArchived/XXX/Document_20241130_DSK_01_0011.jpg'],
['Z:/MTGArchived/SCG/Document_20240325_0253.jpg', 'Document_20240325_0253.jpg', 'Z:/MTGArchived/XXX/Document_20240325_0253.jpg'],
['Z:/MTGArchived/ALA/image20230316132637.jpg', 'image20230316132637.jpg', 'Z:/MTGArchived/XXX/image20230316132637.jpg'],
['Z:/MTGArchived/ALA/Document_20240331_0075.jpg', 'Document_20240331_0075.jpg', 'Z:/MTGArchived/XXX/Document_20240331_0075.jpg'],
['Z:/MTGArchived/DSK/Document_20241130_DSK_02_0084.jpg', 'Document_20241130_DSK_02_0084.jpg', 'Z:/MTGArchived/XXX/Document_20241130_DSK_02_0084.jpg'],
['Z:/MTGArchived/4ED/Document_20240719_4ED_0002.jpg', 'Document_20240719_4ED_0002.jpg', 'Z:/MTGArchived/XXX/Document_20240719_4ED_0002.jpg'],
['Z:/MTGArchived/4ED/Document_20240719_4ED_0001.jpg', 'Document_20240719_4ED_0001.jpg', 'Z:/MTGArchived/XXX/Document_20240719_4ED_0001.jpg'],
['Z:/MTGArchived/DSK/Document_20241130_DSK_01_0096.jpg', 'Document_20241130_DSK_01_0096.jpg', 'Z:/MTGArchived/XXX/Document_20241130_DSK_01_0096.jpg'],
['Z:/MTGArchived/DSK/Document_20241130_DSK_02_0068.jpg', 'Document_20241130_DSK_02_0068.jpg', 'Z:/MTGArchived/XXX/Document_20241130_DSK_02_0068.jpg'],
['Z:/MTGArchived/WOE/image20230919161914.jpg', 'image20230919161914.jpg', 'Z:/MTGArchived/XXX/image20230919161914.jpg'],
['Z:/MTGArchived/KHM/image20230314084956.jpg', 'image20230314084956.jpg', 'Z:/MTGArchived/XXX/image20230314084956.jpg'],
['Z:/MTGArchived/PCY/Document_20240719_PCY_0012.jpg', 'Document_20240719_PCY_0012.jpg', 'Z:/MTGArchived/XXX/Document_20240719_PCY_0012.jpg'],
['Z:/MTGArchived/EMN/image20220118144647.jpg', 'image20220118144647.jpg', 'Z:/MTGArchived/XXX/image20220118144647.jpg'],
['Z:/MTGArchived/EMN/image20220118144652.jpg', 'image20220118144652.jpg', 'Z:/MTGArchived/XXX/image20220118144652.jpg'],
['Z:/MTGArchived/DSK/Document_20241130_DSK_01_0037.jpg', 'Document_20241130_DSK_01_0037.jpg', 'Z:/MTGArchived/XXX/Document_20241130_DSK_01_0037.jpg'],
['Z:/MTGArchived/DSK/Document_20241130_DSK_02_0064.jpg', 'Document_20241130_DSK_02_0064.jpg', 'Z:/MTGArchived/XXX/Document_20241130_DSK_02_0064.jpg'],
['Z:/MTGArchived/M20/Document_20240413_0024.jpg', 'Document_20240413_0024.jpg', 'Z:/MTGArchived/XXX/Document_20240413_0024.jpg'],
['Z:/MTGArchived/DSK/Document_20241130_DSK_01_0144.jpg', 'Document_20241130_DSK_01_0144.jpg', 'Z:/MTGArchived/XXX/Document_20241130_DSK_01_0144.jpg'],
['Z:/MTGArchived/MH3/Document_20240703_MH3_0191.jpg', 'Document_20240703_MH3_0191.jpg', 'Z:/MTGArchived/XXX/Document_20240703_MH3_0191.jpg'],
['Z:/MTGArchived/MH3/Document_20240703_MH3_0003.jpg', 'Document_20240703_MH3_0003.jpg', 'Z:/MTGArchived/XXX/Document_20240703_MH3_0003.jpg'],
['Z:/MTGArchived/MH3/Document_20240703_MH3_0130.jpg', 'Document_20240703_MH3_0130.jpg', 'Z:/MTGArchived/XXX/Document_20240703_MH3_0130.jpg'],
['Z:/MTGArchived/ORI/image20220116204916.jpg', 'image20220116204916.jpg', 'Z:/MTGArchived/XXX/image20220116204916.jpg'],
['Z:/MTGArchived/MH3/Document_20240703_MH3_0014.jpg', 'Document_20240703_MH3_0014.jpg', 'Z:/MTGArchived/XXX/Document_20240703_MH3_0014.jpg'],
['Z:/MTGArchived/ELD/image20220930122322.jpg', 'image20220930122322.jpg', 'Z:/MTGArchived/XXX/image20220930122322.jpg'],
['Z:/MTGArchived/3ED/Document_20240720_XXX_01_0009.jpg', 'Document_20240720_XXX_01_0009.jpg', 'Z:/MTGArchived/XXX/Document_20240720_XXX_01_0009.jpg'],
['Z:/MTGArchived/WOT/image20230919161044.jpg', 'image20230919161044.jpg', 'Z:/MTGArchived/XXX/image20230919161044.jpg'],
['Z:/MTGArchived/MRD/Document_20240717_MRD_0011.jpg', 'Document_20240717_MRD_0011.jpg', 'Z:/MTGArchived/XXX/Document_20240717_MRD_0011.jpg'],
['Z:/MTGArchived/MH3/Document_20240703_MH3_0177.jpg', 'Document_20240703_MH3_0177.jpg', 'Z:/MTGArchived/XXX/Document_20240703_MH3_0177.jpg'],
['Z:/MTGArchived/ELD/image20220929160022.jpg', 'image20220929160022.jpg', 'Z:/MTGArchived/XXX/image20220929160022.jpg'],
['Z:/MTGArchived/ELD/image20220929160006.jpg', 'image20220929160006.jpg', 'Z:/MTGArchived/XXX/image20220929160006.jpg'],
['Z:/MTGArchived/ELD/image20220930121137.jpg', 'image20220930121137.jpg', 'Z:/MTGArchived/XXX/image20220930121137.jpg'],
['Z:/MTGArchived/MRD/Document_20240717_MRD_0004.jpg', 'Document_20240717_MRD_0004.jpg', 'Z:/MTGArchived/XXX/Document_20240717_MRD_0004.jpg'],
['Z:/MTGArchived/AVR/image20230316135615.jpg', 'image20230316135615.jpg', 'Z:/MTGArchived/XXX/image20230316135615.jpg'],
['Z:/MTGArchived/AVR/image20230316135533.jpg', 'image20230316135533.jpg', 'Z:/MTGArchived/XXX/image20230316135533.jpg'],
['Z:/MTGArchived/KHM/image20230314085007.jpg', 'image20230314085007.jpg', 'Z:/MTGArchived/XXX/image20230314085007.jpg'],
['Z:/MTGArchived/ELD/image20220930163349.jpg', 'image20220930163349.jpg', 'Z:/MTGArchived/XXX/image20220930163349.jpg'],
['Z:/MTGArchived/MH3/Document_20240703_MH3_FOIL_0013.jpg', 'Document_20240703_MH3_FOIL_0013.jpg', 'Z:/MTGArchived/XXX/Document_20240703_MH3_FOIL_0013.jpg'],
['Z:/MTGArchived/KHM/image20230314085012.jpg', 'image20230314085012.jpg', 'Z:/MTGArchived/XXX/image20230314085012.jpg'],
['Z:/MTGArchived/WWK/image20230316133151.jpg', 'image20230316133151.jpg', 'Z:/MTGArchived/XXX/image20230316133151.jpg'],
['Z:/MTGArchived/KHM/image20230314084743.jpg', 'image20230314084743.jpg', 'Z:/MTGArchived/XXX/image20230314084743.jpg'],

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