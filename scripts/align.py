# Script to align multi-lingual texts from 'extracted' folder (supposedly processed by extract.py).
# Created Date: 08 July 2015
# Modified Date: 20 July 2015
# Coded by Cong Duy Vu Hoang (vhoang2@student.unimelb.edu.au)
# Usage: [python] align.py <INPUT_FOLDER> <OUTPUT_FOLDER> <yes|no> <parallelN>

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

def ReadArticleLangInfo(fiLangPath):
	if not os.path.exists(fiLangPath): return None

	al = CLangArticleInfo()

	zf = gzip.open(fiLangPath, 'rb')
	spki = None
	#lines = zf.readlines() # it's not a good idea doing this way!
        for line in zf:
                pline = line.strip()

		#print pline

               	if pline.find('<dt>') != -1 and pline.find('</dt>') != -1:
			al.dt = RemoveHTMLtags(pline)
		if pline.find('<loc>') != -1 and pline.find('</loc>') != -1:
                        al.loc = RemoveHTMLtags(pline)
		if pline.find('<lang>') != -1 and pline.find('</lang>') != -1:
                        al.lang = RemoveHTMLtags(pline)
		if pline.find('<topic>') != -1 and pline.find('</topic>') != -1:
                        al.arrTopics.append(RemoveHTMLtags(pline))
			al.dictTopic2Spks[len(al.arrTopics) - 1] = []
		if pline.find('<name>') != -1 and pline.find('</name>') != -1:
			spki.name = RemoveHTMLtags(pline)
		if pline.find('<title>') != -1 and pline.find('</title>') != -1:
                        spki.title = RemoveHTMLtags(pline)
		if pline.find('<nlang>') != -1 and pline.find('</nlang>') != -1:
                        spki.nlang = RemoveHTMLtags(pline)
		if pline.find('<text>') != -1 and pline.find('</text>') != -1:
                        spki.texts.append(RemoveHTMLtags(pline) + '\n')
		if pline.find('<speaker>') != -1:
			spki = CSpeakerInfo()                        
		if pline.find('</speaker>') != -1:
                        al.dictTopic2Spks[len(al.arrTopics) - 1].append(spki)	
	zf.close()

	return al

def ValidateArticleInfo(dictMLI):
	errTable = {}
	
	if dictMLI[0] == None: return errTable

	global langs

	#print '*t*',

	# check no. of topics first
	numTopics = len(dictMLI[0].arrTopics)	
        for l in range(1, len(langs)):
        	if dictMLI[l] == None:
			continue
		if len(dictMLI[l].arrTopics) != numTopics:
			#print langs[l],
			errTable['t-' + langs[l]] = 0			

	#print ''

	#print '*sp*',

	# check no. of speakers for every topic
	for t in range(0, len(dictMLI[0].arrTopics)):
                numSpeakers = len(dictMLI[0].dictTopic2Spks[t])
		for l in range(1, len(langs)):
                	if dictMLI[l] == None: continue
                        if len(dictMLI[l].dictTopic2Spks[t]) != numSpeakers:
	                   	#print str(t) + '-' + langs[l],
				errTable['sp-' + str(t) + '-' + langs[l]] = 0
	#print ''

	return errTable

#----
tokenizer = 'perl /home/vhoang2/data/europarl/tools/tokenizer.perl'
sentsplitter = 'perl /home/vhoang2/data/europarl/tools/split-sentences-e.perl'
# include two steps:
# - tokenization
# - sentence splitting
def PreprocessTexts(texts, lang, th):
	if len(texts) == 0: return []

	otexts = []

	global strDTNow
	global flagUseTokenizer

	tfiFile = 'tmp/inpfile' + '-' + strDTNow + '-' + str(th) + '.txt'
	tfotkFile = 'tmp/tokenizedfile' + '-' + strDTNow + '-' + str(th) + '.txt'
	tfossFile = 'tmp/ssplittedfile' + '-' + strDTNow + '-' + str(th) + '.txt'

	tfi = open(tfiFile, 'wb')
	for text in texts:
		print >>tfi, text
	tfi.close()

	cmdline = ''

	cmdline = sentsplitter + ' -q 1 ' + '-l ' + lang + ' < ' + tfiFile + ' > ' + tfossFile	
	rval = subprocess.call(cmdline, shell=True)
        if rval != 0:
		print 'Failed (sentence splitter)!'
	else:	
		if flagUseTokenizer == True:
			cmdline = tokenizer + ' -q 1 ' + '-l ' + lang + ' < ' + tfossFile + ' > ' + tfotkFile
			rval = subprocess.call(cmdline, shell=True)
			if rval != 0:
				 print 'Failed (tokenizer)!'
			else:
				otexts = [line.strip() for line in open(tfotkFile, 'rb')]

			#os.remove(os.path.abspath(tfossFile))
		else:
			otexts = [line.strip() for line in open(tfossFile, 'rb')]

		#os.remove(os.path.abspath(tfotkFile))

	#os.remove(os.path.abspath(tfiFile))

	return otexts
