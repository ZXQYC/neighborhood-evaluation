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

# load the mongodb key from .env
dotenv.load_dotenv()
MONGO_KEY = os.getenv('MONGO')

# create the app
app = Flask(__name__)

# read address dataframe
addr_frame = pd.read_csv('addresses_with_tax.csv')
# create a dictionary based on the address dataframe, keyed by CompleteAddress
addr_dict_caddr = {r['CompleteAddress']: r for (i,r) in addr_frame.iterrows()}
# we don't need addr_frame anymore
del addr_frame

# get the cluster result
f_cres = open('cluster_result.json')
clust_res = json.load(f_cres)
f_cres.close()
clust_res_keys = list(clust_res.keys())

def randPair(node_i, node_j):
    """Get a random pair of houses from two clusters"""
    return [random.choice(clust_res[node_i]['addrs']), random.choice(clust_res[node_j]['addrs'])]

def randPairs(node_i, node_j, n):
    """Get several random pairs of houses from two clusters"""
    return [randPair(node_i,node_j) for i in range(n)]

def addrXY(addr):
    """Get the (longitude,latitude) coordinates for an address"""
    a = addr_dict_caddr[addr]
    return a['X'], a['Y']

def addrDist(addr_1, addr_2):
    """Finds the distance between two addresses"""
    return latlon.approx_dist(addrXY(addr_1), addrXY(addr_2))

def gen_sample_same():
    """Generate a random pair of houses from the same cluster"""
    # choose random node
    while True:
        node_i = random.choice(clust_res_keys)
        if len(clust_res[node_i]['addrs']) < 2:
            continue
        # look for 2 houses that are relatively far apart, taking max out of N=3 samples
        pairs = randPairs(node_i, node_i, 3)
        ans = max(pairs, key=lambda x: addrDist(*x))
        return ans

def gen_sample_diff():
    """Generate a random pair of houses from different, adjacent clusters"""
    while True:
        node_i = random.choice(clust_res_keys)
        if len(clust_res[node_i]['edges']) == 0:
            continue
        node_j = random.choice(clust_res[node_i]['edges'])
        if len(clust_res[node_i]['addrs']) < 1 or len(clust_res[node_j]['addrs']) < 1:
            continue
        # look for 2 houses that are relatively close
        pairs = randPairs(node_i, node_j, 3)
        ans = min(pairs, key=lambda x: addrDist(*x))
        return ans

def gen_sample():
    """Generate a random sample of two houses,
    with a 50% chance of being in the same cluster,
    and a 50% chance of being in adjacent clusters"""
    if random.randrange(2) == 0:
        print("DIFF")
        return gen_sample_diff()
    else:
        print("SAME")
        return gen_sample_same()

def randstr(size=12):
    """Generate a random string with a given size (default 12)"""
    pos = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    N = len(pos)
    ans = ''.join(pos[random.randrange(N)] for i in range(size))
    return ans

class DBException(Exception):
    """An exception with our database"""
    pass

class Database:
    """A class for handling our MongoDB database"""
    def __init__(self, dbname):
        """Initialize the database, given the database name"""
        self.client = pymongo.MongoClient(MONGO_KEY)
        self.db = self.client[dbname]
    def user_gen_new_pass(self):
        """Create a random new password that doesn't exist in the database yet"""
        ans = ''
        while not ans or self.db.users.find_one({'pass': ans}):
            ans = randstr()
        return ans
    def user_create_new(self, user):
        """Create a new user with a given username.
        Throws an exception if the username is not valid.
        Input:
         - user (str): the username
        Output (dict): A dictionary of the form {'user': username, 'pass': password},
            where username and password are strings.
        """
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
        """Get a user given details about the user. """
        return self.db.users.find_one(details)
    def yn_add(self, a1, a2, guess, ip, pw):
        """Add someone's guess to the database.
        Input:
         - a1 (str): the first address
         - a2 (str): the second address
         - guess (str): the guess
         - ip (str): the IP address the guess originated from
         - pw (str): the password of the user making the guess
        """
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
    """The frontend for registering a new user"""
    return render_template('auth/register.html')

@app.route('/auth/backend/register')
def page_auth_backend_register():
    """The backend for registering a new user"""
    user = request.args.get('user', '')
    try:
        ans = database.user_create_new(user)
        return json.dumps(ans), 200
    except DBException as e:
        return str(e), 400

@app.route('/auth/login')
def page_auth_login():
    """The login page"""
    return render_template('auth/login.html')

@app.route('/auth/backend/login')
def page_auth_backend_login():
    """The backend for logging in"""
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
    """The logout page"""
    return render_template('auth/logout.html')

@app.route('/')
def page_slash():
    """The index page"""
    return render_template('slash.html')

@app.route('/yngen')
def page_yngen():
    """The page that generates a new pair of houses to evaluate. Redirects to the evaluation page."""
    choice = gen_sample()
    return redirect("/yn?a1=%s&a2=%s" % (choice[0], choice[1]))

@app.route('/yn')
def page_yn():
    """The evaluation page."""
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
    """The backend for receiving an evaluation from the user"""
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
