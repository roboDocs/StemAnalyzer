from mojo.UI import *
from AppKit import *

import math
import StemAnalyzerModule as module

from mojo.subscriber import *
import ezui

minStemY = minStemX = 20
maxStemY = maxStemX = 400

class StemAnalyzerWindow(Subscriber, ezui.WindowController):
	
	debug = False
	
	def build(self):
		
		self.roundTo5 = 1
		self.stemSnapHList = []
		self.stemSnapVList = []
		
		self.containers_setup = False
		self.glyphsStemsList = []
		
		
		self.horzColor = (255/255, 68/255, 79/255, 255/255)
		self.horzAccent = (255/255, 213/255, 213/255, 255/255)
		self.vertAccent = (212/255, 250/255, 236/255, 255/255)
		self.vertColor = (0/255, 159/255, 0/255, 255/255)

		
		content = """
		*VerticalStack					  @stemStack
		[ ] Round Values to 5			  @roundCheckbox
		(Analyze Selected Glyphs)		  @analyzeButton
		-----
		Horizontal (Y):				 
		{arrow.up.arrow.down} [__]		  @horizontalTextField
		Vertical (X):				 
		{arrow.left.arrow.right} [__]	  @verticalTextField
		------
		(Copy to PS StemSnap)			  @copyButton
		"""


		descriptionData=dict(
			stemStack=dict(
				width=250,
			),
			roundCheckbox=dict(
				value=True
			),
			horizontalTextField=dict(
				valueType="integerList",
			),
			verticalTextField=dict(
				valueType="integerList",
			),
		)

		self.w = ezui.EZPanel(
            title="StemAnalyzer",
			content=content,
			descriptionData=descriptionData,
			controller=self
		)

	def started(self):		
		# took this method from Ryan Bugden!
		self.glyphEditor = CurrentGlyphWindow()
		if self.glyphEditor:
			self.setUpContainers()
			self.drawContent()
		self.w.open()
		
		
	def setUpContainers(self):
		# took this method from Ryan Bugden!
		self.container = self.glyphEditor.extensionContainer(
			identifier="com.sansplomb.stemAnalyzer",
			location="foreground",
			clear=True
		)
		self.containers_setup = True
		
	def glyphEditorWillOpen(self, info):
		self.glyphEditor = info["glyphEditor"]
		self.setUpContainers()
		
	def glyphEditorDidOpen(self, info):
		self.drawContent()

	def glyphEditorDidSetGlyph(self, info):
		# took this method from Ryan Bugden!
		if self.containers_setup == True:
			self.container.clearSublayers()
			self.containers_setup = False
			
		self.glyph = info["glyph"]
		self.glyphEditor = info["glyphEditor"]
		self.setUpContainers()
		self.drawContent()

	def destroy(self):
		self.container.clearSublayers()
		
	def roundCheckboxCallback(self, sender):
		self.roundTo5 = self.w.getItem("roundCheckbox").get()
		
	def copyButtonCallback(self, sender):
		f.info.postscriptStemSnapH = self.stemSnapHList
		f.info.postscriptStemSnapV = self.stemSnapVList
		
	def interpolatePoints(self, a,b,v):
		x = a[0] + v * (b[0] - a[0])
		y = a[1] + v * (b[1] - a[1])
		return (x,y)
		
	def getPointBounds(self,points):
		xs = [p.x for p in points]
		ys = [p.y for p in points]
		x = min(xs)
		y = min(ys)
		xMax = max(xs)
		yMax = max(ys)
		w = xMax - x
		h = yMax - y
		return (x,y,w,h)
			
	def drawTextAtPoint(self,path,pos,text,mainColor,acctColor):
		path.appendTextLineSublayer(
			position=pos,
			size=(20, 20),
			backgroundColor=acctColor,
			pointSize=8,
			weight="bold",
			text=text,
			fillColor=mainColor,
			horizontalAlignment="center",
			verticalAlignment="center",
			cornerRadius=6,
			padding=(6, 3),
			borderWidth=1,
			borderColor=mainColor,
		)
		
	def drawSquiggle(self,path,point1,point2,orientation):
		pen = path.getPen()
		pen.moveTo((point1.x,point1.y))
		if orientation == "v":
			scale = abs(point2.x - point1.x)/2.5
			pen.curveTo(
				(self.interpolatePoints((point1.x,point1.y),(point2.x,point2.y),1/3)[0],point1.y+scale),
				(self.interpolatePoints((point1.x,point1.y),(point2.x,point2.y),2/3)[0],point2.y-scale),
				(point2.x,point2.y))
		if orientation == "h":
			scale = abs(point2.y - point1.y)/2.5
			pen.curveTo(
				(point1.x+scale,self.interpolatePoints((point1.x,point1.y),(point2.x,point2.y),1/3)[1]),
				(point2.x-scale,self.interpolatePoints((point1.x,point1.y),(point2.x,point2.y),2/3)[1]),
				(point2.x,point2.y))
				
		pen.endPath()
		path.setStrokeJoin("round")
		

	def drawContent(self):
		for gStems in self.glyphsStemsList:
			if gStems[0] == CurrentGlyph().name:
				valuesListX = []
				for stem in gStems[1]:
					startPoint, endPoint = stem[0], stem[1]
					startPoint.x = startPoint.x
					startPoint.y = startPoint.y
					endPoint.x = endPoint.x
					endPoint.y = endPoint.y
					length = float(stem[2][0])
			
					vPathLayer = self.container.appendPathSublayer(
						fillColor=None,
						strokeColor=self.vertColor,
						strokeWidth=2
					)
					self.drawSquiggle(vPathLayer,startPoint,endPoint,"v")
					center_x = startPoint.x + (endPoint.x - startPoint.x) * 0.5
					center_y = startPoint.y + (endPoint.y - startPoint.y) * 0.5
					valuesListX.append((center_x, center_y, length))
		
				for x, y, lengthValue in valuesListX:
					if lengthValue.is_integer():
						t = "%i"
					else:
						t = "%.2f"
					textPath = self.container.appendTextLineSublayer()
					self.drawTextAtPoint(textPath, (x,y), f"{t % lengthValue}", self.vertColor, self.vertAccent)
			
			# ----------------------------------
			# ----------------------------------
			
				valuesListY = []
				for stem in gStems[2]:
					startPoint, endPoint = stem[0], stem[1]
					length = float(stem[2][1])
				
					hPathLayer = self.container.appendPathSublayer(
						fillColor=None,
						strokeColor=self.horzColor,
						strokeWidth=2
					)
					self.drawSquiggle(hPathLayer,startPoint,endPoint,"h")
					center_x = startPoint.x + (endPoint.x - startPoint.x) * 0.5
					center_y = startPoint.y + (endPoint.y - startPoint.y) * 0.5
					valuesListY.append((center_x, center_y, length))
					
				for x, y, lengthValue in valuesListY:
					if lengthValue.is_integer():
						t = "%i"
					else:
						t = "%.2f"
					textPath = self.container.appendTextLineSublayer()
					self.drawTextAtPoint(textPath, (x,y), f"{t % lengthValue}", self.horzColor, self.horzAccent)

	
	
	def analyzeButtonCallback(self, sender):
		
		self.glyphsStemsList = []
		self.stemsValuesXList = []
		self.stemsValuesYList = []
		self.stemSnapHList = []
		self.stemSnapVList = []
		roundedStemsXList = []
		roundedStemsYList = []
		originalStemsXList = []
		originalStemsYList = []
		
		self.f = CurrentFont()
		if self.f.info.italicAngle != None:
			self.ital = - self.f.info.italicAngle
		else:
			self.ital = 0
		#self.progress = self.startProgress("Preparing")
		tickCount = 0
		for g in self.f:
			if g.selected:
				tickCount += 1
		
		#self.progress.setTickCount(tickCount)
		#self.progress.update("Analysing Selected Glyphs")
		for g in self.f.selectedGlyphs:
			self.g_hPoints = make_hPointsList(g)
			(self.stemsListX, self.stemsListY) = makeStemsList(self.f, self.g_hPoints, g, self.ital)
			if self.roundTo5 == 1:
				for stem in self.stemsListX:
					roundedStemsXList.append(module.roundbase(stem[2][0], 5))
				for stem in self.stemsListY:
					roundedStemsYList.append(module.roundbase(stem[2][1], 5))	
				
				self.stemsValuesXList = roundedStemsXList
				self.stemsValuesYList = roundedStemsYList
				self.glyphsStemsList.append((g.name, self.stemsListX, self.stemsListY))
				
			else:
				for stem in self.stemsListX:
					originalStemsXList.append(stem[2][0])
				for stem in self.stemsListY:
					originalStemsYList.append(stem[2][1])
				
				self.stemsValuesXList = originalStemsXList
				self.stemsValuesYList = originalStemsYList
				
				self.glyphsStemsList.append((g.name, self.stemsListX, self.stemsListY))
				
		
		valuesXDict = {}
		for StemXValue in self.stemsValuesXList:
			try:
				valuesXDict[StemXValue] += 1
			except KeyError:
				valuesXDict[StemXValue] = 1		
		valuesYDict = {}
		for StemYValue in self.stemsValuesYList:
			try:
				valuesYDict[StemYValue] += 1
			except KeyError:
				valuesYDict[StemYValue] = 1
		
		keyValueXList = list(valuesXDict.items())
		keyValueXList = sorted(keyValueXList, reverse=True, key=module.compare)
		keyValueXList = keyValueXList[:12]

		keyValueYList = list(valuesYDict.items())
		keyValueYList = sorted(keyValueYList, reverse=True, key=module.compare)
		keyValueYList = keyValueYList[:12]
		
		
		for keyValue in keyValueXList:
			self.stemSnapVList.append(keyValue[0])
		
		self.w.getItem("verticalTextField").set(self.stemSnapVList)

		for keyValue in keyValueYList:
			self.stemSnapHList.append(keyValue[0])
		
		self.w.getItem("horizontalTextField").set(self.stemSnapHList)
		
