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

['Z:/MTGArchived/DRK/image20220314105716.jpg','image20220314105716.jpg','Z:/MTGArchived/XXX/image20220314105716.jpg'],
['Z:/MTGArchived/C17/image20230827204012.jpg','image20230827204012.jpg','Z:/MTGArchived/XXX/image20230827204012.jpg'],
['Z:/MTGArchived/9ED/image20221230130221.jpg','image20221230130221.jpg','Z:/MTGArchived/XXX/image20221230130221.jpg'],
['Z:/MTGArchived/ZNC/image20221230130611.jpg','image20221230130611.jpg','Z:/MTGArchived/XXX/image20221230130611.jpg'],
['Z:/MTGArchived/WTH/image20230827142902.jpg','image20230827142902.jpg','Z:/MTGArchived/XXX/image20230827142902.jpg'],
['Z:/MTGArchived/EXO/image20221230130448.jpg','image20221230130448.jpg','Z:/MTGArchived/XXX/image20221230130448.jpg'],
['Z:/MTGArchived/ZEN/image20220914121110.jpg','image20220914121110.jpg','Z:/MTGArchived/XXX/image20220914121110.jpg'],
['Z:/MTGArchived/2ED/image20221230130211.jpg','image20221230130211.jpg','Z:/MTGArchived/XXX/image20221230130211.jpg'],
['Z:/MTGArchived/MRD/Document_20240717_MRD_0006.jpg','Document_20240717_MRD_0006.jpg','Z:/MTGArchived/XXX/Document_20240717_MRD_0006.jpg'],
['Z:/MTGArchived/ULG/image20221230130057.jpg','image20221230130057.jpg','Z:/MTGArchived/XXX/image20221230130057.jpg'],
['Z:/MTGArchived/C21/image20221230125438.jpg','image20221230125438.jpg','Z:/MTGArchived/XXX/image20221230125438.jpg'],
['Z:/MTGArchived/3ED/image20220315114959.jpg','image20220315114959.jpg','Z:/MTGArchived/XXX/image20220315114959.jpg'],
['Z:/MTGArchived/C17/image20230827204007.jpg','image20230827204007.jpg','Z:/MTGArchived/XXX/image20230827204007.jpg'],
['Z:/MTGArchived/GRN/image20221230130102.jpg','image20221230130102.jpg','Z:/MTGArchived/XXX/image20221230130102.jpg'],
['Z:/MTGArchived/M11/image20221230130216.jpg','image20221230130216.jpg','Z:/MTGArchived/XXX/image20221230130216.jpg'],
['Z:/MTGArchived/MOM/image20230426120835.jpg','image20230426120835.jpg','Z:/MTGArchived/XXX/image20230426120835.jpg'],
['Z:/MTGArchived/MOM/image20230503165216.jpg','image20230503165216.jpg','Z:/MTGArchived/XXX/image20230503165216.jpg'],
['Z:/MTGArchived/BOK/Document_20240717_BOK_0036.jpg','Document_20240717_BOK_0036.jpg','Z:/MTGArchived/XXX/Document_20240717_BOK_0036.jpg'],
['Z:/MTGArchived/4ED/image20220315133051.jpg','image20220315133051.jpg','Z:/MTGArchived/XXX/image20220315133051.jpg'],
['Z:/MTGArchived/DSK/Document_20241130_DSK_02_0055.jpg','Document_20241130_DSK_02_0055.jpg','Z:/MTGArchived/XXX/Document_20241130_DSK_02_0055.jpg'],
['Z:/MTGArchived/DSK/Document_20241130_DSK_01_0110.jpg','Document_20241130_DSK_01_0110.jpg','Z:/MTGArchived/XXX/Document_20241130_DSK_01_0110.jpg'],
['Z:/MTGArchived/EMN/Document_20240710_EMN_FOIL_0001.jpg','Document_20240710_EMN_FOIL_0001.jpg','Z:/MTGArchived/XXX/Document_20240710_EMN_FOIL_0001.jpg'],
['Z:/MTGArchived/DRK/image20220314105836.jpg','image20220314105836.jpg','Z:/MTGArchived/XXX/image20220314105836.jpg'],
['Z:/MTGArchived/CHK/image20220314133705.jpg','image20220314133705.jpg','Z:/MTGArchived/XXX/image20220314133705.jpg'],
['Z:/MTGArchived/CSP/image20221230130314.jpg','image20221230130314.jpg','Z:/MTGArchived/XXX/image20221230130314.jpg'],
['Z:/MTGArchived/PCY/image20230102111211.jpg','image20230102111211.jpg','Z:/MTGArchived/XXX/image20230102111211.jpg'],
['Z:/MTGArchived/BLB/Document_20240906_BLB_0100.jpg','Document_20240906_BLB_0100.jpg','Z:/MTGArchived/XXX/Document_20240906_BLB_0100.jpg'],
['Z:/MTGArchived/P02/Document_20240719_P02_0005.jpg','Document_20240719_P02_0005.jpg','Z:/MTGArchived/XXX/Document_20240719_P02_0005.jpg'],
['Z:/MTGArchived/MOM/image20230503165100.jpg','image20230503165100.jpg','Z:/MTGArchived/XXX/image20230503165100.jpg'],
['Z:/MTGArchived/ONE/image20230426124430.jpg','image20230426124430.jpg','Z:/MTGArchived/XXX/image20230426124430.jpg'],
['Z:/MTGArchived/LGN/image20221230130124.jpg','image20221230130124.jpg','Z:/MTGArchived/XXX/image20221230130124.jpg']

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