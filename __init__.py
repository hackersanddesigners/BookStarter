import flask
from flask import request
from flask_plugin import Plugin
from api import *
from bs4 import BeautifulSoup
import re, copy, sys, os, glob
# import config

sys.path.insert(0, '.../../..')
from config import config as conf

WIKI         = conf['wiki']['base_url']
SUBJECT_NS   = conf['wiki']['subject_ns']
STYLES_NS    = conf['wiki']['styles_ns']

plugin = Plugin(
		static_folder='static',
		template_folder='templates'
)

# Endpoint for the plugin for getting the rendered publication
# path: /plugin/<plugin-name>/pdf/<publication-name>
# plugin & application name are probably the same
# this overwrites the default /pdf route

@plugin.route('/pdf/<string:pagename>', methods=['GET', 'POST'])
def pagedjs(pagename):	
	publication = get_publication(
		WIKI,
		SUBJECT_NS,
		STYLES_NS,
		pagename,
	)
	return filter(flask.render_template(
		'custom.html', 
		title = pagename,
		html  = publication['html'],
	))
 

# The filters in this plugin work on request time
# this endpoint returns the filtered html, 
# Theres no link in the UI to get to it.
# path: /plugin/<plugin-name>/html_filtered/<publication-name>

@plugin.route('/html_filtered/<string:pagename>', methods=['GET', 'POST'])
def filtered_html(pagename):
	publication = get_publication(
		WIKI,
		SUBJECT_NS,
		STYLES_NS,
		pagename,
	)
	return filter(flask.render_template(
		'inspect.html', 
		title = pagename,
		html  = publication['html'],
		css   = publication['css']
	))

# misc transformations of the mediawiki html
def filter(html):
	print("filtering...")	
	soup = BeautifulSoup(html, 'html.parser')
	soup = imageSpreads(soup)
	html = str(soup) #soup.prettify() # dont use prettify. It causes whitespace in layout in some instances #
	html = removeSrcSets(html)
	return html

# somethings wrong with the srcsets from the wiki. We only need originals anyway.
def removeSrcSets(html):
	"""
		html = string (HTML)
	"""
	html = re.sub(r"srcset=", "xsrcset=", html)
	return html


# Creates the html necessary for spreads
# <section class="full-spread-image-section">
# 	<div class="full-page-image full-page-image-left">
# 		<div>
# 			<img src="src" />
# 		</div>
# 	</div>
# 	<div class="full-page-image">
# 		<div>
# 			<img src="src" />
# 		</div>
# 	</div>
# </section>

def createSpreadSection(soup, img):
	section = soup.new_tag('section', **{"class": 'full-spread-image-section'}) # outer section
	fpi = soup.new_tag('div', **{"class":'full-page-image full-page-image-left'}) # outer wrapper for image
	div = soup.new_tag('div') # inner wrapper for image
	if( img ):
		div.append(img) # image in inner div
	else:
		print( "missing image for spread?	")
	fpi.append(div) # div in outer wrapper
	section.append(fpi) # wrapper in section
	fpi2 = copy.copy(fpi)  # copied
	fpi2['class'] = "full-page-image full-page-image-right"
	section.append(fpi2)
	return section

# Finds span.spread in the HTML content and replaces
# them with the spread appropriate html structure
def imageSpreads(soup):
	spreads = soup.find_all(class_='spread')
	if( spreads ):
		for spread in spreads:
			img = spread.find("img")
			if( not img ):
				print( "missing image for spread?	", spread)
			else:
				section = createSpreadSection(soup, img)
				caption = spread.find(class_='thumbcaption')
				if(caption): # is thumbnail, check for caption
					if( len(caption.contents) > 1):
						to_remove = caption.find(class_='magnify')
						to_remove.extract()
						caption['class'] = 'full-spread-image-caption'
						section.div.next_sibling.append(caption) # append the caption to the right page
			spread.replace_with(section)
			if(section.next_sibling and section.next_sibling.name == 'p'):
				p = section.next_sibling
				if len(p.get_text(strip=True)) == 0:
					p.extract() # Remove empty tag
	return soup
