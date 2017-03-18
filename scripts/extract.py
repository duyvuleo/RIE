# Script to extract required data from 'all' folder (supposed downloaded by fetch.py).
# Created Date: 03 July 2015
# Modified Date: 10 July 2015
# Coded by Cong Duy Vu Hoang (vhoang2@student.unimelb.edu.au)
# Usage: [python] extract.py <INPUT_FOLDER> <OUTPUT_FOLDER> 

# from Python basics
import os
import sys
import re
import codecs
import subprocess
import gzip

TAG_RE = re.compile(r'<[^>]+>')
def RemoveHTMLtags(line):
	return TAG_RE.sub('', line)

def RemoveDoubleSpaces(line):
	return re.sub(' +',' ', line)

def GetLinesInFile(fiInp):
	arr = []
	
	with codecs.open(fiInp, 'r', 'utf-8') as f:
    		arr = f.readlines()

	return arr

def LookForPattern(arrLines, start, pat):
	i = -1
	for i in range(start, len(arrLines)):
		if re.search(pat, arrLines[i]):
			return i, arrLines[i]

	return (i + 1), ""

def GetSpeakerInfo(arrLines, start):
	index = start
	
	#name
	#sp = arrLines[start].find('class="doc_subtitle_level1_bis">') + len('class="doc_subtitle_level1_bis">')
	#ep = arrLines[start].find('</span>', sp)
	#name = arrLines[start][sp:ep]
	name = RemoveDoubleSpaces(RemoveHTMLtags(arrLines[start].strip()))
	if name.find("(") != -1 and name[len(name) - 1] != ')':
		name = name + ')'

	title = ""
	nlang = ""
	j = 1
	arrTmp = []
	while j < 5:
		if start + j < len(arrLines):
			sp = arrLines[start + j].replace('<span class="bold"></span>', '').find('<span class="italic">')
			if sp >= 0 and sp < 7:
				val = arrLines[start + j]
				sp = val.find('>', 2)
				ep = val.find('<', sp + 1)
				val = val[sp+1:ep].strip()
				
				fAdd = 1
				if len(arrTmp) > 0:
					if len(val) > 4:
						fAdd = 0

				if fAdd:
					arrTmp.append(val)
					index = start + j
					
		j = j + 1 

	if len(arrTmp) == 2:
		title = arrTmp[0]
		nlang = arrTmp[1]
	elif len(arrTmp) == 1:
		if arrTmp[0] != "" and arrTmp[0][len(arrTmp[0]) - 1] == ')':
			nlang = arrTmp[0]
		else:
			title = arrTmp[0]

	if nlang != "":
		sp = nlang.find('(')
		ep = nlang.find(')', sp + 1)
		nlang = nlang[sp+1:ep]

	return name.strip(), title.strip(), nlang.strip(), index

def FindContent(start, first, arrLines):
	sp = start

	# start of text
	while first == 0 and sp < len(arrLines):
		if IsPattern(arrLines[sp], '<p class="contents">'):			
			break

		sp = sp + 1

	#end of text
	while sp < len(arrLines):
		if IsPattern(arrLines[sp], '</p>'):
			break

		sp = sp + 1

	text = ""
	for r in range(start, sp + 1):
		if r < len(arrLines):
			text = text + arrLines[r].strip()
		else:
			break
			
	return text, sp + 1

def GetSpeakerTexts(i, arrLines, langID):
	arr = []

	io = i + 1
	first = 1
	while io < len(arrLines):
		cont, io = FindContent(io, first, arrLines)
		if cont != "":
			#line = '<' + langID + '>' + RemoveDoubleSpaces(RemoveHTMLtags(cont)).strip() + '</' + langID + '>'
			line = '<text>' + RemoveDoubleSpaces(RemoveHTMLtags(cont)).strip() + '</text>'
			arr.append(line)
			
			if first == 1: first = 0
		
		io = io + 1					
		if io < len(arrLines) and IsPattern(arrLines[io], '</td><td width="16">'):
			break
	
	return arr, io

