#!/usr/bin/env python3
# thugboss.py - tasking and collection script that generates tasks
#   into the task queue (thug_ctrl) and collects thuglet responses
#   from the response queue (thug_resp).

import argparse
import datetime
import json
import logging
import os
import sys
import time
import urllib.parse

from thugd import thugd as thugd

BASEPATH = os.path.dirname(os.path.abspath(__file__))
DATETIME = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOGSPATH = os.path.join(BASEPATH, "logs")

if not os.path.exists(LOGSPATH):
    os.mkdir(LOGSPATH)

thuglog = logging.getLogger(__name__)
fmt = logging.Formatter("%(message)s")
logname = "{}.log".format(DATETIME)
hdl = logging.FileHandler(os.path.join(LOGSPATH, logname))
hdl.setFormatter(fmt)
thuglog.setLevel(logging.INFO)
thuglog.addHandler(hdl)

class ThugBoss(thugd.DistributedThug):
    def __init__(self, config):
        super(ThugBoss, self).__init__(config)
        self.tasks = []
        self.pending = 0

    def load_tasks(self, jsonfile, opts=None):
        """
        generates tasks from input json file
            if an 'opts' key exists, it will be applied to each url

        @jsonfile: json file containing thug opts and urls
        """
        if opts:
            opts = opts.split()

        if os.access(jsonfile, os.R_OK):
            with open(jsonfile, "r") as fp:
                data = json.load(fp)

            # task file options are prioritized
            tf_opts = data.get("opts")
            if tf_opts:
                opts = tf_opts

            urls = data.get("urls")
            urls = set(urls)
            self._add_task(urls, opts)

    def load_input(self, urls, opts=None):
        """
        generates tasks from user input
            if an 'opts' is specified, it will be applied to each url

        @urls: list of urls
        @opts: string of options to pass to thug
        """
        if isinstance(urls, str):
            urls = [urls]
        if opts:
            opts = opts.split()
        urls = set(urls)
        self._add_task(urls, opts)

    def _add_task(self, urls, opts=None):
        """
        populates self.tasks with urls and opts input
        """
        for url in urls:
            task_id, url = self._url_id(url)
            task = {
                "id": task_id,
                "url": url
            }
            if opts:
                task["opts"] = opts
            self.tasks.append(task)

    def _url_id(self, url):
        """
        converts url to a task_id ; prepends with protocol if missing
        """
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        name = urllib.parse.urlparse(url)
        date = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
        task_id = "{}_{}".format(name.netloc, date)
        return (task_id, url)

    def task_thugs(self):
        """
        publishes each task entry from self.tasks
        """
        self.pending = len(self.tasks)
        print("[*] ThugBoss created {} tasks".format(self.pending))
        while self.tasks:
            task = self.tasks.pop()
            print(thugd.console_y("[+] sending task: {}".format(task.get("url"))))
            self.publish(task, self.task_queue)

    def flush(self):
        """
        attempts to flush contents of task and response queues
            there may be cases when not all tasks/responses are removed,
            such as when a task is in mid-processing and is placed back
            into the queue due to a failure condition, or task is finished
            and placed into the response queue
        """
        while self.consume_one(queue=self.task_queue):
            pass
        print(thugd.console_y("[*] thug_ctrl queue flushed"))
        while self.consume_one(queue=self.resp_queue):
            pass
        print(thugd.console_y("[*] thug_resp queue flushed"))

    def collect(self):
        """
        collects expected task responses
            while ideally we'd only get the total number of tasks generated,
            there may be stray response messages in the queue, which will
            still get collected
        """
        while self.pending > 0 or self.resp_count > 0:
            body = self.consume_one(queue=self.resp_queue)

            if body is None:
                time.sleep(1)
                continue

            self.pending -= 1
            data = json.loads(thugd.decode(body))
            body = None

            thuglog.info(data)
            self.process_response(data)

    def process_response(self, data):
        """
        this gets executed per valid consumed message
            and can be changed as needed ; default is to print
        """
        print(thugd.console_g(data.get("url")))
        for k, v in data.items():
            print("{}\n{}".format(thugd.console_r(k), v))
        print(thugd.console_y("-"*80))


def main(args):
    boss = ThugBoss(args.conf)

    if args.flush:
        boss.flush()
        return

    if args.task:
        boss.load_tasks(jsonfile=args.task, opts=args.opts)
    if args.urls:
        boss.load_input(urls=args.urls, opts=args.opts)

    try:
        if args.send:
            boss.task_thugs()
        if args.recv:
            boss.collect()
    except KeyboardInterrupt:
        print(thugd.console_r("[!] Thugboss terminated."))


if __name__ == "__main__":
    cfg = os.path.join(BASEPATH, "thugd", "thugd.ini")
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conf", default=cfg)
    parser.add_argument("-t", "--task",
        help="JSON taskfile")
    parser.add_argument("-u", "--urls", nargs="+",
        help="list of URLs")
    parser.add_argument("-o", "--opts", default="-T 30 -E -v -Y -U -t 50 -u win7ie90",
        help="Thug options")
    parser.add_argument("-r", "--recv", action="store_true",
        help="only recv results")
    parser.add_argument("-s", "--send", action="store_true",
        help="only send tasks")
    parser.add_argument("-f", "--flush", action="store_true",
        help="flush contents of tasks and results queues")
    args = parser.parse_args()

    if args.send == args.recv == False:
        args.send = args.recv = True

    main(args)