# ------------------------------
# ---- classless functions -----
# ------------------------------


def make_hPointsList(g):
	contoursList = []
	hPointsList = []
	for i in range(len(g)):
		pointsList = []
		for j in g[i].points:
			pointsList.append(j)
		contoursList.append(pointsList)

	for contour_index in range(len(contoursList)):
		for point_index in range(len(contoursList[contour_index])):
			currentPoint = contoursList[contour_index][point_index]
			if point_index == 0:
				prevPoint = contoursList[contour_index][len(contoursList[contour_index])-1]
			else:
				prevPoint = contoursList[contour_index][point_index-1]
			if point_index == len(contoursList[contour_index]) -1:
				nextPoint = contoursList[contour_index][0]
			else:
				nextPoint = contoursList[contour_index][point_index+1]
			
			if currentPoint.type != 'offcurve':
				directionIN = module.direction(prevPoint, currentPoint)
				directionOUT = module.direction(currentPoint, nextPoint)
				vectorIN = module.angle(prevPoint, currentPoint)
				vectorOUT = module.angle(currentPoint, nextPoint)
				
				hPoint = (currentPoint, contour_index, point_index, directionIN, directionOUT, vectorIN, vectorOUT)
				hPointsList.append(hPoint)
				
	return hPointsList
	
