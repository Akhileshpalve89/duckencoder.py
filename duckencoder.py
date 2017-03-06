#!/usr/bin/python
import sys
import getopt
import os

def readResource(filename):
	result_dict={}
	lines=[]
	with open(filename,"r") as f:
		lines= f.readlines()
	for l in lines:
		# remove comment from line
		l=l.split("//")[0]
		# remove line breaks
		l=l.strip().replace("\r\n","").replace("\n","")

		# skip empty lines
		if len(l) == 0:
			continue

		splitted = l.split("=")
		key = splitted[0].strip()
		val = splitted[1].strip()
		result_dict[key]=val

	return result_dict


def parseScriptLine(line, keyProp, langProp):
	result=""

	# split line into command and arguments
	instr=line.split(" ",1)
	instr[0]=instr[0].strip()
	if len(instr) > 1:
		instr[1]=instr[1].strip()

	# DELAY (don't check if second argument is present and int type)
	if instr[0] == "DELAY":
		delay = int(instr[1])
		result = delay2USBBytes(delay)

	# STRING
	elif instr[0] == "STRING":
		if len(instr) == 1:
			return ""
		# for every char
		for c in instr[1]:
			keydata = ASCIIChar2USBBytes(c, keyProp, langProp)
			if len(keydata) > 0:
				result  += keydata

	# STRING_DELAY
	elif instr[0] == "STRING_DELAY":
		if len(instr) < 2:
			return ""

		# split away delay argument from remaining string
		splitted=instr[1].split(" ",1)
		splitted[0]=splitted[0].strip()
		splitted[1]=splitted[1].strip()

		# build delaystr
		delay = int(splitted[0])
		delaystr = delay2USBBytes(delay)

		# for every char
		chars=splitted[1]
		for c in chars:
			keydata = ASCIIChar2USBBytes(c, keyProp, langProp)
			if len(keydata) > 0:
				result  += keydata + delaystr

	elif instr[0] == "CONTROL" or  instr[0] == "CTRL":
		# check if second argument after CTRL / Control
		if len(instr) > 1:
			# given key with CTRL modifier
			result = keyInstr2USBBytes(instr[1], keyProp, langProp) + prop2USBByte("MODIFIERKEY_CTRL", keyProp, langProp)
		else:
			# left CTRL without modifier
			result = prop2USBByte("KEY_LEFT_CTRL") + "\x00"

	elif instr[0] == "ALT":
		# check if second argument after  ALT
		if len(instr) > 1:
			# given key with CTRL modifier
			result = keyInstr2USBBytes(instr[1], keyProp, langProp) + prop2USBByte("MODIFIERKEY_ALT", keyProp, langProp)
		else:
			# left ALT without modifier
			result = prop2USBByte("KEY_LEFT_ALT") + "\x00"

	elif instr[0] == "SHIFT":
		# check if second argument after  ALT
		if len(instr) > 1:
			# given key with CTRL modifier
			result = keyInstr2USBBytes(instr[1], keyProp, langProp) + prop2USBByte("MODIFIERKEY_SHIFT", keyProp, langProp)
		else:
			# left SHIFT without modifier
			result = prop2USBByte("KEY_LEFT_SHIFT") + "\x00"

	elif instr[0] == "CTRL-ALT":
		# check if second argument after CTRL+ ALT
		if len(instr) > 1:
			# key
			result += keyInstr2USBBytes(instr[1], keyProp, langProp)
			# modifier for CTRL and ALT or'ed  together
			result += chr(ord(prop2USBByte("MODIFIERKEY_CTRL", keyProp, langProp)) | ord(prop2USBByte("MODIFIERKEY_ALT", keyProp, langProp)))
		else:
			return ""

	elif instr[0] == "CTRL-SHIFT":
		# check if second argument after CTRL+ SHIFT
		if len(instr) > 1:
			# key
			result += keyInstr2USBBytes(instr[1], keyProp, langProp)
			# modifier for CTRL and SHIFT or'ed  together
			result += chr(ord(prop2USBByte("MODIFIERKEY_CTRL", keyProp, langProp)) | ord(prop2USBByte("MODIFIERKEY_SHIFT", keyProp, langProp)))
		else:
			return ""


	elif instr[0] == "COMMAND-OPTION":
		# check if second argument after CTRL+ SHIFT
		if len(instr) > 1:
			# key
			result += keyInstr2USBBytes(instr[1], keyProp, langProp)
			# modifier for CTRL and SHIFT or'ed  together
			result += chr(ord(prop2USBByte("MODIFIERKEY_LEFT_GUI", keyProp, langProp)) | ord(prop2USBByte("MODIFIERKEY_ALT", keyProp, langProp)))
		else:
			return ""

	elif instr[0] == "ALT-SHIFT":
		# check if second argument after CTRL+ SHIFT
		if len(instr) > 1:
			# key
			result += keyInstr2USBBytes(instr[1], keyProp, langProp)
			# modifier for CTRL and SHIFT or'ed  together
			result += chr(ord(prop2USBByte("MODIFIERKEY_LEFT_ALT", keyProp, langProp)) | ord(prop2USBByte("MODIFIERKEY_SHIFT", keyProp, langProp)))
		else:
			# key
			result += prop2USBByte("KEY_LEFT_ALT", keyProp, langProp)
			# modifier for CTRL and SHIFT or'ed  together
			result += chr(ord(prop2USBByte("MODIFIERKEY_LEFT_ALT", keyProp, langProp)) | ord(prop2USBByte("MODIFIERKEY_SHIFT", keyProp, langProp)))

	elif instr[0] == "ALT-TAB":
		# check if second argument after CTRL+ SHIFT
		if len(instr) > 1:
			return ""
		else:
			# key
			result += prop2USBByte("KEY_TAB", keyProp, langProp)
			# modifier for CTRL and SHIFT or'ed  together
			result += prop2USBByte("MODIFIERKEY_LEFT_ALT", keyProp, langProp)

	elif instr[0] == "GUI" or instr[0] == "WINDOWS":
		# check if second argument after  ALT
		if len(instr) > 1:
			# given key with CTRL modifier
			result = keyInstr2USBBytes(instr[1], keyProp, langProp) + prop2USBByte("MODIFIERKEY_LEFT_GUI", keyProp, langProp)
		else:
			# left SHIFT without modifier
			result = prop2USBByte("KEY_LEFT_GUI", keyProp, langProp) + prop2USBByte("MODIFIERKEY_LEFT_GUI", keyProp, langProp)

	elif instr[0] == "COMMAND":
		# check if second argument after  ALT
		if len(instr) > 1:
			# given key with CTRL modifier
			result = keyInstr2USBBytes(instr[1], keyProp, langProp) + prop2USBByte("MODIFIERKEY_LEFT_GUI", keyProp, langProp)
		else:
			# left SHIFT without modifier
			result = prop2USBByte("KEY_COMMAND", keyProp, langProp) + "\x00"

	else:
		# Everything else is handled as direct key input (worst case would be the first letter of a line interpreted as single key)
		result = keyInstr2USBBytes(instr[0], keyProp, langProp) + "\x00"

	return result

