from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import resolve, reverse
from django.urls.exceptions import Resolver404

unauthentication_allowed_url_names = [
    'login',
    'register',
    'logout'
]


def request_validation(get_response):

    def middleware(request):
        error = False
        try:
            resolved_url = resolve(request.path)
        except Resolver404:
            if settings.ENVIRONMENT == 'prod':
                return render(
                        request,
                        'giftexchange/errors/error.html',
                        context={},
                        status=404
                    )
        # if not resolved_url.url_name in unauthentication_allowed_url_names:
        #     if not request.session.get('user_is_authenticated'):
        #         if settings.ENVIRONMENT == 'prod':
        #             return render(
        #                 request,
        #                 'giftexchange/errors/login_required.html',
        #                 context={},
        #                 status=403
        #             )

        response = get_response(request)
        status_code = str(response.status_code)

        if status_code.startswith('5') or status_code.startswith('4'):
            if settings.ENVIRONMENT == 'prod':
                return render(
                        request,
                        'giftexchange/errors/error.html',
                        context={},
                        status=response.status_code
                    )

        return response

    return middleware
