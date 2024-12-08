# made as a backup to the python scanne

# program to capture single image from webcam in python 
import cv2 as cv
  
# initialize the camera 
# If you have multiple camera connected with  
# current device, assign a value in cam_port  
# variable according to that 
cam_port = 0
cam = cv.VideoCapture(cam_port) 

while(True): 
      
    # Capture the video frame 
    # by frame 
    ret, frame = cam.read() 
  
    # Display the resulting frame 
    cv.imshow('frame', frame) 
      
    # the 'q' button is set as the 
    # quitting button you may use any 
    # desired button of your choice 
    if cv.waitKey(1) & 0xFF == ord('q'): 
        break
  
# After the loop release the cap object 
cam.release() 
# Destroy all the windows 
cv.destroyAllWindows() 


# # reading the input using the camera 
# result, image = cam.read() 

# # If image will detected without any error,  
# # show result 
# if result: 
  
#     # showing result, it take frame name and image  
#     # output 
#     cv.imshow("GeeksForGeeks", image) 
  
#     # saving image in local storage 
#     cv.imwrite("GeeksForGeeks.png", image) 
  
#     # If keyboard interrupt occurs, destroy image  
#     # window 
#     cv.waitKey(0) 
#     cv.destroyWindow("GeeksForGeeks") 

# # If captured image is corrupted, moving to else part 
# else: 
#     print("No image detected. Please! try again") 