from django.db.models import Q

from fame.models import Fame, FameLevels, ExpertiseAreas
from socialnetwork.models import Posts, SocialNetworkUsers, PostExpertiseAreasAndRatings

# general methods independent of html and REST views
# should be used by REST and html views


def _get_social_network_user(user) -> SocialNetworkUsers:
    """Given a FameUser, gets the social network user from the request. Assumes that the user is authenticated."""
    try:
        user = SocialNetworkUsers.objects.get(id=user.id)
    except SocialNetworkUsers.DoesNotExist:
        raise PermissionError("User does not exist")
    return user


def timeline(user: SocialNetworkUsers, start: int = 0, end: int = None, published=True):
    """Get the timeline of the user. Assumes that the user is authenticated."""
    _follows = user.follows.all()
    posts = Posts.objects.filter(
        (Q(author__in=_follows) & Q(published=published)) | Q(author=user)
    ).order_by("-submitted")
    if end is None:
        return posts[start:]
    else:
        return posts[start : end + 1]


def search(keyword: str, start: int = 0, end: int = None, published=True):
    """Search for all posts in the system containing the keyword. Assumes that all posts are public"""
    posts = Posts.objects.filter(
        Q(content__icontains=keyword)
        | Q(author__email__icontains=keyword)
        | Q(author__first_name__icontains=keyword)
        | Q(author__last_name__icontains=keyword),
        published=published,
    ).order_by("-submitted")
    if end is None:
        return posts[start:]
    else:
        return posts[start : end + 1]


def follows(user: SocialNetworkUsers, start: int = 0, end: int = None):
    """Get the users followed by this user. Assumes that the user is authenticated."""
    _follows = user.follows.all()
    if end is None:
        return _follows[start:]
    else:
        return _follows[start : end + 1]


def followers(user: SocialNetworkUsers, start: int = 0, end: int = None):
    """Get the followers of this user. Assumes that the user is authenticated."""
    _followers = user.followed_by.all()
    if end is None:
        return _followers[start:]
    else:
        return _followers[start : end + 1]


def follow(user: SocialNetworkUsers, user_to_follow: SocialNetworkUsers):
    """Follow a user. Assumes that the user is authenticated. If user already follows the user, signal that."""
    if user_to_follow in user.follows.all():
        return {"followed": False}
    user.follows.add(user_to_follow)
    user.save()
    return {"followed": True}


def unfollow(user: SocialNetworkUsers, user_to_unfollow: SocialNetworkUsers):
    """Unfollow a user. Assumes that the user is authenticated. If user does not follow the user anyway, signal that."""
    if user_to_unfollow not in user.follows.all():
        return {"unfollowed": False}
    user.follows.remove(user_to_unfollow)
    user.save()
    return {"unfollowed": True}


def submit_post(
    user: SocialNetworkUsers,
    content: str,
    cites: Posts = None,
    replies_to: Posts = None,
):
    """Submit a post for publication. Assumes that the user is authenticated.
    returns a tuple of three elements:
    1. a dictionary with the keys "published" and "id" (the id of the post)
    2. a list of dictionaries containing the expertise areas and their truth ratings
    3. a boolean indicating whether the user was banned and logged out and should be redirected to the login page
    """

    # Create post instance
    post = Posts.objects.create(
        content=content,
        author=user,
        cites=cites,
        replies_to=replies_to,
    )

    # Classify the content into expertise areas
    contains_bullshit, expertise_areas = post.determine_expertise_areas_and_truth_ratings()

    # Assume the post can be published initially
    post.published = not contains_bullshit

    # Initialize the redirect to logout flag
    redirect_to_logout = False

    #########################
    # T1 Implementation 
    #########################

    # Fetching the user's fame level
    fame_levels = Fame.objects.filter(user=user)
    
    # Going through expertise area of the post
    for area in expertise_areas:
        # Check fame level for the expertise area and then prevent the post from being published if the fame level is negative
        negative_fame = fame_levels.filter(expertise_area=area['expertise_area'], fame_level__numeric_value__lte=0)
        if negative_fame.exists():
            post.published = False
            break

    #########################
    # T2 Implementation 
    #########################

    negative_truth_ratings = PostExpertiseAreasAndRatings.objects.filter(post=post, truth_rating__numeric_value__lt=0)

    for elem in negative_truth_ratings:
        expertise_area = elem.expertise_area
        current_fame = fame_levels.filter(expertise_area=expertise_area).first()

        if current_fame:
            try:
                next_lower_fame_level = current_fame.fame_level.get_next_lower_fame_level()
                current_fame.fame_level = next_lower_fame_level
                current_fame.save()
            except ValueError:
                # Ban user and unpublish their posts
                user.is_active = False
                user.is_banned = True
                user.save()
                redirect_to_logout = True
                Posts.objects.filter(author=user).update(published=False)
                break  # Exit the loop as the user is banned
        else:
            Fame.objects.create(user=user, expertise_area=expertise_area, fame_level=FameLevels.objects.get(name="Confuser"))

    post.save()

    return (
        {"published": post.published, "id": post.id},
        expertise_areas,
        redirect_to_logout,
    )



