import web

class FiltersR:
    """
    This endpoint is for getting filters
    """
    def GET(self):
        web.header("Content-Type","text/html")
        return ""
