import time
import os
import zlib
import pickle

class DataCollector:
	"""Manages data collection from a revision control repository."""
	def __init__(self):
		self.stamp_created = time.time()
		self.cache = {}
	
	##
	# This should be the main function to extract data from the repository.
	def collect(self, dir):
		self.dir = dir
		self.projectname = os.path.basename(os.path.abspath(dir))
	
	##
	# Load cacheable data
	def loadCache(self, cachefile):
		if not os.path.exists(cachefile):
			return
		print 'Loading cache...'
		f = open(cachefile)
		try:
			self.cache = pickle.loads(zlib.decompress(f.read()))
		except:
			# temporary hack to upgrade non-compressed caches
			f.seek(0)
			self.cache = pickle.load(f)
		f.close()
	
	##
	# Produce any additional statistics from the extracted data.
	def refine(self):
		pass

	##
	# : get a dictionary of author
	def getAuthorInfo(self, author):
		return None
	
	def getActivityByDayOfWeek(self):
		return {}

	def getActivityByHourOfDay(self):
		return {}

	# : get a dictionary of domains
	def getDomainInfo(self, domain):
		return None

	##
	# Get a list of authors
	def getAuthors(self):
		return []
	
	def getFirstCommitDate(self):
		return datetime.datetime.now()
	
	def getLastCommitDate(self):
		return datetime.datetime.now()
	
	def getStampCreated(self):
		return self.stamp_created
	
	def getTags(self):
		return []
	
	def getTotalAuthors(self):
		return -1
	
	def getTotalCommits(self):
		return -1
		
	def getTotalFiles(self):
		return -1
	
	def getTotalLOC(self):
		return -1
	
	##
	# Save cacheable data
	def saveCache(self, cachefile):
		print 'Saving cache...'
		f = open(cachefile, 'w')
		#pickle.dump(self.cache, f)
		data = zlib.compress(pickle.dumps(self.cache))
		f.write(data)
		f.close()