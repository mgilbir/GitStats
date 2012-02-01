import datetime
import re

#Our project imports
from DataCollector import DataCollector
import CommandLineProcessor
import SortingTools


class GitDataCollector(DataCollector):
	def __init__(self, conf):
		DataCollector.__init__(self)
		self.conf = conf

	def collect(self, dir):
		DataCollector.collect(self, dir)

		try:
			self.total_authors = int(CommandLineProcessor.getpipeoutput(['git log', 'git shortlog -s', 'wc -l']))
		except:
			self.total_authors = 0
		#self.total_lines = int(getoutput('git-ls-files -z |xargs -0 cat |wc -l'))

		self.activity_by_hour_of_day = {} # hour -> commits
		self.activity_by_day_of_week = {} # day -> commits
		self.activity_by_month_of_year = {} # month [1-12] -> commits
		self.activity_by_hour_of_week = {} # weekday -> hour -> commits
		self.activity_by_hour_of_day_busiest = 0
		self.activity_by_hour_of_week_busiest = 0
		self.activity_by_year_week = {} # yy_wNN -> commits
		self.activity_by_year_week_peak = 0

		self.authors = {} # name -> {commits, first_commit_stamp, last_commit_stamp, last_active_day, active_days, lines_added, lines_removed}

		# domains
		self.domains = {} # domain -> commits

		# author of the month
		self.author_of_month = {} # month -> author -> commits
		self.author_of_year = {} # year -> author -> commits
		self.commits_by_month = {} # month -> commits
		self.commits_by_year = {} # year -> commits
		self.first_commit_stamp = 0
		self.last_commit_stamp = 0
		self.last_active_day = None
		self.active_days = set()

		# lines
		self.total_lines = 0
		self.total_lines_added = 0
		self.total_lines_removed = 0

		# timezone
		self.commits_by_timezone = {} # timezone -> commits

		# tags
		self.tags = {}
		lines = CommandLineProcessor.getpipeoutput(['git show-ref --tags']).split('\n')
		for line in lines:
			if len(line) == 0:
				continue
			(hash, tag) = line.split(' ')

			tag = tag.replace('refs/tags/', '')
			output = CommandLineProcessor.getpipeoutput(['git log "%s" --pretty=format:"%%at %%an" -n 1' % hash])
			if len(output) > 0:
				parts = output.split(' ')
				stamp = 0
				try:
					stamp = int(parts[0])
				except ValueError:
					stamp = 0
				self.tags[tag] = { 'stamp': stamp, 'hash' : hash, 'date' : datetime.datetime.fromtimestamp(stamp).strftime('%Y-%m-%d'), 'commits': 0, 'authors': {} }

		# collect info on tags, starting from latest
		tags_sorted_by_date_desc = map(lambda el : el[1], reversed(sorted(map(lambda el : (el[1]['date'], el[0]), self.tags.items()))))
		prev = None
		for tag in reversed(tags_sorted_by_date_desc):
			cmd = 'git shortlog -s "%s"' % tag
			if prev != None:
				cmd += ' "^%s"' % prev
			output = CommandLineProcessor.getpipeoutput([cmd])
			if len(output) == 0:
				continue
			prev = tag
			for line in output.split('\n'):
				parts = re.split('\s+', line, 2)
				commits = int(parts[1])
				author = parts[2]
				self.tags[tag]['commits'] += commits
				self.tags[tag]['authors'][author] = commits

		# Collect revision statistics
		# Outputs "<stamp> <date> <time> <timezone> <author> '<' <mail> '>'"
		lines = CommandLineProcessor.getpipeoutput(['git rev-list --pretty=format:"%at %ai %an <%aE>" HEAD', 'grep -v ^commit']).split('\n')
		for line in lines:
			parts = line.split(' ', 4)
			author = ''
			try:
				stamp = int(parts[0])
			except ValueError:
				stamp = 0
			timezone = parts[3]
			author, mail = parts[4].split('<', 1)
			author = author.rstrip()
			mail = mail.rstrip('>')
			domain = '?'
			if mail.find('@') != -1:
				domain = mail.rsplit('@', 1)[1]
			date = datetime.datetime.fromtimestamp(float(stamp))

			# First and last commit stamp
			if self.last_commit_stamp == 0:
				self.last_commit_stamp = stamp
			self.first_commit_stamp = stamp

			# activity
			# hour
			hour = date.hour
			self.activity_by_hour_of_day[hour] = self.activity_by_hour_of_day.get(hour, 0) + 1
			# most active hour?
			if self.activity_by_hour_of_day[hour] > self.activity_by_hour_of_day_busiest:
				self.activity_by_hour_of_day_busiest = self.activity_by_hour_of_day[hour]

			# day of week
			day = date.weekday()
			self.activity_by_day_of_week[day] = self.activity_by_day_of_week.get(day, 0) + 1

			# domain stats
			if domain not in self.domains:
				self.domains[domain] = {}
			# commits
			self.domains[domain]['commits'] = self.domains[domain].get('commits', 0) + 1

			# hour of week
			if day not in self.activity_by_hour_of_week:
				self.activity_by_hour_of_week[day] = {}
			self.activity_by_hour_of_week[day][hour] = self.activity_by_hour_of_week[day].get(hour, 0) + 1
			# most active hour?
			if self.activity_by_hour_of_week[day][hour] > self.activity_by_hour_of_week_busiest:
				self.activity_by_hour_of_week_busiest = self.activity_by_hour_of_week[day][hour]

			# month of year
			month = date.month
			self.activity_by_month_of_year[month] = self.activity_by_month_of_year.get(month, 0) + 1

			# yearly/weekly activity
			yyw = date.strftime('%Y-%W')
			self.activity_by_year_week[yyw] = self.activity_by_year_week.get(yyw, 0) + 1
			if self.activity_by_year_week_peak < self.activity_by_year_week[yyw]:
				self.activity_by_year_week_peak = self.activity_by_year_week[yyw]

			# author stats
			if author not in self.authors:
				self.authors[author] = {}
			# commits
			if 'last_commit_stamp' not in self.authors[author]:
				self.authors[author]['last_commit_stamp'] = stamp
			self.authors[author]['first_commit_stamp'] = stamp
			self.authors[author]['commits'] = self.authors[author].get('commits', 0) + 1

			# author of the month/year
			yymm = date.strftime('%Y-%m')
			if yymm in self.author_of_month:
				self.author_of_month[yymm][author] = self.author_of_month[yymm].get(author, 0) + 1
			else:
				self.author_of_month[yymm] = {}
				self.author_of_month[yymm][author] = 1
			self.commits_by_month[yymm] = self.commits_by_month.get(yymm, 0) + 1

			yy = date.year
			if yy in self.author_of_year:
				self.author_of_year[yy][author] = self.author_of_year[yy].get(author, 0) + 1
			else:
				self.author_of_year[yy] = {}
				self.author_of_year[yy][author] = 1
			self.commits_by_year[yy] = self.commits_by_year.get(yy, 0) + 1

			# authors: active days
			yymmdd = date.strftime('%Y-%m-%d')
			if 'last_active_day' not in self.authors[author]:
				self.authors[author]['last_active_day'] = yymmdd
				self.authors[author]['active_days'] = 1
			elif yymmdd != self.authors[author]['last_active_day']:
				self.authors[author]['last_active_day'] = yymmdd
				self.authors[author]['active_days'] += 1

			# project: active days
			if yymmdd != self.last_active_day:
				self.last_active_day = yymmdd
				self.active_days.add(yymmdd)

			# timezone
			self.commits_by_timezone[timezone] = self.commits_by_timezone.get(timezone, 0) + 1

		# TODO Optimize this, it's the worst bottleneck
		# outputs "<stamp> <files>" for each revision
		self.files_by_stamp = {} # stamp -> files
		revlines = CommandLineProcessor.getpipeoutput(['git rev-list --pretty=format:"%at %T" HEAD', 'grep -v ^commit']).strip().split('\n')
		lines = []
		for revline in revlines:
			time, rev = revline.split(' ')
			linecount = self.getFilesInCommit(rev)
			lines.append('%d %d' % (int(time), linecount))

		self.total_commits = len(lines)
		for line in lines:
			parts = line.split(' ')
			if len(parts) != 2:
				continue
			(stamp, files) = parts[0:2]
			try:
				self.files_by_stamp[int(stamp)] = int(files)
			except ValueError:
				print 'Warning: failed to parse line "%s"' % line

		# extensions
		self.extensions = {} # extension -> files, lines
		lines = CommandLineProcessor.getpipeoutput(['git ls-tree -r -z HEAD']).split('\000')
		self.total_files = len(lines)
		for line in lines:
			if len(line) == 0:
				continue
			parts = re.split('\s+', line, 4)
			sha1 = parts[2]
			filename = parts[3]

			if filename.find('.') == -1 or filename.rfind('.') == 0:
				ext = ''
			else:
				ext = filename[(filename.rfind('.') + 1):]
			if len(ext) > self.conf['max_ext_length']:
				ext = ''

			if ext not in self.extensions:
				self.extensions[ext] = {'files': 0, 'lines': 0}

			self.extensions[ext]['files'] += 1
			try:
				self.extensions[ext]['lines'] += self.getLinesInBlob(sha1)
			except:
				print 'Warning: Could not count lines for file "%s"' % line

		# line statistics
		# outputs:
		#  N files changed, N insertions (+), N deletions(-)
		# <stamp> <author>
		self.changes_by_date = {} # stamp -> { files, ins, del }
		lines = CommandLineProcessor.getpipeoutput(['git log --shortstat --pretty=format:"%at %an"']).split('\n')
		lines.reverse()
		files = 0; inserted = 0; deleted = 0; total_lines = 0
		author = None
		for line in lines:
			if len(line) == 0:
				continue

			# <stamp> <author>
			if line.find('files changed,') == -1:
				pos = line.find(' ')
				if pos != -1:
					try:
						(stamp, author) = (int(line[:pos]), line[pos+1:])
						self.changes_by_date[stamp] = { 'files': files, 'ins': inserted, 'del': deleted, 'lines': total_lines }
						if author not in self.authors:
							self.authors[author] = { 'lines_added' : 0, 'lines_removed' : 0 }
						self.authors[author]['lines_added'] = self.authors[author].get('lines_added', 0) + inserted
						self.authors[author]['lines_removed'] = self.authors[author].get('lines_removed', 0) + deleted
					except ValueError:
						print 'Warning: unexpected line "%s"' % line
				else:
					print 'Warning: unexpected line "%s"' % line
			else:
				numbers = re.findall('\d+', line)
				if len(numbers) == 3:
					(files, inserted, deleted) = map(lambda el : int(el), numbers)
					total_lines += inserted
					total_lines -= deleted
					self.total_lines_added += inserted
					self.total_lines_removed += deleted
				else:
					print 'Warning: failed to handle line "%s"' % line
					(files, inserted, deleted) = (0, 0, 0)
				#self.changes_by_date[stamp] = { 'files': files, 'ins': inserted, 'del': deleted }
		self.total_lines = total_lines
	
	def refine(self):
		# authors
		# name -> {place_by_commits, commits_frac, date_first, date_last, timedelta}
		authors_by_commits = SortingTools.getkeyssortedbyvaluekey(self.authors, 'commits')
		authors_by_commits.reverse() # most first
		for i, name in enumerate(authors_by_commits):
			self.authors[name]['place_by_commits'] = i + 1

		for name in self.authors.keys():
			a = self.authors[name]
			a['commits_frac'] = (100 * float(a['commits'])) / self.getTotalCommits()
			date_first = datetime.datetime.fromtimestamp(a['first_commit_stamp'])
			date_last = datetime.datetime.fromtimestamp(a['last_commit_stamp'])
			delta = date_last - date_first
			a['date_first'] = date_first.strftime('%Y-%m-%d')
			a['date_last'] = date_last.strftime('%Y-%m-%d')
			a['timedelta'] = delta
	
	def getActiveDays(self):
		return self.active_days

	def getActivityByDayOfWeek(self):
		return self.activity_by_day_of_week

	def getActivityByHourOfDay(self):
		return self.activity_by_hour_of_day

	def getAuthorInfo(self, author):
		return self.authors[author]
	
	def getAuthors(self, limit = None):
		res = SortingTools.getkeyssortedbyvaluekey(self.authors, 'commits')
		res.reverse()
		return res[:limit]
	
	def getCommitDeltaDays(self):
		return (self.last_commit_stamp - self.first_commit_stamp) / 86400 + 1

	def getDomainInfo(self, domain):
		return self.domains[domain]

	def getDomains(self):
		return self.domains.keys()
	
	def getFilesInCommit(self, rev):
		try:
			res = self.cache['files_in_tree'][rev]
		except:
			res = int(CommandLineProcessor.getpipeoutput(['git ls-tree -r --name-only "%s"' % rev, 'wc -l']).split('\n')[0])
			if 'files_in_tree' not in self.cache:
				self.cache['files_in_tree'] = {}
			self.cache['files_in_tree'][rev] = res

		return res

	def getFirstCommitDate(self):
		return datetime.datetime.fromtimestamp(self.first_commit_stamp)
	
	def getLastCommitDate(self):
		return datetime.datetime.fromtimestamp(self.last_commit_stamp)
	
	def getLinesInBlob(self, sha1):
		try:
			res = self.cache['lines_in_blob'][sha1]
		except:
			res = int(CommandLineProcessor.getpipeoutput(['git cat-file blob %s' % sha1, 'wc -l']).split()[0])
			if 'lines_in_blob' not in self.cache:
				self.cache['lines_in_blob'] = {}
			self.cache['lines_in_blob'][sha1] = res
		return res

	def getTags(self):
		lines = CommandLineProcessor.getpipeoutput(['git show-ref --tags', 'cut -d/ -f3'])
		return lines.split('\n')
	
	def getTagDate(self, tag):
		return self.revToDate('tags/' + tag)
	
	def getTotalAuthors(self):
		return self.total_authors
	
	def getTotalCommits(self):
		return self.total_commits

	def getTotalFiles(self):
		return self.total_files
	
	def getTotalLOC(self):
		return self.total_lines
	
	def revToDate(self, rev):
		stamp = int(CommandLineProcessor.getpipeoutput(['git log --pretty=format:%%at "%s" -n 1' % rev]))
		return datetime.datetime.fromtimestamp(stamp).strftime('%Y-%m-%d')	