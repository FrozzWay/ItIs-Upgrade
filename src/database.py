import geoip2.database
import geoip2.errors
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    create_engine, Column, Integer, String,
    func, select, DateTime, ForeignKey, Boolean, and_, distinct, text)
import os
from sqlalchemy.exc import InvalidRequestError, UnboundExecutionError

from log_parser import parser

Base = declarative_base()

path_to_geoip2_db = os.path.join(os.getcwd(), 'static', 'GeoLite2-Country.mmdb')


class CartRequests(Base):
    __tablename__ = "cart_requests"

    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('cart_info.id'))
    datetime = Column(DateTime(timezone=False))
    goods_id = Column(Integer, ForeignKey('goods.id'))
    amount = Column(Integer)

    def __repr__(self):
        return f"cart_id= {self.cart_id}, datetime= {self.datetime}, goods_id= {self.goods_id}, amount= {self.amount}"


class Goods(Base):
    __tablename__ = "goods"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    category_id = Column(Integer, ForeignKey('category.id'))

    category = relationship("Category", back_populates="goods")

    def __repr__(self):
        return f"id= {self.id}, name= {self.name}, category_id= {self.category_id}"


class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    goods = relationship("Goods", back_populates="category")


class CartInfo(Base):
    __tablename__ = "cart_info"

    id = Column(Integer, primary_key=True)
    ip = Column(String(50))
    payed = Column(Boolean)
    payed_time = Column(DateTime(timezone=False))


class IpCountry(Base):
    __tablename__ = 'ip_country'

    ip = Column(String(50), primary_key=True)
    country = Column(String(50))

    def __repr__(self):
        return f'ip: {self.ip}\ncountry: {self.country}'


class GoodsRequests(Base):
    __tablename__ = "goods_requests"

    id = Column(Integer, primary_key=True)
    ip = Column(String(50))
    datetime = Column(DateTime(timezone=False))
    goods_id = Column(Integer, ForeignKey('goods.id'))
    category_id = Column(Integer, ForeignKey('category.id'))