def prop2USBByte(prop, keyProp, langProp):
	if prop in keyProp:
		keyval = keyProp[prop]
	elif prop in langProp:
		keyval = langProp[prop]

	if keyval == None:
		print "Error: No keycode entry for " + key_entry
		print "Warning this could corrupt generated output file"
		return ""
	if keyval[0:2].upper() == "0X":
		# conver to int from hex
		keyval = int(keyval,16)
	else:
		# convert to int
		keyval = int(keyval)

	# convert byte key / modifier value to binary string character
	return chr(keyval)


# converts a delay given as interger to payload bytes
def delay2USBBytes(delay):
	result = ""
	count = delay/255
	remain = delay % 255
	for i in range(count):
		result += "\x00\xFF"
	result += "\x00"+chr(remain)
	return result


# returns USB key byte and modifier byte for the given partial single key instruction
def keyInstr2USBBytes(keyinstr, keyProp, langProp):
	key_entry = "KEY_" + keyinstr.strip()
	result = ""
	keyval = None


	# check keyboard property (first attempt)
	if key_entry in keyProp:
		keyval = keyProp[key_entry]
	elif key_entry in langProp:
		keyval = langProp[key_entry]

	# try to translate into valid KEY, if no hit on first attempt
	if keyval == None:
		if keyinstr == "ESCAPE":
			keyinstr == "ESC"
		elif keyinstr == "DEL":
			keyinstr == "DELETE"
		elif keyinstr == "BREAK":
			keyinstr == "PAUSE"
		elif keyinstr == "CONTROL":
			keyinstr == "CTRL"
		elif keyinstr == "DOWNARROW":
			keyinstr == "DOWN"
		elif keyinstr == "UPARROW":
			keyinstr == "UP"
		elif keyinstr == "LEFTARROW":
			keyinstr == "LEFT"
		elif keyinstr == "RIGHTARROW":
			keyinstr == "RIGHT"
		elif keyinstr == "MENU":
			keyinstr == "APP"
		elif keyinstr == "WINDOWS":
			keyinstr == "GUI"
		elif keyinstr == "PLAY" or keyinstr == "PAUSE":
			keyinstr == "MEDIA_PLAY_PAUSE"
		elif keyinstr == "STOP":
			keyinstr == "MEDIA_STOP"
		elif keyinstr == "MUTE":
			keyinstr == "MEDIA_MUTE"
		elif keyinstr == "VOLUMEUP":
			keyinstr == "MEDIA_VOLUME_INC"
		elif keyinstr == "VOLUMEDOWN":
			keyinstr == "MEDIA_VOLUME_DEC"
		elif keyinstr == "SCROLLLOCK":
			keyinstr == "SCROLL_LOCK"
		elif keyinstr == "NUMLOCK":
			keyinstr == "NUM_LOCK"
		elif keyinstr == "CAPSLOCK":
			keyinstr == "CAPS_LOCK"
		else:
			keyinstr = keyinstr[0:1].upper()

	# second attempt
	key_entry = "KEY_" + keyinstr.strip()

	if key_entry in keyProp:
		keyval = keyProp[key_entry]
	elif key_entry in langProp:
		keyval = langProp[key_entry]

	if keyval == None:
		print "Error: No keycode entry for " + key_entry
		print "Warning this could corrupt generated output file"
		return ""
	if keyval[0:2].upper() == "0X":
		# conver to int from hex
		keyval = int(keyval,16)
	else:
		# convert to int
		keyval = int(keyval)

	# convert byte key / modifier value to binary string character
	return chr(keyval)