#----

# To use existing translation system (e.g. Google Translate) --> expected to be slow due to the use of Google Translate
def AlignTextsAlgo1(texts1, lang1, texts2, lang2):
	# to be implemented if we encounter some problems with AlignTextsAlgo2()
	return []

# Church and Gale sentence alignment algorithm
cgsentaligner = 'perl sentence-align.perl'
def AlignTextsAlgo2(texts1, lang1, texts2, lang2, th):
	global strDTNow

	fi1 = 'tmp/sinptexts1' + '-' + strDTNow + '-' + str(th) + '.txt'
	fi2 = 'tmp/tinptexts2' + '-' + strDTNow + '-' + str(th) + '.txt' 
	fi3 = 'tmp/souttexts1' + '-' + strDTNow + '-' + str(th) + '.txt'
	fi4 = 'tmp/touttexts2' + '-' + strDTNow + '-' + str(th) + '.txt'

	tfi = open(fi1, 'wb')
        for text in texts1:
                print >>tfi, text
        tfi.close()

	tfi = open(fi2, 'wb')
        for text in texts2:
                print >>tfi, text
        tfi.close()

	otexts = []

	cmdline = cgsentaligner + ' ' + fi1 + ' ' + fi2 + ' ' + fi3 + ' ' + fi4
        rval = subprocess.call(cmdline, shell=True)
        if rval != 0:
                print 'Failed (CG text aligner)!'
        else:
                alntexts1 = [line.rstrip() for line in open(fi3, 'rb')]
		alntexts2 = [line.rstrip() for line in open(fi4, 'rb')]
		#print '***',
		flag = 0
		flag2 = 0
		prevs = ''
		prevt = ''
		for i in range(0, len(alntexts1)):
			#print '[ ', alntexts1[i]
			#rint  alntexts2[i], ' ]'
			if alntexts1[i] == '<P>':
				flag = 1

			if flag == 0: # to start a paragraph
				otexts.append('\t\t\t<p>')				
				flag = -1
				flag2 = 1
			if flag == 1: # to close a paragraph
				otexts.append('\t\t\t</p>')
				flag = 0
			if flag == -1: # within a paragraph
				#otexts.append('\t\t\t\t<s>')
				#otexts.append('\t\t\t\t\t<' + lang1 + '>' + alntexts1[i] + '</' + lang1 + '>')
				#otexts.append('\t\t\t\t\t<' + lang2 + '>' + alntexts2[i] + '</' + lang2 + '>')
				if '' != alntexts1[i] and '' != alntexts2[i]:
					if '' != prevs:
						otexts.append(prevs.lstrip() + ' ' + alntexts1[i])
						prevs = ''
					else:
						otexts.append(alntexts1[i])
					if '' != prevt:					
						otexts.append(prevt.lstrip() + ' ' + alntexts2[i])
						prevt = ''
					else:
						otexts.append(alntexts2[i])
					flag2 = 2
				else:
					if '' == alntexts1[i]:
						if flag2 == 1:
							prevt = prevt + ' ' + alntexts2[i]
						elif flag2 == 2:
							otexts[len(otexts) - 1] = otexts[len(otexts) - 1] + ' ' + alntexts2[i]
					if '' == alntexts2[i]:
                                                if flag2 == 1:
	                                                prevs = prevs + ' ' + alntexts1[i]
                                                elif flag2 == 2:
        	                                        otexts[len(otexts) - 2] = otexts[len(otexts) - 2] + ' ' + alntexts1[i]
				
				#otexts.append('\t\t\t\t</s>')
		#print '***'

	return otexts

