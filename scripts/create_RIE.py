# from Python basics
import os
import sys
import re
import codecs
import subprocess
import gzip
from datetime import datetime, timedelta
from os import listdir
from os.path import isfile, join
import shutil

TAG_RE = re.compile(r'<[^>]+>')
def RemoveHTMLtags(line):
        return TAG_RE.sub('', line)

def Preprocess(line):
	line = RemoveHTMLtags(line)
	line = line.replace('\t', '')

	#others (maybe)

	return line
	

# === MAIN FUNCTION ===
print('*** Script to create RIE corpus ***')
print('*** Coded by Cong Duy Vu Hoang (vhoang2@student.unimelb.edu.au) ***\n')
argc = len(sys.argv);
if argc != 4:
        print 'Invalid argument!\n[python] create_RIE.py <INPUT_FOLDER> <OUTPUT_FOLDER> <SUFFIX>\n'
        sys.exit()

#argument info
print "Argument list:"
for i in range(0, argc):
        print "arg " + str(i) + ": " + sys.argv[i]

print "OK!\n"

if not os.path.exists(sys.argv[2] + '/train'):
    os.makedirs(sys.argv[2] + '/train')
if not os.path.exists(sys.argv[2] + '/train' + '/files-' + sys.argv[3]):
    os.makedirs(sys.argv[2] + '/train' + '/files-' + sys.argv[3])
if not os.path.exists(sys.argv[2] + '/dev'):
    os.makedirs(sys.argv[2] + '/dev')
if not os.path.exists(sys.argv[2] + '/dev' + '/files-' + sys.argv[3]):
    os.makedirs(sys.argv[2] + '/dev' + '/files-' + sys.argv[3])
if not os.path.exists(sys.argv[2] + '/test'):
    os.makedirs(sys.argv[2] + '/test')
if not os.path.exists(sys.argv[2] + '/test' + '/files-' + sys.argv[3]):
    os.makedirs(sys.argv[2] + '/test' + '/files-' + sys.argv[3])

# list all files in sys.argv[1]
onlyfiles = [ f for f in listdir(sys.argv[1]) if isfile(join(sys.argv[1],f)) ]

fsraw = ['train/train.raw.' + sys.argv[3],'dev/dev.raw.' + sys.argv[3],'test/test.raw.' + sys.argv[3]]
fwstu = ['train/train.stu.' + sys.argv[3],'dev/dev.stu.' + sys.argv[3],'test/test.stu.' + sys.argv[3]]
rawfiles = {}

