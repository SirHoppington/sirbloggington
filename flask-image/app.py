import sys

from flask import Flask, request, jsonify, flash, render_template, url_for
from flask_bootstrap import Bootstrap
from flask_flatpages import FlatPages
from flask_frozen import Freezer

app = Flask(__name__)
pages = FlatPages(app)
freezer = Freezer(app)

# this is a comment that has been edited!

def my_renderer(text):
    """Inject markdown renderering into jinja template"""
    rendered_body = render_template_string(text)
    pygmented_body = markdown.markdown(rendered_body, extensions=['codehilite', 'fenced_code'])
    return pygmented_body

app.config.update({
    'FLATPAGES_EXTENSION' : ['.md', '.markdown'],
    'FLATPAGES_HTML_RENDER' : my_renderer
})

@freezer.register_generator
def pagelist():
  for page in pages:
   yield url_for('page', path=page.path)

@app.route('/')
def index():
  articles = (p for p in pages if 'published' in p.meta)
  latest = sorted(articles, reverse=True, key=lambda p: p.meta['published'])
  return render_template('index.html', articles=latest[:10])

@app.route('/<path:path>/')
def page(path):
  page = pages.get_or_404(path)
  articles = (p for p in pages if 'published' in p.meta)
  latest = sorted(articles, reverse=True, key=lambda p: p.meta['published'])
  return render_template('page.html', page=page, articles=latest[:10])

if __name__=='__main__':
    if len(sys.argv) > 1 and sys.argv[1] =='build':
        freezer.freeze()
    else:
        app.run(debug=True, host='0.0.0.0')

