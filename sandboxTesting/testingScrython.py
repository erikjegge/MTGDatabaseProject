import scrython


card = scrython.cards.Named(fuzzy='Peerless Samurai',set='NEO')

##print(len(card))
print(card.name())
print(card.prices('usd'))
print(card.prices('usd_foil'))
print(card.type_line())
print(card.colors())
print(card.mana_cost())
print(card.id())
print(card.collector_number())


#card = scrython.cards.Collector(code='NEO',collector_number='96')
#print(card.id())
#print(card.name())
#print(card.prices('usd'))
#print(card.prices('usd_foil'))
#print(card.type_line())
#print(card.colors())
#print(card.mana_cost())
#print(card.id())