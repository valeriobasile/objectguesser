#!/usr/bin/env python

import web
import logging as log
import json
import operator
import math

log.basicConfig(filename='log/server.log',level=log.INFO)

urls = (
        '/guess', 'guess',
)

app = web.application(urls, globals())


def cosine_similarity(v1,v2):
    "compute cosine similarity of v1 to v2: (v1 dot v2)/{||v1||*||v2||)"
    sumxx, sumxy, sumyy = 0, 0, 0
    for i in range(len(v1)):
        x = v1[i]; y = v2[i]
        sumxx += x*x
        sumyy += y*y
        sumxy += x*y
    return sumxy/math.sqrt(sumxx*sumyy)

def median(lst):
    sortedLst = sorted(lst)
    lstLen = len(lst)
    index = (lstLen - 1) // 2

    if (lstLen % 2):
        return sortedLst[index]
    else:
        return (sortedLst[index] + sortedLst[index + 1])/2.0

def hmean(lst):
    return len(lst) / sum(1. / val for val in lst)

def parse_query(data, vicinity):
    query = json.loads(data)

    distances = ["near_{0}".format(x) for x in range(vicinity+1)]

    query_objects = query['local_objects']
    #query_objects.append([query["context_room_label"],1,"","near_0"])
    #query_objects.append([query["context_surface_label"],1,"","near_0"])
    # fix missing objects
    objects = filter(lambda x: x[0] in vectors['tools'], query_objects)

    # filter for distance
    objects = filter(lambda x: x[3] in distances, objects)

    query_cooccurrences = query['co_occurrences']
    cooccurrences = filter(lambda x: x[0] in vectors['tools'], query_cooccurrences)
    cooccurrences = filter(lambda x: x[2] in distances, cooccurrences)

    labels = map(lambda x: x[0], objects)

    room = query['context_room_label']
    surface = query['context_surface_label']

    return objects, labels, cooccurrences, room, surface

def relatedness(o, objects, method):
    if o in objects:
        return 0

    m = map(lambda x: cosine_similarity(vectors['tools'][o], vectors['tools'][x]), objects)
    #m = [((1.0-weights)*i)+(weights*frequencies[o]) for i in m]

    print o
    print objects
    print m
    if len(m)>1:
        if method == 'prod':
            return reduce(lambda x,y:x*y, m)
        elif method == 'median':
            return 1.0 - median(m)
        elif method == 'harm':
            return 1.0 - hmean(m)
        elif method == 'avg':
            return sum(m)/float(len(m))
        else: # default is max
            return max(m)
    else:
        return 0.0

# read NASARI vectors
vectors = dict()
frequencies = dict()
for cat in ['tools', 'rooms', 'furniture']:
    log.info('reading vectors')
    vectors[cat] = dict()
    with open('vectors/{0}_vectors.txt'.format(cat)) as f:
        for line in f:
            fields = line.rstrip().split(' ')
            label = fields[1]
            coordinates = map(eval, fields[2:])
            vectors[cat][label] = coordinates

    # read objects frequencies
    log.info('reading frequencies')
    frequencies[cat] = dict()
    with open('frequencies/{0}_frequencies.txt'.format(cat)) as f:
        for line in f:
            fields = line.rstrip().split(' ')
            label = fields[1]
            frequency = eval(fields[0])
            frequencies[cat][label] = frequency
    # normalizing
    #m = float(max(frequencies.values()))
    #frequencies = {k: float(v)/m for k, v in frequencies.items()}

class guess:
    def POST(self):
        # default values
        args = web.input(n='10', p='2', m='prod', t='0')
        n = eval(args.n)
        proximity = eval(args.p)
        threshold = eval(args.t)
        objects, labels, cooccurrences, room, surface = parse_query(web.data(), proximity)

        result = []
        for o in vectors['tools'].keys():
            r = relatedness(o, labels, method=args.m)

            if room in vectors['rooms']:
                roomrel = cosine_similarity(vectors['tools'][o], vectors['rooms'][room])
            else:
                roomrel = 0.0
            if surface in vectors['furniture']:
                surfrel = cosine_similarity(vectors['tools'][o], vectors['furniture'][surface])
            else:
                surfrel = 0.0

            if o in frequencies['tools']:
                freq = frequencies['tools'][o]
            else:
	            freq = 0
            if freq >= threshold:
                result.append({'object':o, 'relatedness':r, 'frequency':freq, 'roomrel':roomrel, 'surfrel':surfrel})
        result_sorted = list(reversed(sorted(result, key=lambda x: x['relatedness'])))

        return json.dumps(result_sorted[:n])

if __name__ == "__main__":
    app.run()
