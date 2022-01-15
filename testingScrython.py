import scrython

card = scrython.cards.Named(exact='Nicol Bolas',set='CHR')


print(card.name())
print(card.prices('usd'))
print(card.prices('usd_foil'))
print(card.type_line())
print(card.colors())
print(card.mana_cost())
print(card.id())
