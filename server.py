import csv

header = None
rows = []

with open('founders.csv', mode='r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for index, row in enumerate(csv_reader):
        if index < 1:
            continue
        elif index == 1:
            header = row
            for idx, element in enumerate(row):
                print(f'{idx} - {element}')
        else:
            rows.append(row)

print(f'Found {len(rows)} rows!')

for row in rows:
    areas = [row[28].strip(), row[29].strip()]
    background = row[21].split(",")

    print(f'{row[0]} {row[2]} - bg:{background} | areas:{areas}')


name = 'Pedro'
area = 'Software and Internet'
background = 'Information Technology'
matches = {}

for row in rows:
    areas = [row[28], row[29]]
    backgrounds = row[21].split(",")

    points = 0

    if area == areas[0]:
        points += 5
    elif area == areas[1]:
        points += 2

    if background in backgrounds:
        points -= 2

    name = "%s %s" % (row[0], row[2])

    if points > 0:
        matches[name] = points


sorted_x = sorted(matches.items(), key=lambda kv: kv[1])
print(sorted_x)


# /members
# /tinder first_name

