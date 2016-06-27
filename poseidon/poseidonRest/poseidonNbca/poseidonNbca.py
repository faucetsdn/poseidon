class poseidonNbca:
    def __init__(self):
        self.modName = 'poseidonNbca'

    def on_get(self, req, resp, resource):
        resp.content_type = 'text/text'
        try:
            resp.body = self.modName + ' found: %s' % (resource)
        except:  # pragma: no cover
            pass
