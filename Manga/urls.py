from django.urls import path
from .views import *

urlpatterns = [
    path("", Manga_chapters_API.as_view()),
    path("user_show", User_show.as_view()),
    path("country", Country_show_API.as_view()),
    path("country/<int:pk>", Country_one_show_API.as_view()),
    path("manga/<slug:slug>/<int:chapter_number>/", MangaChapterDetailView.as_view()),
    path("manga/<int:pageID>/comments", MangaPageCommentView.as_view()),
    path("manga/<slug:slug>", One_Manga_API.as_view()),
    path("manga/<slug:slug>/chapters/", MangaChapterListView.as_view()),
    path('manga/chapters/<int:pk>/like/', MangaChapterLikeAPIView.as_view()),
    path("manga/add/", One_manga_add_API.as_view()),
    path("tags_list",Tags_API.as_view()),
    path("<int:pk>", One_Manga_API.as_view()),
    path('<int:pk>/like/', AddLike.as_view()),
    path('<int:pk>/dislike/', AddDislike.as_view()),
    path("user_renobe",User_manga.as_view()),
    path("manga/chapters_add/<int:pk>",Manga_chapter_add.as_view()),
    path("last_chapter/<int:pk>",Manga_last_chapter.as_view()),
]
