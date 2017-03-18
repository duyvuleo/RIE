# Script to collect statistics of desired aligned data (supposedly processed by align.py).
# Created Date: 30 July 2015
# Modified Date: 
# Coded by Cong Duy Vu Hoang (vhoang2@student.unimelb.edu.au)
# Usage: [python] stats.py <INPUT_FOLDER> <OUTPUT_FILE>

# from Python basics
import os
import sys
import re
import codecs
import subprocess
import gzip
from time import gmtime, strftime
from multiprocessing import Process, Lock # for parallel programming
import threading # for multi-threading programming

TAG_RE = re.compile(r'<[^>]+>')
def RemoveHTMLtags(line):
        return TAG_RE.sub('', line)

class CWordCount:
	def __init__(self):
		self.countS = 0
		self.countT = 0

	def Inc_countS(self, c):
		self.countS = self.countS + c
	
	def Inc_countT(self, c):
		self.countT = self.countT + c

class CStats:
	def __init__(self):
		self.noArt = 0 # no. of articles (debates)
		self.noTopSen = 0 # no. of topic sentences
		self.noTotSen = 0 # no. of total sentences
		self.noTotPar = 0 # no. of total paragraphs
		self.noRunWords = CWordCount() # no. of running words (including punctuation)
		self.noVoc = CWordCount() # vocabulary
		self.noSpk = 0 # no. of total speakers
		self.dictSWord2Count = {}
		self.dictTWord2Count = {}

	def Inc_noArt(self):
		self.noArt = self.noArt + 1
	
	def Inc_noTopSen(self):
		self.noTopSen = self.noTopSen + 1
	
	def Inc_noTotSen(self):
		self.noTotSen = self.noTotSen + 1

	def Inc_noSpk(self):
		self.noSpk = self.noSpk + 1

	def Inc_noTotPar(self):
		self.noTotPar = self.noTotPar + 1
	
	def Count_Words(self, src, trg):
		# do something here
		words_src = src.split(' ')
		words_trg = trg.split(' ')

		self.noRunWords.Inc_countS(len(words_src))
		self.noRunWords.Inc_countT(len(words_trg))

		for sword in words_src:
			if sword in self.dictSWord2Count:
				self.dictSWord2Count[sword] = self.dictSWord2Count[sword] + 1
			else:
				self.dictSWord2Count[sword] = 1

		for tword in words_trg:
                        if tword in self.dictTWord2Count:
                                self.dictTWord2Count[tword] = self.dictTWord2Count[tword] + 1
                        else:
                                self.dictTWord2Count[tword] = 1

	def Count_Words_Src(self, src):
		words_src = src.split(' ')

		self.noRunWords.Inc_countS(len(words_src))

		for sword in words_src:
			if sword in self.dictSWord2Count:
				self.dictSWord2Count[sword] = self.dictSWord2Count[sword] + 1
			else:
				self.dictSWord2Count[sword] = 1

	def Count_Words_Trg(self, trg):
		words_trg = trg.split(' ')

		self.noRunWords.Inc_countT(len(words_trg))

		for tword in words_trg:
                        if tword in self.dictTWord2Count:
                                self.dictTWord2Count[tword] = self.dictTWord2Count[tword] + 1
                        else:
                                self.dictTWord2Count[tword] = 1

	def Calc_noVoc(self):
		self.noVoc.countS = len(self.dictSWord2Count)
		self.noVoc.countT = len(self.dictTWord2Count)

# === MAIN FUNCTION ===
print('*** Coded by Cong Duy Vu Hoang (vhoang2@student.unimelb.edu.au) ***\n')
argc = len(sys.argv);
if argc != 3:
        print 'Invalid argument!\n[python] stats.py <INPUT_FOLDER> <OUTPUT_FILE> \n'
        sys.exit()

#argument info
print "Argument list:"
for i in range(0, argc):
        print "arg " + str(i) + ": " + sys.argv[i]

print "OK!\n"

from os import listdir
from os.path import isfile, join
onlyfiles = [ f for f in listdir(sys.argv[1]) if isfile(join(sys.argv[1],f)) ]

dictStats = {}
count = 0
for fi in onlyfiles:
	fiPath = sys.argv[1] + '/' + fi

	if fi.endswith('.log'): continue

	print fi
	
	# parse fi
	toks = fi.split('.')
	
	# this should not happen anyway!	
	if len(toks) != 5: continue

	if not (toks[2]) in dictStats:
		dictStats[toks[2]] = CStats()

	langs = toks[2].split('-')

	dictStats[toks[2]].Inc_noArt()

	flag = 0	
	zfi = gzip.open(fiPath, 'rb')
	for line in zfi:
		sline = line.strip()

		if sline.find('<dt>') != -1:
			flag = 1 # do nothing
		elif sline.find('<topic>') != -1:
			flag = 2
		elif sline.find('<name>') != -1:
			flag = 3
		elif sline.find('<p>') != -1:
			flag = 4
		elif sline.find('<en>') != -1:
			flag = 5 
		else: flag = 0
		
		if flag == 2: dictStats[toks[2]].Inc_noTopSen()
		if flag == 3: dictStats[toks[2]].Inc_noSpk()
		if flag == 4: dictStats[toks[2]].Inc_noTotPar()
		if flag == 5: dictStats[toks[2]].Inc_noTotSen()

		if sline.find('<' + langs[0] + '>') != -1: # and sline.find('</' + langs[0] + '>') != -1:			
			dictStats[toks[2]].Count_Words_Src(RemoveHTMLtags(sline).replace('\t', ''))

		if sline.find('<' + langs[1] + '>') != -1: # and sline.find('</' + langs[1] + '>') != -1:
			dictStats[toks[2]].Count_Words_Trg(RemoveHTMLtags(sline).replace('\t', ''))				
	zfi.close()

	count = count + 1

# write dictStats to file
if len(dictStats) > 0:
	foStat = open(sys.argv[2], 'wb')
	for key, val in dictStats.iteritems():
		dictStats[key].Calc_noVoc()
		print >>foStat, '*** Language pair: ', key
		print >>foStat, 'No. of articles: ', val.noArt # no. of articles (debates)
		print >>foStat, 'No. of topic sentences: ', val.noTopSen # no. of topic sentences
		print >>foStat, 'No. of total sentence pairs: ', val.noTotSen # no. of total sentences
		print >>foStat, 'No. of total paragraphs: ', val.noTotPar # no. of total paragraphs
		print >>foStat, 'No. of running words: ', val.noRunWords.countS, '(source) - ', val.noRunWords.countT, '(target)' # no. of running words (including punctuation)
		print >>foStat, 'Vocabulary: ', val.noVoc.countS, '(source) - ', val.noVoc.countT, '(target)' # vocabulary
		print >>foStat, 'No. of total speakers: ', val.noSpk # no. of total speakers
		print >>foStat, '-----------------------------------------\n'
	foStat.close()

print '\nNo. of files processed: ' + str(count)

