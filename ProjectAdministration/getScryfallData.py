import os
import asyncio
from datetime import date
from pickle import FALSE, TRUE
import scrython
import pyodbc
import aiohttp
from decouple import config
import requests
import cv2
from skimage.metrics import structural_similarity as ssim
import numpy as np
from rapidfuzz import process, fuzz

today = date.today()
d1 = today.strftime("%m/%d/%Y")

server = config('SERVER')
database = config('DATABASE')
username = config('DB_USERNAME')
password = config('DB_PASSWORD')
driver= '{ODBC Driver 17 for SQL Server}'
gSet = ''
gName = ''
gNamePrev = ''
IMAGE_PATH = "./candidates/"

def getKnownCards(set):
    conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = conn.cursor()

    query = ("SELECT cardName "
            "FROM [dbo].[tbl_MTGCardLibrary] "
            "WHERE [set] = '"+set+"' "
                "AND cardID IS NOT NULL "
                "AND cardName <> 'XXX' "
            "GROUP BY cardName ")

    cursor.execute(query)

    result = cursor.fetchall()

    conn.close
    cursor.close

    card_names = [row[0] for row in result]

    return card_names

conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = conn.cursor()

onlyNewCards = False

if onlyNewCards:
    query = ("SELECT cardName, [set] "
            "FROM [dbo].[tbl_MTGCardLibrary] "
            "WHERE [Type] IS NULL "
            "GROUP BY cardName, [set] "
            "ORDER BY [set], cardName" )
else:
    # changed this to be, ALL but only if the card hasn't been added yet today
    query = ("SELECT cl.cardName, cl.[set], cl.cardID "
                "FROM [dbo].[tbl_MTGCardLibrary] cl "
                "WHERE cl.cardID NOT IN (SELECT cardID FROM (SELECT cardID, asOfDate "
                                        "FROM [dbo].[tbl_MTGPriceHistory] "
                                        "WHERE asOfDate = DATEADD(dd, 0, DATEDIFF(dd, 0, GETDATE())) "
                                        "GROUP BY cardID, asOfDate) a) "
                "AND [set] <> 'XXX' "
                "GROUP BY cl.cardName, cl.[set], cl.cardID " )

cursor.execute(query)

result = cursor.fetchall()

conn.close
cursor.close

listOfCards = [list(i) for i in result]

for r in listOfCards:
    try:
        conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
        cursor = conn.cursor()

        print('<><><><><><><><><><><><><><><><>')
        print(r[0])
        # matching here
        # if the name unaltered is already in the list 
        # if not xxx both for set and also for card name

        gName = r[0] #.replace("'", "''")
        setfinal = r[1]
        fixedName = ''

        if setfinal == '_CON':
            setfinal = 'CON'

        if setfinal == 'XXX':
            data = scrython.cards.Search(q="++{}".format(r[0]))
            if len(data.data()) == 1:
                for card in data.data():
                    setfinal = card['set'].upper()

        if setfinal == 'XXX':
            continue

        if onlyNewCards and gName != 'XXX':
            if setfinal != gSet:
                card_list = getKnownCards(setfinal)

            match = process.extractOne(
                gName,
                card_list,
                scorer=fuzz.token_set_ratio
            )

            if match:
                card_name, score, index = match

                if score >= 85:
                    print(f"Matched: {card_name} ({score}%)")
                    fixedName = card_name
                else:
                    print("No confident match found")

        gSet = setfinal

        if fixedName:
            card = scrython.cards.Named(exact=fixedName,set=setfinal)
        else:
            card = scrython.cards.Named(exact=gName,set=setfinal)

        #card names can have single quotes
        #cardName = gName

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
                    "WHERE cardName = '"+gName.replace("'", "''")+"' AND ([set] = '"+str(r[1])+"')"
        )

        try:
            cursor.execute(sqlString)
            conn.commit()
        except pyodbc.OperationalError as e:
            print("Commit failed:", e)
            # Optionally reconnect or log the failure
            pass

        sqlString = (
                    "UPDATE [dbo].[tbl_MTGCardLibrary] "
                    "SET manaCost = '"+str(manaCost)+"', color = '"+str(colors)+"', [type] = '"+str(type)+"', [cardID] = '"+str(cardId)+"', cardName = '"+str(realName)+"' "
                    "WHERE cardName = '"+gName.replace("'", "''")+"' AND [set] = '"+setfinal+"' "
        )

        try:
            cursor.execute(sqlString)
            conn.commit()
        except pyodbc.OperationalError as e:
            print("Commit failed:", e)
            # Optionally reconnect or log the failure
            pass


        sqlString = (
                    "IF NOT EXISTS(SELECT 1 FROM [dbo].[tbl_MTGPriceHistory] WHERE [cardID] = '"+str(cardId)+"' AND [asOfDate] = '"+d1+"') "
                    "INSERT INTO [dbo].[tbl_MTGPriceHistory]  "
                    "VALUES('"+str(cardId)+"', "+str(price)+", '"+d1+"',"+str(foilPrice)+") "
        )

        try:
            cursor.execute(sqlString)
            conn.commit()
        except pyodbc.OperationalError as e:
            print("Commit failed:", e)
            # Optionally reconnect or log the failure
            pass

        conn.close
        cursor.close


    except (scrython.foundation.ScryfallError, asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ContentTypeError):
        print('card not found')
        conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
        cursor = conn.cursor()
        sqlString = (
                    "UPDATE [dbo].[tbl_MTGCardLibrary] "
                    "SET [cardID] = NULL, [Type] = NULL "
                    "WHERE cardName = '"+gName.replace("'", "''")+"' AND [set] = '"+gSet+"' AND boxCode <> 0"
        )

        try:
            cursor.execute(sqlString)
            conn.commit()
        except pyodbc.OperationalError as e:
            print("Commit failed:", e)
            # Optionally reconnect or log the failure
            pass
        conn.close
        cursor.close
        pass

conn.close
cursor.close