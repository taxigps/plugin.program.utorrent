import urllib, urllib2, cookielib, sys, os
from base64 import b64encode
import xbmc
import urlparse

__addonname__ = sys.modules[ "__main__" ].__addonname__
__addon__     = sys.modules[ "__main__" ].__addon__
__language__  = sys.modules[ "__main__" ].__language__

# base paths
BASE_DATA_PATH = sys.modules[ "__main__" ].__profile__
BASE_RESOURCE_PATH = sys.modules[ "__main__" ].BASE_RESOURCE_PATH
COOKIEFILE = os.path.join( BASE_DATA_PATH, "uTorrent_cookies" )

def _create_base_paths():
    """ creates the base folders """
    if ( not os.path.isdir( BASE_DATA_PATH ) ):
        os.makedirs( BASE_DATA_PATH )
_create_base_paths()

class Url(object):
    def __init__(self, address=None, port=8080, user=None, password=None, path='/gui/', https=False):
        url = '{proto}://{username}:{password}@{hostname}:{port}/{path}/'.format(
            proto='https' if https else 'http',
            username=urllib.quote(user),
            password=urllib.quote(password),
            hostname=address,
            port=port,
            path=path.strip('/')
        )
        self.token = None
        self.url = urlparse.urlparse(url)

    def getBaseUrl(self, withToken=False):
        query = ''
        if withToken:
            query = '?token=' + urllib.quote_plus(self.token)
        return '{proto}://{hostname}:{port}/{path}/{query}'.format(
            proto=self.url.scheme,
            hostname=self.url.hostname,
            port=self.url.port,
            path=self.url.path.strip('/'),
            query=query
        )

    def getActionUrl(self, action='', hash=''):
        params = {
            'token': self.token,
            'action': action
        }
        if hash:
            params['hash'] = hash

        query = dict(urlparse.parse_qsl(self.url.query))
        query.update(params)
        query = urllib.urlencode(query)
        if query:
            query = '?' + query

        return '{proto}://{hostname}:{port}/{path}/{query}'.format(
            proto=self.url.scheme,
            hostname=self.url.hostname,
            port=self.url.port,
            path=self.url.path.strip('/'),
            query=query
        )

    def getProxyUrl(self, sid, f):
        path = self.url.path.strip('/').split('/')
        path.pop()
        path = '/'.join(path)
        query = urllib.urlencode({
            'sid': sid,
            'file': f
        })
        return '{proto}://{username}:{password}@{hostname}:{port}/{path}/proxy?{query}'.format(
            proto=self.url.scheme,
            username=urllib.quote(self.url.username),
            password=urllib.quote(self.url.password),
            hostname=self.url.hostname,
            port=self.url.port,
            path=path,
            query=query
        )

def MultiPart(fields,files,ftype) :
    Boundary = '----------ThIs_Is_tHe_bouNdaRY_---$---'
    CrLf = '\r\n'
    L = []

    ## Process the Fields required..
    for (key, value) in fields:
        L.append('--' + Boundary)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    ## Process the Files..
    for (key, filename, value) in files:
        L.append('--' + Boundary)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        ## Set filetype based on .torrent or .nzb files.
        if ftype == 'torrent':
            filetype = 'application/x-bittorrent'
        else:
            filetype = 'text/xml'
        L.append('Content-Type: %s' % filetype)
        ## Now add the actual Files Data
        L.append('')
        L.append(value)
    ## Add End of data..
    L.append('--' + Boundary + '--')
    L.append('')
    ## Heres the Main stuff that we will be passing back..
    post = CrLf.join(L)
    content_type = 'multipart/form-data; boundary=%s' % Boundary
    ## Return the formatted data..
    return content_type, post

class Client(object):
    def __init__(self, baseurl):
        self.baseurl = baseurl
        self.token = None
        if baseurl.url.username:
            password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_manager.add_password(realm=None, uri=baseurl.getBaseUrl(), user=baseurl.url.username, passwd=baseurl.url.password)
            self.MyCookies = cookielib.LWPCookieJar()
            if os.path.isfile(COOKIEFILE):
                self.MyCookies.load(COOKIEFILE)
            opener = urllib2.build_opener(
                urllib2.HTTPCookieProcessor(self.MyCookies)
                , urllib2.HTTPBasicAuthHandler(password_manager)
                , urllib2.HTTPDigestAuthHandler(password_manager)
            )
            opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) chromeframe/4.0')]
            urllib2.install_opener(opener)


    def CmdGetToken(self):
        data = self.HttpCmd('token.html')
        return data

    def HttpCmd(self, path, postdta=None, content=None):
        url = self.baseurl.getBaseUrl()
        url = urlparse.urljoin(url, path)

        xbmc.log( "%s::HttpCmd - url: %s" % ( __addonname__, url ), xbmc.LOGDEBUG )
        ## Standard code

        req = urllib2.Request(url,postdta)

        ## Process only if Upload..
        if content != None   :
                req.add_header('Content-Type',content)
                req.add_header('Content-Length',str(len(postdta)))

        response = urllib2.urlopen(req)
        link=response.read()
        xbmc.log( "%s::HttpCmd - data: %s" % ( __addonname__, str(link) ), xbmc.LOGDEBUG )
        response.close()
        self.MyCookies.save(COOKIEFILE)
        return link


