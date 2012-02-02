import os
import shutil
import datetime
import time
import glob

#Our project imports
from report_creator import ReportCreator
from gnuplot_graph_creator import GnuplotGraphCreator
from command_line_processor import *
from sorting_tools import *

class HTMLReportCreator(ReportCreator):
	def __init__(self, conf):
		ReportCreator.__init__(self)
		self.conf = conf

	def html_linkify(self, text):
		return text.lower().replace(' ', '_')

	def html_header(self, level, text):
		name = self.html_linkify(text)
		return '\n<h%d><a href="#%s" name="%s">%s</a></h%d>\n\n' % (level, name, name, text, level)

	def create(self, data, path):
		ReportCreator.create(self, data, path)
		self.title = self.data.projectname

		# copy static files. Looks in the binary directory, ../share/gitstats and /usr/share/gitstats
		binarypath = os.path.dirname(os.path.abspath(__file__))
		secondarypath = os.path.join(binarypath, '..', 'share', 'gitstats')
		basedirs = [binarypath, secondarypath, '/usr/share/gitstats']
		for file in ('gitstats.css', 'sortable.js', 'arrow-up.gif', 'arrow-down.gif', 'arrow-none.gif'):
			for base in basedirs:
				src = base + '/' + file
				if os.path.exists(src):
					shutil.copyfile(src, self.path + '/' + file)
					break
			else:
				print 'Warning: "%s" not found, so not copied (searched: %s)' % (file, basedirs)

		self.createIndex()

		self.createActivityReport()
		
		self.createAuthorsReport()

		self.createFilesReport()

		self.createLinesReport()

		self.createTagsReport()

		# TODO: Choose the correct graph creator

		graph_creator = GnuplotGraphCreator(path, self.conf)
		graph_creator.createAll()
	
	def createIndex(self):
		f = open(self.path + "/index.html", 'w')
		format = '%Y-%m-%d %H:%M:%S'
		self.printHeader(f)

		f.write('<h1>GitStats - %s</h1>' % self.data.projectname)

		self.printNav(f)

		f.write('<dl>')
		f.write('<dt>Project name</dt><dd>%s</dd>' % (self.data.projectname))
		f.write('<dt>Generated</dt><dd>%s (in %d seconds)</dd>' % (datetime.datetime.now().strftime(format), time.time() - self.data.getStampCreated()))
		f.write('<dt>Generator</dt><dd><a href="http://gitstats.sourceforge.net/">GitStats</a> (version %s)</dd>' % getversion())
		f.write('<dt>Report Period</dt><dd>%s to %s</dd>' % (self.data.getFirstCommitDate().strftime(format), self.data.getLastCommitDate().strftime(format)))
		f.write('<dt>Age</dt><dd>%d days, %d active days (%3.2f%%)</dd>' % (self.data.getCommitDeltaDays(), len(self.data.getActiveDays()), (100.0 * len(self.data.getActiveDays()) / self.data.getCommitDeltaDays())))
		f.write('<dt>Total Files</dt><dd>%s</dd>' % self.data.getTotalFiles())
		f.write('<dt>Total Lines of Code</dt><dd>%s (%d added, %d removed)</dd>' % (self.data.getTotalLOC(), self.data.total_lines_added, self.data.total_lines_removed))
		f.write('<dt>Total Commits</dt><dd>%s (average %.1f commits per active day, %.1f per all days)</dd>' % (self.data.getTotalCommits(), float(self.data.getTotalCommits()) / len(self.data.getActiveDays()), float(self.data.getTotalCommits()) / self.data.getCommitDeltaDays()))
		f.write('<dt>Authors</dt><dd>%s</dd>' % self.data.getTotalAuthors())
		f.write('</dl>')

		f.write('</body>\n</html>')
		f.close()
	
	def createActivityReport(self):
		f = open(self.path + '/activity.html', 'w')
		self.printHeader(f)
		f.write('<h1>Activity</h1>')
		self.printNav(f)

		#f.write('<h2>Last 30 days</h2>')

		#f.write('<h2>Last 12 months</h2>')

		# Weekly activity
		WEEKS = 32
		f.write(self.html_header(2, 'Weekly activity'))
		f.write('<p>Last %d weeks</p>' % WEEKS)

		# generate weeks to show (previous N weeks from now)
		now = datetime.datetime.now()
		deltaweek = datetime.timedelta(7)
		weeks = []
		stampcur = now
		for i in range(0, WEEKS):
			weeks.insert(0, stampcur.strftime('%Y-%W'))
			stampcur -= deltaweek

		# top row: commits & bar
		f.write('<table class="noborders"><tr>')
		for i in range(0, WEEKS):
			commits = 0
			if weeks[i] in self.data.activity_by_year_week:
				commits = self.data.activity_by_year_week[weeks[i]]

			percentage = 0
			if weeks[i] in self.data.activity_by_year_week:
				percentage = float(self.data.activity_by_year_week[weeks[i]]) / self.data.activity_by_year_week_peak
			height = max(1, int(200 * percentage))
			f.write('<td style="text-align: center; vertical-align: bottom">%d<div style="display: block; background-color: red; width: 20px; height: %dpx"></div></td>' % (commits, height))

		# bottom row: year/week
		f.write('</tr><tr>')
		for i in range(0, WEEKS):
			f.write('<td>%s</td>' % (WEEKS - i))
		f.write('</tr></table>')

		# Hour of Day
		f.write(self.html_header(2, 'Hour of Day'))
		hour_of_day = self.data.getActivityByHourOfDay()
		f.write('<table><tr><th>Hour</th>')
		for i in range(0, 24):
			f.write('<th>%d</th>' % i)
		f.write('</tr>\n<tr><th>Commits</th>')
		fp = open(self.path + '/hour_of_day.dat', 'w')
		for i in range(0, 24):
			if i in hour_of_day:
				r = 127 + int((float(hour_of_day[i]) / self.data.activity_by_hour_of_day_busiest) * 128)
				f.write('<td style="background-color: rgb(%d, 0, 0)">%d</td>' % (r, hour_of_day[i]))
				fp.write('%d %d\n' % (i, hour_of_day[i]))
			else:
				f.write('<td>0</td>')
				fp.write('%d 0\n' % i)
		fp.close()
		f.write('</tr>\n<tr><th>%</th>')
		totalcommits = self.data.getTotalCommits()
		for i in range(0, 24):
			if i in hour_of_day:
				r = 127 + int((float(hour_of_day[i]) / self.data.activity_by_hour_of_day_busiest) * 128)
				f.write('<td style="background-color: rgb(%d, 0, 0)">%.2f</td>' % (r, (100.0 * hour_of_day[i]) / totalcommits))
			else:
				f.write('<td>0.00</td>')
		f.write('</tr></table>')
		f.write('<img src="hour_of_day.{0}" alt="Hour of Day" />'.format(self.conf['image_type']))
		fg = open(self.path + '/hour_of_day.dat', 'w')
		for i in range(0, 24):
			if i in hour_of_day:
				fg.write('%d %d\n' % (i + 1, hour_of_day[i]))
			else:
				fg.write('%d 0\n' % (i + 1))
		fg.close()

		# Day of Week
		f.write(self.html_header(2, 'Day of Week'))
		day_of_week = self.data.getActivityByDayOfWeek()
		f.write('<div class="vtable"><table>')
		f.write('<tr><th>Day</th><th>Total (%)</th></tr>')
		fp = open(self.path + '/day_of_week.dat', 'w')
		for d in range(0, 7):
			commits = 0
			if d in day_of_week:
				commits = day_of_week[d]
			fp.write('%d %d\n' % (d + 1, commits))
			f.write('<tr>')
			f.write('<th>%d</th>' % (d + 1))
			if d in day_of_week:
				f.write('<td>%d (%.2f%%)</td>' % (day_of_week[d], (100.0 * day_of_week[d]) / totalcommits))
			else:
				f.write('<td>0</td>')
			f.write('</tr>')
		f.write('</table></div>')
		f.write('<img src="day_of_week.{0}" alt="Day of Week" />'.format(self.conf['image_type']))
		fp.close()

		# Hour of Week
		f.write(self.html_header(2, 'Hour of Week'))
		f.write('<table>')

		f.write('<tr><th>Weekday</th>')
		for hour in range(0, 24):
			f.write('<th>%d</th>' % (hour))
		f.write('</tr>')

		for weekday in range(0, 7):
			f.write('<tr><th>%d</th>' % (weekday + 1))
			for hour in range(0, 24):
				try:
					commits = self.data.activity_by_hour_of_week[weekday][hour]
				except KeyError:
					commits = 0
				if commits != 0:
					f.write('<td')
					r = 127 + int((float(commits) / self.data.activity_by_hour_of_week_busiest) * 128)
					f.write(' style="background-color: rgb(%d, 0, 0)"' % r)
					f.write('>%d</td>' % commits)
				else:
					f.write('<td></td>')
			f.write('</tr>')

		f.write('</table>')

		# Month of Year
		f.write(self.html_header(2, 'Month of Year'))
		f.write('<div class="vtable"><table>')
		f.write('<tr><th>Month</th><th>Commits (%)</th></tr>')
		fp = open (self.path + '/month_of_year.dat', 'w')
		for mm in range(1, 13):
			commits = 0
			if mm in self.data.activity_by_month_of_year:
				commits = self.data.activity_by_month_of_year[mm]
			f.write('<tr><td>%d</td><td>%d (%.2f %%)</td></tr>' % (mm, commits, (100.0 * commits) / totalcommits))
			fp.write('%d %d\n' % (mm, commits))
		fp.close()
		f.write('</table></div>')
		f.write('<img src="month_of_year.{0}" alt="Month of Year" />'.format(self.conf['image_type']))

		# Commits by year/month
		f.write(self.html_header(2, 'Commits by year/month'))
		f.write('<div class="vtable"><table><tr><th>Month</th><th>Commits</th></tr>')
		for yymm in reversed(sorted(self.data.commits_by_month.keys())):
			f.write('<tr><td>%s</td><td>%d</td></tr>' % (yymm, self.data.commits_by_month[yymm]))
		f.write('</table></div>')
		f.write('<img src="commits_by_year_month.{0}" alt="Commits by year/month" />'.format(self.conf['image_type']))
		fg = open(self.path + '/commits_by_year_month.dat', 'w')
		for yymm in sorted(self.data.commits_by_month.keys()):
			fg.write('%s %s\n' % (yymm, self.data.commits_by_month[yymm]))
		fg.close()

		# Commits by year
		f.write(self.html_header(2, 'Commits by Year'))
		f.write('<div class="vtable"><table><tr><th>Year</th><th>Commits (% of all)</th></tr>')
		for yy in reversed(sorted(self.data.commits_by_year.keys())):
			f.write('<tr><td>%s</td><td>%d (%.2f%%)</td></tr>' % (yy, self.data.commits_by_year[yy], (100.0 * self.data.commits_by_year[yy]) / totalcommits))
		f.write('</table></div>')
		f.write('<img src="commits_by_year.{0}" alt="Commits by Year" />'.format(self.conf['image_type']))
		fg = open(self.path + '/commits_by_year.dat', 'w')
		for yy in sorted(self.data.commits_by_year.keys()):
			fg.write('%d %d\n' % (yy, self.data.commits_by_year[yy]))
		fg.close()

		# Commits by timezone
		f.write(self.html_header(2, 'Commits by Timezone'))
		f.write('<table><tr>')
		f.write('<th>Timezone</th><th>Commits</th>')
		max_commits_on_tz = max(self.data.commits_by_timezone.values())
		for i in sorted(self.data.commits_by_timezone.keys(), key = lambda n : int(n)):
			commits = self.data.commits_by_timezone[i]
			r = 127 + int((float(commits) / max_commits_on_tz) * 128)
			f.write('<tr><th>%s</th><td style="background-color: rgb(%d, 0, 0)">%d</td></tr>' % (i, r, commits))
		f.write('</tr></table>')

		f.write('</body></html>')
		f.close()

	def createAuthorsReport(self):
		f = open(self.path + '/authors.html', 'w')
		self.printHeader(f)

		f.write('<h1>Authors</h1>')
		self.printNav(f)

		# Authors :: List of authors
		f.write(self.html_header(2, 'List of Authors'))

		f.write('<table class="authors sortable" id="authors">')
		f.write('<tr><th>Author</th><th>Commits (%)</th><th>+ lines</th><th>- lines</th><th>First commit</th><th>Last commit</th><th class="unsortable">Age</th><th>Active days</th><th># by commits</th></tr>')
		for author in self.data.getAuthors(self.conf['max_authors']):
			info = self.data.getAuthorInfo(author)
			f.write('<tr><td>%s</td><td>%d (%.2f%%)</td><td>%d</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%d</td><td>%d</td></tr>' % (author, info['commits'], info['commits_frac'], info['lines_added'], info['lines_removed'], info['date_first'], info['date_last'], info['timedelta'], info['active_days'], info['place_by_commits']))
		f.write('</table>')

		allauthors = self.data.getAuthors()
		if len(allauthors) > self.conf['max_authors']:
			rest = allauthors[self.conf['max_authors']:]
			f.write('<p class="moreauthors">These didn\'t make it to the top: %s</p>' % ', '.join(rest))

		# Authors :: Author of Month
		f.write(self.html_header(2, 'Author of Month'))
		f.write('<table class="sortable" id="aom">')
		f.write('<tr><th>Month</th><th>Author</th><th>Commits (%)</th><th class="unsortable">Next top 5</th></tr>')
		for yymm in reversed(sorted(self.data.author_of_month.keys())):
			authordict = self.data.author_of_month[yymm]
			authors = getkeyssortedbyvalues(authordict)
			authors.reverse()
			commits = self.data.author_of_month[yymm][authors[0]]
			next = ', '.join(authors[1:5])
			f.write('<tr><td>%s</td><td>%s</td><td>%d (%.2f%% of %d)</td><td>%s</td></tr>' % (yymm, authors[0], commits, (100.0 * commits) / self.data.commits_by_month[yymm], self.data.commits_by_month[yymm], next))

		f.write('</table>')

		f.write(self.html_header(2, 'Author of Year'))
		f.write('<table class="sortable" id="aoy"><tr><th>Year</th><th>Author</th><th>Commits (%)</th><th class="unsortable">Next top 5</th></tr>')
		for yy in reversed(sorted(self.data.author_of_year.keys())):
			authordict = self.data.author_of_year[yy]
			authors = getkeyssortedbyvalues(authordict)
			authors.reverse()
			commits = self.data.author_of_year[yy][authors[0]]
			next = ', '.join(authors[1:5])
			f.write('<tr><td>%s</td><td>%s</td><td>%d (%.2f%% of %d)</td><td>%s</td></tr>' % (yy, authors[0], commits, (100.0 * commits) / self.data.commits_by_year[yy], self.data.commits_by_year[yy], next))
		f.write('</table>')

		# Domains
		f.write(self.html_header(2, 'Commits by Domains'))
		domains_by_commits = getkeyssortedbyvaluekey(self.data.domains, 'commits')
		domains_by_commits.reverse() # most first
		f.write('<div class="vtable"><table>')
		f.write('<tr><th>Domains</th><th>Total (%)</th></tr>')
		fp = open(self.path + '/domains.dat', 'w')
		n = 0
		totalcommits = self.data.getTotalCommits()
		for domain in domains_by_commits:
			if n == self.conf['max_domains']:
				break
			commits = 0
			n += 1
			info = self.data.getDomainInfo(domain)
			fp.write('%s %d %d\n' % (domain, n , info['commits']))
			f.write('<tr><th>%s</th><td>%d (%.2f%%)</td></tr>' % (domain, info['commits'], (100.0 * info['commits'] / totalcommits)))
		f.write('</table></div>')
		f.write('<img src="domains.{0}" alt="Commits by Domains" />'.format(self.conf['image_type']))
		fp.close()

		f.write('</body></html>')
		f.close()

	def createFilesReport(self):
		f = open(self.path + '/files.html', 'w')
		self.printHeader(f)
		f.write('<h1>Files</h1>')
		self.printNav(f)

		f.write('<dl>\n')
		f.write('<dt>Total files</dt><dd>%d</dd>' % self.data.getTotalFiles())
		f.write('<dt>Total lines</dt><dd>%d</dd>' % self.data.getTotalLOC())
		f.write('<dt>Average file size</dt><dd>%.2f bytes</dd>' % ((100.0 * self.data.getTotalLOC()) / self.data.getTotalFiles()))
		f.write('</dl>\n')

		# Files :: File count by date
		f.write(self.html_header(2, 'File count by date'))

		# use set to get rid of duplicate/unnecessary entries
		files_by_date = set()
		for stamp in sorted(self.data.files_by_stamp.keys()):
			files_by_date.add('%s %d' % (datetime.datetime.fromtimestamp(stamp).strftime('%Y-%m-%d'), self.data.files_by_stamp[stamp]))

		fg = open(self.path + '/files_by_date.dat', 'w')
		for line in sorted(list(files_by_date)):
			fg.write('%s\n' % line)
		#for stamp in sorted(self.data.files_by_stamp.keys()):
		#	fg.write('%s %d\n' % (datetime.datetime.fromtimestamp(stamp).strftime('%Y-%m-%d'), self.data.files_by_stamp[stamp]))
		fg.close()
			
		f.write('<img src="files_by_date.{0}" alt="Files by Date" />'.format(self.conf['image_type']))

		#f.write('<h2>Average file size by date</h2>')

		# Files :: Extensions
		f.write(self.html_header(2, 'Extensions'))
		f.write('<table class="sortable" id="ext"><tr><th>Extension</th><th>Files (%)</th><th>Lines (%)</th><th>Lines/file</th></tr>')
		for ext in sorted(self.data.extensions.keys()):
			files = self.data.extensions[ext]['files']
			lines = self.data.extensions[ext]['lines']
			f.write('<tr><td>%s</td><td>%d (%.2f%%)</td><td>%d (%.2f%%)</td><td>%d</td></tr>' % (ext, files, (100.0 * files) / self.data.getTotalFiles(), lines, (100.0 * lines) / self.data.getTotalLOC(), lines / files))
		f.write('</table>')

		f.write('</body></html>')
		f.close()

	def createLinesReport(self):
		f = open(self.path + '/lines.html', 'w')
		self.printHeader(f)
		f.write('<h1>Lines</h1>')
		self.printNav(f)

		f.write('<dl>\n')
		f.write('<dt>Total lines</dt><dd>%d</dd>' % self.data.getTotalLOC())
		f.write('</dl>\n')

		f.write(self.html_header(2, 'Lines of Code'))
		f.write('<img src="lines_of_code.{0}" />'.format(self.conf['image_type']))

		fg = open(self.path + '/lines_of_code.dat', 'w')
		for stamp in sorted(self.data.changes_by_date.keys()):
			fg.write('%d %d\n' % (stamp, self.data.changes_by_date[stamp]['lines']))
		fg.close()

		f.write('</body></html>')
		f.close()

	def createTagsReport(self):
		f = open(self.path + '/tags.html', 'w')
		self.printHeader(f)
		f.write('<h1>Tags</h1>')
		self.printNav(f)

		f.write('<dl>')
		f.write('<dt>Total tags</dt><dd>%d</dd>' % len(self.data.tags))
		if len(self.data.tags) > 0:
			f.write('<dt>Average commits per tag</dt><dd>%.2f</dd>' % (1.0 * self.data.getTotalCommits() / len(self.data.tags)))
		f.write('</dl>')

		f.write('<table class="tags">')
		f.write('<tr><th>Name</th><th>Date</th><th>Commits</th><th>Authors</th></tr>')
		# sort the tags by date desc
		tags_sorted_by_date_desc = map(lambda el : el[1], reversed(sorted(map(lambda el : (el[1]['date'], el[0]), self.data.tags.items()))))
		for tag in tags_sorted_by_date_desc:
			authorinfo = []
			authors_by_commits = getkeyssortedbyvalues(self.data.tags[tag]['authors'])
			for i in reversed(authors_by_commits):
				authorinfo.append('%s (%d)' % (i, self.data.tags[tag]['authors'][i]))
			f.write('<tr><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>' % (tag, self.data.tags[tag]['date'], self.data.tags[tag]['commits'], ', '.join(authorinfo)))
		f.write('</table>')

		f.write('</body></html>')
		f.close()

	def printHeader(self, f, title = ''):
		f.write(
"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>GitStats - %s</title>
<link rel="stylesheet" href="%s" type="text/css" />
<meta name="generator" content="GitStats %s" />
<script type="text/javascript" src="sortable.js"></script>
</head>
<body>
""" % (self.title, self.conf['style'], getversion()))

	def printNav(self, f):
		f.write("""
<div class="nav">
<ul>
<li><a href="index.html">General</a></li>
<li><a href="activity.html">Activity</a></li>
<li><a href="authors.html">Authors</a></li>
<li><a href="files.html">Files</a></li>
<li><a href="lines.html">Lines</a></li>
<li><a href="tags.html">Tags</a></li>
</ul>
</div>
""")
