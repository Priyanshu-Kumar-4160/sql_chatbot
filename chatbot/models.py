from django.db import models

# Create your models here.

from django.db import models

class Customer(models.Model):
    name  = models.CharField(max_length=100)
    city  = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount   = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.customer.name} – ₹{self.amount}"