def ExtractArticleInfo(langID, fi):
	countS = 0

	fiFullPath = sys.argv[1] + "/" + langID + "/" + fi
	print fiFullPath

	if not os.path.exists(fiFullPath): return 0

	# read input file
	fiFullPathLang = fiFullPath.replace('/EN/', '/' + langID + '/')
	arrLines = GetLinesInFile(fiFullPathLang)

	# create output file
	foFullPath = sys.argv[2] + "/" + fi[0:len(fi)-5] + "." + langID + ".pxml" #my personalized XML
	#fOut = codecs.open(foFullPath, 'w', 'utf-8')
	fOut = gzip.open(foFullPath + ".gz", "wb")
	
	i = 0

	#-----
	# The output file should follow the XML format as follows:
	'''
	<filename> (supposedly <date>.<lang>.pxml)
	<dt>dt</dt>
	<loc>loc</loc>
	<lang>lang</lang>

	<topic>topic 1</topic>
	<speakers> 
		<speaker>
			<name>name 1</name>
			<title>title 1</title>
			<nlang>nlang 1</nlang>
			<texts>
				<text>text 1</text>
				...
			</texts>
		</speaker>
        	<speaker>
        	<name>name 2</name>
            	<title>title 2</title>
            	<nlang>nlang 2</nlang>
            	<texts>
                	<text>text 1</text>
                	...
            	</texts>
        	</speaker>
	...
	</speakers>
	...	
	'''

	# find date and location
	# pattern: <td class="doc_title" align="left"
	i, line = LookForPattern(arrLines, i, "<td class=\"doc_title\" align=\"left\"")
	dt, loc = GetLocDt(line)
	#print dt,loc

	#write to file
	#print >>fOut, "<dt>" + dt + "</dt>"
	#print >>fOut, "<loc>" + loc + "</loc>"
	#print >>fOut, ""
	fOut.write("<dt>" + dt.encode('utf-8') + "</dt>\n")
	fOut.write("<loc>" + loc.encode('utf-8') + "</loc>\n")
	fOut.write("<lang>" + langID + "</lang>\n")
	fOut.write("\n")
	
	# find topics	
	while i < len(arrLines):
		# find topic 1
		# pattern: <table ...  class="doc_title">
		i, line = LookForPattern(arrLines, i, "<table (.)+ class=\"doc_title\"")
		topic = GetTopic(line)
		#print topic
		
		i = i + 1

		# look for speakers and their multi-lingual infos
		#write to file
		#print >>fOut, "<topic>" + topic + "</topic>"
		#print >>fOut, "<speakers>"
		fOut.write("<topic>" + topic.encode('utf-8') + "</topic>\n")
		fOut.write("<speakers>\n")
		
		nlang = ""
		title = ""
		name = ""
		while i < len(arrLines):
			if IsPattern(arrLines[i], "class=\"doc_subtitle_level1_bis\""):
				#print arrLines[i]
				name, title, nlang, i = GetSpeakerInfo(arrLines, i) #name, title, nlang

				arrTrans = []
				arrTrans, i = GetSpeakerTexts(i, arrLines, langID)

				#write to file
				#print >>fOut, "\t<speaker>"
				#print >>fOut, "\t\t<name>" + name + "</name>"
				#print >>fOut, "\t\t<title>" + title + "</title>"
				#print >>fOut, "\t\t<nlang>" + nlang + "</nlang>"
				#print >>fOut, "\t\t<texts>"
				fOut.write("\t<speaker>\n")
				fOut.write("\t\t<name>" + name.encode('utf-8') + "</name>\n")
				fOut.write("\t\t<title>" + title.encode('utf-8') + "</title>\n")
				fOut.write("\t\t<nlang>" + nlang.encode('utf-8') + "</nlang>\n")
				fOut.write("\t\t<texts>\n")				
				for j in range(0, len(arrTrans)):
					#print >>fOut, "\t\t\t" + arrTrans[j]
					fOut.write("\t\t\t" + arrTrans[j].encode('utf-8') + "\n")
				#print >>fOut, "\t\t</texts>"
				#print >>fOut, "\t</speaker>"
				fOut.write("\t\t</texts>\n")
				fOut.write("\t</speaker>\n")

				countS = countS + len(arrTrans)

			i = i + 1
						
			if i < len(arrLines) and IsPattern(arrLines[i], "<table (.)+ class=\"doc_title\""):
				break

		#write to file
		#print >>fOut, "</speakers>"
		#print >>fOut, ""
		fOut.write("</speakers>\n")
		fOut.write("\n")

	#-----

	fOut.close()

	#subprocess.check_call(['gzip', foFullPath]) #stupid gzip

	return countS

def IsPattern(line, pat):
	return re.search(pat, line)

def GetLocDt(line):
	#sp = line.find('<td')
	#sp = line.find('>', sp + 3)
	#ep = line.find('<', sp + 1)

	#tokens = line[sp+1:ep].split("-")
	nline = RemoveDoubleSpaces(RemoveHTMLtags(line.strip()))
	pc = nline.rfind('-')
	tokens = []
	tokens.append(nline[0:pc-1])
	tokens.append(nline[pc+2:])

	if len(tokens) == 2:
		return tokens[0], tokens[1]

	return "", ""

def GetTopic(line):
	#sp = line.find('class=\"doc_title\">')
	#sp = line.find('/>', sp + 2)
	#ep = line.find('</td>', sp + 1)

	#return line[sp+3:ep]
	return RemoveDoubleSpaces(RemoveHTMLtags(line.strip()))

langs = ['EN', 'BG', 'ES', 'DA', 'DE', 'ET', 'EL', 'FR', 'HR', 'IT', 'LV', 'LT', 'HU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SL', 'FI', 'SV']

argc = len(sys.argv);
if argc != 3:
	print "Invalid argument!\n[python] extract.py <INPUT_FOLDER>> <OUTPUT_FOLDER>\n"
	sys.exit()

#argument info
print "Argument list:"
for i in range(0, argc):
	print "arg " + str(i) + ": " + sys.argv[i]

print "OK!"

import shutil
if os.path.exists(sys.argv[2]): shutil.rmtree(os.path.abspath(sys.argv[2]))
if not os.path.exists(sys.argv[2]): os.makedirs(sys.argv[2])

from os import listdir
from os.path import isfile, join
onlyfiles = [ f for f in listdir(sys.argv[1] + "/" + langs[0]) if isfile(join(sys.argv[1] + "/" + langs[0],f)) ]

print "\nStart to process files in " + sys.argv[1] + "\EN" #use English articles as samples
count = 0
arrGenCounts = []
for i in range(0, len(langs)): arrGenCounts.append(0)
for fi in onlyfiles:	

	if fi.endswith(".swp"):
		print "Junk file. Ignored!"
		continue
		
	print "Processing file: \"" + fi + "\""

	# look for articles in all languages (incl. English)
	for l in range(0, len(langs)):
		arrGenCounts[l] = arrGenCounts[l] + ExtractArticleInfo(langs[l], fi)
	
	count = count + 1 #count no. of English articles only

	# for debug only
	#if count == 100:
	#	break

print "-----------------------------------\nNo. of articles processed: %d" % count
foStat = open(sys.argv[2] + "/" + "langs.stat", "w")
print >>foStat, "Estimated no. of sentences for each language:"
for l in range(0, len(langs)):
	print >>foStat, langs[l] + "\t" + str(arrGenCounts[l])
foStat.close()