counter = 0
filecounts = [0,0,0]
sentcounts = [0,0,0]
for f in onlyfiles:
	pf = sys.argv[1] + '/' + f

	#check date
	if f.endswith('.gz'):
		toks = f.split('.')
		
		d = toks[0] #date
		l = toks[2] #language pair
		ltoks = l.split('-')

		dc = datetime.strptime(d, '%Y%m%d')	
		flag = 0
		if dc >= datetime.strptime('19990720', '%Y%m%d') and dc <= datetime.strptime('20091217', '%Y%m%d'):#train
			shutil.copy(pf, sys.argv[2] + '/' + 'train/' + 'files-' + sys.argv[3] + '/' + f)
			filecounts[0] = filecounts[0] + 1
			flag = 1
		elif dc >= datetime.strptime('20100118', '%Y%m%d') and dc <= datetime.strptime('20101216', '%Y%m%d'):#dev
			shutil.copy(pf, sys.argv[2] + '/' + 'dev/' + 'files-' + sys.argv[3] + '/' + f)
			filecounts[1] = filecounts[1] + 1
			flag = 2
		elif dc >= datetime.strptime('20110117', '%Y%m%d') and dc <= datetime.strptime('20110623', '%Y%m%d'):#test
			shutil.copy(pf, sys.argv[2] + '/' + 'test/' + 'files-' + sys.argv[3] + '/' + f)
			filecounts[2] = filecounts[2] + 1		
			flag = 3

		#create files here
		if flag == 0: continue

		if not (str(flag) + '-raw-' + l in rawfiles):
			rawfiles[str(flag) + '-raw-' + l] = gzip.open(sys.argv[2] + '/' + fsraw[int(flag) - 1] + '.' + l + '.gz', 'wb')

		if not (str(flag) + '-stu-' + l in rawfiles):
			rawfiles[str(flag) + '-stu-' + l] = gzip.open(sys.argv[2] + '/' + fwstu[int(flag) - 1] + '.' + l + '.gz', 'wb')

		#process content of file
		zf = gzip.open(pf, 'rb')
		fstu = 0	
		for line in zf:
			if line.strip() == '': continue

			#------------------------------------------
			#write necessary lines of texts to raw file			
			fw = False
			if line.find('\t\t\t\t\t') == 0: fw = True

			'''						
			if (line.find('<' + ltoks[0] + '>') != -1 and line.find('</' + ltoks[0] + '>') != -1):
				fw = True
			if (line.find('<' + ltoks[1] + '>') != -1 and line.find('</' + ltoks[1] + '>') != -1):
				fw = True
			'''
			
			if fw:
				rawfiles[str(flag) + '-raw-' + l].write(Preprocess(line))
			#------------------------------------------

			#------------------------------------------
			#write to structural file
			if line.find('<dt>') == 0 or line.find('</dt>') == 0:
				fstu = 1
				continue
			elif line.find('<loc>') == 0 or line.find('</loc>') == 0:
				fstu = 2
				continue
			elif line.find('<topic>') == 0 or line.find('</topic>') == 0:
				fstu = 3
				continue
			elif line.find('<speakers>') == 0:
				fstu = 4
				continue
			elif line.find('<speaker>') != -1 or line.find('</speaker>') != -1:
				fstu = 5
				continue
			elif line.find('<name>') != -1 or line.find('</name>') != -1:
				fstu = 6
				continue
			elif line.find('<title>') != -1 and line.find('</title>') != -1:
				fstu = 7
			elif line.find('<title>') != -1 or line.find('</title>') != -1:
				fstu = 8
				continue
			elif line.find('<nlang>') != -1 and line.find('</nlang>') != -1:
				fstu = 9
			elif line.find('<text>') != -1 or line.find('</text>') != -1:
				fstu = 0
				continue
			elif line.find('<p>') != -1:
				if fstu != 11: p = 0
				fstu = 10
				continue
			elif line.find('</p>') != -1:
				fstu = 11
				p = p + 1
				continue
			elif line.find('<s>') != -1 or line.find('</s>') != -1:
				fstu = 12
				continue
			elif line.find('</speakers>') == 0:
				continue

			if fstu == 1:		
				lang = line[line.find('<') + 1:line.find('>')]		
				if lang == ltoks[0]:
					rawfiles[str(flag) + '-stu-' + l].write('===\n')
					rawfiles[str(flag) + '-stu-' + l].write('DT' + ' ' + Preprocess(line).strip() + ' ||| ')
				elif lang == ltoks[1]:
					rawfiles[str(flag) + '-stu-' + l].write(Preprocess(line))
			
			if fstu == 2:
				lang = line[line.find('<') + 1:line.find('>')]		
				if lang == ltoks[0]:
					rawfiles[str(flag) + '-stu-' + l].write('LOC' + ' ' + Preprocess(line).strip() + ' ||| ')
				elif lang == ltoks[1]:
					rawfiles[str(flag) + '-stu-' + l].write(Preprocess(line))
				
			if fstu == 3:
				lang = line[line.find('<') + 1:line.find('>')]		
				if lang == ltoks[0]:
					rawfiles[str(flag) + '-stu-' + l].write('TOC' + ' ' + Preprocess(line).strip() + ' ||| ')
				elif lang == ltoks[1]:
					rawfiles[str(flag) + '-stu-' + l].write(Preprocess(line))

			if fstu == 6:
				lang = line[line.find('<') + 1:line.find('>')]		
				if lang == ltoks[0]:
					rawfiles[str(flag) + '-stu-' + l].write('SPK' + ' ' + Preprocess(line).strip() + ' ||| ')
				elif lang == ltoks[1]:
					rawfiles[str(flag) + '-stu-' + l].write(Preprocess(line).strip() + ' ||| ')
			if fstu == 7 or fstu == 8:
				title = Preprocess(line).strip()
				if title == '':
					rawfiles[str(flag) + '-stu-' + l].write('* ||| ')
				else:
					rawfiles[str(flag) + '-stu-' + l].write(title + ' ||| ')	
			if fstu == 9:
				nlang = Preprocess(line).strip()
				if nlang == '':
					rawfiles[str(flag) + '-stu-' + l].write('*\n')
				else:
					rawfiles[str(flag) + '-stu-' + l].write(nlang + '\n')
			
			if fstu == 12:
				lang = line[line.find('<') + 1:line.find('>')]	
				if lang == ltoks[0]:
					rawfiles[str(flag) + '-stu-' + l].write('SENT ' + str(p) + ' ' + Preprocess(line).strip() + ' ||| ')
				elif lang == ltoks[1]:
					rawfiles[str(flag) + '-stu-' + l].write(Preprocess(line))
				sentcounts[int(flag) - 1] = sentcounts[int(flag) - 1] + 1 											
			
			#------------------------------------------

		zf.close()

	counter = counter + 1

	sys.stdout.write('\r')
   	sys.stdout.write("processed files %d" % counter)
    	sys.stdout.flush()

	#if counter == 50: break #for debug only

for ffk, ffv in rawfiles.iteritems():
	ffv.close()

#statistics
print '\nSome basic stats stuffs:'
print 'no. of files in train: ' + str(filecounts[0])
print 'no. of sent pairs in train: ' + str(sentcounts[0])
print 'no. of files in dev: ' + str(filecounts[1])
print 'no. of sent pairs in dev: ' + str(sentcounts[1])
print 'no. of files in test: ' + str(filecounts[2])
print 'no. of sent pairs in test: ' + str(sentcounts[2])

