from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from fame.views.html import fame_list
from socialnetwork import api
from socialnetwork.api import _get_social_network_user
from socialnetwork.serializers import PostsSerializer
from fame.serializers import FameSerializer
from socialnetwork.models import SocialNetworkUsers

@require_http_methods(["GET"])
@login_required
def timeline(request):
    # using the serializer to get the data, then use JSON in the template!
    # avoids having to do the same thing twice

    # get extra URL parameters:
    keyword = request.GET.get("search", "")
    published = request.GET.get("published", True)
    error = request.GET.get("error", None)

    # if keyword is not empty, use search method of API:
    if keyword and keyword != "":
        context = {
            "posts": PostsSerializer(
                api.search(keyword, published=published), many=True
            ).data,
            "searchkeyword": keyword,
            "error": error,
        }
    else:  # otherwise, use timeline method of API:
        context = {
            "posts": PostsSerializer(
                api.timeline(
                    _get_social_network_user(request.user), published=published
                ),
                many=True,
            ).data,
            "searchkeyword": "",
            "error": error,
        }

    return render(request, "timeline.html", context=context)


@require_http_methods(["POST"])
@login_required
def follow(request):
    myuser = _get_social_network_user(request.user)
    userid = request.POST.get("follow")
    user = SocialNetworkUsers.objects.get(id=int(userid))
    x = api.follow(myuser, user)
    user, fame = api.fame(user)
    if (x== True):
        follows_bool = True
    else:
        follows_bool = False
    context = {
        "fame": FameSerializer(fame, many=True).data,
        "user": user if user else "",
        "follows_bool": follows_bool,
        "userid": userid
    }
    return fame_list(request)

@require_http_methods(["POST"])
@login_required
def unfollow(request):
    #raise NotImplementedError("Not implemented yet")
    myuser = _get_social_network_user(request.user)
    userid = request.POST.get("unfollow")
    user = SocialNetworkUsers.objects.get(id=int(userid))
    x = api.unfollow(myuser, user)
    user, fame = api.fame(user)
    if (x== True):
        follows_bool = False
    else:
        follows_bool = True
    context = {
        "fame": FameSerializer(fame, many=True).data,
        "user": user if user else "",
        "follows_bool": follows_bool,
        "userid": userid
    }
    return fame_list(request)
