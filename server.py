#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import json
import os

import requests
from bottle import route, run, request, response, static_file

header = None
rows = []
members = []

ocean_map = {
    "Low": 1,
    "Med-Low": 2,
    "Med": 3,
    "Med-High": 4,
    "High": 5
}

BG_FACTOR = 5
FIRST_AREA_FACTOR = 5
SECOND_AREA_FACTOR = 2
OCEAN_FACTOR = 0.5

trello_file_location = os.environ.get('TRELLO_FILE_LOCATION')
founders_csv_file_location = os.environ.get('FOUNDERS_FILE_LOCATION')

cards = requests.get(trello_file_location).json()

out_filename = '/tmp/out.csv'
try:
    founders_csv_response = requests.get(founders_csv_file_location, allow_redirects=True)
    with open(out_filename, 'wb') as fd:
        for chunk in founders_csv_response.iter_content(chunk_size=128):
            fd.write(chunk)
except Exception as e:
    pass


def load_images():
    images = {}
    for card in cards:
        card_name = card['name'].replace('\t', ' ').strip()
        image_url = card['attachments'][0]['url']
        images[card_name] = image_url
    return images


images = load_images()

with open(out_filename, mode='r', encoding='utf-8') as csv_file:
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
            name = "%s %s" % (row[0].strip(), row[2].strip())
            member = {
                "name": "%s %s" % (row[0], row[2]),
                "background": background,
                "areas": [row[28].strip(), row[29].strip()]
            }

            oceans = range(37, 41)

            scores = {}
            for ocean in oceans:
                if row[ocean].strip() != '':
                    scores[header[ocean]] = ocean_map[row[ocean]]

            member["scores"] = scores

            try:
                member["image"] = images[name]
            except Exception as e:
                print("couldn't find image for: %s" % name)
            members.append(member)


def find_member(member_name):
    source_member = None
    for member in members:
        if member['name'] == member_name:
            source_member = member
    return source_member


def calculate_background_score(source_member, comparison_member):
    source_member_bgs = source_member['background']
    comparison_member_bgs = comparison_member['background']

    matched_bgs = 0
    for bg in source_member_bgs:
        if bg in comparison_member_bgs:
            matched_bgs += 1

    bg_score = BG_FACTOR * matched_bgs

    if bg_score == 0:
        return 1 - bg_score

    normalized = (bg_score - 1) / (14 - 0)
    return 1 - normalized


def calculate_areas_score(source_member, comparison_member):
    source_member_areas = source_member['areas']
    comparison_member_areas = comparison_member['areas']

    areas_score = 0

    for i, area in enumerate(source_member_areas):
        if area == comparison_member_areas[0]:
            areas_score += FIRST_AREA_FACTOR
        elif area == comparison_member_areas[1]:
            areas_score += SECOND_AREA_FACTOR

    areas_final_score = BG_FACTOR * areas_score

    if areas_final_score == 0:
        return areas_final_score

    normalized = (areas_final_score - 1) / (13 - 0)
    return normalized


def calculate_ocean_score(source_member, comparison_member):
    try:
        match_score = get_entrepreneurship(source_member, comparison_member)
        reduced_score = 0.01 * match_score
        return reduced_score
    except Exception as e:
        # return big value
        return 1


def get_matches(request_name):
    print("getting matches for %s" % request_name)
    matches = []

    source_member = find_member(request_name)
    mb_areas = source_member['areas'][0]
    mb_background = source_member['background']

    if not mb_areas or not mb_background:
        return None

    # Christian hack ;)
    if request_name.startswith('Christian'):
        match = {
            "name": "Borat",
            "score": 100000,
            "background": "Film Industry",
            "areas": "Decision Making, Solving Poverty",
            "image": "https://i.guim.co.uk/img/media/60e266b4b2cb38e4df1407c9f591742da9c2fc50/106_246_1132_1463/master/1132.jpg?width=700&quality=85&auto=format&fit=max&s=40e68cf5d0339b868fa1718651821a90"
        }
        return [match]

    for iter_member in members:
        if iter_member['name'] == request_name:
            continue

        match = {
            "name": iter_member['name'],
            "background": iter_member['background'],
            "areas": iter_member['areas']
        }

        if 'image' in iter_member:
            match["image"] = iter_member['image']

        bg_score = calculate_background_score(source_member, iter_member)
        area_score = calculate_areas_score(source_member, iter_member)
        ocean_score = calculate_ocean_score(source_member, iter_member)

        match["bg_score"] = bg_score
        match["area_score"] = area_score
        match["ocean_score"] = ocean_score

        total_score = area_score + bg_score + ocean_score
        normalized_total_score = (total_score - 1) / (3 - 0)

        match["score"] = normalized_total_score

        # if points > 0:
        matches.append(match)

    sorted_x = sorted(matches, key=lambda kv: kv['score'], reverse=True)
    return sorted_x


def get_similarity(optimal, sum_score):
    result = 0
    for ocean, score in optimal.items():
        if ocean in sum_score:
            difference = abs(score - sum_score[ocean])
            result += difference
    return result


def get_entrepreneurship(member_a, member_b):
    optimal_scores = {
        "Agreeableness": 2,
        "Conscientiousness": 10,
        "Openness": 10,
        "Neuroticism": 2
    }

    sum_scores = {}

    for ocean_opt in optimal_scores:
        if ocean_opt in member_a['scores'] and ocean_opt in member_b['scores']:
            sum_scores[ocean_opt] = member_a['scores'][ocean_opt] + member_b['scores'][ocean_opt]

    similarity = get_similarity(optimal_scores, sum_scores)
    return similarity


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
    matches = get_matches(request_name)
    return json.dumps(matches)


@route('/static/<filename:path>')
def server_static(filename):
    return static_file(filename, root='static')


run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
