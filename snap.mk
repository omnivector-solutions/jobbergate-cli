# snap variables

curdir          := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

VERSION 		:= $(shell python $(curdir)/setup.py --version)
CPU_TYPE 		:= amd64
SNAP_TARGET		:= $(curdir)/jobbergate-cli_$(VERSION)_$(CPU_TYPE).snap
