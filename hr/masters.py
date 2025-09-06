from django.db import models


class District(models.Model):
"""Employee home district master (NOT for colleges)."""
name = models.CharField(max_length=120, unique=True)
state = models.CharField(max_length=120, blank=True)


class Meta:
ordering = ["name"]


def __str__(self):
return self.name


class College(models.Model):
code = models.CharField(max_length=20, unique=True, blank=True, help_text="Short code e.g., NGP13")
name = models.CharField(max_length=200, unique=True)
address = models.CharField(max_length=255, blank=True)


class Meta:
ordering = ["name"]


def __str__(self):
return f"{self.name} ({self.code})" if self.code else self.name


class DesignationMaster(models.Model):
name = models.CharField(max_length=120, unique=True)
level = models.CharField(max_length=20, blank=True)


def __str__(self):
return self.name


class ServiceMaster(models.Model):
name = models.CharField(max_length=120, unique=True)


def __str__(self):
return self.name