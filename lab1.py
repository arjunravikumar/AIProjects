"""Terrain type	Color on map	Photo (legend)
Open land	#F89412 (248,148,18)	A
Rough meadow	#FFC000 (255,192,0)	B
Easy movement forest	#FFFFFF (255,255,255)	C · D
Slow run forest	#02D03C (2,208,60)	E
Walk forest	#028828 (2,136,40)	F
Impassible vegetation	#054918 (5,73,24)	G
Lake/Swamp/Marsh	#0000FF (0,0,255)	H · I · J
Paved road	#473303 (71,51,3)	K · L
Footpath	#000000 (0,0,0)	M · N
Out of bounds	#CD0065 (205,0,101)	"""

from PIL import Image
import sys
from array import *
import math
import time

season = ""
outputImageFilename = ""
elevation = []
path = []
terrainToSpeedRelation = {"#F89412" : 1,"#473303" : 1, "#000000" : 2, "#FFFFFF" : 2, "#02D03C" : 3,
"#FFC000":4, "#028828" : 4,"#0000FF": 1000,"#054918": 1000,"#CD0065" : 1000, "#FF0000":1, '#EE30FF':1,"#00FFE5":1,"#836565":8}
rgbTerrain = None
imageHeight = 0
imageWidth = 0
pixelColoursOfImage = []
distanceFactor = 12
elevationFactor = 5
terrainFactor = 3

class Pixel:
	def __init__(self, parent=None, position=None):
		self.parent = parent
		self.location = position
		self.g = 0
		self.h = 0
		self.f = 0

	def __eq__(self, nextPix):
		return self.location == nextPix.location

def openTheTerrainImage(terrainImage):
	global rgbTerrain
	global outputImage
	global imageWidth
	global imageHeight
	global pixelColoursOfImage
	im = Image.open(terrainImage)
	outputImage = im.copy()
	rgbTerrain = outputImage.convert('RGB')
	imageWidth,imageHeight = outputImage.size
	for x in range (0,imageWidth):
		pixelColoursOfImage.append([])
		for y in range (0, imageHeight):
			rgbTerrain = outputImage.convert('RGB')
			r, g, b = rgbTerrain.getpixel((x, y))
			pixelColoursOfImage[x].append("")
			pixelColoursOfImage[x][y] = "#{:02X}{:02X}{:02X}".format(r, g, b)

def notTravelableTerrain(x,y):
	if(terrainToSpeedRelation[getColourOfPixel(x,y)] == 1000):
		return True
	return False

def saveAndShowImage(outputImageFilename):
	outputImage.show()
	outputImage.save(outputImageFilename , "PNG")

def changePixelColour(x,y,colorToPut):
	global outputImage
	global pixelColoursOfImage
	pixelColoursOfImage[x][y] = "#{:02X}{:02X}{:02X}".format(colorToPut[0], colorToPut[1], colorToPut[2])
	outputImage.putpixel((x,y),colorToPut)

def putTraversedPath(x,y):
	changePixelColour(x,y,(255,0,0))

def putCheckpoint(x,y):
	for i in range(-1,1):
		for j in range(-1,1):
			changePixelColour(x+i,y+j,(238, 48, 255))

def freezeWater(x,y):
	changePixelColour(x,y,(0, 255, 229))

def mudNearWater(x,y):
	changePixelColour(x,y,(131, 101, 101))

def getColourOfPixel(x,y):
	global pixelColoursOfImage
	return pixelColoursOfImage[x][y]

def loadDataFromElevationFile(elevationFile):
	global elevation
	file = open(elevationFile,"r+")
	for line in file:
		elevation.append([float(x) for x in line.split()])

def loadDataFromPathFile(pathFile):
	global path
	file = open(pathFile,"r+")
	for line in file:
		path.append([int(x) for x in line.split()])

def getElevation(currX,currY,desX,desY):
	global elevation
	if(currX < len(elevation) and desX < len(elevation) and currY < len(elevation[currX]) and desY < len(elevation[currX])):
		return elevation[desX][desY] - elevation[currX][currY]
	return 0