def AlignMultilingualTexts(textsEN, l, tp, spk, dictMLI, errTable, th):
	global langs

	if ('t-' + langs[l]) in errTable: return []
        if dictMLI[l] == None: return []
        if ('sp-' + str(tp) + '-' + langs[l]) in errTable: return []

	# get alignments from texts of other languages
	speakerLANG = dictMLI[l].dictTopic2Spks[tp][spk]
	textsLANG = PreprocessTexts(speakerLANG.texts, langs[l].lower(), th)
	return AlignTextsAlgo2(textsEN, 'en', textsLANG, langs[l], th) # perform sentence alignment algorithm

def ProcessFilesWStat(locker, filesP, th, dictStats, counter):
	for fi in filesP:
		if fi.endswith(".swp"):
			print "Junk file. Ignored!"
			continue
			
		fi = fi.replace('.html', '')

		locker.acquire()
		print 'Processing date: \"' + fi + '\" ' + '(' + counter.GetValue() + ') ' + '(p' + str(th) + ')'
		counter.IncBy(1)
		locker.release()
		
		# read English first
		dictMLI = {}
		for l in range(0, len(langs)):
			fiLangPath = sys.argv[1] + '/' + 'extracted' + '/' + fi + '.' + langs[l].upper() + '.pxml.gz'
			dictMLI[l] = ReadArticleLangInfo(fiLangPath)
			#if ali != None: dictMLI[l].print2screen() # for debug only

		errTable = ValidateArticleInfo(dictMLI)
		#print errTable
		foErr = open(sys.argv[2] + '/' + fi + '.log', 'wb')
		for key in errTable.keys(): 
			print >>foErr, key
		foErr.close()

		# create output file (gzed)
		# the output file will follow the format as follows:
		'''
		<filename> (supposedly <date>.aligned.<lang1>-<lang2>.pxml.gz)
		<dt>
			<en>dt_en</en>
			<it>dt_it</it>
			...
		</dt>
		<loc>
			<en>loc_en</en>
			<it>loc_it</it>
			...
		</loc>
		
		<topic>
			<en>topic_en 1</en>
			<it>topic_it 1</it>
			...
		</topic>
		<speakers> 
			<speaker>
				<name>
					<en>name_en 1</en>
					<it>name_it 1</it>
					...
				</name>
				<title>
					<en>title_en 1</en>
					<it>title_it 1</it>
					...
				</title>
				<nlang>nlang 1</nlang>
				<text>
					<p>
						<s>	
							<en>text_en 1</en>
							<it>text_it 1</it>
						</s>
						...
					</p>
					...
				</text>			
			</speaker>
			<speaker>
				...
			</speaker>
			...
		</speakers>
		
		...

		'''

		ignored = 0		
		zfos = [None]	
		for l in range(1, len(langs)): 
			if dictMLI[l] == None: zfos.append(None); continue
			foFile = sys.argv[2] + '/' + fi + '.aligned.' + 'en-' + langs[l]  + '.pxml.gz'
			if isfile(foFile): ignored = 1; break			
			zfos.append(gzip.open(foFile, 'wb'))
			locker.acquire()
			if not ('en-' + langs[l]) in dictStats:
				dictStats['en-' + langs[l]] = CStats()
			locker.release()

		if ignored == 1: print '(Ignored!)'; continue

		for l in range(1, len(langs)):
			if dictMLI[l] == None: continue
			locker.acquire()
			dictStats['en-' + langs[l]].Inc_noArt()
			locker.release()
			zfos[l].write('<dt>\n')
			zfos[l].write('\t<en>' + dictMLI[0].dt + '</en>\n')
			zfos[l].write('\t<' + langs[l] + '>' + dictMLI[l].dt + '</' + langs[l] + '>\n')		
			zfos[l].write('</dt>\n')
			zfos[l].write('<loc>\n')
			zfos[l].write('\t<en>' + dictMLI[0].loc + '</en>\n')
			zfos[l].write('\t<' + langs[l] + '>' + dictMLI[l].loc + '</' + langs[l] + '>\n')
			zfos[l].write('</loc>\n\n')

		for t in range(0, len(dictMLI[0].arrTopics)):
			for l in range(1, len(langs)):
				if dictMLI[l] == None: continue
				if ('t-' + langs[l]) in errTable: continue
				locker.acquire()
				dictStats['en-' + langs[l]].Inc_noTopSen()
				locker.release()
				zfos[l].write('<topic>\n')
				zfos[l].write('\t<en>' + dictMLI[0].arrTopics[t] + '</en>\n')
				zfos[l].write('\t<' + langs[l] + '>' + dictMLI[l].arrTopics[t] + '</' + langs[l] + '>\n')	
				zfos[l].write('</topic>\n')
				zfos[l].write('<speakers>\n')

			for k in range(0, len(dictMLI[0].dictTopic2Spks[t])):
				 # get all English texts
				textsEN = PreprocessTexts(dictMLI[0].dictTopic2Spks[t][k].texts, 'en', th)
				for l in range(1, len(langs)):
					if dictMLI[l] == None: continue
					if ('sp-' + str(t) + '-' + langs[l]) in errTable: continue
					speaker = dictMLI[l].dictTopic2Spks[t][k]
					if speaker == None: continue
					locker.acquire()
					dictStats['en-' + langs[l]].Inc_noSpk()
					locker.release()
					zfos[l].write('\t<speaker>\n')
					zfos[l].write('\t\t<name>\n')
					zfos[l].write('\t\t\t<en>' + dictMLI[0].dictTopic2Spks[t][k].name + '</en>\n')
					zfos[l].write('\t\t\t<' + langs[l] + '>' + speaker.name + '</' + langs[l] + '>\n')
					zfos[l].write('\t\t</name>\n')
					if '' != dictMLI[0].dictTopic2Spks[t][k].title:
						zfos[l].write('\t\t<title>\n')
						zfos[l].write('\t\t\t<en>' + dictMLI[0].dictTopic2Spks[t][k].title + '</en>\n')	
						zfos[l].write('\t\t\t<' + langs[l] + '>' + speaker.title + '</' + langs[l] + '>\n')
						zfos[l].write('\t\t</title>\n')
					else:
						zfos[l].write('\t\t<title></title>\n')
					zfos[l].write('\t\t<nlang>')
					zfos[l].write(dictMLI[0].dictTopic2Spks[t][k].nlang)
					zfos[l].write('</nlang>\n')
					alntexts = AlignMultilingualTexts(textsEN, l, t, k, dictMLI, errTable, th)
					zfos[l].write('\t\t<text>\n')
					ii = 0
					while ii < len(alntexts):
						if alntexts[ii].find('<p>') == -1 and alntexts[ii].find('</p>') == -1:
							zfos[l].write('\t\t\t\t<s>\n')
							zfos[l].write('\t\t\t\t\t<' + langs[0] + '>' + alntexts[ii] + '</' + langs[0] + '>\n')
							zfos[l].write('\t\t\t\t\t<' + langs[l] + '>' + alntexts[ii + 1] + '</' + langs[l] + '>\n')
							zfos[l].write('\t\t\t\t</s>\n')
							locker.acquire()
							dictStats['en-' + langs[l]].Inc_noTotSen()
							dictStats['en-' + langs[l]].Count_Words(alntexts[ii], alntexts[ii + 1])
							locker.release()
							ii = ii + 1
						else:
							zfos[l].write(alntexts[ii] + '\n')
							if alntexts[ii].find('<p>') != -1: 
								locker.acquire()
								dictStats['en-' + langs[l]].Inc_noTotPar()
								locker.release()
						ii = ii + 1
					zfos[l].write('\t\t</text>\n')
					zfos[l].write('\t</speaker>\n')

			for l in range(1, len(langs)):
				if dictMLI[l] == None: continue
				if ('t-' + langs[l]) in errTable: continue
				zfos[l].write('</speakers>\n\n')
		
		for l in range(1, len(langs)):
			if dictMLI[l] == None: continue
			zfos[l].close()			
			locker.acquire()
			dictStats['en-' + langs[l]].Calc_noVoc()
			locker.release()

