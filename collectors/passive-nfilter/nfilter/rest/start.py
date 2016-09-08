import web


class StartR:
    """
    This endpoint is for starting a filter
    """

    @staticmethod
    def GET(filter_id):
        web.header('Content-Type', 'text/html')
        return filter_id
