"""Whoosh searcher.

This module allows red-R to search and index help documentaiton from within Red-R.  This allows us to build and use help documentaiton entirely from within the program without having to make sphinx index these files each time help is run, representing a big savings of time.  All we really need to do is to index the files and build them new each time."""

#import redREnviron
import os, sys, re

from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh import qparser
from whoosh import highlight
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser

textFind = re.compile(r'[^><]+?(?=<|$)', re.DOTALL)

# try:
    # indexDir = os.path.join(sys.argv[1], 'doc', 'helpIndex')
    # rrdir = sys.argv[1]
# except:
#import redREnviron

#indexDir = os.path.join(redREnviron.directoryNames['redRDir'], 'doc', 'helpIndex')
#rrdir = redREnviron.directoryNames['redRDir']
pachageHelpTemplate = 'libraries/%s/help'
coreHelpTemplate = 'doc'

def createIndex(root):
    
    indexDir = os.path.join(root, 'doc', 'helpIndex')
    if os.path.exists(indexDir):
        import shutil
        shutil.rmtree(indexDir)
    if not os.path.exists(indexDir):
        os.mkdir(indexDir)
        
    # make the schema object to store the records in.
    schema = Schema(title=TEXT(stored = True), path = ID(stored=True, unique = True), content = TEXT(stored = True))
    ix = create_in(indexDir, schema)
    writer = ix.writer()
    import glob
    
    # record the core documentation
    for r in glob.glob(os.path.join(root, 'doc', '_build', '*.html')):
        print 'indexing %s' % r
        with open(r, 'r') as f:
            cont = ' '.join([t.group() for t in re.finditer(textFind, unicode(f.read(), 'UTF-8'))])
            #print cont
            writer.add_document(title = unicode(cont.strip().split('\n')[0]), path = unicode(r), content = cont) 
    
    # record the core documentaiton
    for r in glob.glob(os.path.join(root, 'doc', '_build', 'core', '*.html')):
        print 'indexing %s' % r
        with open(r, 'r') as f:
            cont = ' '.join([t.group() for t in re.finditer(textFind, unicode(f.read(), 'UTF-8'))])
            #print cont
            writer.add_document(title = unicode(cont.strip().split('\n')[0]), path = unicode(r), content = cont) 
            
            
    # record the package documetation
    for r in glob.glob(os.path.join(root, 'libraries', '*', 'help', 'userDoc', '*', '*.html')):
        print 'indexing %s' % r
        with open(r, 'r') as f:
            cont = ' '.join([t.group() for t in re.finditer(textFind, unicode(f.read(), 'UTF-8'))])
            #print cont
            writer.add_document(title = unicode(cont.strip().split('\n')[0]), path = unicode(r), content = cont) 
        
    
    writer.commit()
    
def searchIndex(term, root):
    """Searches for the term in the indexes and returns a list of matches.  The list will contain a dict with items 'title' and 'path'."""
    ix = open_dir(os.path.join(root, 'doc', 'helpIndex'))
    with ix.searcher() as searcher:
        q = MultifieldParser(["title", "content"], schema = ix.schema, group = qparser.OrGroup).parse(term)
        r = searcher.search(q, limit = 50)
        r.fragmenter = highlight.ContextFragmenter(surround=40)
        r.formatter = highlight.HtmlFormatter()
        res = []
        for re in r:
            res.append({'title':re['title'], 'path':re['path'], 'highlight':re.highlights("content")})
            
    return res
    