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

# read the knowledge bases
log.info('reading knowledge bases')

comentions = dict()
with open('kb/eslyes.ntf') as f:
    for line in f:
        freq, object1, relation, object2 = line.rstrip().split(' ')
        freq = '1'
        # convert to plain label
        object1 = object1[1:-1].split('/')[-1]
        object2 = object2[1:-1].split('/')[-1]
        relation = relation[1:-1].split('#')[-1]
        if relation == 'comention':
            if not object1 in comentions:
                comentions[object1] = []
            comentions[object1].append((object2, eval(freq)))
            if not object2 in comentions:
                comentions[object2] = []
            comentions[object2].append((object1, eval(freq)))

tools = set()
rooms = set()
furniture = set()
location_room = dict()
location_furniture = dict()

with open('kb/eslyes_toolslocation.nt') as f:
    for line in f:
        s, p, o = line.rstrip()[:-2].split(' ')
        # convert to plain label
        relation = p[1:-1].split('#')[-1]
        entity1 = s[1:-1].split('/')[-1]
        if relation == 'likelyfound':
            tools.add(entity1)
            room = o[1:-1].split('/')[-1]
            rooms.add(room)
            if entity1 in location_room:
                location_room[entity1].append(room)
            else:
                location_room[entity1] = [room]
        elif relation == 'category':
            category = o[1:-1].split('#')[-1]
            if category == 'room':
                rooms.add(entity1)
            elif category == 'tool':
                tools.add(entity1)

with open('kb/eslyes_toolsfurniture.nt') as f:
    for line in f:
        s, p, o = line.rstrip()[:-2].split(' ')
        # convert to plain label
        relation = p[1:-1].split('#')[-1]
        entity1 = s[1:-1].split('/')[-1]
        if relation == 'likelyfound':
            tools.add(entity1)
            f = o[1:-1].split('/')[-1]
            furniture.add(f)
            if entity1 in location_furniture:
                location_furniture[entity1].append(f)
            else:
                location_furniture[entity1] = [f]
        elif relation == 'category':
            category = o[1:-1].split('#')[-1]
            if category == 'furniture':
                furniture.add(entity1)
            elif category == 'tool':
                tools.add(entity1)

# read NASARI vectors
log.info('reading vectors')
vectors = dict()
with open('tools_vectors.txt') as f:
    for line in f:
        fields = line.rstrip().split(' ')
        label = fields[1]
        coordinates = map(eval, fields[2:])
        vectors[label] = coordinates

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
    query_objects.append([query["context_room_label"],1,"","near_0"])
    query_objects.append([query["context_surface_label"],1,"","near_0"])
    # fix missing objects
    objects = filter(lambda x: x[0] in vectors, query_objects)

    # filter for distance
    objects = filter(lambda x: x[3] in distances, objects)

    labels = map(lambda x: x[0], objects)

    return objects, labels

def relatedness(o, objects, method):
    if o in objects:
        return 0
    m = map(lambda x: cosine_similarity(vectors[o], vectors[x]), objects)
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

class guess:
    def POST(self):
        # default values
        args = web.input(n='10', p='2', m='max')
        n = eval(args.n)
        proximity = eval(args.p)

        objects, labels = parse_query(web.data(), proximity)

        result = []
        for o in vectors.keys():
            r = relatedness(o, labels, method=args.m)
            result.append({'object':o, 'relatedness':r})
        result_sorted = list(reversed(sorted(result, key=lambda x: x['relatedness'])))

        return json.dumps(result_sorted[:n])

if __name__ == "__main__":
    app.run()
