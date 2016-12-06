"""
This module contains all functions related to
video reading and editing
"""

import os
import subprocess as sp
import json
import math
import numpy
import statistics
import re
import base64

FFMPEG_BIN = os.path.realpath('./bin/ffmpeg.exe')
FFPROBE_BIN = os.path.realpath('./bin/ffprobe.exe')
WATERMARK_LENGTH = 32
DIMENSION = 3 # Size of square to read
PROGRESSBAR_LENGTH = 57

outputMsg_cache = ""
def updateScreen(watermark):
	global outputMsg_cache

	# Calculate progress and printable watermark 
	progress = 0
	pW = []
	for w in watermark:
		if w is None:
			pW.append('??')
		else:
			v = str(w)+' ' if (w < 10) else str(w)
			pW.append(v)
			progress += 1
	progress = (progress / len(watermark)) * PROGRESSBAR_LENGTH
	progress = math.floor(progress)
	
	# Generate output
	progressBar = ""
	for i in range(PROGRESSBAR_LENGTH): progressBar += "|" if (i < progress) else " "
	
	outputMsg = '\n' + \
				'  ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::\n' + \
				'  ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::\n' + \
				'  ::                                                                ::\n' + \
				'  ::                    DECODIFICANDO MENSAJE...                    ::\n' + \
				'  ::                                                                ::\n' + \
				'  ::                                                                ::\n' + \
				'  ::   '+pW[0]+'   '+pW[1]+'   '+pW[2]+'   '+pW[3]+'   '+pW[4]+'   ' + \
						  pW[5]+'   '+pW[6]+'   '+pW[7]+'   '+pW[8]+'   '+pW[9]+'   ' + \
						  pW[10]+'   '+pW[11]+'    ::\n' + \
				'  ::   '+pW[12]+'   '+pW[13]+'   '+pW[14]+'   '+pW[15]+'   '+pW[16]+'   ' + \
						  pW[17]+'   '+pW[18]+'   '+pW[19]+'   '+pW[20]+'   '+pW[21]+'   ' + \
						  pW[22]+'   '+pW[23]+'    ::\n' + \
				'  ::             '+pW[24]+'   '+pW[25]+'   '+pW[26]+'   '+pW[27]+'   ' + \
									pW[28]+'   '+pW[29]+'   '+pW[30]+'   '+pW[31]+'              ::\n' + \
				'  ::                                                                ::\n' + \
				'  ::                                                                ::\n' + \
				'  ::                                                                ::\n' + \
				'  ::   ' + progressBar + '    ::\n' + \
				'  ::                                                                ::\n' + \
				'  ::                                                                ::\n' + \
				'  ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::\n' + \
				'  ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::'

	# Clear screen and print dialog
	if not outputMsg == outputMsg_cache:
		os.system('cls')
		outputMsg_cache = outputMsg
		print(outputMsg)

def getVideoInfo(filePath):
	# Call subprocess and get response
	proc = sp.Popen('"' + FFPROBE_BIN + '" -v quiet -print_format json -show_format -show_streams "' + filePath + '"', \
		stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
	res = json.loads(proc.stdout.read().decode("utf-8"))
	
	# Check if valid video file
	if not 'streams' in res: return False
	
	# Get resolution from response
	resolution = False
	for stream in res['streams']:
		if stream['codec_type'] == "video":
			resolution = {"width": stream['width'], "height": stream['height']}
			break

	# Return resolution
	return resolution

def getDataFromPixel(px):
	return (int(px[0]) + int(px[1]) + int(px[2])) % 64

def watermarkToMessage(watermark):
	dict = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
	b64 = ""
	for w in watermark: b64 += dict[w]
	b64 = re.sub('A+$', '', b64)
	msg = base64.b64decode(b64)
	return msg
	

def getMessage(filePath):
	# Get video info
	resolution = getVideoInfo(filePath)
	if resolution is False: return False
	
	# Create empty array for the encoded message
	watermark = [None] * WATERMARK_LENGTH;
	updateScreen(watermark)
	
	# Create array of pixel indexes to read in a frame
	pixels = []
	pointer = resolution['width'] * (resolution['height'] - 1) * 3
	pointer_tag = 0
	for column in range(DIMENSION):
		for row in range(DIMENSION):
			k = row * 3
			pixels.append([pointer_tag+k, pointer+k])
		x = resolution['width'] * 3
		pointer -= x
		pointer_tag += x
	
	# Open binary stream to FFMPEG
	cmd = [FFMPEG_BIN,
		'-i', filePath,
		'-f', 'image2pipe',
		'-pix_fmt', 'rgb24',
		'-vcodec', 'rawvideo',
		'-']
	nullOutput = open(os.devnull, "w")
	pipe = sp.Popen(cmd, stdout=sp.PIPE, stderr=nullOutput.fileno())
	
	# Loop until we have a solution
	bufferBytes = resolution['width'] * resolution['height'] * 3
	while pipe.poll() is None:
		# Read frame bytes
		frameBytes = pipe.stdout.read(bufferBytes)
		pipe.stdout.flush()
		
		# Convert output to numpy uInt8 array
		frameBytes = numpy.fromstring(frameBytes, dtype='uint8')
		
		# Get possible watermark position and message values from frame
		position = []
		message = []
		for px in pixels:
			posData = getDataFromPixel([ frameBytes[px[0]], frameBytes[px[0]+1], frameBytes[px[0]+2] ])
			msgData = getDataFromPixel([ frameBytes[px[1]], frameBytes[px[1]+1], frameBytes[px[1]+2] ])
			position.append(posData)
			message.append(msgData)
		
		# Save mode (if exists)
		if (statistics.variance(position) < 3) and (statistics.variance(message) < 3):
			position = statistics.mode(position)
			message = statistics.mode(message)
			watermark[position] = message
			updateScreen(watermark)
		
		# Check if we have finished
		haveWeFinished = True
		for w in watermark:
			if w is None:
				haveWeFinished = False
				break
		if haveWeFinished: break
	
	# Close pipe
	pipe.stdout.close()
	
	# Convert watermark to string
	result = watermarkToMessage(watermark)
	
	# Return injected message
	return result