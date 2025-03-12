from django_rest_framework_recursive.fields import RecursiveField
from rest_framework import serializers
from .models import *


class TagsSerializers(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ["id", "tags"]


class MangaPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MangaPage
        fields = "__all__"


class MangaChapterListSerializer(serializers.ModelSerializer):
    pages = MangaPageSerializer(many=True, read_only=True)
    volume = serializers.StringRelatedField()
    is_liked = serializers.SerializerMethodField()
    total_likes = serializers.SerializerMethodField()

    def get_is_liked(self, obj):
        user = self.context["request"].user
        return user.is_authenticated and obj.likes.filter(id=user.id).exists()

    def get_total_likes(self, obj):
        return obj.total_likes()

    class Meta:
        model = MangaChapters
        fields = ["id", "chapter_title", "chapter_number", "is_liked", "total_likes", "date_time", "volume", "pages",
                  "manga"]


class MangaChapterDetailSerializer(serializers.ModelSerializer):
    pages = MangaPageSerializer(many=True, read_only=True)
    volume = serializers.StringRelatedField()
    manga = serializers.StringRelatedField()
    is_last_chapter = serializers.SerializerMethodField()
    is_first_chapter = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    total_likes = serializers.SerializerMethodField()

    class Meta:
        model = MangaChapters
        fields = [
            "id",
            "chapter_title",
            "chapter_number",
            "date_time",
            "manga",
            "volume",
            "pages",
            "is_last_chapter",
            "is_first_chapter",
            "is_liked",
            "total_likes",
        ]

    def get_is_last_chapter(self, obj):
        last_chapter = obj.volume.chapters.order_by("-chapter_number").first()
        return last_chapter == obj

    def get_is_first_chapter(self, obj):
        first_chapter = obj.volume.chapters.order_by("chapter_number").first()
        return first_chapter == obj

    def get_is_liked(self, obj):
        user = self.context["request"].user
        return user.is_authenticated and obj.likes.filter(id=user.id).exists()

    def get_total_likes(self, obj):
        return obj.total_likes()


class MangaVolumeSerializer(serializers.ModelSerializer):
    chapters = MangaChapterListSerializer(many=True, read_only=True)

    class Meta:
        model = MangaVolume
        fields = ["id", "volume_number", "cover_image", "chapters"]


class MangaSerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True)
    total_likes = serializers.SerializerMethodField()
    total_dislikes = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    disliked = serializers.SerializerMethodField()
    chapters = MangaChapterListSerializer(many=True, read_only=True)

    def get_liked(self, obj):
        request = self.context.get("request")
        return obj.likes.filter(id=request.user.id).exists()

    def get_disliked(self, obj):
        request = self.context.get("request")
        return obj.dislikes.filter(id=request.user.id).exists()

    def get_total_dislikes(self, obj):
        return obj.total_dislikes()

    def get_total_likes(self, obj):
        return obj.total_likes()

    class Meta:
        model = Manga
        fields = "__all__"

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    replies = RecursiveField(many=True, read_only=True)
    class Meta:
        model = Comment
        fields = ["id", "user", "content", "created_at", "replies", "parent"]

class MangaAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manga
        fields = "__all__"


class MangaChaptersSerializers(serializers.ModelSerializer):
    manga = MangaSerializer()
    volume = MangaVolumeSerializer()

    class Meta:
        model = MangaChapters
        fields = "__all__"


class MangaChaptersSerializersAdd(serializers.ModelSerializer):
    class Meta:
        model = MangaChapters
        fields = "__all__"


class MangaSerializerWriterId(serializers.ModelSerializer):
    writer_user_id = serializers.StringRelatedField()

    class Meta:
        model = Manga
        fields = ("writer_user_id",)


class CountrySerializers(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = "__all__"


class IntSer(serializers.Serializer):
    chapter_number = serializers.IntegerField()
