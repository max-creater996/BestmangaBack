from django.db import models
from django.db.models import F
from Users.models import User


class Country(models.Model):
    country_name = models.CharField(max_length=155)
    country_banner = models.ImageField(upload_to="photos/%Y/%m/%d/")

    def __str__(self):
        return self.country_name


class MangaVolume(models.Model):
    volume_number = models.IntegerField()
    manga = models.ForeignKey("Manga", related_name="volumes", on_delete=models.CASCADE)
    cover_image = models.ImageField(upload_to='manga_volumes/', null=True, blank=True)

    def __str__(self):
        return f'{self.volume_number}'

    class Meta:
        ordering = ["volume_number"]


class MangaChapters(models.Model):
    chapter_title = models.CharField(max_length=155)
    date_time = models.DateTimeField(auto_now_add=True, null=True)
    chapter_number = models.IntegerField(default=0)
    manga = models.ForeignKey("Manga", related_name="chapters", on_delete=models.SET_NULL, null=True)
    volume = models.ForeignKey(MangaVolume, related_name="chapters", on_delete=models.SET_NULL, null=True, blank=True)
    pages = models.ManyToManyField('MangaPage', related_name="chapter_pages")
    likes = models.ManyToManyField(User, blank=True, related_name='chapter_likes')

    def __str__(self):
        return f'Том {self.volume.volume_number if self.volume else "-"}, Глава {self.chapter_number}: {self.chapter_title}'

    def total_likes(self):
        return self.likes.count()

    class Meta:
        ordering = ["volume", "-chapter_number"]


class MangaPage(models.Model):
    image = models.ImageField(upload_to='manga_pages/')
    page_number = models.IntegerField()

    def __str__(self):
        return f'Page {self.page_number}'


class MangaView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    manga = models.ForeignKey("Manga", on_delete=models.CASCADE, related_name="views_log")
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'manga')


class Manga(models.Model):
    manga_status_choices = (
        ("выпускается", "выпускается"),
        ("работа приостановлена", "работа приостановлена"),
        ("Заброшенна", "Заброшенна")
    )
    translation_status_choices = (
        ("перевод идет", "перевод идет"),
        ("перевод приостановлен", "перевод приостановлен"),
        ("Заброшенна", "Заброшенна")
    )
    mangatypes_choices = (
        ("манга", "манга"),
        ("манхва", "манхва"),
        ("маньхуа", "маньхуа"),
        ("руманга", "руманга"),
    )
    slug = models.SlugField(unique=True)
    writer_user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="writer")
    manga_name = models.CharField(max_length=255, unique=True)
    manga_title = models.TextField()
    manga_img = models.ImageField(upload_to="photos/%Y/%m/%d/", null=True)
    date_join = models.DateField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField("Tags")
    country = models.ForeignKey(Country, on_delete=models.SET_DEFAULT, default="неизвестно")
    manga_status = models.CharField(max_length=155, choices=manga_status_choices)
    translation_status = models.CharField(max_length=155, choices=translation_status_choices)
    manga_type = models.CharField(max_length=50, choices=mangatypes_choices)
    note = models.CharField(max_length=255, default="отсутствует")
    likes = models.ManyToManyField(User, blank=True, related_name='likes')
    dislikes = models.ManyToManyField(User, blank=True, related_name='dislikes')
    views = models.PositiveIntegerField(default=0)

    def increment_views(self, user):
        if not MangaView.objects.filter(user=user, manga=self).exists():
            MangaView.objects.create(user=user, manga=self)
            Manga.objects.filter(id=self.id).update(views=F('views') + 1)

    def total_likes(self):
        return self.likes.count()

    def total_dislikes(self):
        return self.dislikes.count()

    def __str__(self):
        return self.manga_name


class Tags(models.Model):
    tags = models.CharField(max_length=55, unique=True)
    description_short = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.tags


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    def __str__(self):
        return f'{self.user.username}'

    class Meta:
        ordering = ["-created_at"]