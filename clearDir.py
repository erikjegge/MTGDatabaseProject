import os, shutil
source = 'Z:/MTGImages'

for subdir, dirs, files in os.walk(source):
        if subdir != source:
                head, tail = os.path.split(subdir)
                if files:
                        for file in files:
                                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    sourceFile = os.path.join(subdir,file)
                                    sourceFile = sourceFile.replace('\\', '/')

                                    try:
                                        os.remove(sourceFile)
                                    except Exception as e:
                                        print('Failed to delete %s. Reason: %s' % (sourceFile, e))

    #try:
        #if os.path.isfile(file_path) or os.path.islink(file_path):
            #os.unlink(file_path)
        #elif os.path.isdir(file_path):
            #shutil.rmtree(file_path)
    #except Exception as e:
        #print('Failed to delete %s. Reason: %s' % (file_path, e))