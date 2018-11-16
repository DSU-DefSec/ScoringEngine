from ..server import app

@app.template_filter('service_short')
def service_short(text):
    """Return the part of a service name after the last '-'"""
    return text.split('-')[-1]