class PostgreSQL:
    def __init__(self):
        self.engine = None

    def init_db(self, path_to_logs_file):
        self.engine = create_engine(f"postgresql://postgres:123@localhost:5432/ITIS", future=True)
        Base.metadata.bind = self.engine

        Base.metadata.drop_all()
        Base.metadata.create_all()

        parser.parse(path_to_logs_file)
        self.fill_db()

    def fill_db(self):
        if self.check_db():
            return
        self.fill_categories()
        self.fill_carts_info()
        self.fill_cart_requests()
        self.fill_ip_country(path_to_geoip2_db)
        self.fill_goods_requests()

    def fill_carts_info(self):
        with Session(self.engine) as session:
            for row in parser.prepared_carts_info:
                session.add(CartInfo(
                    id=getattr(row, "id"),
                    ip=getattr(row, "ip"),
                    payed=getattr(row, "payed"),
                    payed_time=getattr(row, "payed_time")
                ))
            session.commit()

    def fill_cart_requests(self):
        with Session(self.engine) as session:
            for row in parser.prepared_cart_requests:
                record = CartRequests(
                    datetime=getattr(row, "datetime"),
                    goods_id=getattr(row, "goods_id"),
                    amount=getattr(row, "amount"),
                    cart_id=getattr(row, "cart_id")
                )
                session.add(record)
            session.commit()

    def fill_categories(self):
        with Session(self.engine) as session:
            for category, goods in parser.prepared_categories.items():

                new_category = Category(name=category)

                for item in goods:
                    new_item = Goods(
                        name=getattr(item, "name"),
                        id=getattr(item, "id")
                    )
                    new_category.goods.append(new_item)

                session.add(new_category)
            session.commit()

    def fill_ip_country(self, filename):
        with Session(self.engine) as session:
            with geoip2.database.Reader(filename) as reader:
                for ip in parser.prepared_ip_list:
                    try:
                        country = reader.country(ip).country.name
                        country = 'Unknown' if (country is None) else country
                    except geoip2.errors.AddressNotFoundError:
                        country = 'Internet Assigned Numbers Authority'
                    session.add(IpCountry(ip=ip, country=country))
                session.commit()

    def fill_goods_requests(self):
        print("Processing filling goods_requests...")
        with Session(self.engine) as session:
            for request in parser.prepared_goods_requests:
                datetime = getattr(request, 'datetime')
                ip = getattr(request, 'ip')
                category = getattr(request, 'category')
                item = getattr(request, 'item')

                if item:
                    goods_id = session.execute(
                        select(Goods.id).
                        where(Goods.name == item)
                    ).scalar()
                else:
                    goods_id = None

                category_id = session.execute(
                    select(Category.id).
                    where(Category.name == category)
                ).scalar()

                session.add(GoodsRequests(
                    ip=ip,
                    datetime=datetime,
                    category_id=category_id,
                    goods_id=goods_id
                ))
            session.commit()
        print("Done filling goods_requests")

    def check_db(self):
        try:
            with Session(self.engine) as session:
                result = session.execute(select(Category))
            return False if result.first() is None else True
        except UnboundExecutionError:
            return False
        except InvalidRequestError:
            return True

    # Сколько брошенных (не оплаченных) корзин имеется за определенный период?
    def rep_unpayed_carts(self, s, p):
        with Session(self.engine) as session:
            stmt = (
                select(distinct(CartRequests.cart_id)).
                join(CartInfo).
                where(CartRequests.datetime < p).
                where(s < CartRequests.datetime).
                where(CartInfo.payed == False)
            )
            result = session.execute(stmt)
        return result.scalars().all()

    # Какое количество пользователей совершали повторные покупки за определенный период?
    def rep_repeated_payments(self, s, p):
        with Session(self.engine) as session:
            stmt = (
                select((func.count(CartInfo.id) - 1).label("amount"), CartInfo.ip).
                where(CartInfo.payed == True).
                where(CartInfo.payed_time < p).
                where(CartInfo.payed_time > s).
                group_by(CartInfo.ip).
                having(func.count(CartInfo.id) > 1)
            )

            data = session.execute(stmt).all()
            data_dict = dict()
            for row in data:
                data_dict[row[1]] = row[0]

            sbqr = stmt.subquery()

            stmt = (
                select(func.sum(sbqr.c.amount))
            )

            amount = session.execute(stmt).scalar()

        return amount, data_dict

    # Товары из какой категории чаще всего покупают совместно с товаром из заданной категории?
    def rep_pattern_buy(self, category, item):
        with Session(self.engine) as session:
            stmt = (
                select(CartRequests.cart_id).
                join(Goods).
                join(Category).
                join(CartInfo).
                where(and_(
                    CartInfo.payed == True,
                    Goods.name == item,
                    Category.name == category
                ))
            )
            result = session.execute(stmt)
            # List of Carts ID that contain specified item
            carts_id = result.scalars().all()

            # Goods(excluding specified one) with additional info - in all carts
            stmt = (
                select(CartRequests.cart_id, CartRequests.goods_id, Category.name.label("category"), CartRequests.amount).
                select_from(CartRequests).
                join(Goods).
                join(Category).
                where(CartRequests.goods_id != 8).
                order_by(CartRequests.cart_id)
            )
            # Goods(excluding specified one) with additional info - only in carts that contain specified item
            stmt = stmt.filter(CartRequests.cart_id.in_(carts_id))
            result = session.execute(stmt)
            goods_per_cart = result.all()

            sbqr = stmt.subquery()
            stmt = select(distinct(sbqr.c.cart_id), sbqr.c.category)

            sbqr = stmt.subquery()
            stmt = select(sbqr.c.category, func.count(sbqr.c.category)).group_by(sbqr.c.category).order_by(func.count(sbqr.c.category).desc())

            result = session.execute(stmt)
        return result.all()

    # Посетители из какой страны чаще всего интересуются товарами из определенных категорий?
    def rep_pattern_view(self, category, item):
        with Session(self.engine) as session:
            stmt = (
                select(IpCountry.country, func.count(IpCountry.country)).
                select_from(GoodsRequests).
                join(Category, Category.id == GoodsRequests.category_id).
                join(IpCountry, IpCountry.ip == GoodsRequests.ip).
                where(Category.name == category).
                group_by(IpCountry.country).
                order_by(func.count(IpCountry.country).desc())
            )
            if item:
                stmt = stmt.join(Goods, Goods.id == GoodsRequests.goods_id).where(Goods.name == item)

            result = session.execute(stmt)
        return result.all()

    # В какое время суток чаще всего просматривают определенную категорию товаров?
    def rep_time_pattern(self, category, k):
        with Session(self.engine) as session:
            stmt = (
                select(func.floor(func.date_part('hour', GoodsRequests.datetime) / k), func.count()).
                join(Category, Category.id == GoodsRequests.category_id).
                where(Category.name == category).
                group_by(func.floor(func.date_part('hour', GoodsRequests.datetime) / k))
            )
            result = session.execute(stmt)
            return result.all()

    # Посетители из какой страны совершают больше всего действий на сайте?
    def rep_actions_per_country(self):
        with Session(self.engine) as session:
            cart_requests = (
                select(CartInfo.ip, CartRequests.datetime).
                join(CartInfo)
            )
            goods_requests = select(GoodsRequests.ip, GoodsRequests.datetime)

            requests = cart_requests.union(goods_requests).subquery()

            stmt = (
                select(IpCountry.country, func.count()).
                select_from(requests).
                join(IpCountry, IpCountry.ip == requests.c.ip).
                group_by(IpCountry.country).
                order_by(func.count().desc())
            )
            result = session.execute(stmt)
        return result.all()

    # Какая нагрузка (число запросов) на сайт за астрономический час?
    def rep_server_load_per_hour(self):
        with Session(self.engine) as session:
            cart_requests = select(
                CartRequests.datetime,
                func.date_part('day', CartRequests.datetime).label('day'),
                func.date_part('hour', CartRequests.datetime).label('hour'),
                func.date_part('month', CartRequests.datetime).label('month')
            )
            goods_requests = select(
                GoodsRequests.datetime,
                func.date_part('day', GoodsRequests.datetime).label('day'),
                func.date_part('hour', GoodsRequests.datetime).label('hour'),
                func.date_part('month', GoodsRequests.datetime).label('month')
            )
            requests = cart_requests.union(goods_requests).subquery()

            stmt = (
                select(func.count().label("count"), requests.c.day, requests.c.hour, requests.c.month).
                select_from(requests).
                group_by(requests.c.day, requests.c.hour, requests.c.month).
                order_by(requests.c.month, requests.c.day, requests.c.hour)
            )
            result = session.execute(stmt)
            statistics = result.all()
            sbqr = stmt.subquery()
            stmt = select(func.avg(sbqr.c.count))

            avg = session.execute(stmt).scalar()

        return avg, statistics

    def overall_statistic(self):
        with Session(self.engine) as session:
            unique_users = session.execute(
                select(func.count()).select_from(IpCountry)
            ).scalar()
            items_views = session.execute(
                select(func.count()).select_from(GoodsRequests)
            ).scalar()
            payed_carts = session.execute(
                select(func.count()).select_from(CartInfo).where(CartInfo.payed == True)
            ).scalar()

            sub = select(func.count()).select_from(IpCountry).group_by(IpCountry.country).subquery()

            countries = session.execute(
                select(func.count()).select_from(sub)
            ).scalar()

            return {
                "unique_users": unique_users,
                "items_views": items_views,
                "payed_carts": payed_carts,
                "countries": countries
            }

    def get_categories(self):
        with Session(self.engine) as session:
            response = {}
            results = session.execute(
                select(Category.name, Goods.name).
                join(Goods)
            ).all()
            for row in results:
                category_name = row[0]
                item_name = row[1]
                if response.get(category_name) is None:
                    response[category_name] = []
                response[category_name].append(item_name)
        return response


db = PostgreSQL()


