# ========================================================
# Atlas textures into pages of a fixed size.
# Don Boogert 2010
# ========================================================

import os
import os.path
import fnmatch
import Image

# ========================================================
# Region class
# rectangular region in 2d space
# ========================================================

class Region:
	def __init__(self, x, y, width, height):
		self.x = x
		self.y = y
		self.width = width
		self.height = height

	def __str__(self):
		return "Region (" + str(self.x) + "," + str(self.y) + "), (" + str(self.width) + "," + str(self.height) + ")"
		 
	def CanFit(self, dimensions):
		return dimensions[0] <= self.width and dimensions[1] <= self.height
	
	def BestSplit(self, dimensions):
		if (self.CanFit(dimensions) == False):
			return 2 # no axis
			
		w = self.width - dimensions[0]
		h = self.height - dimensions[1]
		
		if (w > h):
			return Split(0, dimensions[0]);
		else:
			return Split(1, dimensions[1]);
			
	def Split(self, split):
		# split on the x-axis
		if (split.axis == 0):
			return [Region(self.x, self.y, split.distance, self.height), Region(self.x + split.distance, self.y, self.width - split.distance, self.height)]
		elif(split.axis == 1):
	 		return [Region(self.x, self.y, self.width, split.distance), Region(self.x, self.y + split.distance, self.width , self.height - split.distance)]
	
	def Area(self):
		return self.width * self.height;
		
# ========================================================					
# Split class
# location and orientation of a region split
# ========================================================

class Split:
	def __init__(self, axis, distance):
		self.axis = axis
		self.distance = distance

# ========================================================
# TextureInfo class
# size and filename of a texture in the Atlas page
# ========================================================

class TextureInfo:
	def __init__(self, textureFilename):	
		self.textureFilename = textureFilename
		im = Image.open(textureFilename)
		self.size = im.size

	def __str__(self):
		return self.textureFilename + ":" + str(self.size)

	def Area(self):
		return self.size[0] * self.size[1];

	def __lt__(self, other):
		return self.Area() < other.Area();

# ========================================================
# Node class
# Node of the Atlas Page Tree
# ========================================================

class Node:
	def __init__(self, region = None):
		self.child1 = None
		self.child2 = None
		self.region = region
		self.textureInfo = None
		
	def __str__(self):
		return str(self.region)	+ ":" + str(self.textureInfo)
		
	def IsEmpty(self):
		return self.textureInfo == None and self.child1 == None and self.child2 == None
	
			
	def AddTexture(self, textureInfo, padding):
		paddedSize = (textureInfo.size[0] + padding[0] * 2, textureInfo.size[1] + padding[1] * 2)
		
		if (paddedSize[0] == self.region.width and paddedSize[1] == self.region.height):
			self.textureInfo = textureInfo
			return
			
		bestSplit = self.region.BestSplit(paddedSize)
			
		regions = self.region.Split(bestSplit)
		
		self.child1 = Node(regions[0])
		self.child2 = Node(regions[1])
		
		if (paddedSize[0] < self.region.width and paddedSize[1] < self.region.height):
			self.child1.AddTexture(textureInfo, padding)
		else:
			self.child1.textureInfo = textureInfo
		
	def RecurseAddToFirstFound(self, textureInfo, padding):
		paddedSize = (textureInfo.size[0] + padding[0] * 2, textureInfo.size[1] + padding[1] * 2)
		
		if(self.IsEmpty() and self.region.CanFit(paddedSize)):
			self.AddTexture(textureInfo, padding)
			return True
		else:
			if (self.child1 != None and self.child1.RecurseAddToFirstFound(textureInfo, padding)):
				return True
			elif (self.child2 != None and self.child2.RecurseAddToFirstFound(textureInfo, padding)):
				return True
			else:
				return False		
		
# ========================================================		
# Page class
# Page of the atlas
# ========================================================