def ProcessFilesWoStat(filesP, th):
	global locker

	for fi in filesP:
		if fi.endswith(".swp"):
			print "Junk file. Ignored!"
			continue
			
		fi = fi.replace('.html', '')

		'''
		locker.acquire()
		print 'Processing date: \"' + fi + '\" ' + '(' + counter.GetValue() + ') ' + '(p' + str(th) + ')'
		counter.IncBy(1)
		locker.release()
		'''

		locker.acquire()
		print 'Processing date: \"' + fi + '\" ' + '(p' + str(th) + ')'
		if isfile(sys.argv[2] + '/' + fi + '.log'): 
			print '(ignored!)'
			locker.release()
			continue
		locker.release()

		# read English first
		dictMLI = {}
		for l in range(0, len(langs)):
			fiLangPath = sys.argv[1] + '/' + 'extracted' + '/' + fi + '.' + langs[l].upper() + '.pxml.gz'
			dictMLI[l] = ReadArticleLangInfo(fiLangPath)
			#if ali != None: dictMLI[l].print2screen() # for debug only

		errTable = ValidateArticleInfo(dictMLI)
		#print errTable
		foErr = open(sys.argv[2] + '/' + fi + '.log', 'wb')
		for key in errTable.keys(): 
			print >>foErr, key
		foErr.close()

		# create output file (gzed)
		# the output file will follow the format as follows:
		'''
		<filename> (supposedly <date>.aligned.<lang1>-<lang2>.pxml.gz)
		<dt>
			<en>dt_en</en>
			<it>dt_it</it>
		</dt>
		<loc>
			<en>loc_en</en>
			<it>loc_it</it>
		</loc>
		
		<topic>
			<en>topic_en 1</en>
			<it>topic_it 1</it>
		</topic>
		<speakers> 
			<speaker>
				<name>
					<en>name_en 1</en>
					<it>name_it 1</it>
				</name>
				<title>
					<en>title_en 1</en>
					<it>title_it 1</it>
				</title>
				<nlang>nlang 1</nlang>
				<text>
					<p>
						<s>	
							<en>text_en 1</en>
							<it>text_it 1</it>
						</s>
						...
					</p>
					...
				</text>			
			</speaker>
			<speaker>
				...
			</speaker>
			...
		</speakers>
		
		...

		'''

		#ignored = 0		
		zfos = [None]	
		for l in range(1, len(langs)): 
			if dictMLI[l] == None: zfos.append(None); continue
			foFile = sys.argv[2] + '/' + fi + '.aligned.' + 'en-' + langs[l]  + '.pxml.gz'
			#if isfile(foFile): ignored = 1; break
			#if os.path.getsize(foFile) > 0: zfos.append(None);continue # to continue previous incomplete run			
			zfos.append(gzip.open(foFile, 'wb'))
			'''
			locker.acquire()
			if not ('en-' + langs[l]) in dictStats:
				dictStats['en-' + langs[l]] = CStats()
			locker.release()
			'''

		#if ignored == 1: print '(Ignored!)'; continue

		for l in range(1, len(langs)):
			if dictMLI[l] == None: continue

			#print '(1)'

			'''
			locker.acquire()
			dictStats['en-' + langs[l]].Inc_noArt()
			locker.release()
			'''
			zfos[l].write('<dt>\n')
			zfos[l].write('\t<en>' + dictMLI[0].dt + '</en>\n')
			zfos[l].write('\t<' + langs[l] + '>' + dictMLI[l].dt + '</' + langs[l] + '>\n')		
			zfos[l].write('</dt>\n')
			zfos[l].write('<loc>\n')
			zfos[l].write('\t<en>' + dictMLI[0].loc + '</en>\n')
			zfos[l].write('\t<' + langs[l] + '>' + dictMLI[l].loc + '</' + langs[l] + '>\n')
			zfos[l].write('</loc>\n\n')

		for t in range(0, len(dictMLI[0].arrTopics)):
			for l in range(1, len(langs)):
				if dictMLI[l] == None: continue
				if ('t-' + langs[l]) in errTable: continue
				'''
				locker.acquire()
				dictStats['en-' + langs[l]].Inc_noTopSen()
				locker.release()
				'''
				zfos[l].write('<topic>\n')
				zfos[l].write('\t<en>' + dictMLI[0].arrTopics[t] + '</en>\n')
				zfos[l].write('\t<' + langs[l] + '>' + dictMLI[l].arrTopics[t] + '</' + langs[l] + '>\n')	
				zfos[l].write('</topic>\n')
				zfos[l].write('<speakers>\n')

			for k in range(0, len(dictMLI[0].dictTopic2Spks[t])):
				 # get all English texts
				textsEN = PreprocessTexts(dictMLI[0].dictTopic2Spks[t][k].texts, 'en', th)
				for l in range(1, len(langs)):
					if dictMLI[l] == None: continue
					if ('sp-' + str(t) + '-' + langs[l]) in errTable: continue
					speaker = dictMLI[l].dictTopic2Spks[t][k]
					if speaker == None: continue
					'''
					locker.acquire()
					dictStats['en-' + langs[l]].Inc_noSpk()
					locker.release()
					'''
					zfos[l].write('\t<speaker>\n')
					zfos[l].write('\t\t<name>\n')
					zfos[l].write('\t\t\t<en>' + dictMLI[0].dictTopic2Spks[t][k].name + '</en>\n')
					zfos[l].write('\t\t\t<' + langs[l] + '>' + speaker.name + '</' + langs[l] + '>\n')
					zfos[l].write('\t\t</name>\n')
					if '' != dictMLI[0].dictTopic2Spks[t][k].title:
						zfos[l].write('\t\t<title>\n')
						zfos[l].write('\t\t\t<en>' + dictMLI[0].dictTopic2Spks[t][k].title + '</en>\n')	
						zfos[l].write('\t\t\t<' + langs[l] + '>' + speaker.title + '</' + langs[l] + '>\n')
						zfos[l].write('\t\t</title>\n')
					else:
						zfos[l].write('\t\t<title></title>\n')
					zfos[l].write('\t\t<nlang>')
					zfos[l].write(dictMLI[0].dictTopic2Spks[t][k].nlang)
					zfos[l].write('</nlang>\n')
					alntexts = AlignMultilingualTexts(textsEN, l, t, k, dictMLI, errTable, th)
					zfos[l].write('\t\t<text>\n')
					ii = 0
					while ii < len(alntexts):
						if alntexts[ii].find('<p>') == -1 and alntexts[ii].find('</p>') == -1:
							zfos[l].write('\t\t\t\t<s>\n')
							zfos[l].write('\t\t\t\t\t<' + langs[0] + '>' + alntexts[ii] + '</' + langs[0] + '>\n')
							zfos[l].write('\t\t\t\t\t<' + langs[l] + '>' + alntexts[ii + 1] + '</' + langs[l] + '>\n')
							zfos[l].write('\t\t\t\t</s>\n')
							'''
							locker.acquire()
							dictStats['en-' + langs[l]].Inc_noTotSen()
							dictStats['en-' + langs[l]].Count_Words(alntexts[ii], alntexts[ii + 1])
							locker.release()
							'''
							ii = ii + 1
						else:
							zfos[l].write(alntexts[ii] + '\n')
							'''
							if alntexts[ii].find('<p>') != -1: 
								locker.acquire()
								dictStats['en-' + langs[l]].Inc_noTotPar()
								locker.release()
							'''
						ii = ii + 1
					zfos[l].write('\t\t</text>\n')
					zfos[l].write('\t</speaker>\n')

			for l in range(1, len(langs)):
				if dictMLI[l] == None: continue
				if ('t-' + langs[l]) in errTable: continue
				zfos[l].write('</speakers>\n\n')
		
		for l in range(1, len(langs)):
			if dictMLI[l] == None: continue
			zfos[l].close()
			'''
			locker.acquire()
			dictStats['en-' + langs[l]].Calc_noVoc()
			locker.release()
			'''
		
