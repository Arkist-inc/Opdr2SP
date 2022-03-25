from msilib.schema import Error
from pymongo import MongoClient
import psycopg2
from psycopg2 import errors
import time


class Database:
    def __init__(self, mongo, postgres):
        self.mongoClient = MongoClient("localhost")
        self.mongodb = self.mongoClient[mongo]
        self.dbname = {"mongo": mongo, "postgres": postgres}

        self.postgres = psycopg2.connect(
                host="localhost",
                dbname=postgres,
                user="postgres",
                password="admin"
            )
        self.connections = {}
        self.cur = self.postgres.cursor()
    
    # Getting data from a mongodb collection
    def getcollectiondata(self, collection):
        return self.mongodb[collection].find()

    def updatedata(self, productmax=-1, profilemax=10000, sessionmax=10000):
        self.cleardb()
        
        print("Connected to", self.dbname["mongo"])
        self.updateproducts(productmax)
        print("Updated products")
        
        self.updateprofiles(profilemax)
        print("Updated profiles")
        
        self.updatesessions(sessionmax)
        print("Updated sessions")
        
        print("the DataBase " + self.dbname["postgres"] + " is updated")
        
    def updateproducts(self, max):
        amount = 0
        for product in self.getcollectiondata("products"):
            amount += 1
            if amount > max != -1:
                break
                
            data = {}
            if not product["_id"].isdigit():
                continue
            data["id"] = product["_id"]
            data["brand"] = self.fix_string(product["brand"])
            data["prijs"] = str(product["price"]["selling_price"]).split(".")[0]
            data["gender"] = product["gender"]
            
            if product["category"] is not None:
                data["category"] = self.fix_string(product["category"])
                data["sub_category"] = self.fix_string(product["sub_category"])
                data["sub_sub_category"] = self.fix_string(product["sub_sub_category"])
                data["sub_sub_sub_category"] = self.fix_string(product["sub_sub_sub_category"])
            data["recommendable"] = product["recommendable"]
    
            values = [f'\'{x}\'' for x in data.values()]
    
            q = (f"INSERT INTO product_data({', '.join(data.keys())})"
                                      f'VALUES ({", ".join(values)});')
                
            self.cur.execute(q)

        self.postgres.commit()
        
    def updateprofiles(self, max):
        profilescol = self.mongodb['visitors']
        
        amount = 0
        for profile in profilescol.find():
            amount += 1
            if amount > max != -1:
                break
            
            if "buids" not in profile.keys():
                continue
            data = {"id": profile["_id"]}
            for x in profile["buids"]:
                self.connections[x] = data['id']
                
            cur = self.postgres.cursor()
            cur.execute(f"INSERT INTO profile(id) VALUES('{data['id']}')")
        
        self.postgres.commit()

    def updatesessions(self, max):
        buids = []
        
        amount = 0
        for session in self.getcollectiondata("sessions_modified"):
            amount += 1
            if amount > max != -1:
                break
                
            # try:
            looked_at = []
            orders = []
            for x in session["events"]:
                product = x["product"]
                if product:
                    if product not in looked_at:
                        looked_at.append(product)
                        
            if "order" in session.keys():
                order = session["order"]
                if order is not None:
                    for product in order["products"]:
                        orders.append(product)
            
            cur = self.postgres.cursor()
            if session['buid'][0] not in buids:
                
                if isinstance(session['buid'][0], list):
                    session['buid'][0] = session['buid'][0][0]
                if session['buid'][0] in self.connections.keys():
                    cur.execute(
                        f"INSERT INTO session(id, profileid) VALUES('{session['buid'][0]}', '{self.connections[session['buid'][0]]}')")
                
                else:
                    cur.execute(f"INSERT INTO session(id) VALUES('{session['buid'][0]}')")

                buids.append(session['buid'][0])
                
                # looked at
                if len(looked_at) > 1:
                    for look in looked_at:
                        if isinstance(look, dict):
                            look = look["id"]
                        if not look.isdigit():
                            continue
                        self.cur.execute(f"INSERT INTO looked_at(product_dataid, sessionid) VALUES('{look}', '{session['buid'][0]}')")
                        
                if len(orders) > 1:
                    for order in orders:
                        if isinstance(order, dict):
                            order = order["id"]
                        if not order.isdigit():
                            continue
                        self.cur.execute(f"INSERT INTO \"order\"(product_dataid, sessionid) VALUES('{order}', '{session['buid'][0]}')")


        self.postgres.commit()
    
    def makeallstring(self, data):
        return [str(x) for x in data]
    
    def cleardb(self):
        with open("sql.txt", "r") as f:
            self.cur.execute(f.read())
        self.postgres.commit

    def fix_string(self, string):
        if string is None:
            return string
        return "".join(['' if x == "'" else x for x in string])
    
    