class Page:
	def __init__(self, width, height):
		self.root = Node(Region(0, 0, width, height))
		self.width = width
		self.height = height 
		
	def AddTexture(self, textureInfo, padding):
		return self.root.RecurseAddToFirstFound(textureInfo,padding)
	
	def WriteDebugRegion(self, img, region, padding):
		
		for x in range(padding[0], region.width -  padding[0]):
			img.putpixel((region.x + x, padding[1] + region.y), (255, 255, 255,255))
			img.putpixel((region.x + x, -padding[1] + region.y + region.height), (255, 255, 255,255))
			
			
		for y in range(padding[1], region.height -  padding[1]):
			img.putpixel((padding[0] + region.x,  region.y + y), (255, 255, 255,255))
			img.putpixel((-padding[0] + region.x + region.width, region.y + y), (255, 255, 255,255))

			
	def WriteRegion(self,img, textureRefs, padding, node):
		if(node.child1 != None and node.child2 != None):
			self.WriteRegion(img, textureRefs, padding, node.child1)
			self.WriteRegion(img, textureRefs, padding, node.child2)
		elif (node.textureInfo != None):
			im = Image.open(node.textureInfo.textureFilename)
			writePos = (node.region.x + padding[0],node.region.y + padding[1])
			img.paste(im,  writePos)
			textureRefs.append( (node.textureInfo.textureFilename, writePos, node.textureInfo.size) )
		
	def Write(self, padding, rootDir, filename):
		print "page: " + rootDir + "/" + filename
		
		img = Image.new("RGBA", (self.width, self.height))
		print img.size
		textureRefs = []
		self.WriteRegion(img, textureRefs, padding, self.root)
		
		if (rootDir != ''):
			outputFilename = rootDir + "/" + filename
		else:
			outputFilename = filename
		
		img.save(outputFilename, "PNG")
		
		xmlFilename = os.path.splitext(filename)
		f = open(rootDir + "/" + xmlFilename[0] + '.xml', 'w')
		f.write("<atlas-page img=\"" + filename + "\">\n")
		
		for textureRef in textureRefs:
			splitTextureRef = os.path.split(textureRef[0])
			splitFileNoExt = os.path.splitext(splitTextureRef[1])
			
			
			f.write("<texture filename=\"" + splitFileNoExt[0] + "\" ")
			f.write("x=\"" + str(textureRef[1][0]) + "\" ")
			f.write("y=\"" + str(textureRef[1][1]) + "\" ")
			f.write("width=\"" + str(textureRef[2][0]) + "\" ")
			f.write("height=\"" + str(textureRef[2][1]) + "\" ")
			
			f.write("/>\n")
		f.write("</atlas-page>")
		
# ==================================================		
# Recurse the folder looking for valid texture files
# ==================================================

def FindSourceTextures(searchDir):
	print "scanning for textures in " +  searchDir + " .. ";
	textures = []
	
	for root, dirs, files in os.walk(searchDir):
		for name in files:
			if fnmatch.fnmatch(name, '*.png'):
				textures.append(TextureInfo(os.path.join(root, name)))
	
	print str(len(textures)) + " found"

	return textures

# ========================================================
# Calculate Atlas layout from a list of textures
# ========================================================
	
def LayoutAtlasPages(textureList, pageWidth, pageHeight, padding):
	print "Generating atlas pages..";

	pages = []
	for textureInfo in textureList:
	
		addedToPage = False
		for page in pages:
			if (page.AddTexture(textureInfo, padding)):
				addedToPage = True
				break
		
		if(addedToPage == False):
			page = Page(pageWidth, pageHeight)
			page.AddTexture(textureInfo, padding)
			pages.append(page)
	
	print str(len(pages)) + " generated"
	return pages 

# ========================================================	
# Composite and write Atlas pages to disk
# ========================================================
	
def WriteAtlasPages(pages, padding, outputDir, baseFilename):
	i = 0
	for page in pages:
		page.Write(padding, outputDir,  baseFilename + str(i) + ".png")
		i = i + 1
	
		
# ========================================================			
# Entry point
# ========================================================

padding = (4,4)

textures = []
textures.extend(FindSourceTextures(os.getcwd()))
textures.sort(reverse=True)
	
pages = LayoutAtlasPages(textures, 1024, 1024, padding)
WriteAtlasPages(pages, padding, os.getcwd() + '', "Atlas")
