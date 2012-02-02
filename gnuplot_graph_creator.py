import os
import glob

#Our project imports
from graph_creator import GraphCreator
from command_line_processor import *

class GnuplotGraphCreator(GraphCreator):
	def __init__(self, path, conf):
		# By default, gnuplot is searched from path, but can be overridden with the
		# environment variable "GNUPLOT"
		self.gnuplot_cmd = 'gnuplot'
		if 'GNUPLOT' in os.environ:
			self.gnuplot_cmd = os.environ['GNUPLOT']
		
		self.path = path
		self.conf = conf
		self.gnuplot_image_specifications = {'svg':'','png':'transparent'}
		self.gnuplot_common = 'set terminal {0} {1}\nset size 1.0,0.5\n'.format(self.conf['image_type'], self.gnuplot_image_specifications[self.conf['image_type']] )

	def createHourOfDay(self):
		filename_data = self.path + '/hour_of_day.plot'
		f = open(filename_data, 'w')
		f.write(self.gnuplot_common)
		f.write(
"""
set output 'hour_of_day.{0}'
unset key
set xrange [0.5:24.5]
set xtics 4
set grid y
set ylabel "Commits"
plot 'hour_of_day.dat' using 1:2:(0.5) w boxes fs solid
""".format(self.conf['image_type']))
		f.close()
		self.__generate_output(filename_data)

	def createDayOfWeek(self):
		filename_data = self.path + '/day_of_week.plot'
		f = open(filename_data, 'w')
		f.write(self.gnuplot_common)
		f.write(
"""
set output 'day_of_week.{0}'
unset key
set xrange [0.5:7.5]
set xtics 1
set grid y
set ylabel "Commits"
plot 'day_of_week.dat' using 1:2:(0.5) w boxes fs solid
""".format(self.conf['image_type']))
		f.close()
		self.__generate_output(filename_data)

	def createDomains(self):
		filename_data = self.path + '/domains.plot'
		f = open(filename_data, 'w')
		f.write(self.gnuplot_common)
		f.write(
"""
set output 'domains.{0}'
unset key
unset xtics
set grid y
set ylabel "Commits"
plot 'domains.dat' using 2:3:(0.5) with boxes fs solid, '' using 2:3:1 with labels rotate by 45 offset 0,1
""".format(self.conf['image_type']))
		f.close()
		self.__generate_output(filename_data)
	
	def createMonthOfYear(self):
		filename_data = self.path + '/month_of_year.plot'
		f = open(filename_data, 'w')
		f.write(self.gnuplot_common)
		f.write(
"""
set output 'month_of_year.{0}'
unset key
set xrange [0.5:12.5]
set xtics 1
set grid y
set ylabel "Commits"
plot 'month_of_year.dat' using 1:2:(0.5) w boxes fs solid
""".format(self.conf['image_type']))
		f.close()
		self.__generate_output(filename_data)

	def createCommitsByYearMonth(self):
		filename_data = self.path + '/commits_by_year_month.plot'
		f = open(filename_data, 'w')
		f.write(self.gnuplot_common)
		f.write(
"""
set output 'commits_by_year_month.{0}'
unset key
set xdata time
set timefmt "%Y-%m"
set format x "%Y-%m"
set xtics rotate by 90 15768000
set bmargin 5
set grid y
set ylabel "Commits"
plot 'commits_by_year_month.dat' using 1:2:(0.5) w boxes fs solid
""".format(self.conf['image_type']))
		f.close()
		self.__generate_output(filename_data)

	def createCommitsByYear(self):
		filename_data = self.path + '/commits_by_year.plot'
		f = open(filename_data, 'w')
		f.write(self.gnuplot_common)
		f.write(
"""
set output 'commits_by_year.{0}'
unset key
set xtics 1 rotate by 90
set grid y
set ylabel "Commits"
set yrange [0:]
plot 'commits_by_year.dat' using 1:2:(0.5) w boxes fs solid
""".format(self.conf['image_type']))
		f.close()
		self.__generate_output(filename_data)

	def createFilesByDate(self):
		filename_data = self.path + '/files_by_date.plot'
		f = open(filename_data, 'w')
		f.write(self.gnuplot_common)
		f.write(
"""
set output 'files_by_date.{0}'
unset key
set xdata time
set timefmt "%Y-%m-%d"
set format x "%Y-%m-%d"
set grid y
set ylabel "Files"
set xtics rotate by 90
set ytics autofreq
set bmargin 6
plot 'files_by_date.dat' using 1:2 w steps
""".format(self.conf['image_type']))
		f.close()
		self.__generate_output(filename_data)
	
	def createLinesOfCode(self):
		filename_data = self.path + '/lines_of_code.plot'
		f = open(filename_data, 'w')
		f.write(self.gnuplot_common)
		f.write(
"""
set output 'lines_of_code.{0}'
unset key
set xdata time
set timefmt "%s"
set format x "%Y-%m-%d"
set grid y
set ylabel "Lines"
set xtics rotate by 90
set bmargin 6
plot 'lines_of_code.dat' using 1:2 w lines
""".format(self.conf['image_type']))
		f.close()
		self.__generate_output(filename_data)


	def __generate_output(self, filename_data):
		os.chdir(self.path)
		files = glob.glob(filename_data)
		for f in files:
			out = getpipeoutput([self.gnuplot_cmd + ' "%s"' % f])
			if len(out) > 0:
				print out