class CSpeakerInfo:
	# variables	
	#name = ''
	#title = ''
	#nlang = ''
	#texts = []	

	# functions
	def __init__(self):
		self.name = ''
		self.title = ''
		self.nlang = ''
		self.texts = []

class CLangArticleInfo:
	# variables
	#dt = ''
	#loc = ''
	#lang = ''
	#arrTopics = [] # array of topic strings
	#dictTopic2Spks = {} # hash table of topic index to speaker infos
	
	# functions
	def __init__(self):
		self.dt = ''
		self.loc = ''
		self.lang = ''
		self.arrTopics = []
		self.dictTopic2Spks = {}

	def print2screen(self):
		print self.dt
		print self.loc
		print self.lang
		#print self.arrTopics		
		print 'No. of topics: %d' % len(self.arrTopics)
		#self.dictTopic2Spks
		for key, val in self.dictTopic2Spks.iteritems():
			print key, len(val), ';',

		print ''

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

	def Calc_noVoc(self):
		self.noVoc.countS = len(self.dictSWord2Count)
		self.noVoc.countT = len(self.dictTWord2Count)

class CMyThread(threading.Thread):
	def __init__(self, threadID, locker, filesP, dictStats, counter):
        	threading.Thread.__init__(self)
        	self.threadID = threadID
        	self.locker = locker
        	self.filesP = filesP
		self.dictStats = dictStats
		self.counter = counter
		self.flag = 1

	def __init__(self, threadID, filesP):
        	threading.Thread.__init__(self)
        	self.threadID = threadID
        	self.filesP = filesP
		self.flag = 0

	def run(self):
		if self.flag == 1:
			ProcessFilesWStat(self.locker, self.filesP, self.threadID, self.dictStats, self.counter)
		elif self.flag == 0:
			ProcessFilesWoStat(self.filesP, self.threadID)

