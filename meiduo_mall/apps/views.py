from django.http import HttpResponse
import logging

logger = logging.getLogger('django')
def log(request):

    logger.info('hehehda')

    return HttpResponse("黑")