import sys
import os
import ffmpeg

# Check parameters
if len(sys.argv) < 3:
	print('Missing essential parameters.\nExample: ' + os.path.basename(__file__) + ' input.mp4 output.txt')
	sys.exit()

# Get parameters
videoPath = sys.argv[1]
outputPath = sys.argv[2]

# Check if file exists
videoPath = os.path.realpath(videoPath)
if not os.path.isfile(videoPath):
	print("Input file does not exists")
	sys.exit()

# Get message bytes
message = ffmpeg.getMessage(videoPath)
if message is False:
	print("Could not find any encoded message in input file")
	sys.exit()

# Save message to file
outputPath = os.path.realpath(outputPath)
f = open(outputPath, 'wb')
f.write(message)
f.close()

# Change terminal message
os.system('cls')
print('\n' + \
	 '  ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::\n' + \
	 '  ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::\n' + \
	 '  ::                                                                ::\n' + \
	 '  ::                ¡MENSAJE DECODIFICADO CON ÉXITO!                ::\n' + \
	 '  ::                                                                ::\n' + \
	 '  ::                                                                ::\n' + \
	 '  ::                                                                ::\n' + \
	 '  ::                                                                ::\n' + \
	 '  ::                                                                ::\n' + \
   	 '  ::' + ('Guardado en ' + os.path.basename(outputPath)).center(64, ' ') + '::\n' + \
	 '  ::                                                                ::\n' + \
	 '  ::                                                                ::\n' + \
	 '  ::   |||||||||||||||||||||||||||||||||||||||||||||||||||||||||    ::\n' + \
	 '  ::                                                                ::\n' + \
	 '  ::                                                                ::\n' + \
	 '  ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::\n' + \
	 '  ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::')