class CCounter():
	def __init__(self):
		self.count = 0

	def GetValue(self):
		return str(self.count)

	def IncBy(self, c):
		self.count = self.count + c	
        				
# to test external translators (e.g. Google Translate, Microsoft Bing Translator)
#print('*** For testing only! ***')

# Google Translate
'''
print('=== Google Translate ===')

import googletrans
gs = googletrans.Googletrans()

languages = gs.get_languages()
print(languages['de'])
print(languages['zh'])
print(languages['vi'])

print(gs.translate('hello', 'de'))
print(gs.translate('hello', 'zh'))
print(gs.translate('hello', 'vi'))

print(gs.detect('some English words'))
'''

# Microsoft Bing Translator
'''
print('=== Microsoft Bing Translator ===')
from mstranslator import Translator
translator = Translator('cdvhoang', 'HlUUMftdkETWa8E9/jzD4l1CzC8sOhRSJxH+kk0MDBg=')
print(translator.translate('hello', lang_from='en', lang_to='vi')) # this service sucks sometimes _^_!!!
'''

# to test Bleualign tool
'''
print('=== Bleualign ===')
from bleualign.align import Aligner

sourcefile = 'test-Bleualign/sourcetext.txt'
targetfile = 'test-Bleualign/targettext.txt'
srctotarget_file = 'test-Bleualign/sourcetranslation.txt'
#targettosrc_file = 'test-Bleualign/targettranslation.txt'
output_file = 'test-Bleualign/output'

options = {}
options['srcfile'] = sourcefile
options['targetfile'] = targetfile
options['srctotarget'] = srctotarget_file
#options['targettosrc'] = targettosrc_file
options['output-src'] = output_file + '-s'
options['output-target'] = output_file + '-t'
options['verbosity'] = 0

#print options

a = Aligner(options)
a.mainloop()
'''

