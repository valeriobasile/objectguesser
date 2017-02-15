#!/usr/bin/env python

from nltk.corpus import wordnet
import sys

#offsets_dict = {s.offset(): s for s in wordnet.all_synsets()}

dbp2bn = dict()
bn2dbp = dict()
with open('resources/bn-dbpedia') as f:
	for line in f:
		bn, dbp = line.rstrip().split(' ')
		dbp2bn[dbp]=bn
		bn2dbp[bn]=dbp

bn2wn = dict()
wn2bn = dict()
with open('resources/bn35-wn31.map') as f:
	for line in f:
		bn, wn, offset = line.rstrip().split(' ')
		if not bn in bn2wn:
			bn2wn[bn]=[wn.lower()]
		else:
			bn2wn[bn].append(wn.lower())

		if not wn in wn2bn:
			wn2bn[wn.lower()]=[bn]
		else:
			wn2bn[wn.lower()].append(bn)

def dbp2synset(dbpedia_id):
	try:
		bn_id =  dbp2bn[dbpedia_id]
		wn_ids = bn2wn[bn_id]
		synsets = []
		for wn_id in wn_ids:
			elements = wn_id.split('-')
			pos = elements[-1]
			sensepos = elements[-2]
			lemma = '-'.join(elements[:-2])
			lemma = lemma.replace('+', '_')
			sense = eval(sensepos.split('#')[1]) - 1
			synsets.append(wordnet.synsets(lemma, pos=pos)[sense])
		synset = synsets[0]
		return synset
	except:
		sys.stderr.write("Mapping error: {0} not found\n".format(dbpedia_id))
		return None

synset_prediction = dbp2synset(sys.argv[1])
synset_ground_truth = dbp2synset(sys.argv[2])

if synset_prediction and synset_ground_truth:
	print synset_prediction.wup_similarity(synset_ground_truth)
else:
	print -1.0
