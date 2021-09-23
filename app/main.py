#!/usr/bin/env python

"""
    Extract index from the request path which should be in the form `/svc/index`
    Given the index, extract the associated urls and cost from the `config.yaml`
    Wait for time = cost -> this is done by sleep for now
    Make parallel calls to all urls in the urls list
    @return if all calls are successful, return success
            if any underlying call fails a 404 is returned
            calling `/statistics` return CPU and memory usage in percent
"""

from flask import Flask
from flask.wrappers import Response
from joblib.parallel import delayed
import yaml
import sys
import time
import psutil
import requests
from requests.exceptions import ConnectionError
import joblib

app = Flask(__name__)

def parse_config() -> list:
    """ Parsse the config file """
    with open("config.yaml", 'r') as y:
        read_data = yaml.load(y, Loader=yaml.FullLoader)
    return read_data

def cpu_usage() -> float:
    """ Get CPU usage """
    return psutil.cpu_percent(interval=0.5)

def mem_usage():
    """ Get memory usage """
    return psutil.virtual_memory().percent

@app.route("/statistics", methods=['GET'])
def get_stats() -> dict:
    """ Get data about CPU and memory usage """
    return {'cpu': cpu_usage(), 'mem': mem_usage() }

def failure_response(url, status):
    """ Send failure response """
    return Response('Error: failed to access {}\n'.format(url), status=status)

@app.route('/svc/<int:index>', methods=['GET'])
def serve(index) -> dict:
    """ Main workhorse function of the app """
    index = list({index})[0] # get the number from the param
    data = parse_config() # get config data
    if len(data) < index + 1: # number of elements in the config should equal to or more than the index
        sys.stderr.write("Error: Config file does not contain correct index")
        return failure_response("svc-{} doesn't exist".format(index), 500)

    d = data[index] # get the config for the given index
    urls = d['svc'] # get all urls to be called
    cost = d['cost'] # cost of this call

    time.sleep(cost) # sleep for time = cost -> TODO: we should change this to something useful
    
    if urls is None: # url list is empty => this is a leaf node
        return {'urls': None, 'cost': cost }
    else: # non-leaf node
        try: # request might fail
            responses = joblib.Parallel(prefer="threads", n_jobs=len(urls))((delayed(requests.get)(url) for url in urls))
        except ConnectionError as e: # send page not found if it does
            s = e.args[0].args[0].split()
            host = s[0].split('=')[1].split(',')[0]
            port = s[1].split('=')[1].split(')')[0]
            return failure_response("{}:{}".format(host, port), 404)

        # # for i, resp in enumerate(responses):
        # #     if resp.status_code != 200:
        # #         return failure_response(urls[i], resp.status_code)
        #     # return failure_response(url, 404)
        # for url in urls: # make calls to the retrieved urls
        #     url = "http://{}".format(url)
        #     try: # request might fail
        #         r = requests.get(url)
        #         responses = joblib.Parallel(delayed(requests.get)(url) for url in urls)
        #     except: # send page not found if it does
        #         return failure_response(url, 404)

        #     # TODO: turn this into parallel code using multiprocessing/joblib
        #     # otherwise all requests are sequential in case of a fanout
        #     if r.status_code != 200: # if any underlying call fails then return immediately
        #         return failure_response(url, r.status_code)

        return {'urls': list(urls), 'cost': cost} # doesn't matter what is returned

if __name__ == "__main__":
    app.run()