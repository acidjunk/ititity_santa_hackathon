import csv

locations = []
weights = []

with open('gifts.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
