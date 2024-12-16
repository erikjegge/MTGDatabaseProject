This project started a few years ago as a way to organize my growing Magic the Gathering collection and get a rough estimate of what everything was worth.

Since then, the collection has grown to over 100,000 cards and I have added many features in order to not only track but identify cards worth selling and flag when to try and sell them.

This project is divided into a few different operational processes.

1.	Computer Vision: Taking a picture of a card and from that, reading in the name of the card to the database. 
2.	Scryfall Data: I read from my database. Then, using the Scryfall API, grab all pricing information for each unique card in my collection. Storing the old data as historical price information so I can track changes for each card. I have a series of SQL queries and procedures that help track historical price changes and cost basis.
3.	Operational Projects: SQL queries that make uploading to ebay a breeze and some python scripts that make certain aspects such as adding pictures to these listings a bit more automated.

Future state, I have a lot of upgrades in mind. 
1.	Automation of Scanning/Picture Process: This part is currently in process. Learning a lot about robotics and automation and I am tracking to have something in the proof-of-concept stage by Jan 2025.
2.	Computer Vision Upgrades: I would like to try to make the computer vision a bit more sophisticated. Adding a way to analyze the card and determine the set it is from. I would also like a way to determine an approximate card grade/condition based on the picture of the card. Both processes I currently do manually.
