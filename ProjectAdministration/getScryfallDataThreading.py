from pickle import FALSE, TRUE
import scrython
import pyodbc
import asyncio
from datetime import date
import aiohttp
from decouple import config 
import threading 
import math

today = date.today()
d1 = today.strftime("%m/%d/%Y")

server = config('SERVER')
database = config('DATABASE')
username = config('DB_USERNAME')
password = config('DB_PASSWORD')
driver= '{ODBC Driver 17 for SQL Server}'

batchSize = 1000    # Number of records committed each time we upload to the DB

onlyNewCards = False

def chunks(xs, n):
    n = max(1, n)
    return list((xs[i:i+n] for i in range(0, len(xs), n)))

def splitList(l,n):
    remainder = l % n
    if remainder == 0:
        return int(l/n)
    else:
        return int(math.ceil(l/n))

def batchUpload(records):
    #print("uploading now!")
    conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = conn.cursor()
    #cardId = r0
    #setfinal = r1
    #cardName = r2
    #manaCost = r3
    #colors = r4
    #cardtype = r5
    #realName = r6
    #price = r7
    #foilPrice = r8
    for r in records:
        sqlString = (
                    "UPDATE [dbo].[tbl_MTGCardLibrary] "
                    "SET [set] = '"+r[1]+"' "
                    "WHERE cardName = '"+r[2]+"' AND [set] = 'XXX' "
        )

        cursor.execute(sqlString)
        conn.commit()

        sqlString = (
                    "UPDATE [dbo].[tbl_MTGCardLibrary] "
                    "SET manaCost = '"+str(r[3])+"', color = '"+str(r[4])+"', [type] = '"+str(r[5])+"', [cardID] = '"+str(r[0])+"', cardName = '"+str(r[6])+"' "
                    "WHERE cardName = '"+r[2]+"' AND [set] = '"+r[1]+"' "
        )

        cursor.execute(sqlString)
        conn.commit()

        sqlString = (
                    "IF NOT EXISTS(SELECT 1 FROM [dbo].[tbl_MTGPriceHistory] WHERE [cardID] = '"+str(r[0])+"' AND [asOfDate] = '"+d1+"') "
                    "INSERT INTO [dbo].[tbl_MTGPriceHistory]  "
                    "VALUES('"+str(r[0])+"', "+str(r[7])+", '"+d1+"',"+str(r[8])+") "
        )

        cursor.execute(sqlString)
        conn.commit()

    conn.close
    cursor.close

def processData(threadName, listOfCards):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    recordCount = 0
    recordBatch = []
    for r in listOfCards:
        try:
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
                cardtype = card.type_line()
                cardtype = cardtype.replace("'", "''")
            except(KeyError):
                cardtype = ''

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

            recordBatch.append([cardId,setfinal,cardName,manaCost,colors,cardtype,realName,price,foilPrice])

        except (scrython.foundation.ScryfallError, asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ContentTypeError):
            print('card not found')
            pass

        recordCount += 1

        if recordCount >= batchSize:
            #batchUpload()
            recordCount = 0
            recordBatch = []


    # catch all at end
    if recordCount > 0:
        #batchUpload()
        recordCount = 0
        recordBatch = []


conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = conn.cursor()

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

listOfCardsChunks = chunks(listOfCards,splitList(len(listOfCards),4))   #four equal chunks

conn.close
cursor.close

thread1 = threading.Thread(target=processData,  
                        args=("thread1", listOfCardsChunks[0])) 

thread2 = threading.Thread(target=processData,  
                        args=("thread2", listOfCardsChunks[1])) 

thread3 = threading.Thread(target=processData,  
                        args=("thread3", listOfCardsChunks[2])) 

thread4 = threading.Thread(target=processData,  
                        args=("thread4", listOfCardsChunks[3])) 

# Start the threads 
thread1.start() 
thread2.start() 
thread3.start() 
thread4.start() 

# Join the threads
thread1.join() 
thread2.join() 
thread3.join() 
thread4.join()
