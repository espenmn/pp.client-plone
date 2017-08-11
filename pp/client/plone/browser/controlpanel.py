# -*- coding: utf-8 -*-

################################################################
# pp.client-plone
# (C) 2013,  ZOPYX Limited, D-72074 Tuebingen, Germany
################################################################


import furl
from Products.Five.browser import BrowserView
from plone.app.registry.browser import controlpanel
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from pp.client.plone.interfaces import IPPClientPloneSettings
from pp.client.plone.i18n import MessageFactory as _


class PPClientPloneSettingsEditForm(controlpanel.RegistryEditForm):

    schema = IPPClientPloneSettings
    label = _(u'Produce & Publish PDF')
    description = _(u'')

    def updateFields(self):
        super(PPClientPloneSettingsEditForm, self).updateFields()

    def updateWidgets(self):
        super(PPClientPloneSettingsEditForm, self).updateWidgets()


class PPClientPloneSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = PPClientPloneSettingsEditForm


class ConnectionTest(BrowserView):

    def connection_test(self):

        registry = getUtility(IRegistry)
        settings = registry.forInterface(IPPClientPloneSettings)

        r = furl.furl(settings.server_url)
        if settings.server_username:
            r.username = settings.server_username
        if settings.server_password:
            r.password = settings.server_password
        server_url = str(r)

        from pp.client.python import version
        result = version.version(server_url=server_url, ssl_cert_verification=True)
        if result.status_code == 200:
            self.context.plone_utils.addPortalMessage(u'Connection to Produce & Publish Server is OK')
        else:
            msg = u'Connection to Produce & Publish Server is not functional (HTTP Code {}, {})'.format(result.status_code, result.text)
            self.context.plone_utils.addPortalMessage(msg, 'error')
        return self.request.response.redirect(self.context.absolute_url() + '/@@pp-client-plone-settings')

