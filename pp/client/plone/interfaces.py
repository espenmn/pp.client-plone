################################################################
# pp.client-plone
# (C) 2013,  ZOPYX Limited, D-72074 Tuebingen, Germany
################################################################

from zope.interface import Interface
from zope import schema
from pp.client.plone.i18n import MessageFactory as _


class IPPContent(Interface):
    """ Marker interface for Plone content to be considered as
        content for Produce & Publish.
    """

class IArchiveFolder(Interface):
    """ Marker interface for folder with archived content that will
        be ignored inside @@asHTML
    """

class IPloneClientConnectorLayer(Interface):
    """A brower layer specific to my product """
   


class IPPClientPloneSettings(Interface):
    """ pp.client-plone settings """

    server_url = schema.TextLine(
        title=_(u'URL of Produce & Publish webservice'),
        description=_(u'URL of Produce & Publish webservice'),
        default=u'https://pp-server.zopyx.com'
    )

    server_username = schema.TextLine(
        title=_(u'Username for webservice'),
        description=_(u'Username for webservice'),
        required=False,
        default=u''
    )

    server_password = schema.TextLine(
        title=_(u'Password for webservice'),
        description=_(u'Password for webservice'),
        required=False,
        default=u''
    )

