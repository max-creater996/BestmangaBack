from rest_framework import generics, status, permissions, mixins
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import *
from .models import *
from django.db.models import OuterRef, Subquery
from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import PermissionDenied
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 4
    page_size_query_param = 'page_size'
    max_page_size = 1000


class Manga_chapter_add(generics.CreateAPIView):
    serializer_class = MangaChaptersSerializersAdd
    queryset = MangaChapters.objects.all()
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        slug = self.kwargs["slug"]
        try:
            manga = Manga.objects.get(slug=slug)
        except Manga.DoesNotExist:
            return Response({"error": "Manga not found"}, status=status.HTTP_404_NOT_FOUND)

        if str(manga.writer_user_id) != str(request.user.username):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()
        data["manga"] = manga.id

        # Определение номера новой главы
        last_chapter = MangaChapters.objects.filter(manga=manga).order_by("-chapter_number").first()
        chapter_number = last_chapter.chapter_number + 1 if last_chapter else 1
        data["chapter_number"] = chapter_number

        # Проверка, что предыдущая глава опубликована
        if last_chapter and not last_chapter.release:
            return Response({"error": "Нельзя создать новую главу, пока предыдущая не опубликована"},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class Manga_chapter_update(generics.UpdateAPIView):
    serializer_class = MangaChaptersSerializersAdd
    permission_classes = (IsAuthenticated,)
    lookup_field = 'chapter_number'

    def get_queryset(self):
        slug = self.kwargs["slug"]
        manga = get_object_or_404(Manga, slug=slug)
        return MangaChapters.objects.filter(manga=manga)

    def update(self, request, *args, **kwargs):
        slug = self.kwargs["slug"]
        try:
            manga = Manga.objects.get(slug=slug)
        except Manga.DoesNotExist:
            return Response({"error": "Manga not found"}, status=status.HTTP_404_NOT_FOUND)

        if str(manga.writer_user_id) != str(request.user.username):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        instance = self.get_object()
        data = request.data.copy()
        data["manga"] = manga.id

        # Проверка на уникальность номера главы, исключая текущий экземпляр
        if MangaChapters.objects.filter(
                manga=manga,
                chapter_number=data.get("chapter_number")
        ).exclude(pk=instance.pk).exists():
            return Response({"error": "Глава с таким номером уже существует"}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка на пропущенные главы
        last_chapter = MangaChapters.objects.filter(manga=manga).exclude(pk=instance.pk).order_by(
            "-chapter_number").first()
        if last_chapter and int(data.get("chapter_number", 0)) > last_chapter.chapter_number + 1:
            return Response({"error": "последняя глава не может быть больше чем на 1 от предыдущей"},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        return Response(serializer.data)


class AddPageToChapterView(generics.CreateAPIView):
    serializer_class = MangaPageSerializer
    queryset = MangaPage.objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        chapter = get_object_or_404(MangaChapters, id=self.kwargs.get("chapter_id"))
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            page_number = serializer.validated_data.get("page_number")
            existing_page = chapter.pages.filter(page_number=page_number).exists()

            if existing_page:
                return Response({"error": "Страница с таким номером уже существует в этой главе."},
                                status=status.HTTP_400_BAD_REQUEST)

            page = serializer.save()
            chapter.pages.add(page)
            return Response({"message": "Страница успешно добавлена", "page": serializer.data},
                            status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdatePageInChapterView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID страницы'),
                    'page_number': openapi.Schema(type=openapi.TYPE_INTEGER, description='Новый номер страницы'),
                },
                required=['id', 'page_number']
            ),
            description="Массив объектов с id страницы и новым page_number"
        )
    )
    def post(self, request, *args, **kwargs):
        chapter = get_object_or_404(MangaChapters, id=self.kwargs.get("chapter_id"))
        
        # Проверяем, что пользователь является автором манги
        if str(chapter.manga.writer_user_id) != str(request.user.username):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        # Получаем массив с новыми номерами страниц
        pages_data = request.data
        if not isinstance(pages_data, list):
            return Response({"error": "Expected array of pages"}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем формат данных
        for page_data in pages_data:
            if not isinstance(page_data, dict) or 'id' not in page_data or 'page_number' not in page_data:
                return Response({"error": "Each page should have 'id' and 'page_number'"}, 
                              status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что все страницы принадлежат этой главе
        page_ids = [page_data['id'] for page_data in pages_data]
        if not chapter.pages.filter(id__in=page_ids).count() == len(page_ids):
            return Response({"error": "Some pages don't belong to this chapter"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что новые номера страниц не конфликтуют
        new_page_numbers = [page_data['page_number'] for page_data in pages_data]
        if len(set(new_page_numbers)) != len(new_page_numbers):
            return Response({"error": "Duplicate page numbers found"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Обновляем номера страниц
        updated_pages = []
        for page_data in pages_data:
            page = chapter.pages.get(id=page_data['id'])
            page.page_number = page_data['page_number']
            page.save()
            updated_pages.append({
                'id': page.id,
                'page_number': page.page_number
            })

        return Response({
            "message": "Номера страниц успешно обновлены",
            "updated_pages": updated_pages
        }, status=status.HTTP_200_OK)


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

class MangaProfileChapterListView(generics.ListAPIView):
    serializer_class = MangaProfileChapterListSerializer

    def get_queryset(self):
        manga = get_object_or_404(Manga, slug=self.kwargs["slug"])
        return MangaChapters.objects.filter(manga=manga).order_by("-chapter_number")  # Сортировка по номеру главы

class User_manga(generics.ListAPIView):
    serializer_class = UserMangaSerializers
    def get_queryset(self):
        return Manga.objects.filter(writer_user_id=self.request.user.id)

class OneMangaAddAPI(generics.CreateAPIView):
    queryset = Manga.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = MangaAddSerializer
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data["writer_user_id"] = request.user.id
        serializer = self.get_serializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class One_Manga_API(generics.RetrieveAPIView):
    lookup_field = "slug"
    queryset = Manga.objects.all()
    serializer_class = MangaSerializer

    def retrieve(self, request, *args, **kwargs):
        manga = self.get_object()
        if request.user.is_authenticated:
            manga.increment_views(request.user)  # Передаём пользователя
        return super().retrieve(request, *args, **kwargs)

class ProfileMangaView(generics.RetrieveAPIView):
    lookup_field = "slug"
    queryset = Manga.objects.all()
    permission_classes = [IsAuthenticated, ]
    serializer_class = ProfileMangaSerializer

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
        last_chapter = MangaChapters.objects.filter(manga=x, release=True).order_by("-chapter_number").first()
        if last_chapter:
            return Response({"chapter_number": last_chapter.chapter_number})
        return Response({"error": "Нет доступных глав"}, status=status.HTTP_404_NOT_FOUND)

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
            manga=OuterRef("manga"),release=True
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

class MangaUpdateAPI(generics.UpdateAPIView):
    queryset = Manga.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = MangaAddSerializer
    parser_classes = (MultiPartParser, FormParser)
    lookup_field = 'slug'

    def update(self, request, *args, **kwargs):
        manga = self.get_object()
        
        # Check if the user is the writer of the manga
        if str(manga.writer_user_id) != str(request.user.username):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()
        # Don't allow changing the writer_user_id
        if 'writer_user_id' in data:
            del data['writer_user_id']
        
        serializer = self.get_serializer(manga, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class MangaVolumeListView(generics.ListAPIView):
    serializer_class = MangaAddVolumeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        slug = self.kwargs["slug"]
        manga = get_object_or_404(Manga, slug=slug)
        return MangaVolume.objects.filter(manga=manga).order_by("volume_number")

class MangaVolumeListCreateView(generics.ListCreateAPIView):
    serializer_class = MangaAddVolumeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        slug = self.kwargs["slug"]
        manga = get_object_or_404(Manga, slug=slug)
        return MangaVolume.objects.filter(manga=manga).order_by("volume_number")

    def perform_create(self, serializer):
        slug = self.kwargs["slug"]
        manga = get_object_or_404(Manga, slug=slug)
        # Проверяем, что текущий пользователь — автор манги
        if str(manga.writer_user_id) != str(self.request.user.username):
            raise PermissionDenied("Вы не являетесь автором этой манги.")
        serializer.save(manga=manga)

class MangaVolumeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MangaAddVolumeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        slug = self.kwargs["slug"]
        manga = get_object_or_404(Manga, slug=slug)
        return MangaVolume.objects.filter(manga=manga)

    def perform_destroy(self, instance):
        # Проверяем, что текущий пользователь — автор манги
        if str(instance.manga.writer_user_id) != str(self.request.user.username):
            raise PermissionDenied("Вы не являетесь автором этой манги.")
        
        # Проверяем, есть ли связанные главы
        if instance.chapters.exists():
            raise PermissionDenied("Нельзя удалить том, который содержит главы. Сначала удалите или переместите все главы из этого тома.")
        
        instance.delete()

class MangaChapterDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = 'chapter_number'

    def get_queryset(self):
        slug = self.kwargs["slug"]
        manga = get_object_or_404(Manga, slug=slug)
        return MangaChapters.objects.filter(manga=manga)

    def destroy(self, request, *args, **kwargs):
        slug = self.kwargs["slug"]
        try:
            manga = Manga.objects.get(slug=slug)
        except Manga.DoesNotExist:
            return Response({"error": "Manga not found"}, status=status.HTTP_404_NOT_FOUND)

        if str(manga.writer_user_id) != str(request.user.username):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