# === MAIN FUNCTION ===
print('*** Sentence Alignment for Multilingual Europarl Data ***')
print('*** Coded by Cong Duy Vu Hoang (vhoang2@student.unimelb.edu.au) ***\n')
argc = len(sys.argv);
if argc != 4 and argc != 5:
        print 'Invalid argument!\n[python] extract.py <INPUT_FOLDER> <OUTPUT_FOLDER> <parallelN> <yes|no> \n'
        sys.exit()

#argument info
print "Argument list:"
for i in range(0, argc):
        print "arg " + str(i) + ": " + sys.argv[i]

print "OK!"

reset = 0
if argc == 5:
	if sys.argv[4] == 'yes': reset = 1
	elif sys.argv[4] == 'no': reset = 0

parallelN = int(sys.argv[3].replace('parallel', ''))

if parallelN <= 0 or parallelN > 20:
	print 'Invalid or not allowed parallelN paramater ([1;20])!\n'
	sys.exit()

import shutil
if reset == 1: 
	if os.path.exists(sys.argv[2]): shutil.rmtree(os.path.abspath(sys.argv[2]))
if not os.path.exists(sys.argv[2]): os.makedirs(sys.argv[2])
if os.path.exists(sys.argv[1] + '/tmp/'): shutil.rmtree(os.path.abspath(sys.argv[1] + '/tmp'))
if not os.path.exists(sys.argv[1] + '/tmp/'): os.makedirs(sys.argv[1] + '/tmp/')

