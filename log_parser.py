import re
from collections import namedtuple


class Parser:
    def __init__(self):
        self.logs = {
            "ip_sorted":  dict(),
            "only_carts_ip_sorted": dict()
        }
        self.prepared_categories = dict()
        self.prepared_cart_requests = []
        self.prepared_carts_info = []
        self.prepared_ip_list = []
        self.prepared_goods_requests = []

    def parse(self, filename):
        self.read_logs(filename)
        self.write_mod_logs()
        self.prepare_categories()
        self.prepare_carts_info()
        self.prepare_cart_requests()
        self.prepare_ip_list()
        self.prepare_goods_requests()

    def read_logs(self, filename):
        with open(filename, "r") as file:
            logs = file.readlines()

        ip_set = set()

        # Grouping logs by ip - all logs
        for line in logs:
            regex = re.match(r'.*INFO: (.*) .*', line)
            ip = regex.group(1)

            if not (ip in ip_set):
                self.logs["ip_sorted"][ip] = []
                ip_set.add(ip)

            self.logs["ip_sorted"][ip].append(line)

        # Grouping logs by ip - only cart requests
        for ip, requests_list in self.logs["ip_sorted"].items():
            cart_requests = []
            for line in requests_list:
                if ("cart" in line or "success" in line) and "pay?" not in line:
                    cart_requests.append(line)
            self.logs["only_carts_ip_sorted"][ip] = cart_requests

    def write_mod_logs(self):
        text = ""
        for val in self.logs["ip_sorted"].values():
            for line in val:
                text += line
        with open("logs_sorted_by_ip.txt", "w") as file:
            file.write(text)

        text = ""
        for val in self.logs["only_carts_ip_sorted"].values():
            for line in val:
                text += line
        with open("logs_sorted_by_ip_only_carts.txt", "w") as file:
            file.write(text)

    def prepare_categories(self):
        container = dict()
        categories = set()

        Item = namedtuple('good', ['name', 'id'])

        previous_line = ""
        for val in self.logs["ip_sorted"].values():
            for line in val:
                if "goods" in line:
                    regex = re.match(r".*goods_id=(\d+).*", line)
                    good_id = regex.group(1)

                    regex = re.match(r".*\.com/([^/]+)/(.*)/", previous_line)
                    category = regex.group(1)
                    good = regex.group(2)

                    item = Item(good, good_id)

                    if category not in categories:
                        categories.add(category)
                        container[category] = []

                    if not (item in container[category]):
                        container[category].append(item)

                previous_line = line

        self.prepared_categories = container

    def prepare_carts_info(self):
        record = namedtuple('cart', ['ip', 'id', 'payed', 'payed_time'])

        for ip, cart_requests in self.logs["only_carts_ip_sorted"].items():

            previous_cart_row = None
            for line in cart_requests:
                regex = re.match(r".*cart_id=(\d+)", line)

                attempt_to_add_goods = True if regex else False
                attempt_to_pay_cart = False if regex else True

                # It is either attempt_to_add_goods...
                if attempt_to_add_goods is True:
                    current_cart = regex.group(1)

                # ... or attempt_to_pay_cart
                if attempt_to_pay_cart:
                    regex = re.match(r".*\| (.*) \[.*_pay_(.*)/", line)

                    payed_time = regex.group(1)
                    payed_cart_id = regex.group(2)

                    payed_cart = record(ip, payed_cart_id, True, payed_time)

                    self.prepared_carts_info.append(payed_cart)

                    # Moving to the next cart
                    previous_cart_row = None
                    continue

                # When shifted to next cart
                if previous_cart_row is None:
                    previous_cart_row = current_cart
                    continue

                # Skipping requests of this cart till the last one
                if current_cart == previous_cart_row:
                    continue

                # Previous_cart was not payed by user, but new cart is created:
                if current_cart != previous_cart_row:
                    cart = record(ip, previous_cart_row, False, None)
                    self.prepared_carts_info.append(cart)
                    # Current cart has nothing to do with the previous cart that we've already added above.
                    previous_cart_row = None

            # User left the cart not payed and has not created the new one.
            if previous_cart_row is not None:
                self.prepared_carts_info.append(record(ip, previous_cart_row, False, None))

    def prepare_cart_requests(self):
        Request = namedtuple('cart_request', ['datetime', 'goods_id', 'amount', 'cart_id'])
        for requests_list in self.logs["only_carts_ip_sorted"].values():
            for line in requests_list:
                regex = re.match(r".*\| (.*) \[.*goods_id=(\d+)&amount=(\d+)&cart_id=(\d+)", line)
                if regex:
                    datetime = regex.group(1)
                    goods_id = regex.group(2)
                    amount = regex.group(3)
                    cart_id = regex.group(4)

                    request = Request(datetime, goods_id, amount, cart_id)
                    self.prepared_cart_requests.append(request)

    def prepare_ip_list(self):
        for ip in self.logs["ip_sorted"].keys():
            self.prepared_ip_list.append(ip)

    def prepare_goods_requests(self):
        Request = namedtuple('goods_request', ['ip', 'datetime', 'category', 'item'])
        for ip, val in self.logs["ip_sorted"].items():
            for line in val:
                regex = re.match(r".*\| (.*) \[.*.com/(?!success_pay_)([^/ ]+)/([^/ \n]*)", line)
                if not regex:
                    continue

                datetime = regex.group(1)
                category = regex.group(2)
                item = regex.group(3)

                request = Request(ip, datetime, category, item)
                self.prepared_goods_requests.append(request)


parser = Parser()
