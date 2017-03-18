# crawl web data
mkdir all
cd all
nice python fetch.py &>all/fetch.log

# extract from crawled data
cd ..
nice python extract.py . extracted/ &>extracted/extract.log

# align all levels for extracted data
cd extracted
nice python align.py . aligned-polished-tok/ parallel10 yes &>aligned-polished-tok/align.log & # delete the existing files
#python align.py . aligned-polished-tok/ parallel10 no &>aligned-polished-tok/align.log & # don't delete the existing files (to be continued with previous run)
#nice python align.py . aligned-polished-tok/ parallel10 yes &>aligned-polished-tok/align.log &
#nice python align.py . aligned-polished-tok/ parallel10 no &>aligned-polished-tok/align.continued.log &
nice python align.py . aligned-polished-notok/ parallel10 yes &>aligned-polished-notok/align.log &

# correct corrupted files in aligned-polished
nice python correct.py aligned-polished-tok/ aligned-polished-tok-corrected/

# compute stats
nice python stats.py aligned-polished-notok/ aligned-polished-notok/stats.txt &>aligned-polished-notok/stats.log &
nice python stats.py aligned-polished-tok/ aligned-polished-tok/stats.txt &>aligned-polished-tok/stats.log &

# do checking stuffs, for example:
# check empty alignments
zgrep -c '<en></en>' aligned/*.en-da.*
zgrep -c '<da>/</da>' aligned/*.en-da.*
# count files
ls -l aligned-polished-notok/ | wc -l
ls -l aligned-polished-tok/ | wc -l
# validate the aligned files
zgrep -c '<en>' aligned-polished-notok/* | wc -l
zgrep -c '<en>' aligned-polished-tok/* | wc -l

# create RIE
nice python create_RIE.py aligned-polished-tok/ RIE/ tok
nice python create_RIE.py aligned-polished-notok/ RIE/ notok

