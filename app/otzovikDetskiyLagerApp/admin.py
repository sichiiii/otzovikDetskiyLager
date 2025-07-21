from django.contrib import admin
from .models import User, GameSituation, Expert, Participant, Volunteer, Document, Photo, Video, FestivalStage

admin.site.register(User)
admin.site.register(GameSituation)
admin.site.register(Expert)
admin.site.register(Participant)
admin.site.register(Volunteer)
admin.site.register(Document)
admin.site.register(Photo)
admin.site.register(Video)
admin.site.register(FestivalStage)
