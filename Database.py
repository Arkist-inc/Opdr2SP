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
        
    def recommend(self, amount, method, item):
        if method == 'collaborative':
            return self.collaborativerecommend(amount, item)
        
        if method == 'content':
            return self.contentrecommend(amount, item)
        
    def collaborativerecommend(self, amount, item):
        #
        q = f"SELECT sessionid from looked_at WHERE product_dataid = '{item}'"
        self.cur.execute(q)
        sessions = self.cur.fetchall()
        
        recommends = []
        for session in sessions:
            q = f"SELECT product_dataid " \
                f"FROM looked_at " \
                f"WHERE sessionid =  '{session[0]}'" \
                f"AND NOT product_dataid ='{item}';"
            
            self.cur.execute(q)
            recommends.append(self.cur.fetchall())
            
        recommendsfinal = []
        for x in recommends:
            for y in x:
                recommendsfinal.append(y)
        
        recommendsfinal = count([x[0] for x in recommendsfinal])
        recommendsfinal = sorted(recommendsfinal.items(), key=lambda x: x[1])[::-1]
        
        if len(recommendsfinal) < 1:
            print("This product was not looked at before")
            
        else:
            return [x[0] for x in recommendsfinal[:amount]]
        
    def contentrecommend(self, amount, item):
        # regel voor content filtering:
        # prijs moet binnen 20% van de originele prijs zitten, sub_sub_category moet hetzelfde zijn
        q = f"SELECT prijs,sub_sub_category FROM product_data WHERE id = '{item}'"
        self.cur.execute(q)
        prijs, category = self.cur.fetchall()[0]
        
        q = f"SELECT id FROM product_data WHERE prijs > {round(prijs / 100 * 80)} AND prijs < {round(prijs / 100 * 120)} " \
            f"AND sub_sub_category = '{category}'"
        self.cur.execute(q)
        recommends = self.cur.fetchall()
        
        return [x[0] for x in recommends[:4]]
    
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
                
            cur = self.cur
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
            
            cur = self.cur
            try:
                if isinstance(session['buid'][0], list):
                    session['buid'][0] = session['buid'][0][0]
                    
                if session['buid'][0] not in buids:
                    buids.append(session['buid'][0])
                    
                    if session['buid'][0] in self.connections.keys():
                        cur.execute(
                            f"INSERT INTO session(id, profileid) VALUES('{session['buid'][0]}', '{self.connections[session['buid'][0]]}')")
                    
                    else:
                        cur.execute(f"INSERT INTO session(id) VALUES('{session['buid'][0]}')")
                        
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
            except psycopg2.errors.UniqueViolation:
                print(buids, session["buid"][0])
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
    

def count(arr):
    counts = {}
    for x in arr:
        if x in counts.keys():
            counts[x] += 1
            
        else:
            counts[x] = 1
        
    return counts