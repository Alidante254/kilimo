from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import datetime, timedelta

class TrustScore(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE)
    score = models.IntegerField(default=100)
    is_blacklisted = models.BooleanField(default=False)

    def _str_(self):
        return f"{self.user.username}'s Trust Score"

class User(AbstractUser):
    date_joined = models.DateTimeField(default=timezone.now)
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True, blank=False)
    password = models.CharField(max_length=128)
    phone_number = models.CharField(max_length=15, unique=True)
    id_number = models.CharField(max_length=50, unique=True)
    loan_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    trustscore = models.OneToOneField(TrustScore, on_delete=models.CASCADE, null=True, blank=True)

    @property
    def max_loan_amount(self):
        trust_score = self.trustscore.score
        adjusted_max_loan = trust_score * 100
        return min(adjusted_max_loan, Loan.LOAN_LIMIT)

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)

class Loan(models.Model):
    LOAN_LIMIT = 5000
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loans")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    duration_months = models.PositiveSmallIntegerField()
    application_date = models.DateField(auto_now_add=True)
    repaid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    disbursed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    loaned_items = models.ManyToManyField('LoanedItem', related_name='loans', blank=True)

    @property
    def remaining_loan_amount(self):
        return max(0, self.amount - self.repaid_amount - self.LOAN_LIMIT)

    @property
    def total_loan_owed(self):
        return self.amount + (self.amount * self.interest_rate / 100)

    def is_item_available(self):
        return all(item.in_stock for item in self.loaned_items.all())

    def _str_(self):
        return f"{self.user.username}'s Loan {self.pk}"

class LoanItem(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='loan_items')
    item = models.ForeignKey('Items', on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def _str_(self):
        return f"{self.loan.user.username}'s Loan Item: {self.item.name}"

class Items(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    in_stock = models.BooleanField(default=True)

    def _str_(self):
        return self.name

class Savings(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name="saving")
    savings_item = models.ForeignKey('SavingsItem', on_delete=models.CASCADE)
    amount_saved = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table='savings'

    def _str_(self):
        return f"{self.user.username}'s Savings for {self.savings_item.item.name}"

    @property
    def remaining_amount(self):
        return max(0, self.savings_item.target_amount - self.amount_saved)

    @property
    def days_saving(self):
        return (datetime.now().date() - self.start_date).days

    @property
    def days_remaining(self):
        return (self.end_date - datetime.now().date()).days

    def is_item_available(self):
        return self.savings_item.item.in_stock

    def save(self, *args, **kwargs):
        # Set the end date to 90 days from the start date
        self.end_date = self.start_date + timedelta(days=90)
        super().save(*args, **kwargs)

class SavingsItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Items, on_delete=models.CASCADE)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()

    def _str_(self):
        return f"{self.user.username}'s Savings Item for {self.item.name}"

    @property
    def remaining_days(self):
        from datetime import date
        today = date.today()
        remaining_days = (self.due_date - today).days
        return max(0, remaining_days)

    @property
    def is_completed(self):
        return self.amount_saved >= self.target_amount

    @property
    def amount_remaining(self):
        return max(0, self.target_amount - self.amount_saved)

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    description = models.CharField(max_length=255)
    is_loan_payment = models.BooleanField(default=False)
    is_savings_payment = models.BooleanField(default=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, null=True, blank=True)
    savings = models.ForeignKey(Savings, on_delete=models.CASCADE, null=True, blank=True)

    def _str_(self):
        return f"{self.user.username}'s Payment ({self.description})"


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('payment', 'Payment'),
        ('loan', 'Loan'),
        ('savings', 'Savings'),
    )

    transaction_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    loan = models.ForeignKey('Loan', on_delete=models.CASCADE, null=True, blank=True)
    savings = models.ForeignKey('Savings', on_delete=models.CASCADE, null=True, blank=True)

    def _str_(self):
        return f"{self.user.username}'s {self.get_transaction_type_display()} Transaction ({self.description})"