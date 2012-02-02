def getkeyssortedbyvalues(dict):
	return map(lambda el : el[1], sorted(map(lambda el : (el[1], el[0]), dict.items())))

# dict['author'] = { 'commits': 512 } - ...key(dict, 'commits')
def getkeyssortedbyvaluekey(d, key):
	return map(lambda el : el[1], sorted(map(lambda el : (d[el][key], el), d.keys())))