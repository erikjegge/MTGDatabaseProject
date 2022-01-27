import scrython
import pyodbc
from datetime import date

today = date.today()
d1 = today.strftime("%m/%d/%Y")

server = 'computervisioneemtg.database.windows.net'
database = 'EEComputerVisionDB'
username = 'eggeej'
password = 'G$y1(5!hwfUsR4<o}HlK'
driver= '{ODBC Driver 17 for SQL Server}'

conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = conn.cursor()

onlyNewCards = True

if onlyNewCards:
    query = ("SELECT cardName, [set] "
            "FROM [dbo].[tbl_MTGCardLibrary] "
            "WHERE [Type] IS NULL "
            "GROUP BY cardName, [set]" )
else:
    query = ("SELECT cardName, [set] "
            "FROM [dbo].[tbl_MTGCardLibrary] "
            "GROUP BY cardName, [set]" )
    
cursor.execute(query)

result = cursor.fetchall() #//result = (1,2,3,) or  result =((1,3),(4,5),)

listOfCards = [list(i) for i in result]

for r in listOfCards:
    try:
        print('<><><><><><><><><><><><><><><><>')
        print(r[0])
        card = scrython.cards.Named(exact=r[0],set=r[1])

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

        cardId = card.id()

        sqlString = (
                    "UPDATE [dbo].[tbl_MTGCardLibrary] "
                    "SET manaCost = '"+str(manaCost)+"', color = '"+str(colors)+"', [type] = '"+str(type)+"', [cardID] = '"+str(cardId)+"' "
                    "WHERE cardName = '"+cardName+"' AND [set] = '"+r[1]+"' "
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

    except (scrython.foundation.ScryfallError):
        print('card not found')
        pass

conn.close
cursor.close