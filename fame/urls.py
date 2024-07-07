from django.urls import path

from fame.views.html import fame_list, get_experts
from fame.views.rest import ExpertiseAreasApiView, FameUsersApiView, FameListApiView
from socialnetwork.views.html import follow, unfollow
app_name = "fame"

urlpatterns = [
    path(
        "api/expertise_areas", ExpertiseAreasApiView.as_view(), name="expertise_areas"
    ),
    path("api/users", FameUsersApiView.as_view(), name="fame_users"),
    path("api/fame", FameListApiView.as_view(), name="fame_fulllist"),
    path("html/fame", fame_list, name="fame_list"),
    path("api/experts",get_experts, name="experts" ),
    path("html/fame/unfollow", unfollow, name="unfollow"),
    path("html/fame/follow", follow, name = "follow")

]
