import DefaultTable
import sstruct
from fontTools.misc.textTools import safeEval

maxpFormat_0_5 = """
		>	# big endian
		tableVersion:			i
		numGlyphs:				H
"""

maxpFormat_1_0_add = """
		>	# big endian
		maxPoints:				H
		maxContours:			H
		maxCompositePoints:		H
		maxCompositeContours:	H
		maxZones:				H
		maxTwilightPoints:		H
		maxStorage:				H
		maxFunctionDefs:		H
		maxInstructionDefs:		H
		maxStackElements:		H
		maxSizeOfInstructions:	H
		maxComponentElements:	H
		maxComponentDepth:		H
"""


class table__m_a_x_p(DefaultTable.DefaultTable):
	
	dependencies = ['glyf']
	
	def decompile(self, data, ttFont):
		dummy, data = sstruct.unpack2(maxpFormat_0_5, data, self)
		self.numGlyphs = int(self.numGlyphs)
		if self.tableVersion == 0x00010000:
			dummy, data = sstruct.unpack2(maxpFormat_1_0_add, data, self)
		else:
			assert self.tableVersion == 0x00005000, "unknown 'maxp' format: %x" % self.tableVersion
		assert len(data) == 0
	
	def compile(self, ttFont):
		if ttFont.has_key('glyf'):
			if ttFont.isLoaded('glyf') and ttFont.recalcBBoxes:
				self.recalc(ttFont)
		else:
			pass # XXX CFF!!!
		data = sstruct.pack(maxpFormat_0_5, self)
		if self.tableVersion == 0x00010000:
			data = data + sstruct.pack(maxpFormat_1_0_add, self)
		else:
			assert self.tableVersion == 0x00005000, "unknown 'maxp' format: %f" % self.tableVersion
		return data
	
	def recalc(self, ttFont):
		"""Recalculate the font bounding box, and most other maxp values except
		for the TT instructions values. Also recalculate the value of bit 1
		of the flags field of the 'head' table.
		"""
		glyfTable = ttFont['glyf']
		hmtxTable = ttFont['hmtx']
		headTable = ttFont['head']
		self.numGlyphs = len(glyfTable)
		xMin = 100000
		yMin = 100000
		xMax = -100000
		yMax = -100000
		maxPoints = 0
		maxContours = 0
		maxCompositePoints = 0
		maxCompositeContours = 0
		maxComponentElements = 0
		maxComponentDepth = 0
		allXMaxIsLsb = 1
		for glyphName in ttFont.getGlyphOrder():
			g = glyfTable[glyphName]
			if g.numberOfContours:
				if hmtxTable[glyphName][1] <> g.xMin:
					allXMaxIsLsb = 0
				xMin = min(xMin, g.xMin)
				yMin = min(yMin, g.yMin)
				xMax = max(xMax, g.xMax)
				yMax = max(yMax, g.yMax)
				if g.numberOfContours > 0:
					nPoints, nContours = g.getMaxpValues()
					maxPoints = max(maxPoints, nPoints)
					maxContours = max(maxContours, nContours)
				else:
					nPoints, nContours, componentDepth = g.getCompositeMaxpValues(glyfTable)
					maxCompositePoints = max(maxCompositePoints, nPoints)
					maxCompositeContours = max(maxCompositeContours, nContours)
					maxComponentElements = max(maxComponentElements, len(g.components))
					maxComponentDepth = max(maxComponentDepth, componentDepth)
		self.xMin = xMin
		self.yMin = yMin
		self.xMax = xMax
		self.yMax = yMax
		self.maxPoints = maxPoints
		self.maxContours = maxContours
		self.maxCompositePoints = maxCompositePoints
		self.maxCompositeContours = maxCompositeContours
		self.maxComponentDepth = maxComponentDepth
		if allXMaxIsLsb:
			headTable.flags = headTable.flags | 0x2
		else:
			headTable.flags = headTable.flags & ~0x2
	
	def testrepr(self):
		items = self.__dict__.items()
		items.sort()
		print ". . . . . . . . ."
		for combo in items:
			print "  %s: %s" % combo
		print ". . . . . . . . ."
	
	def toXML(self, writer, ttFont):
		if self.tableVersion <> 0x00005000:
			writer.comment("Most of this table will be recalculated by the compiler")
			writer.newline()
		formatstring, names, fixes = sstruct.getformat(maxpFormat_0_5)
		if self.tableVersion == 0x00010000:
			formatstring, names_1_0, fixes = sstruct.getformat(maxpFormat_1_0_add)
			names = names + names_1_0
		else:
			assert self.tableVersion == 0x00005000, "unknown 'maxp' format: %f" % self.tableVersion
		for name in names:
			value = getattr(self, name)
			if type(value) == type(0L):
				value=int(value)
			if name == "tableVersion":
				value = hex(value)
			writer.simpletag(name, value=value)
			writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		setattr(self, name, safeEval(attrs["value"]))
		
