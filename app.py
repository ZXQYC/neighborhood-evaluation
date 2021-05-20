import time
import random
import json
import os

import numpy as np
import pandas as pd

import dotenv
import pymongo
from flask import Flask, render_template, request, redirect
from markupsafe import Markup

import latlon

dotenv.load_dotenv()
MONGO_KEY = os.getenv('MONGO')

app = Flask(__name__)

addr_frame = pd.read_csv('addresses_with_tax.csv')
addr_dict_caddr = {r['CompleteAddress']: r for (i,r) in addr_frame.iterrows()}
del addr_frame
# addr_dicts = addr_frame.to_dict('records')

f_agnes = open('cluster_result.json')
agnes = json.load(f_agnes)
f_agnes.close()
agnes_keys = list(agnes.keys())

def randPair(node_i, node_j):
    return [random.choice(agnes[node_i]['addrs']), random.choice(agnes[node_j]['addrs'])]

def randPairs(node_i, node_j, n):
    return [randPair(node_i,node_j) for i in range(n)]

def addrXY(addr):
    a = addr_dict_caddr[addr]
    return a['X'], a['Y']

def addrDist(addr_1, addr_2):
    return latlon.approx_dist(addrXY(addr_1), addrXY(addr_2))

def gen_sample_same():
    # choose random node
    while True:
        node_i = random.choice(agnes_keys)
        if len(agnes[node_i]['addrs']) < 2:
            continue
        # look for 2 houses that are relatively far apart, taking max out of N=3 samples
        pairs = randPairs(node_i, node_i, 3)
        ans = max(pairs, key=lambda x: addrDist(*x))
        return ans

def gen_sample_diff():
    while True:
        node_i = random.choice(agnes_keys)
        if len(agnes[node_i]['edges']) == 0:
            continue
        node_j = random.choice(agnes[node_i]['edges'])
        if len(agnes[node_i]['addrs']) < 1 or len(agnes[node_j]['addrs']) < 1:
            continue
        # look for 2 houses that are relatively close
        pairs = randPairs(node_i, node_j, 3)
        ans = min(pairs, key=lambda x: addrDist(*x))
        return ans

def gen_sample():
    if random.randrange(2) == 0:
        print("DIFF")
        return gen_sample_diff()
    else:
        print("SAME")
        return gen_sample_same()

def randstr(size=12):
    pos = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    N = len(pos)
    ans = ''.join(pos[random.randrange(N)] for i in range(size))
    return ans

class DBException(Exception):
    pass

class Database:
    def __init__(self, dbname):
        self.client = pymongo.MongoClient(MONGO_KEY)
        self.db = self.client[dbname]
    def user_gen_new_pass(self):
        ans = ''
        while not ans or self.db.users.find_one({'pass': ans}):
            ans = randstr()
        return ans
    def user_create_new(self, user):
        if len(user) < 2 or len(user) > 32:
            raise DBException('Username length must be between 2 and 32 characters')
        if not user.isalnum():
            raise DBException('Username must consist only of numbers and letters')
        existing = self.db.users.find_one({'user': user})
        if existing:
            raise DBException('Username is already taken')
        toinsert = {'user': user, 'pass': self.user_gen_new_pass()}
        ans = toinsert.copy()
        self.db.users.insert_one(toinsert)
        return ans
    def user_get(self, details):
        return self.db.users.find_one(details)
    def yn_add(self, a1, a2, guess, ip, pw):
        userdata = self.user_get({'pass': pw})
        if not userdata:
            raise DBException('Invalid credentials. Please try logging out and back in again.')
        self.db.guesses.insert_one({
            'a1': a1,
            'a2': a2,
            'guess': guess,
            'ip': ip,
            'time': time.time(),
            'user': userdata['user'],
        })

database = Database('datax')

@app.route('/auth/register')
def page_auth_register():
    return render_template('auth/register.html')

@app.route('/auth/backend/register')
def page_auth_backend_register():
    user = request.args.get('user', '')
    try:
        ans = database.user_create_new(user)
        return json.dumps(ans), 200
    except DBException as e:
        return str(e), 400

@app.route('/auth/login')
def page_auth_login():
    return render_template('auth/login.html')

@app.route('/auth/backend/login')
def page_auth_backend_login():
    user = request.args.get('user', '')
    pw = request.args.get('pass', '')
    dat = {'user': user, 'pass': pw}
    hasuser = database.user_get(dat)
    if hasuser:
        return 'OK', 200
    else:
        dat2 = {'user': user}
        hasuser2 = database.user_get(dat2)
        if hasuser2:
            return 'Wrong password', 400
        else:
            return 'User does not exist', 400

@app.route('/auth/logout')
def page_auth_logout():
    return render_template('auth/logout.html')

@app.route('/')
def page_slash():
    return render_template('slash.html')

@app.route('/yngen')
def page_yngen():
    choice = gen_sample()
    return redirect("/yn?a1=%s&a2=%s" % (choice[0], choice[1]))

@app.route('/yn')
def page_yn():
    a1 = request.args.get('a1')
    a2 = request.args.get('a2')
    try:
        h1 = addr_dict_caddr[a1]
        h2 = addr_dict_caddr[a2]
    except KeyError:
        return "Error: invalid houses. <a href='/yngen'>Generate new question?</a>"
    t1 = render_template('houseinfo.html', house=h1)
    t2 = render_template('houseinfo.html', house=h2)
    res = render_template('askYesNo.html',
                          house_template_1=Markup(t1),
                          house_template_2=Markup(t2),
                          house1=h1,
                          house2=h2
                          )
    return res

@app.route('/ynsubmit')
def page_ynsubmit():
    pw = request.args.get('pass', '')
    a1 = request.args.get('a1')
    a2 = request.args.get('a2')
    guess = request.args.get('guess')
    if guess == 'error':
        err = request.args.get('error',default='')
    print("RECEIVED ANSWER\n - house 1: %s\n - house 2: %s\n - guess: %s" % (a1, a2, guess))
    try:
        h1 = addr_dict_caddr[a1]
        h2 = addr_dict_caddr[a2]
    except KeyError:
        print(" - (BAD)")
        return "House(s) not found in database", 400
    print(" - (valid!)")
    try:
        database.yn_add(
            a1=a1,
            a2=a2,
            guess=guess,
            ip=request.remote_addr,
            pw=pw,
        )
        return "OK"
    except DBException as e:
        return str(e), 400
