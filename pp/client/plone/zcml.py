################################################################
# pp.client-plone
# (C) 2013,  ZOPYX Limited, D-72074 Tuebingen, Germany
################################################################

"""'
ZCML directives for pp.client-plone
"""

import os

from zope.interface import Interface
from zope.schema import TextLine 

from pp.core.resources_registry import registerResource

class IResourcesDirectory(Interface):
    """ Used for specifying SmartPrintNG resources """

    name = TextLine(
        title=u"name",
        description=u'Resource name',
        default=u"",
        required=True)

    directory = TextLine(
        title=u"Directory name",
        description=u'Directory path containing template, styles and other resources',
        default=u"",
        required=True)


def resourcesDirectory(_context, name, directory):
    zcml_filename = _context.info.file
    directory = os.path.join(os.path.dirname(zcml_filename), directory)
    registerResource(name, directory)

