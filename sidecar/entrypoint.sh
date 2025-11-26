#!/bin/bash
set -e

printenv | grep -v "no_proxy"

printenv | grep -v "no_proxy" > /etc/environment

exec cron -f -L 15
