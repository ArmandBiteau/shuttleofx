

class Bundle:
    def __init__(self, bundleId, name, userId):
        self.bundleId = bundleId
        self.userId = userId
        self.companyId = None
        self.name = name
        self.description = ""
        self.shared = False
        self.contributors = []
        self.architecture = []
        self.plugins = []
        self.uploaded = False

    def setDescription(self, description):
        self.description = description

    def addPluginId(self, plugin):
        self.plugin.append(plugin)

    def printBundle():
        print "Bundle :"
        print "bundleId:", self.bundleId
        print "userId:", self.userId
        print "companyId:", self.companyId
        print "name:", self.name
        print "description:", self.description
        print "shared:", self.shared
        print "contributors:", self.contributors
        print "architecture:", self.architecture
        print "plugins:", self.plugins
        print "uploaded:", self.uploaded
