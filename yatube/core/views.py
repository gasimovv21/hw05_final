from django.shortcuts import render


def page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)

def http_version_not_supported(request, *args, **argv):
    return render(request, 'core/500.html', status=500)

def forbidden(request, exception):
    return render(request, 'core/403.html',  {'path': request.path}, status=403)

def csrf_failure(request, reason=''):
    return render(request, 'core/403csrf.html')