def getDistanceBetweenPoints(currX,currY,desX,desY):
	height = getElevation(currX,currY,desX,desY)
	displacement = abs(currX-desX)+abs(currY-desY)
	distance = math.sqrt(pow(displacement,2)+pow(height,2))
	return distance

def getDistance(currX,currY,desX,desY):
	return (math.hypot(abs(desX - currX), abs(desY - currY)))

def calculateHofNForThePoint(currX,currY,desX,desY,destination):
	terrain = getColourOfPixel(desX,desY);
	distanceToDestination = getDistance(desX,desY,destination[0],destination[1])
	distanceToDestination = distanceToDestination + getDistanceBetweenPoints(currX,currY,desX,desY)
	elevation = getElevation(currX,currY,desX,desY)
	totalH = (distanceToDestination*distanceFactor) + (elevation * elevationFactor) + (terrainToSpeedRelation[terrain] * terrainFactor)
	return totalH

def calculateGofNForThePoint(currX,currY,desX,desY,start):
	return getDistance(desX,desY,start[0],start[1])

def checkIfPositionOutOfBounds(currX,currY):
	if currX > (imageWidth - 1) or currX < 0 or currY > (imageHeight -1) or currY < 0:
		return True
	return False

def startAstarPathFinder(start,destination):
	global imageWidth
	global imageHeight
	unVisitedList = []
	visitedList = []
	startPixel = Pixel(None, start)
	startPixel.g = startPixel.h = startPixel.f = 0
	destinationPixel = Pixel(None, destination)
	destinationPixel.g = destinationPixel.h = destinationPixel.f = 0
	unVisitedList.append(startPixel)

	while(len(unVisitedList)>0):
		currentPixel = unVisitedList[0]
		currentIndex = 0
		for index, item in enumerate(unVisitedList):
			if item.f < currentPixel.f:
				currentPixel = item
				currentIndex = index
		unVisitedList.pop(currentIndex)
		visitedList.append(currentPixel)

		if currentPixel == destinationPixel:
			locPath = []
			current = currentPixel
			while current is not None:
				putTraversedPath(current.location[0],current.location[1])
				current = current.parent
			return currentPixel.g
		for x in range(-1,2):
			for y in range(-1,2):
				if not(x == 0 and y == 0):
					pixelPosition = (currentPixel.location[0] + x, currentPixel.location[1] + y)
					if checkIfPositionOutOfBounds(pixelPosition[0],pixelPosition[1]) and notTravelableTerrain(pixelPosition[0],pixelPosition[1]):
						continue
					neighbour = Pixel(currentPixel, pixelPosition)
					found = False
					for closedChild in visitedList:
						if neighbour == closedChild:
							found = True
							continue
					neighbour.g = currentPixel.g + \
					getDistanceBetweenPoints(currentPixel.location[0],currentPixel.location[1],neighbour.location[0],neighbour.location[1])
					neighbour.h = calculateHofNForThePoint(currentPixel.location[0],currentPixel.location[1],neighbour.location[0],neighbour.location[1],destination)
					neighbour.f = neighbour.g + neighbour.h
					for openNode in unVisitedList:
						if neighbour == openNode and neighbour.f > openNode.f:
							found = True
							continue
					if(found == False):
						unVisitedList.append(neighbour)

def startPathFinder():
	distance = 0
	for i in range(0,len(path)-1):
		if(not(notTravelableTerrain(path[i][0],path[i][1])) and  not(notTravelableTerrain(path[i+1][0],path[i+1][1]))):
			distance = distance + startAstarPathFinder(tuple(path[i]),tuple(path[i+1]))
			putCheckpoint(path[i][0],path[i][1])
		elif(not(notTravelableTerrain(path[i][0],path[i][1]))):
			print(path[i]," is in ",getColourOfPixel(path[i][0],path[i][1]))
			return
		else:
			print(path[i+1]," is in ",getColourOfPixel(path[i+1][0],path[i+1][1]))
			return
	print("\n\nTotal Distanc Covered:",distance)