def getColor(point1, point2, g):
	hasSomeBlack = False
	hasSomeWhite = False
	color = ''
	
	if abs(point2.x - point1.x) < maxStemX or abs(point2.y - point1.y) < maxStemY:
		hypothLength = int(module.hypothenuse(point1, point2))
		for j in range(1, hypothLength-1):
			cp_x = point1.x + ((j)/hypothLength)*(point2.x - point1.x)
			cp_y = point1.y + ((j)/hypothLength)*(point2.y - point1.y) 
			if g.pointInside((cp_x, cp_y)):
				hasSomeBlack = True
			else:
				hasSomeWhite = True
			if hasSomeBlack and hasSomeWhite:
				break
			
	if hasSomeBlack and hasSomeWhite:	
		color = 'Gray'
	elif hasSomeBlack:
		color = 'Black'
	else:
		color = 'White'
	return color


def makeStemsList(f, g_hPoints, g, italicAngle):
	stemsListX_temp = []
	stemsListY_temp = []
	stemsListX = []
	stemsListY = []	
	for source_hPoint in range(len(g_hPoints)):
		for target_hPoint in range(len(g_hPoints)):
			sourcePoint = g_hPoints[source_hPoint][0]
			targetPoint = g_hPoints[target_hPoint][0]
			directionIn_source = g_hPoints[source_hPoint][3]
			directionOut_source = g_hPoints[source_hPoint][4]
			directionIn_target = g_hPoints[target_hPoint][3]
			directionOut_target = g_hPoints[target_hPoint][4]
			angleIn_source =  g_hPoints[source_hPoint][5]
			angleOut_source = g_hPoints[source_hPoint][6]
			angleIn_target =  g_hPoints[target_hPoint][5]
			angleOut_target = g_hPoints[target_hPoint][6]
			color = getColor(sourcePoint, targetPoint, g)
			if color == 'Black':
				c_distance = module.distance(sourcePoint, targetPoint)
				stem = (sourcePoint, targetPoint, c_distance)
				hypoth = module.hypothenuse(sourcePoint, targetPoint)
				## if Source and Target are almost aligned
				# closeAngle(angleIn_source, angleIn_target) or closeAngle(angleOut_source, angleOut_target) or 
				if module.closeAngle(angleIn_source, angleOut_target) or module.closeAngle(angleOut_source, angleIn_target):
					## if Source and Target have opposite direction
					if module.opposite(directionIn_source, directionIn_target) or module.opposite(directionIn_source, directionOut_target) or module.opposite(directionOut_source, directionIn_target):
						
						## if they are horizontal, treat the stem on the Y axis
						if (module.isHorizontal(angleIn_source) or module.isHorizontal(angleOut_source)) and (module.isHorizontal(angleIn_target) or module.isHorizontal(angleOut_target)):
							if (minStemY - 20*(minStemY/100) < c_distance[1] < maxStemY + 20*(maxStemY/100)) and (minStemY - 20*(minStemY/100) <= hypoth <= maxStemY + 20*(maxStemY/100)):
								stemsListY_temp.append(stem)
								
						## if they are vertical, treat the stem on the X axis		
						if (module.isVertical(angleIn_source) or module.isVertical(angleOut_source)) and (module.isVertical(angleIn_target) or module.isVertical(angleOut_target)):
							
							if (minStemX - 20*(minStemX/100) <= c_distance[0] <= maxStemX + 20*(maxStemX/100)) and (minStemX - 20*(minStemX/100)<= hypoth <= maxStemX + 20*(maxStemX/100)):
								stemsListX_temp.append(stem)
	# avoid duplicates, filters temporary stems
	yList = []
	for stem in stemsListY_temp:
		def pred0(y):
			return module.approxEqual(stem[0].y, y)
		def pred1(y):
			return module.approxEqual(stem[1].y, y)
		if not module.exists(yList, pred0) or not module.exists(yList, pred1):
			stemsListY.append(stem)
			yList.append(stem[0].y)
			yList.append(stem[1].y)

	xList = []
	for stem in stemsListX_temp:
		(preRot0x, preRot0y) = module.rotated(stem[0], italicAngle)
		(preRot1x, preRot1y) = module.rotated(stem[1], italicAngle)
		def pred0(x):
			#print(preRot0x, x)
			return module.approxEqual(preRot0x, x)
		def pred1(x):
			#print(preRot1x, x)
			return module.approxEqual(preRot1x, x)
		if not module.exists(xList,pred0) or not module.exists(xList,pred1):
			stemsListX.append(stem)
			xList.append(preRot0x)
			xList.append(preRot1x)
	
	return (stemsListX, stemsListY)
	