# returns USB key byte and modifier byte for the given ASCII key as binary String
# Layout translation is done by the value given by langProp
def ASCIIChar2USBBytes(char, keyProp, langProp):
	result =  ""
	# convert ordinal char value to hex string
	val = ord(char)
	hexval = str(hex(val))[2:].upper()
	if len(hexval) == 1:
		hexval = "0" + hexval

	# translate into name used in language property file (f.e. ASCII_2A)
	name=""
	if val < 0x80:
		name = "ASCII_" + hexval
	else:
		name = "ISO_8859_1_" + hexval

	# check if name  present in language property file
	if not name in langProp:
		print char + " interpreted as " + name + ", but not found in chosen language property file. Skipping character!"
	else:
		# if name, parse values (names of keyboard property entries) in language property file
		for key_entry in langProp[name].split(","):
			keyval = None
			key_entry = key_entry.strip()
			# check keyboard property
			if key_entry in keyProp:
				keyval = keyProp[key_entry]
			elif key_entry in langProp:
				keyval = langProp[key_entry]
			if keyval == None:
				print "Error: No keycode entry for " + key_entry
				print "Warning this could corrupt generated output file"
				return ""
			if keyval[0:2].upper() == "0X":
				# conver to int from hex
				keyval = int(keyval,16)
			else:
				# convert to int
				keyval = int(keyval)

			# convert byte key / modifier value to binary string character
			result += chr(keyval)
		# check if modifier has been added
		if len(result) == 1:
			result += "\x00"
	return result


