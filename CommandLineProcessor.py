import time
import platform
import subprocess

VERSION = 0

ON_LINUX = (platform.system() == 'Linux')
exectime_external = 0.0

def getpipeoutput(cmds, quiet = False):
	global exectime_external
	start = time.time()
	if not quiet and ON_LINUX and os.isatty(1):
		print '>> ' + ' | '.join(cmds),
		sys.stdout.flush()
	p0 = subprocess.Popen(cmds[0], stdout = subprocess.PIPE, shell = True)
	p = p0
	for x in cmds[1:]:
		p = subprocess.Popen(x, stdin = p0.stdout, stdout = subprocess.PIPE, shell = True)
		p0 = p
	output = p.communicate()[0]
	end = time.time()
	if not quiet:
		if ON_LINUX and os.isatty(1):
			print '\r',
		print '[%.5f] >> %s' % (end - start, ' | '.join(cmds))
	exectime_external += (end - start)
	return output.rstrip('\n')

def getversion():
	global VERSION
	if VERSION == 0:
		VERSION = getpipeoutput(["git rev-parse --short HEAD"]).split('\n')[0]
	return VERSION

def getexectimeexternal():
	return exectime_external