# ------------------------------
# ---- fix min and max vals ----
# ------------------------------

f = CurrentFont()
if f:
    if f.info.italicAngle != None:
    	ital = - f.info.italicAngle
    else:
    	ital = 0

    if "O" in f.keys():
    	g = f['O']
    	O_hPoints = make_hPointsList(g)
    	(O_stemsListX, O_stemsListY) = makeStemsList(f, O_hPoints, g, ital)
    	Xs = []
    	for i in O_stemsListX:
    		Xs.append(i[2][0])
    	maxX = max(Xs)
    	maxStemX = maxX + 10*(maxX/100)
    	maxStemY = maxX + 10*(maxX/100)
    else:
    	print("WARNING: glyph 'O' missing")


    if "o" in f.keys():
    	g = f['o']
    	if not g:
    		print("WARNING: glyph 'o' missing")
    	o_hPoints = make_hPointsList(g)
    	(o_stemsListX, o_stemsListY) = makeStemsList(f, o_hPoints, g, ital)
    	Ys = []
    	for i in o_stemsListY:
    		Ys.append(i[2][1])
    	minY = min(Ys)
    	minStemX = minY - 30*(minY/100)
    	minStemY = minY - 30*(minY/100)
    else:
    	print("WARNING: glyph 'o' missing")
# ------------------------------
# ------------------------------
# ------------------------------


StemAnalyzerWindow()
		