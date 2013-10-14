################################################################
# pp.client-plone
# (C) 2013,  ZOPYX Limited, D-72074 Tuebingen, Germany
################################################################

""" 
Resources registry for templates, styles etc.
"""

import os
from logger import  LOG

# mapping name -> directory
resources_registry = dict()

def registerResource(name, directory):
    if not os.path.exists(directory):
        raise IOError('Directory "%s" does not exit' % directory)
    resources_registry[name] = directory
    LOG.info('Registered resource directory "%s" as "%s"' % (directory, name))
