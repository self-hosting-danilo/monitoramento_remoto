from django.db import models

class Hospital(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


class AirCentral(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)


class OxygenCentral(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)

class ChatTelegram(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    chat_id = models.CharField(verbose_name='Id chat', null=True, blank=True)