def rate_post(
    user: SocialNetworkUsers, post: Posts, rating_type: str, rating_score: int
):
    """Rate a post. Assumes that the user is authenticated. If user already rated the post with the given rating_type,
    update that rating score."""
    user_rating = None
    try:
        user_rating = user.userratings_set.get(post=post, rating_type=rating_type)
    except user.userratings_set.model.DoesNotExist:
        pass

    if user == post.author:
        raise PermissionError(
            "User is the author of the post. You cannot rate your own post."
        )

    if user_rating is not None:
        # update the existing rating:
        user_rating.rating_score = rating_score
        user_rating.save()
        return {"rated": True, "type": "update"}
    else:
        # create a new rating:
        user.userratings_set.add(
            post,
            through_defaults={"rating_type": rating_type, "rating_score": rating_score},
        )
        user.save()
        return {"rated": True, "type": "new"}


def fame(user: SocialNetworkUsers):
    """Get the fame of a user. Assumes that the user is authenticated."""
    try:
        user = SocialNetworkUsers.objects.get(id=user.id)
    except SocialNetworkUsers.DoesNotExist:
        raise ValueError("User does not exist")

    return user, Fame.objects.filter(user=user)




def experts():
    """Return for each existing expertise area in the fame profiles a list of the users having positive fame for that
    expertise area. The list should be a Python dictionary with keys ``user'' (for the user) and ``fame_level_numeric''
    (for the corresponding fame value), and should be ranked, i.e. users with the highest fame are shown first, in case
    there is a tie, within that tie sort by date_joined (most recent first). Note that expertise areas with no expert
    may be omitted.
    """
    
        
    #########################
    # T3 Implementation 
    #########################

    
    user_expertise = {}

    # Fetching all expertise areas
    expertise_areas = ExpertiseAreas.objects.all()

    for area in expertise_areas:
        # Fetching positive fame level users for the current expertise area
        area_experts = Fame.objects.filter(expertise_area=area, fame_level__numeric_value__gt=0).order_by('-fame_level__numeric_value', 'user__date_joined')
        
        # Return only expertise areas with experts
        if area_experts.exists():
            user_expertise[area.id] = []

            for expert in area_experts:
                user = expert.user
                fame_level_numeric = expert.fame_level.numeric_value
                
                user_expertise[area.id].append({"user": user, "fame_level_numeric": fame_level_numeric})
        
    return user_expertise
      


def bullshitters():
    """Return for each existing expertise area in the fame profiles a list of the users having negative fame for that
    expertise area. The list should be a Python dictionary with keys ``user'' (for the user) and ``fame_level_numeric''
    (for the corresponding fame value), and should be ranked, i.e. users with the lowest fame are shown first, in case
    there is a tie, within that tie sort by date_joined (most recent first). Note that expertise areas with no expert
    may be omitted.
    """
    
    #########################
    # T4 Implementation 
    #########################


    user_bullshitter = {}

    # Fetching all expertise areas
    expertise_areas = ExpertiseAreas.objects.all()

    for area in expertise_areas:
        # Fetching negative fame level users for the current expertise area
        area_bullshitters = Fame.objects.filter(expertise_area=area, fame_level__numeric_value__lt=0).order_by('fame_level__numeric_value', 'user__date_joined')
        
        # Return only expertise areas with bullshitters
        if area_bullshitters.exists():
            user_bullshitter[area.id] = []

            for bullshitter in area_bullshitters:
                user = bullshitter.user
                fame_level_numeric = bullshitter.fame_level.numeric_value
                
                user_bullshitter[area.id].append({"user": user, "fame_level_numeric": fame_level_numeric})
        
    return user_bullshitter