def doBFSandChangeColorForWinter(x,y):
	queue = [] 
	queue.append((x,y))
	while len(queue) > 0: 
		currX , currY = queue.pop(0) 
		for i in range(-1,2):
			for j in range(-1,2):
				if not(i == 0 and j == 0):
					if currX+i>0 and currX+i< imageWidth and currY+j > 0 and currY+j < imageHeight:
						if (getColourOfPixel(currX+i,currY+j) == "#0000FF") and (getDistance(x,y,currX+i,currY+j) <= 7): 
							queue.append((currX+i,currY+j))
							freezeWater(currX+i,currY+j)

def changeSeasonToWinter():
	waterEdges = []
	for x in range(1,imageWidth):
		for y in range(1,imageHeight):
			if(getColourOfPixel(x,y) == "#0000FF"):
				for i in range(-1,2):
					for j in range(-1,2):
						if not(i == 0 and j == 0):
							if x+i > 0 and x+i < imageWidth and y+j > 0 and y+j < imageHeight:
								if(getColourOfPixel(x+i,y+j) != "#0000FF"):
									waterEdges.append((x,y))
	for index in range(0,len(waterEdges)):
		doBFSandChangeColorForWinter(waterEdges[index][0],waterEdges[index][1])

def changeSeasonToFall():
	terrainToSpeedRelation["#000000"] = terrainToSpeedRelation["#000000"] + 1
	terrainToSpeedRelation["#FFC000"] = terrainToSpeedRelation["#FFC000"] + 2
	terrainToSpeedRelation["#FFFFFF"] = terrainToSpeedRelation["#FFFFFF"] + 2
	terrainToSpeedRelation["#02D03C"] = terrainToSpeedRelation["#02D03C"] + 3
	terrainToSpeedRelation["#028828"] = terrainToSpeedRelation["#028828"] + 4

def doBFSandChangeColorForSpring(x,y):
	queue = [] 
	queue.append((x,y))
	while len(queue) > 0: 
		currX , currY = queue.pop(0) 
		for i in range(-1,2):
			for j in range(-1,2):
				if not(i == 0 and j == 0):
					if currX+i>0 and currX+i< imageWidth and currY+j > 0 and currY+j < imageHeight:
						if (getColourOfPixel(currX+i,currY+j) != "#0000FF") and \
						(getColourOfPixel(currX+i,currY+j) != "#836565") and \
						(getColourOfPixel(currX+i,currY+j) != "#CD0065") and \
						(getDistance(x,y,currX+i,currY+j) <= 15) and (getElevation(x,y,currX+i,currY+j) <= 1): 
							queue.append((currX+i,currY+j))
							mudNearWater(currX+i,currY+j)

def changeSeasonToSpring():
	waterEdges = []
	for x in range(1,imageWidth):
		for y in range(1,imageHeight):
			if(getColourOfPixel(x,y) == "#0000FF"):
				for i in range(-1,2):
					for j in range(-1,2):
						if not(i == 0 and j == 0):
							if x+i > 0 and x+i < imageWidth and y+j > 0 and y+j < imageHeight:
								if(getColourOfPixel(x+i,y+j) != "#0000FF"):
									waterEdges.append((x,y))
	for index in range(0,len(waterEdges)):
		doBFSandChangeColorForSpring(waterEdges[index][0],waterEdges[index][1])

def changeImageForSeason(season):
	if(season == "winter"):
		changeSeasonToWinter()
	if(season == "fall"):
		changeSeasonToFall()
	if(season == "spring"):
		changeSeasonToSpring()

def main():
	start = time.time()
	openTheTerrainImage(sys.argv[1])
	end = time.time()
	print("Read Terrain Image Time:",end-start,"seconds")
	start = time.time()
	loadDataFromElevationFile(sys.argv[2])
	end = time.time()
	print("Read Elevation File:",end-start,"seconds")
	start = time.time()
	loadDataFromPathFile(sys.argv[3])
	end = time.time()
	print("Open Path File:",end-start,"seconds")
	start = time.time()
	changeImageForSeason(sys.argv[4])
	end = time.time()
	print("Change Image For Seasons:",end-start,"seconds")
	start = time.time()
	startPathFinder()
	end = time.time()
	print("Path Finding Time:",end-start,"seconds")
	saveAndShowImage(sys.argv[5])

main()