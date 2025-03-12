from django.contrib import admin
from .models import *

# Настройка отображения страницы главы манги
class MangaPageInline(admin.TabularInline):
    model = MangaChapters.pages.through
    extra = 1  # количество пустых полей для добавления

# Настройка глав манги
class MangaChaptersInline(admin.TabularInline):
    model = MangaChapters
    extra = 1  # количество пустых полей для добавления
    inlines = [MangaPageInline]  # Подключение страниц главы

@admin.register(Manga)
class MangaAdmin(admin.ModelAdmin):
    list_display = ('manga_name', 'manga_status', 'translation_status', 'country', 'date_join', 'last_update')
    search_fields = ('manga_name', 'manga_status', 'translation_status')
    list_filter = ('manga_status', 'translation_status', 'country')
    inlines = [MangaChaptersInline]  # Включение глав для манги

    # Связываем slug с manga_name
    prepopulated_fields = {'slug': ('manga_name',)}

@admin.register(MangaChapters)
class MangaChaptersAdmin(admin.ModelAdmin):
    list_display = ('chapter_title', 'chapter_number', 'manga', 'date_time')
    search_fields = ('chapter_title', 'chapter_number')
    list_filter = ('manga', 'date_time')
    inlines = [MangaPageInline]  # Включение страниц главы

@admin.register(MangaVolume)
class MangaVolumeAdmin(admin.ModelAdmin):
    list_display = ('manga',"volume_number")
    search_fields = ('manga',"volume_number")

@admin.register(MangaPage)
class MangaPageAdmin(admin.ModelAdmin):
    list_display = ('page_number',)
    search_fields = ('page_number',)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('country_name',)
    search_fields = ('country_name',)

@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('tags', 'description_short')
    search_fields = ('tags',)

@admin.register(MangaView)
class MangaViewAdmin(admin.ModelAdmin):
    list_display = ('manga',)
    search_fields = ('manga',)


@admin.register(Comment)
class MangaViewAdmin(admin.ModelAdmin):
    list_display = ('user',"created_at")
    search_fields = ('user',"created_at")
