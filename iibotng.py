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
		self.proc = None
		self.halt = 1

	def __del__(self):
		for resource in self.resources:
			print "Purging %s" % ( resource )
			self.resources[resource].close()
			open(resource,"w").close()
		self.disconnect()

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
		self.proc = subprocess.Popen(cmd)
		time.sleep(5)
		self.servers[host] = []
		self.halt = 0

	def disconnect(self):
		if self.proc:
			os.kill(self.proc.pid,9)

	def joinChannel(self, host, channel):
		if host not in self.servers:
			return -1
		self.writeResource("%s/%s/in" % ( self.iidir, host ), "/j %s" %(channel))
		self.servers[host].append(channel)
		return 1
	
	def processMessageLine(self, line, container, key):
		if line == "":
			return container
		datestamp = line[0:16]
		line = line[16:]
		if "> " in line and "<" in line:
			user = line.split(">")[0].split("<")[1]
			message = line.split("> ")[1]
		else:
			user = "<IRCD>"
			message = line

		if user == self.nick:
			return container

		if message[0] == "-" and user != "<IRCD>": ## do commands
			command = message.split(" ")[0][1:]
			if command in self.commands:
				resp = self.commands[command](self, datestamp, user, message, key)
				print resp

		if user != "<IRCD>":
			for phrase in self.watchPhrases:
				if phrase in message:
					self.watchPhrases[phrase](self, datestamp, user, message, key)

		if key not in container:
			container[key] = []
		container[key].append((datestamp,user,message))
		return container

	def normalizeResource(self, resource):
		if self.iidir not in resource:
			resource = self.iidir + "/" + resource
		resource = resource.replace("//","/")
		return resource

	def readResource(self, resource):
		resource = self.normalizeResource(resource)
		if resource not in self.resources:
			self.resources[resource] = open(resource,"r")
		tmp = self.resources[resource].readlines()
		data = []
		for t in tmp:
			data.append(t.replace("\n",""))
		return data

	def writeResource(self, resource, message):
		resource = self.normalizeResource(resource)
		if resource not in self.resources:
			self.resources[resource] = open(resource, "a")
		if message[-1] != "\n":
			message = message + "\n"
		print message
		self.resources[resource].write(message)
		self.resources[resource].flush()

	def getMessages(self):
		messages = {}
		if self.halt:
			return messages
		for server in self.servers:
			out = self.readResource("%s/%s/out" % (self.iidir, server))
			for line in out:
				messages = self.processMessageLine(line, messages, server)
			for channel in self.servers[server]:
				chanout = self.readResource("%s/%s/%s/out" % (self.iidir, server, channel))
				for line in chanout:
					messages = self.processMessageLine(line, messages, server+"/"+channel)
		if len(messages) == 0:
			return None
		return messages

	def addCommand(self, cmd, func):
		if cmd in self.commands:
			print "Already bound %s to %s" % ( self.commands[cmd], cmd )
			return -1
		self.commands[cmd] = func

	def addWatchPhrase(self, phrases, func):
		if type(phrases) == type(""):
			phrases = [phrases]
		for phrase in phrases:
			if phrase in self.watchPhrases:
				print "Already using '%s' for %s" % ( phrase, func)
				return -1
			self.watchPhrases[phrase] = func