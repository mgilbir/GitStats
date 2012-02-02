class GraphCreator:
	"""
		A template that can be inherited by all the clases that implement graphics creation for the tool
	"""

	def createAll(self):
		self.createDayOfWeek()
		self.createDomains()
		self.createMonthOfYear()
		self.createCommitsByYearMonth()
		self.createCommitsByYear()
		self.createFilesByDate()
		self.createLinesOfCode()

	def createHourOfDay(self):
		"""
			# hour of day
		"""

	def createDayOfWeek(self):
		"""
			# day of week
		"""
	
	def createDomains(self):
		"""
			# Domains
		"""

	def createMonthOfYear(self):
		"""
			# Month of Year
		"""
	
	def createCommitsByYearMonth(self):
		"""
			# commits_by_year_month
		"""

	def createCommitsByYear(self):
		"""
			# commits_by_year
		"""

	def createFilesByDate(self):
		"""
			# Files by date
		"""

	def createLinesOfCode(self):
		"""
			# Lines of Code
		"""