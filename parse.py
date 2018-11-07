import csv

data = []

with open('gifts.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        print(row['GiftId'], row['last_name'])