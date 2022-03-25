from Database import Database


Product = 26197
method = "content" # keuze uit ["collaborative", "ccontent"]
aantal_producten = 4

if __name__ == '__main__':
    database = Database("ShoppingMinds", "RecommendationEngine")
    
    recommendations = database.recommend(aantal_producten, method, Product)
    print(recommendations)