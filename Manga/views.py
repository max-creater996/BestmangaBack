from rest_framework import generics, status, permissions, mixins
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import *
from .models import *
from django.db.models import OuterRef, Subquery
from django.contrib.contenttypes.models import ContentType

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 4
    page_size_query_param = 'page_size'
    max_page_size = 1000

class Manga_chapter_add(generics.CreateAPIView):
    serializer_class = MangaChaptersSerializersAdd
    queryset = MangaChapters.objects.all()
    def post(self, request, *args, **kwargs):
        x = self.kwargs['pk']
        writer_user_id = Manga.objects.get(id=kwargs['pk']).writer_user_id
        if str(writer_user_id) == str(request.user.username):
            request.data['manga'] = kwargs['pk']
            request.data['chapter_number'] = MangaChapters.objects.filter(manga=x).order_by("-chapter_number")[0].chapter_number + 1
            return self.create(request, *args, **kwargs)
        else:
            print("blya")
            return Response(status=status.HTTP_401_UNAUTHORIZED)

class MangaChapterDetailView(generics.RetrieveAPIView):
    serializer_class = MangaChapterDetailSerializer
    lookup_field = "chapter_number"

    def get_queryset(self):
        manga = get_object_or_404(Manga, slug=self.kwargs["slug"])
        return MangaChapters.objects.filter(manga=manga)


class MangaChapterLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        chapter = get_object_or_404(MangaChapters, pk=pk)
        user = request.user

        if chapter.likes.filter(id=user.id).exists():
            chapter.likes.remove(user)
            liked = False
        else:
            chapter.likes.add(user)
            liked = True

        return Response({"liked": liked, "total_likes": chapter.total_likes()})


class MangaChapterListView(generics.ListAPIView):
    serializer_class = MangaChapterListSerializer

    def get_queryset(self):
        manga = get_object_or_404(Manga, slug=self.kwargs["slug"])
        return MangaChapters.objects.filter(manga=manga).order_by("-chapter_number")  # Сортировка по номеру главы

class User_manga(generics.ListAPIView):
    serializer_class = MangaSerializer
    lookup_field = "slug"
    def get_queryset(self):
        return Manga.objects.filter(writer_user_id=self.request.user.id)

class One_manga_add_API(generics.CreateAPIView):
    queryset = Manga.objects.all()
    permission_classes = [IsAuthenticated, ]
    serializer_class = MangaAddSerializer

    def post(self, request, *args, **kwargs):
        request.data["writer_user_id"] = request.user.id
        return self.create(request, *args, **kwargs)

class One_Manga_API(generics.RetrieveAPIView):
    lookup_field = "slug"
    queryset = Manga.objects.all()
    permission_classes = [IsAuthenticated, ]
    serializer_class = MangaSerializer

    def retrieve(self, request, *args, **kwargs):
        manga = self.get_object()
        if request.user.is_authenticated:
            manga.increment_views(request.user)  # Передаём пользователя
        return super().retrieve(request, *args, **kwargs)

class MangaPageCommentView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        page_id = self.kwargs.get("pageID")
        return Comment.objects.filter(content_type__model="mangapage", object_id=page_id, parent__isnull=True)

    def perform_create(self, serializer):
        page_id = self.kwargs.get("pageID")
        content_type = ContentType.objects.get(model="mangapage")
        serializer.save(
            content_type=content_type,
            object_id=page_id,
            user=self.request.user,
        )

class Tags_API(generics.ListAPIView):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializers

class Country_show_API(generics.ListAPIView):
    serializer_class = CountrySerializers
    queryset = Country.objects.all()

class Country_one_show_API(generics.RetrieveAPIView):
    serializer_class = CountrySerializers
    queryset = Country.objects.all()

class Manga_last_chapter(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request,*args, **kwargs):
        x = self.kwargs['pk']
        return Response({"chapter_number": MangaChapters.objects.filter(manga=x).order_by("-chapter_number")[0].chapter_number})

class Manga_chapters_API(generics.ListAPIView):
    """
        Manga Chapters API

        get:
        Return a list of all the manga chapters.
        """
    """
        API возвращает последние главы каждой манги.
        """
    serializer_class = MangaChaptersSerializers

    def get_queryset(self):
        latest_chapter_subquery = MangaChapters.objects.filter(
            manga=OuterRef("manga")
        ).order_by("-chapter_number").values("id")[:1]

        return MangaChapters.objects.filter(id__in=Subquery(latest_chapter_subquery))

class AddLike(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, format=None):
        try:
            post = Manga.objects.get(pk=pk)
        except Manga.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        is_dislike = False

        for dislike in post.dislikes.all():
            if dislike == request.user:
                is_dislike = True
                break

        if is_dislike:
            post.dislikes.remove(request.user)

        is_like = False

        for like in post.likes.all():
            if like == request.user:
                is_like = True
                break

        if not is_like:
            post.likes.add(request.user)

        if is_like:
            post.likes.remove(request.user)

        return Response(status=status.HTTP_200_OK)

class User_show(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        return Response({"user_id": request.user.pk})

class AddDislike(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request, pk, format=None):
        try:
            post = Manga.objects.get(pk=pk)
        except Manga.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        like_exists = post.likes.filter(id=request.user.id).exists()
        if like_exists:
            post.likes.remove(request.user)

        dislike_exists = post.dislikes.filter(id=request.user.id).exists()
        if not dislike_exists:
            post.dislikes.add(request.user)
        else:
            post.dislikes.remove(request.user)

        return Response(status=status.HTTP_200_OK)
