from django.test import TestCase
from apps.customers.models import Customer
from apps.customers.services import find_customer_by_phone


class FindCustomerByPhoneTests(TestCase):
    def setUp(self):
        # Turli formatlarda saqlangan mijozlar
        self.full = Customer.objects.create(name="To'liq +998", phone="+998 90 123 45 67")
        self.local9 = Customer.objects.create(name="9 xonali", phone="911234567")
        self.plain12 = Customer.objects.create(name="12 xonali", phone="998931112233")

    def _assert_match(self, incoming, expected):
        found = find_customer_by_phone(incoming)
        self.assertIsNotNone(found, f"'{incoming}' uchun mijoz topilmadi")
        self.assertEqual(found.id, expected.id, f"'{incoming}' noto'g'ri mijozga bog'landi")

    # ---- Telegram '+' bilan yuboradigan to'liq raqam ----
    def test_full_plus_format(self):
        self._assert_match("+998901234567", self.full)
        self._assert_match("998901234567", self.full)
        self._assert_match("90 123 45 67", self.full)  # 9 xonali lokal

    # ---- Mijoz 9 xonali saqlangan, Telegram 998 bilan yuboradi ----
    def test_stored_9_incoming_12(self):
        self._assert_match("+998911234567", self.local9)
        self._assert_match("998911234567", self.local9)
        self._assert_match("911234567", self.local9)

    # ---- Mijoz 998... saqlangan ----
    def test_stored_12_plain(self):
        self._assert_match("+998931112233", self.plain12)
        self._assert_match("931112233", self.plain12)

    # ---- Begona / mavjud bo'lmagan raqam topilmasligi kerak ----
    def test_unknown_number(self):
        self.assertIsNone(find_customer_by_phone("+1 555 010 2929"))
        self.assertIsNone(find_customer_by_phone("700000000"))

    # ---- Bo'sh raqam ----
    def test_empty(self):
        self.assertIsNone(find_customer_by_phone(""))
        self.assertIsNone(find_customer_by_phone("   "))
