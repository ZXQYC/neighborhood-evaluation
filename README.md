# Community Mapping Neighborhood Evaluation Website

This website is used for evaluating neighborhood clusterings for houses in Champaign. It asks users to evaluate whether or not 2 houses should belong in the same neighborhood. 

## Setup

First, install requirements using:

```
pip install -r requirements.txt
```

Then, you need to create a MongoDB server. I created one at `https://www.mongodb.com/`, but other sources may work too. Get the connection string for your MongoDB server. If you used `https://www.mongodb.com/`, this might look something like this:
```
mongodb+srv://<username>:<password>@<somename>.<something>.mongodb.net/<dbname>?retryWrites=true&w=majority
```
Now, create a file in the base project directory named `.env`, and put the following in it:
```
MONGO=YOUR_ACCESS_STRING_HERE
```

## Running the website

To run the website, use the command
```commandline
flask run
```

## Changing `cluster_result.json`

The two houses chosen for evaluation are based on the clustering specified in `cluster_result.json`. You can switch out this file to make the website evaluate your own clustering. The JSON file should contain a dictionary, where the keys are the names of clusters, and the values are objects with the following attributes:

- `"addrs"`: An array of strings. Each element is an address contained inside the cluster.
- `"edges"`: An array of strings. Each element is the name of a cluster that is adjacent to the cluster.

Here's a small example:
```json
{
  "cluster1": {
    "addrs": [
      "1000 Some Street, Champaign, IL 61822",
      "1001 Some Street, Champaign, IL 61822"
    ],
    "edges": [
      "cluster2"
    ]
  },
  "cluster2": {
    "addrs": [
      "1003 Some Street, Champaign, IL 61822"
    ],
    "edges": [
      "cluster1"
    ]
  }
}
```