def parseScript(source, keyProp, langProp):
#	result_dict={}
	result=""
	lines=source.splitlines(True)

	lastLine=None
	for l in lines:
		l = l.strip()

		# skip comments
		if l[0:2] == "//":
			continue

		# skip comments
		if l[0:4] == "REM ":
			continue

		# remove line breaks
		l=l.replace("\r\n","").replace("\n","")

		# skip empty lines
		if len(l) == 0:
			continue

		# check for repeat instruction
		if l[0:7] == "REPEAT ":
			# check for second arg and presence of las instruction
			instr = l.split(" ", 1)
			if len(instr) == 1 or lastLine == None:
				#second arg missing
				continue
			else:
				for i in range(int(instr[1].strip())):
					result += parseScriptLine(lastLine, keyProp, langProp)
		else:
			result += parseScriptLine(l, keyProp, langProp)

		lastLine=l

	return result

def usage():
	usagescr = '''Duckencoder python port 1.0 by MaMe82
=====================================

Creds to: 	hak5Darren for original duckencoder
		https://github.com/hak5darren/USB-Rubber-Ducky

Converts payload created by DuckEncoder to sourcefile for DigiSpark Sketch
Extended to pass data from stdin to stdout

Usage: python duckencoder.py -i [file ..]			Encode DuckyScript source given by -i file
   or: python duckencoder.py -i [file ..] -o [outfile ..]	Encode DuckyScript source to outputfile given by -o

Arguments:
   -i [file ..] 	Input file in DuckyScript format
   -o [file ..] 	Output File for encoded payload, defaults to inject.bin
   -l <layout name>	Keyboard Layout (us/fr/pt/de ...)
   -p, --pastthru	Read script from stdin and print result on stdout (ignore -i, -o)
   -r, --rawpassthru    Like passthru, but input is read as STRING instead of duckyscript
   -h			Print this help screen
'''
	print(usagescr)



def generatePayload(source, lang):
	# check if language file exists
	keyboard=readResource("./resources/keyboard.properties")
	language=readResource("./resources/" + lang + ".properties")

	payload = parseScript(source, keyboard, language)
	return payload


def main(argv):
	ifile = ""
	source = None
	ofile = "inject.bin"
	payload = None
	lang="us"
	rawpassthru = False
	try:
		opts, args = getopt.getopt(argv, "hi:o:l:pr", ["help", "input=", "output=", "language=", "passthru", "rawpassthru"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ("-i", "--input"):
			ifile = arg
			if not os.path.isfile(ifile) or not os.access(ifile, os.R_OK):
				print("Input file " + ifile + " doesn't exist or isn't readable")
				sys.exit(2)
			with open(ifile, "rb") as f:
				source = f.read()
		elif opt in ("-l", "--language"):
			lfile = "./resources/"+ arg +".properties"
			if not os.path.isfile(lfile) or not os.access(lfile, os.R_OK):
				print("Language file " + lfile + " doesn't exist or isn't readable")
				sys.exit(2)
			lang=arg
		elif opt in ("-o", "--output"):
			ofile = arg
		elif opt in ("-p", "--passsthru"):
			# read input from stdin, no outfile
			ofile = None
			source = ""
			for line in sys.stdin:
				source += line
			#print "Source: " + source
		elif opt in ("-r", "--rawpasssthru"):
			# read input from stdin, no outfile
			rawpassthru = True
			ofile = None
			source = ""
			for line in sys.stdin:
				source += line

	if source is None:
		print("You have to provide a source file (-i option)")
		sys.exit(2)

	if rawpassthru == True:
		# parse raw ascii data
		result = ""
		keyboard=readResource("./resources/keyboard.properties")
		language=readResource("./resources/" + lang + ".properties")
		for line in source:
			for c in line:
				keydata = ASCIIChar2USBBytes(c, keyboard, language)
				if len(keydata) > 0:
					result  += keydata
	else:
		# parse source as DuckyScript
		result = generatePayload(source, lang)

	if ofile is None:
		# print to stdout
		#print(result)
		sys.stdout.write(result)
	else:
		# write to ofile
		with open(ofile, "w") as f:
			f.write(result)


if __name__ == "__main__":
	if len(sys.argv) < 2:
		usage()
		sys.exit()
	main(sys.argv[1:])


