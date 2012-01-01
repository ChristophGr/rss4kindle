def escapeFileName(name, escapechar = "_"):
    import re
    return re.sub("[:\/\\\\\?!]", "_", name)

def download(url, dest = None, force = False):
    import os
    print "downloading " + url
    if not dest:
        dest = escapeFileName(url)
    if not force and os.path.exists(dest):
        return dest
    import urllib
    webFile = urllib.urlopen(url)
    localFile = open(dest, 'w')
    localFile.write(webFile.read())
    webFile.close()
    localFile.close()
    return dest