langs = ['en', 'bg', 'es', 'da', 'de', 'et', 'el', 'fr', 'hr', 'it', 'lv', 'lt', 'hu', 'mt', 'nl', 'pl', 'pt', 'ro', 'sk', 'sl', 'fi', 'sv']

flagUseTokenizer = True # whether or not to use tokenizer

from os import listdir
from os.path import isfile, join
onlyfiles = [ f for f in listdir(sys.argv[1] + '/EN') if isfile(join(sys.argv[1] + '/EN',f)) ]

# to fix dates containing unexpected errors
#onlyfiles = ['20000704.html', '20050926.html', '20090424.html', '20100705.html', '20111213.html', '20140227.html']

'''
# test PreprocessTexts
fi = open('test-Bleualign/sourcetext.txt', 'r')
texts = fi.readlines()
fi.close()
otexts = PreprocessTexts(texts, 'en')
for text in texts: print text
exit()
'''

# to support parallel processing (for improving program's speed)
partN = len(onlyfiles) / parallelN

filesP = []
sp = 0
ep = sp
for th in range(parallelN):
	if th == parallelN - 1:
		filesP.append(onlyfiles[sp:])
	else:
		filesP.append(onlyfiles[sp:(ep + partN)])

	ep = ep + partN
	sp = ep

print "\nStart to process files in " + sys.argv[1] + '/' + 'extracted:'  #use English articles as samples
strDTNow = strftime("%Y-%m-%d-%H:%M:%S", gmtime())
dictStats = {}
counter = CCounter()

locker = Lock() # concurrency

'''
# multi-processes
processes = [Process(target=ProcessFiles, args=(locker, filesP[th], th, dictStats, count)) for th in range(parallelN)]

for p in processes:
	p.start()

for p in processes:
	p.join()
'''

# multi-threads
threads = []
for threadID in range(parallelN):
    #thread = CMyThread(threadID, locker, filesP[threadID], dictStats, counter)
    thread = CMyThread(threadID, filesP[threadID]) # don't collect statistics for faster processing
    thread.start()
    threads.append(thread)

# Wait for all threads to complete
for th in threads:
    th.join()

#--------------------------------------

print 'All threads completed!'

if counter.GetValue() > 0: print 'No. of dates processed: ', counter.GetValue()

# write dictStats to file
if len(dictStats) > 0:
	foStat = open(sys.argv[2] + '/stats.txt', 'wb')
	for key, val in dictStats.iteritems():
		print >>foStat, '***', key
		print >>foStat, 'No. of articles: ', val.noArt # no. of articles (debates)
		print >>foStat, 'No. of topic sentences: ', val.noTopSen # no. of topic sentences
		print >>foStat, 'No. of total sentences: ', val.noTotSen # no. of total sentences
		print >>foStat, 'No. of total paragraphs: ', val.noTotPar # no. of total paragraphs
		print >>foStat, 'No. of running words: ', val.noRunWords.countS, '(source) - ', val.noRunWords.countT, '(target)' # no. of running words (including punctuation)
		print >>foStat, 'Vocabulary: ', val.noVoc.countS, '(source) - ', val.noVoc.countT, '(target)' # vocabulary
		print >>foStat, 'No. of total speakers: ', val.noSpk # no. of total speakers
		print >>foStat, '-----------------------------------------\n'
	foStat.close()

shutil.rmtree(os.path.abspath(sys.argv[1] + '/tmp/'))

