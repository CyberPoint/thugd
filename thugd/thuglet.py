#!/usr/bin/env python3
# thuglet.py - runs on each thug container and listens for tasks
#   from the task queue (thug_ctrl), runs thug, and sends results
#   to the response queue (thug_resp).
import argparse
import json
import subprocess
import sys
import time
import logging
import traceback

import thugd

logging.basicConfig(level=logging.WARN, format="%(message)s")

class Thuglet(thugd.DistributedThug):
    timeout = 1800  # 30 mins

    def start(self):
        logging.warn(thugd.console_g("* Thuglet has started."))
        self.consume(self._callback, queue=self.task_queue)

    def __del__(self):
        logging.warn(thugd.console_r("! Thuglet has terminated."))

    def _callback(self, channel, method, properties, body):
        """
        callback function used by consume()
        """
        try:
            self.process_task(body)
        except Exception as e:
            logging.error(thugd.console_r("! Exception encountered."))
            logging.error(traceback.print_exc())
            # place into thug_skip queue and move on
            self.publish(body, self.skip_queue)

        channel.basic_ack(delivery_tag=method.delivery_tag)

    def process_task(self, body):
        """
        this gets executed per valid consummed message
            publishes a response message with status of task execution
            and does some housekeeping by archiving thug analysis files
        """
        data = json.loads(thugd.decode(body))

        url = data.get("url")
        logging.warn(thugd.console_y("+ Processing: {}".format(url)))

        command = [ "thug" ]
        opts = data.get("opts")
        if opts:
            for opt in opts:
                command.append(opt)

        command.append(url)
        rc, out, status = self._execute(command, url)

        if status is False:
            self.publish(body, self.skip_queue)

        report = {
            "id": data.get("id"),
            "rc": rc,
            "url": url,
            "raw": out
        }

        self.publish(report, self.resp_queue)
        logging.warn(thugd.console_g("+ Completed: {}".format(url)))

    def _execute(self, command, url):
        """
        execute a command
        """
        p = subprocess.Popen(command,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT
        )

        status = True
        i = 1
        while p.poll() is None:
            if i >= self.timeout:
                p.send_signal(15)
                status = False
                logging.error(thugd.console_r("! Timeout: {}".format(url)))
                break
            else:
                i += 1
                time.sleep(1)

        out, _ = p.communicate()
        out = thugd.decode(out).strip()
        rc = p.returncode
        return (rc, out, status)


def main(args):
    time.sleep(5)
    thuglet = Thuglet(args.config)
    thuglet.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="thugd.ini")
    args = parser.parse_args()

    main(args)
