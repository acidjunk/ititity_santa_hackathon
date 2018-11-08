Santa
=====

pip install -r requirements.txt

======

To Run:

python solution.py

======

Update:
Hey guys,

So unfortunately we did not win. Our solution only worked for 29 locations, after that it just seemed to run indefinitely.
We did not determine that this was going on at that time, since it looked like it was still calculating.
 
When I woke up this morning it suddenly hit me why our solution stopped working after 29 packages.
Basically the first 29 items are within the capacity we set for the vehicle (sleigh) (500kg).
After that the vehicle is full. Since the algorithm originally was made for multiple vehicles they did't have this issue (they simply has another vehicle available).

(Their examples has 4 vehicle's with 15 capacity, so the maximum amount of location they can travel to is 60. Their amount of location is 16.)

We kinda made the assumption that the vehicle would reset after it returned to the north pole, which was not included in the original algorithm.

Ow yeah and just increasing the amount of vehicles would not work, since it would then find the optimal solution for multiple vehicles.
So then it would start dividing the locations evenly.

In case Santa ever decide to get more sleighs, you see that the solution actually works very well.
Just change these:
capacities = [500,500 ]
data["num_vehicles"] = 2
_limit = 31 # This is the amount of locations loaded from the csv. 31 is just and example that it would work beyond 29 packages.

Anyway thank you for the hackathon,

Regards,

Twan