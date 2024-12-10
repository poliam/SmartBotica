from django.db import models
from django.conf import settings


class DosageForm(models.Model):
    """
    Represents the physical form of the medicine (e.g., Tablet, Syrup).
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
class PharmacologicCategory(models.Model):
    """
    Represents pharmacological categories (e.g., Antibiotics, Analgesics).
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Stock(models.Model):
    CLASSIFICATION_CHOICES = [
        ('RX', 'Prescription Drug (RX)'),
        ('OTC', 'Over-the-Counter (OTC)'),
    ]

    item_no = models.AutoField(primary_key=True)
    generic_name = models.CharField(max_length=100)
    brand_name = models.CharField(max_length=100)
    dosage_strength = models.CharField(max_length=50, null=True, blank=True)
    form = models.ForeignKey(DosageForm, on_delete=models.CASCADE, related_name="stocks")
    classification = models.CharField(
        max_length=3,
        choices=CLASSIFICATION_CHOICES,
        default='OTC',
    )
    pharmacologic_category = models.ForeignKey(
        PharmacologicCategory, on_delete=models.CASCADE, related_name="stocks"
    )
    quantity = models.PositiveIntegerField(default=0)
    threshold = models.PositiveIntegerField(default=0)  # Add threshold field
    expiry_date = models.DateField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    def is_below_threshold(self):
        """
        Check if the stock is below the threshold.
        """
        return self.quantity < self.threshold

    def __str__(self):
        return f"{self.generic_name} ({self.brand_name})"


class StockHistory(models.Model):
    """
    Represents the history of changes in stock levels.
    """
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='history')
    quantity_added = models.IntegerField()
    total_quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"History for {self.stock.generic_name} on {self.date}"

