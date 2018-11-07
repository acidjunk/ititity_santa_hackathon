import csv
import structlog

logger = structlog.get_logger()

locations = []
weights = []

logger.info("Started")
with open('gifts.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        locations.append((row["Latitude"], row["Longitude"]))
        weights.append(row["Weight"])
logger.info("Loaded location and weights", locations=len(locations), weights=len(weights))