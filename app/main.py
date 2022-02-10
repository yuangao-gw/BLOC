#!/usr/bin/env python3

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
import logging

LOCAL_RESPONSE_TIME = 0
TOTAL_RESPONSE_TIME = 0
START_TIME = time.process_time_ns()
FREQ = 0

app = Flask(__name__)


def isPrime(x) -> bool:
    k = 0
    for i in range(2, x // 2 + 1):
        if(x % i == 0):
            k = k + 1
    if k <= 0:
        return True
    else:
        return False


def largestPrime(x) -> int:
    prime = -1
    for num in range(x):
        if isPrime(num):
            prime = num
    return prime


def parse_config() -> list:
    """ Parse the config file """
    with open("config.yaml", 'r') as y:
        read_data = yaml.load(y, Loader=yaml.FullLoader)
    return read_data


def cpu_usage() -> float:
    """ Get CPU usage """
    return psutil.cpu_percent(interval=0.5)


def mem_usage():
    """ Get memory usage """
    return psutil.virtual_memory().percent


@app.route("/health_check", methods=["GET"])
def health_check():
    return "OK\n"


@app.route("/statistics", methods=['GET'])
def get_stats() -> dict:
    """ Get data about CPU and memory usage """
    return {'cpu': cpu_usage(),
            'mem': mem_usage(),
            'local_response_time':  LOCAL_RESPONSE_TIME,
            'total_response_time': TOTAL_RESPONSE_TIME,
            'frequency of requests': FREQ
            }


def failure_response(url: str, status: int) -> Response:
    """ Send failure response """
    return Response('Error: failed to access {}\n'.format(url), status=status)


@app.route('/svc/<int:index>', methods=['GET'])
def serve(index) -> dict:
    """ Main workhorse function of the app """
    global LOCAL_RESPONSE_TIME
    global TOTAL_RESPONSE_TIME
    global START_TIME
    global FREQ

    # measure how many requests are we getting
    tmp = time.process_time_ns()
    FREQ = tmp - START_TIME
    START_TIME = tmp

    start = time.process_time_ns()

    Log_Format = "%(levelname)s %(asctime)s - %(message)s"

    logging.basicConfig(format=Log_Format,
                        level=logging.INFO)
    logger = logging.getLogger("mico_serve_logger")
    logger.info("serve called")

    index = list({index})[0]  # get the number from the param
    data = parse_config()  # get config data
    if len(data) < index + 1:  # number of elements in the config should equal to or more than the index
        sys.stderr.write("Error: Config file does not contain correct index")
        return failure_response("svc-{} doesn't exist".format(index), 500)

    d = data[index]  # get the config for the given index
    urls = d['svc']  # get all urls to be called
    cost = d['cost']  # cost of this call

    p = 100
    for i in range(cost):
        largestPrime(p)
    LOCAL_RESPONSE_TIME = time.process_time_ns() - start

    if urls is None or len(urls) == 0:  # url list is empty => this is a leaf node
        TOTAL_RESPONSE_TIME = time.process_time_ns() - start
        logger.info(
            f"No URLs: local: {LOCAL_RESPONSE_TIME} total: {TOTAL_RESPONSE_TIME}")
        return {'urls': None, 'cost': cost}
    else:  # non-leaf node
        try:  # request might fail
            _ = joblib.Parallel(prefer="threads", n_jobs=len(urls))(
                (delayed(requests.get)("http://{}".format(url)) for url in urls))
        except ConnectionError as e:  # send page not found if it does
            s = e.args[0].args[0].split()
            host = s[0].split('=')[1].split(',')[0]
            port = s[1].split('=')[1].split(')')[0]

            TOTAL_RESPONSE_TIME = time.process_time_ns() - start
            logger.info(
                f"Conn Err: local: {LOCAL_RESPONSE_TIME} total: {TOTAL_RESPONSE_TIME}")

            return failure_response("{}:{}".format(host, port), 404)

        logger.info(
            f"Success: local: {LOCAL_RESPONSE_TIME} total: {TOTAL_RESPONSE_TIME}")
        TOTAL_RESPONSE_TIME = time.process_time_ns() - start

        # doesn't matter what is returned
        return {'urls': list(urls), 'cost': cost}


if __name__ == "__main__":
    app.run(host='0.0.0.0')
