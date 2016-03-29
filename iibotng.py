#!/usr/bin/python
# the new iibot framework

import os
import time
import subprocess

class iibot:
	def __init__(self, nick, iidir, iipath="/usr/bin/ii"):
		self.nick = nick
		self.iidir = iidir
		self.iipath = iipath 
		self.servers = {}
		self.commands = {}
		self.watchPhrases = {}
		self.resources = {}
		self.addCommand('exit',self.myQuit)
		self.proc = {}
		self.halt = 1

	def __del__(self):
		for resource in self.resources:
			print "Purging %s" % ( resource )
			self.resources[resource].close()
			open(resource,"w").close()
		self.disconnect()

	##properly quit
	def myQuit(me, self, ds, user, msg, key):
		self.halt = 1
		self.__del__()

	## Note, ssl will require the patch at http://tools.suckless.org/ii/patches/ii-1.7-ssl.diff
	def connect(self, host, ssl=0):
		if host in self.servers:
			print "Already connected to %s" % (host)
			return -1
		cmd = [self.iipath, "-s", host, "-n", self.nick, "-i", self.iidir]
		if ssl:
			cmd += ["-e","ssl"]
		cmd.append("&")
		self.proc[host] = subprocess.Popen(cmd)
		time.sleep(5)
		self.servers[host] = []
		self.halt = 0

	def disconnect(self, host=None):
		if host and host in self.proc:
			os.kill(self.proc[host].pid,9)
		else:
			for host in self.proc:
				os.kill(self.proc[host].pid,9)

	def joinChannel(self, host, channel):
		if host not in self.servers:
			return -1
		self.writeResource("%s/%s/in" % ( self.iidir, host ), "/j %s" %(channel))
		self.servers[host].append(channel)
		return 1
	
	## This is where most of the work is done, processing messages that come in
	## We pass this the raw message line itself, the "container" which is the messages return dict, and the key
	## Key will be the path (minus self.iidir) to a resource dir.  This can be used for /in and /out comms
	def processMessageLine(self, line, container, key):
		if line == "":  ## ignore empty lines sent by the IRCD or readlines() having no results
			return container
		## do message parsing
		datestamp = line[0:16]
		line = line[16:]
		if "> " in line and "<" in line:
			user = line.split(">")[0].split("<")[1]
			message = line.split("> ")[1]
		else:
			user = "<IRCD>"
			message = line

		if user == self.nick: ## ignore yourself
			return container

		if message[0] == "-" and user != "<IRCD>": ## do commands
			command = message.split(" ")[0][1:]
			if command in self.commands:
				resp = self.commands[command](self, datestamp, user, message, key)
				print resp

		if user != "<IRCD>": ## respond to watch phrases
			for phrase in self.watchPhrases:
				if phrase in message:
					self.watchPhrases[phrase](self, datestamp, user, message, key)

		if key not in container:
			container[key] = []
		container[key].append((datestamp,user,message))
		return container

	## a little helper function to make sure resources are the same (as we use them as keys and don't want dups)
	## also checks/prepends iidir
	def normalizeResource(self, resource):
		if self.iidir not in resource:
			resource = self.iidir + "/" + resource
		resource = resource.replace("//","/")
		return resource

	## get messages from a location
	def readResource(self, resource):
		resource = self.normalizeResource(resource)
		if resource not in self.resources:
			self.resources[resource] = open(resource,"r")
		tmp = self.resources[resource].readlines()
		data = []
		for t in tmp:
			data.append(t.replace("\n",""))
		return data

	## write messages to a resource
	def writeResource(self, resource, message):
		resource = self.normalizeResource(resource)
		if resource not in self.resources:
			self.resources[resource] = open(resource, "a")
		if message[-1] != "\n":
			message = message + "\n"
		self.resources[resource].write(message)
		self.resources[resource].flush()

	## This is used for polling all current messages
	## This will return messages as lists under a dict, keyd by resource dirs (e..g irc.url.com/#channame)
	## This will also process commands and watch phrases
	def getMessages(self):
		messages = {}
		if self.halt: ## if we're done and have run the exit, we don't want to try and poll file handles we closed (sometimes happens)
			return messages
		for server in self.servers:  ## for each server we're connected to, check for IRCD level messages
			out = self.readResource("%s/%s/out" % (self.iidir, server))
			for line in out:
				messages = self.processMessageLine(line, messages, server)
			for channel in self.servers[server]:  ## for each channel per server, check for messages
				chanout = self.readResource("%s/%s/%s/out" % (self.iidir, server, channel))
				for line in chanout:
					messages = self.processMessageLine(line, messages, server+"/"+channel)
		if len(messages) == 0:
			return None
		return messages

	## bind commands
	def addCommand(self, cmd, func):
		if cmd in self.commands:
			print "Already bound %s to %s" % ( self.commands[cmd], cmd )
			return -1
		self.commands[cmd] = func
	
	## bind watch phrases
	## phrases can be either a string or list of strings that will be "fuzzy" matched against (basically 'if word in line')
	def addWatchPhrase(self, phrases, func):
		if type(phrases) == type(""):
			phrases = [phrases]
		for phrase in phrases:
			if phrase in self.watchPhrases:
				print "Already using '%s' for %s" % ( phrase, func)
				return -1
			self.watchPhrases[phrase] = func