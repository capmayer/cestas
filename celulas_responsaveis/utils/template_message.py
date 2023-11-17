from django.shortcuts import render


def consumer_message(request, message):
    context = {"back_url": request.META.get("HTTP_REFERER", ""), "message": message}
    return render(request, "info_message.html", context)
