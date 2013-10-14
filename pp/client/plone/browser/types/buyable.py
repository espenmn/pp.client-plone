
from ..compatible import InitializeClass
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class HTMLView(BrowserView):
    """ This view renders a HMTL fragment for the configured content type """

    template = ViewPageTemplateFile('buyable.pt')

    def __call__(self, *args, **kw):
        return self.template(self.context)

InitializeClass(HTMLView)

