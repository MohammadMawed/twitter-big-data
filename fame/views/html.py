from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from fame.serializers import FameSerializer
from socialnetwork import api
from socialnetwork.api import _get_social_network_user
from socialnetwork.models import SocialNetworkUsers


@require_http_methods(["GET", "POST"])
@login_required
def fame_list(request):
    # try to get the user from the request parameters:
    userid = request.GET.get("userid", None)
    if (request.method =="POST"):
        if (request.POST.get("unfollow") != None):
            userid = request.POST.get("unfollow")
        else:
            userid = request.POST.get("follow")
    user = None
    follows_bool = None
    if userid is None:
        user = _get_social_network_user(request.user)
    else:
        try:
            myuser = _get_social_network_user(request.user)
            user = SocialNetworkUsers.objects.get(id=userid)
            followers = myuser.follows.all().filter(id = userid)
            if (len(followers)==1):
                follows_bool = True
            else:
                follows_bool = False
        except ValueError:
            pass
     
    user, fame = api.fame(user)
    context = {
        "userid" : userid,
        "fame": FameSerializer(fame, many=True).data,
        "user": user if user else "",
        "follows_bool": follows_bool
    }
    return render(request, "fame.html", context=context)

@require_http_methods(["GET"])
@login_required
def get_experts(request):
    context = api.experts()
    
    
    return render(request, "experts.html", context={"experts": api.experts()})
@require_http_methods(["GET"])
@login_required
def get_bulshitters(request):
    context = api.bullshitters()
    return render(request, "bulshitters.html", context={"bulshitters": api.bullshitters()})
