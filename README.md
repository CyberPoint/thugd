# thugd

distributed [thug](https://github.com/buffer/thug/) with docker containers

## Overview
The following containers will be created:
- rabbitmq
- thuglet

The rabbitmq container is bound to the host system's TCP/5672 & TCP/15672, and
is used by the thugboss.py script to generate tasks and collect results.
TCP/15672 is the rabbitmq management port, which can be useful for debugging.

Thuglets (thug containers) are configured to run the `thuglet.py` script and
listens for thugboss generated tasks from the `thug_ctrl` queue. Each thuglet
will then send responses back to a separate `thug_resp` queue, containing
results. If an error or timeout occurs with the thug execution, the message is
ack'd and republished into the `thug_skip` queue.

Mongodb is used to house all thuglet results and is NOT containerized.
Thuglets can access mongodb via TCP/27017, and is configured through
`/etc/thug/logging.conf`.

## Installation
* [Docker Engine (1.10.0+)](https://docs.docker.com/engine/installation/linux/ubuntulinux/)
* [Docker Compose (1.6+)](https://docs.docker.com/compose/install/)
* mongodb
* python3-pika
* (optional) mongodb-clients

```
$ sudo apt-get install mongodb python3-pika mongodb-clients
```

## Usage
* Create/modify `./thugd/thugd.ini`
* Create/modify `./tasks/tasks.json`
* Run `docker-compose up -d`
* (optional) scale multiple thuglets
* Run `thugboss.py`

## Examples

### add thuglets
```
$ docker-compose scale thuglet=10
```

### use a task list
```
$ ./thugboss.py -t ./tasks/tasks.json
```

### use cli args
```
$ ./thugboss.py -u URL1 URL2 URL3
```

### republish tasks
```
$ ./thugboss.py --retry --timeout 3600
```

## Vagrant
This is mostly for dev/testing. Ansible provisioner handles the setup.
```
$ vagrant up
$ vagrant ssh
```

## Attribution
* docker-thugd is based on thugctrl.py & thugd.py from [buffer/thug](https://github.com/buffer/thug/tree/master/tools/distributed).
* Dockerfile is based on [remnux/thug](https://github.com/REMnux/docker/tree/master/thug).

### Original License
see https://github.com/buffer/thug/blob/master/tools/README.md

```
Copyright (C) 2011-2016 Angelo Dell'Aera buffer@antifork.org
License: GNU General Public License, version 2
```

thugd.py - Thug daemon
```
By thorsten.sick@avira.com
For the iTES project (www.ites-project.org)
```
