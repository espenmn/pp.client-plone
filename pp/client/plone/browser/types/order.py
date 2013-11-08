
from ..compatible import InitializeClass
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bda.plone.orders.browser.views import OrderView

class HTMLView(OrderView):
    """ This view renders a HMTL fragment for bda.plone.orders """
    
    template = ViewPageTemplateFile('order.pt')

    def __call__(self, *args, **kw):
        return self.template(self.context)

InitializeClass(HTMLView)

