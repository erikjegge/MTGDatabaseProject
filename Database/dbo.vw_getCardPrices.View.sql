/****** Object:  View [dbo].[vw_getCardPrices]    Script Date: 1/21/2022 8:27:24 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[vw_getCardPrices]
AS
SELECT        TOP (100) PERCENT tMCL.pkCard, tMCL.cardName, tMCL.isEnabled, tMCL.color, tMCL.type, tMCL.[set], tMCL.filepath, tMCL.manaCost, tMCL.isFoil, tMCL.boxCode, tMCL.cardID, 
                         CASE WHEN [isFoil] = 1 THEN oc.foilPrice ELSE oc.price END AS EstPrice
FROM            dbo.tbl_MTGCardLibrary AS tMCL INNER JOIN
                             (SELECT        tMPH.pkPriceHistory, tMPH.cardID, tMPH.price, tMPH.foilPrice
                               FROM            dbo.tbl_MTGPriceHistory AS tMPH INNER JOIN
                                                             (SELECT        cardID, MAX(pkPriceHistory) AS PHID
                                                               FROM            dbo.tbl_MTGPriceHistory
                                                               GROUP BY cardID) AS ic ON ic.PHID = tMPH.pkPriceHistory) AS oc ON oc.cardID = tMCL.cardID
ORDER BY EstPrice DESC
GO
