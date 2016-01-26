#!/usr/bin/env python

import web
import logging as log
import json
import operator

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

def parse_query(data):
    query = json.loads(data)
    objects = map(lambda x: x[0], query['local_objects'])
    return objects

class guess:
    def POST(self):
        result = []
        objects = parse_query(web.data())
        candidates = dict()
        for o1 in objects:
            if o1 in comentions:
                for o2 ,freq in comentions[o1]:
                    if o2 in candidates:
                        candidates[o2] += freq
                    else:
                        candidates[o2] = freq
        candidates_sorted = list(reversed(sorted(candidates.items(), key=operator.itemgetter(1))))
        for candidate in candidates_sorted:
            if candidate[0] in tools:
                result.append({'object':candidate[0], 'likelihood':candidate[1]})
        return json.dumps(result)

if __name__ == "__main__":
    app.run()
