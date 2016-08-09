import web

class StartR:
    """
    This endpoint is for starting a filter
    """
    def GET(self, filter_id):
        web.header("Content-Type","text/html")
        return filter_id
