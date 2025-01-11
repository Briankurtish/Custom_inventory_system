class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f"Path: {request.path}, User: {request.user}, Authenticated: {request.user.is_authenticated}")
        return self.get_response(request)
