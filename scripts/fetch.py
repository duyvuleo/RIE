from datetime import datetime, timedelta
import os
import subprocess

#start = datetime.strptime('20 July 1999', '%d %B %Y')
start = datetime.strptime('01 November 1993', '%d %B %Y')#date founded
#start = datetime.strptime('22 April 2009', '%d %B %Y')
now = datetime.now()

langs = ['EN', 'BG', 'ES', 'DA', 'DE', 'ET', 'EL', 'FR', 'HR', 'IT', 'LV', 'LT', 'HU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SL', 'FI', 'SV']

for lang in langs:
    if not os.path.exists(lang):
        os.mkdir(lang)

while start <= now:
    date = start.strftime('%Y%m%d')
    print date
    start = start + timedelta(days=1)

    for lang in langs:
        url = 'http://www.europarl.europa.eu/sides/getDoc.do?pubRef=-//EP//TEXT+CRE+%s+ITEMS+DOC+XML+V0//%s' % (date, lang)
        outfile = '%s/%s.html' % (lang, date)
        if not os.path.exists(outfile):
            cmdline = 'wget -q -O %s %s' % (outfile, url)
            rval = subprocess.call(cmdline, shell=True)
            if rval != 0:
                print date, lang, 'failed (wget): cleaning up'
                break

            # need to search for 
            pipe = subprocess.Popen('grep "Application error" %s' % outfile, shell=True, stdout=subprocess.PIPE)
            lines = pipe.stdout.readlines()
            if lines:
                print date, lang, 'failed (url): cleaning up'
                os.unlink(outfile)
                pipe.wait()
                del pipe
                if lang == 'EN':
                    break
            else:
                print date, lang, 'success'
                pipe.wait()
                del pipe

    #break	
