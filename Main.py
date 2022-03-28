from Database import Database

Updatedatabase = False  # Als true dan wordt de database helemaal leeg gemaakt en opnieuw gevuld dit duurt wel
# meer dan een half uur als je de volledige dataset inlaad
productmax = 10000  # aantal producten om in te laden, -1 is alles
profilemax = 10000  # aantal profielen om in te laden, -1 is alles
sessionmax = 100000  # aantal sessions om in te laden, -1 is alles

Product = 32450  # het product waarvan de recommendatie moet worden gegeven
method = "content"  # keuze uit ["collaborative", "ccontent"]
aantal_producten = 20  # aantal recommendaties
aanvullen = True  # of het moet worden aangevuld vanuit de andere soort recommendatie

if __name__ == '__main__':
    database = Database("ShoppingMinds", "RecommendationEngine")
    
    if Updatedatabase:
        database.updatedata(productmax=productmax, profilemax=profilemax, sessionmax=sessionmax)
    
    recommendations = database.recommend(aantal_producten, method, Product, aanvullen=aanvullen)
    print(recommendations)
    