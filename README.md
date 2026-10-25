# Car Framework
Unified framework for all RPI and UNO based cars that require CV

## main.py
Captures the frame, puts it in a async q to allow other functions from other files to use it

Also calls the functions from other files and puts them in a async loop

## sender.py
Compresses the file into AVIF format and sends it and also runs the detection loop

## trackhuman.py
uses the tracked location values to send controlls. This can be completely swapped out for other projects with other needs

# Models:
yolov8n-pose and yolov8n converted to NCNN from pytorch for speed reasons

This will recieve a version of yolov8n that has recieved distillation from yolov26l

# License:
GNU LGPL-3.0
