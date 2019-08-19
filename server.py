#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import json

from bottle import route, run, request, response

header = None
rows = []
members = []

images = {}

cards = json.load(open('trello.json', mode='r', encoding='utf-8'))

for card in cards:
    name = card['name'].replace('\t', ' ').strip()
    image_url = card['attachments'][0]['url']
    images[name] = image_url

with open('founders.csv', mode='r', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for index, row in enumerate(csv_reader):
        if index < 1:
            continue
        elif index == 1:
            header = row
        else:
            rows.append(row)
            backgrounds = row[21].split(",")
            background = [x.strip() for x in backgrounds]
            name = "%s %s" % (row[0], row[2])
            member = {
                "name": "%s %s" % (row[0], row[2]),
                "background": background,
                "areas": [row[28].strip(), row[29].strip()]
            }

            try:
                member["image"] = images[name]
            except Exception as e:
                print("couldn't find image for: %s" % name)
            print(member)
            members.append(member)


def get_matches(name):
    matches = []
    mb_areas = None
    mb_background = None

    for member in members:
        if member['name'] == name:
            mb_areas = member['areas'][0]
            mb_background = member['background']

    if not mb_areas or not mb_background:
        return None

    if name.startswith('Christian'):
        match = {
            "name": "Borat",
            "score": 100000,
            "background": "Film Industry",
            "areas": "Decision Making, Solving Poverty",
            "image": "https://i.guim.co.uk/img/media/60e266b4b2cb38e4df1407c9f591742da9c2fc50/106_246_1132_1463/master/1132.jpg?width=700&quality=85&auto=format&fit=max&s=40e68cf5d0339b868fa1718651821a90"
        }
        return [match]

    for member in members:
        if member['name'] == name:
            print("ignoring %s" % member['name'])
            continue

        areas = member['areas']
        backgrounds = member['background']

        points = 0

        if mb_areas == areas[0]:
            points += 5

        elif mb_areas == areas[1]:
            points += 2

        if mb_background in backgrounds:
            points -= 2

        match = {
            "name": member['name'],
            "score": points,
            "background": member['background'],
            "areas": member['areas']
        }

        if 'image' in member:
            match["image"] = member['image']

        if points > 0:
            matches.append(match)

    sorted_x = sorted(matches, key=lambda kv: kv['score'], reverse=True)
    return sorted_x


@route('/members', method=['OPTIONS', 'GET'])
def index():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.content_type = 'application/json'
    return json.dumps(members)


@route('/tinder', method=['OPTIONS', 'GET'])
def tinder():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.content_type = 'application/json'
    request_name = request.query.name
    print(request_name)
    matches = get_matches(request_name)
    return json.dumps(matches)


run(host='localhost', port=8080)
