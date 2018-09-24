#!/usr/bin/python
import random
with open('users.txt', 'r') as f:
    users = [line.strip() for line in f.readlines()]
password = 'Password1!'
input_ids = [11,12,13,14]
num_creds = 25
creds = {}
for input_id in input_ids:
    used = []
    for i in range(num_creds):
        user = random.choice(users)
        while user in used:
            user = random.choice(users)
        used.append(user)
        if not user in creds:
            creds[user] = []
        creds[user].append(input_id)

i=26
for user,ids in creds.items():
    print("{}:{},{},{}".format(i, user, password, ids).replace(' ',''))
    i += 1
