################################################################
# pp.client-plone
# (C) 2013,  ZOPYX Limited, D-72074 Tuebingen, Germany
################################################################

import os
import furl
import fs.zipfs
import codecs
import shutil
import tempfile
import requests
import zipfile

from compatible import InitializeClass
from plone.registry.interfaces import IRegistry
from Products.Five.browser import BrowserView
from Products.ATContentTypes.interface.folder import IATFolder
from ZPublisher.Iterators import filestream_iterator
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.pagetemplate.pagetemplatefile import PageTemplate
from zope.component import getUtility

from pp.client.plone.logger import LOG
from pp.core.transformation import Transformer
from pp.core.resources_registry import getResource

from pp.client.plone.interfaces import IPPClientPloneSettings
from util import getLanguageForObject

cwd = os.path.dirname(os.path.abspath(__file__))

ZIP_OUTPUT = 'PP_ZIP_OUTPUT' in os.environ


class ProducePublishView(BrowserView):
    """ Produce & Publish view (using Produce & Publish server) """

    # default transformations used for the default PDF view.
    # 'transformations' can be overriden within a derived ProducePublishView.
    # If you don't need any transformation -> redefine 'transformations'
    # as empty list or tuple

    # Table of contents is not working with phantomjs or epub, so
    # we leave it off.


    transformations = (
        'makeImagesLocal',
        'convertFootnotes',
        'removeCrapFromHeadings',
        'fixHierarchies',
#        'addTableOfContents',
        )

    def __init__(self, context, request):
        self.request = request
        self.context = context

    @property
    def resource(self):
        resource_id = self.request.get('resource', 'pp-default')
        try:
            return getResource(resource_id)
        except KeyError:
            raise KeyError(u'No resource "{}" registered'.format(resource_id))


    def copyResourceFromURL(self, url, destdir):
        """ Copy over resources for a global or local resources directory into the
            destination directory.
        """

        result = requests.get(url)
        if not result.ok:
            raise RuntimeError('Unable to retrieve resource by URL {0}'.format(url))

        zip_out = tempfile.mktemp(suffix='.zip')
        with open(zip_out, 'w') as fp:
            fp.write(result.content)

        fslayer = fs.zipfs.ZipFS(zip_out, 'r')
        self.copyResourceFiles(destdir, fslayer)
        os.unlink(zip_out)

    def copyResourceFiles(self, destdir, fslayer=None):
        """ Copy over resources for a global or local resources directory into the
            destination directory.
        """

        if not fslayer:
            fslayer = self.resource.fslayer

        for dirname, filenames in fslayer.walk():
            for filename in filenames:
                fullpath = os.path.join(dirname, filename)
                with fslayer.open(fullpath, 'rb') as fp:
                    content = fp.read()

                if fullpath.startswith('/'):
                    fullpath = fullpath[1:]
                destpath = os.path.join(destdir, fullpath)
                if not os.path.exists(os.path.dirname(destpath)):
                    os.makedirs(os.path.dirname(destpath))
                with open(destpath, 'wb') as fp:
                    fp.write(content)

    def transformHtml(self, html, destdir, transformations=None):
        """ Perform post-rendering HTML transformations """

        if transformations is None:
            transformations = self.transformations

        # the request can override transformations as well
        if self.request.has_key('transformations'):
            t_from_request = self.request['transformations']
            if isinstance(t_from_request, basestring):
                transformations = t_from_request and t_from_request.split(',') or []
            else:
                transformations = t_from_request

        T = Transformer(transformations,
                        context=self.context,
                        destdir=destdir)
        return T(html)

    def __call__(self, *args, **kw):

        try:
            return self.__call2__(*args, **kw)
        except:
            LOG.error('Conversion failed', exc_info=True)
            raise


    def __call2__(self, *args, **kw):
        """ URL parameters:
            'language' -  'de', 'en'....used to override the language of the
                          document
            'converter' - default to on the converters registered with
                          zopyx.convert2 (default: pdf-prince)
            'resource' - the name of a registered resource (directory)
            'resource_url' - a URL referencing a ZIPped resource archive
            'template' - the name of a custom template name within the choosen
                         'resource'
            'supplementary_css' - a CSS string injected into the template
            'cover' - Url to an image to be used as cover
            'cmd_options' More options for the converter
        """

        # Output directory
        tmpdir_prefix = os.path.join(tempfile.gettempdir(), 'produce-and-publish')
        if not os.path.exists(tmpdir_prefix):
            os.makedirs(tmpdir_prefix)
        destdir = tempfile.mkdtemp(dir=tmpdir_prefix, prefix=self.context.getId() + '-')

        # debug/logging
        params = kw.copy()
        params.update(self.request.form)
        LOG.info('new job (%s, %s) - outdir: %s' % (args, params, destdir))

        # get hold of the language (hyphenation support)
        language = getLanguageForObject(self.context)
        if params.get('language'):
            language = params.get('language')

        # call the dedicated @@asHTML on the top-level node. For a leaf document
        # this will return either a HTML fragment for a single document or @@asHTML
        # might be defined as an aggregator for a bunch of documents (e.g. if the
        # top-level is a folderish object
        html_view = self.context.restrictedTraverse('@@asXML', None)
        if not html_view:
            html_view = self.context.restrictedTraverse('@@asHTML', None)
            if not html_view:
                raise RuntimeError('Object neither provides @@asHTML or @@asXML views (%s, %s)' %
                                   (self.context.absolute_url(1), self.context.portal_type))
        html_fragment = html_view()

        # arbitrary application data
        data = params.get('data', None)

        resource_id = self.request.get('resource', 'pp-default')
        resource_url = self.request.get('resource_url')

        cmdoptions = self.request.get('cmd_options', None)

        #import pdb; pdb.set_trace()

        cover = self.request.get('cover', '')

        if cover:
            cmdoptions += " --cover=%s" % cover

        if resource_url:
            self.copyResourceFromURL(resource_url, destdir)
        else:
            self.copyResourceFiles(destdir)

        template_id = params.get('template', 'pdf_template.pt')
        template = PageTemplate()
        if not os.path.exists(os.path.join(destdir, template_id)):
            raise IOError('Resource does not contain template file {}'.format(template_id))
        with open(os.path.join(destdir, template_id), 'rb') as fp:
            template.write(fp.read())

        # Now render the complete HTML document
        supplementary_css = params.get('supplementary_css', None)
        html = template(self,
                        context=self.context,
                        request=self.request,
                        language=language,
                        body=html_fragment,
                        supplementary_css=supplementary_css,
                        data=data,
                        )

        # and apply transformations
        transformations = params.get('transformations', self.transformations)
        html = self.transformHtml(html, destdir, transformations)

        # and store it in a dedicated working directory
        dest_filename = os.path.join(destdir, 'index.html')
        with codecs.open(dest_filename, 'wb', encoding='utf-8') as fp:
            fp.write(html)

        # create a local ZIP file containing all the data for the conversion
        # basically for debugging purposes only.
        if ZIP_OUTPUT or 'zip_output' in params:
            archivename = tempfile.mktemp(suffix='.zip')
            fp = zipfile.ZipFile(archivename, "w", zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(destdir):
                for fn in files:
                    absfn = os.path.join(root, fn)
                    zfn = absfn[len(destdir)+len(os.sep):] #XXX: relative path
                    fp.write(absfn, zfn)
            fp.close()
            LOG.info('ZIP file written to %s' % archivename)

        if 'no_conversion' in params:
            return destdir

        converter = params.get('converter', 'pdfreactor8')

        # Produce & Publish server integration

        registry = getUtility(IRegistry)
        settings = registry.forInterface(IPPClientPloneSettings)

        r = furl.furl(settings.server_url)
        if settings.server_username:
            r.username = settings.server_username
        if settings.server_password:
            r.password = settings.server_password
        server_url = str(r)

        from pp.client.python import pdf

        #import pdb; pdb.set_trace()

        #result = pdf.pdf(destdir, converter, server_url=server_url, ssl_cert_verification=True, cover=cover)
        result = pdf.pdf(destdir, converter, server_url=server_url, ssl_cert_verification=True, cmd_options=cmdoptions)
        if result['status']  == 'OK':
            output_filename = result['output_filename']
            LOG.info('Output file: %s' % output_filename)
            return output_filename
        else:
            LOG.error('Conversion failed ({})'.format(result['output']))
            raise RuntimeError(result['output'])

InitializeClass(ProducePublishView)


class PDFDownloadView(ProducePublishView):

    def __call__(self, *args, **kw):
        output_file = super(PDFDownloadView, self).__call__(*args, **kw)
        mimetype = os.path.splitext(os.path.basename(output_file))[1]
        R = self.request.response
        R.setHeader('content-type', 'application/%s' % mimetype)
        R.setHeader('content-disposition', 'attachment; filename="%s%s"' % (self.context.getId(), mimetype))
        R.setHeader('pragma', 'no-cache')
        R.setHeader('cache-control', 'no-cache')
        R.setHeader('Expires', 'Fri, 30 Oct 1998 14:19:41 GMT')
        R.setHeader('content-length', os.path.getsize(output_file))
        return filestream_iterator(output_file, 'rb').read()

InitializeClass(PDFDownloadView)
