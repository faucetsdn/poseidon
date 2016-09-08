import web


class FiltersR:
    """
    This endpoint is for getting filters
    """

    @staticmethod
    def GET():
        web.header('Content-Type', 'text/html')
        return ''
