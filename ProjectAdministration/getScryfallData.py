from pickle import FALSE, TRUE
import scrython
import pyodbc
import asyncio
from datetime import date
import aiohttp
from decouple import config

today = date.today()
d1 = today.strftime("%m/%d/%Y")

server = config('SERVER')
database = config('DATABASE')
username = config('DB_USERNAME')
password = config('DB_PASSWORD')
driver= '{ODBC Driver 17 for SQL Server}'

conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = conn.cursor()

onlyNewCards = False

if onlyNewCards:
    query = ("SELECT cardName, [set] "
            "FROM [dbo].[tbl_MTGCardLibrary] "
            "WHERE [Type] IS NULL "
            "GROUP BY cardName, [set]" )
else:
    # changed this to be, ALL but only if the card hasn't been added yet today
    query = ("SELECT cl.cardName, cl.[set], cl.cardID "
                "FROM [dbo].[tbl_MTGCardLibrary] cl "
                "WHERE cl.cardID NOT IN (SELECT cardID FROM (SELECT cardID, asOfDate "
                                        "FROM [dbo].[tbl_MTGPriceHistory] "
                                        "WHERE asOfDate = DATEADD(dd, 0, DATEDIFF(dd, 0, GETDATE())) "
                                        "GROUP BY cardID, asOfDate) a) "
                "GROUP BY cl.cardName, cl.[set], cl.cardID " )

cursor.execute(query)

result = cursor.fetchall()

listOfCards = [list(i) for i in result]

for r in listOfCards:
    try:
        print('<><><><><><><><><><><><><><><><>')
        print(r[0])
        if r[1] == 'XXX':
            data = scrython.cards.Search(q="++{}".format(r[0]))
            setfinal = r[1]
            if len(data.data()) == 1:
                for card in data.data():
                    setfinal = card['set'].upper()
        else:
            setfinal = r[1]

        card = scrython.cards.Named(exact=r[0],set=setfinal)

        #card names can have single quotes
        cardName = r[0].replace("'", "''")

        price = card.prices('usd')
        if not price:
            price = 0.0

        foilPrice = card.prices('usd_foil')
        if not foilPrice:
            foilPrice = 0.0

        try:
            type = card.type_line()
            type = type.replace("'", "''")
        except(KeyError):
            type = ''

        try:
            manaCost = card.mana_cost()
        except(KeyError):
            manaCost = ''

        try:
            colors = ''.join(card.colors())
        except(KeyError):
            colors = ''

        # change name for double cards
        try:
            realName = ''.join(card.name())
            realName = realName.replace("'", "''")
        except(KeyError):
            realName = ''

        cardId = card.id()

        sqlString = (
                    "UPDATE [dbo].[tbl_MTGCardLibrary] "
                    "SET [set] = '"+setfinal+"' "
                    "WHERE cardName = '"+cardName+"' AND [set] = 'XXX' "
        )

        cursor.execute(sqlString)
        conn.commit()

        sqlString = (
                    "UPDATE [dbo].[tbl_MTGCardLibrary] "
                    "SET manaCost = '"+str(manaCost)+"', color = '"+str(colors)+"', [type] = '"+str(type)+"', [cardID] = '"+str(cardId)+"', cardName = '"+str(realName)+"' "
                    "WHERE cardName = '"+cardName+"' AND [set] = '"+setfinal+"' "
        )

        cursor.execute(sqlString)
        conn.commit()

        sqlString = (
                    "IF NOT EXISTS(SELECT 1 FROM [dbo].[tbl_MTGPriceHistory] WHERE [cardID] = '"+str(cardId)+"' AND [asOfDate] = '"+d1+"') "
                    "INSERT INTO [dbo].[tbl_MTGPriceHistory]  "
                    "VALUES('"+str(cardId)+"', "+str(price)+", '"+d1+"',"+str(foilPrice)+") "
        )

        cursor.execute(sqlString)
        conn.commit()

    except (scrython.foundation.ScryfallError, asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ContentTypeError):
        print('card not found')
        pass

conn.close
cursor.close