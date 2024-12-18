/****** Object:  View [dbo].[vw_getCardPrices]    Script Date: 12/8/2024 12:01:49 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[vw_getCardPrices]
AS
SELECT        TOP (100) PERCENT tMCL.pkCard, tMCL.cardName, tMCL.isEnabled, tMCL.color, tMCL.type, tMCL.[set], tMCL.filepath, tMCL.manaCost, tMCL.isFoil, tMCL.boxCode, tMCL.cardID AS Expr1, 
                         CASE WHEN [isFoil] = 1 THEN oc.foilPrice ELSE oc.price END AS EstPrice, dbo.tbl_MTGLotCostBasis.pkCostBasisLot, dbo.tbl_MTGLotCostBasis.lotCostBasis / NULLIF (dbo.tbl_MTGLotCostBasis.numberOfCards, 0) 
                         AS EstimatedCostBasis, dbo.tbl_MTGWHPriceHistory.FivePPD, dbo.tbl_MTGWHPriceHistory.FivePVD, dbo.tbl_MTGWHPriceHistory.TenPPD, dbo.tbl_MTGWHPriceHistory.TenPVD, dbo.tbl_MTGWHPriceHistory.ALLPPD, 
                         dbo.tbl_MTGWHPriceHistory.ALL10PVD, tMCL.damaged, dbo.tbl_MTGLotCostBasis.datePurchased
FROM            dbo.tbl_MTGCardLibrary AS tMCL INNER JOIN
                             (SELECT        tMPH.pkPriceHistory, tMPH.cardID, tMPH.price, tMPH.foilPrice
                               FROM            dbo.tbl_MTGPriceHistory AS tMPH INNER JOIN
                                                             (SELECT        cardID, MAX(pkPriceHistory) AS PHID
                                                               FROM            dbo.tbl_MTGPriceHistory
                                                               GROUP BY cardID) AS ic ON ic.PHID = tMPH.pkPriceHistory) AS oc ON oc.cardID = tMCL.cardID INNER JOIN
                         dbo.tbl_MTGWHPriceHistory ON oc.cardID = dbo.tbl_MTGWHPriceHistory.cardID LEFT OUTER JOIN
                         dbo.tbl_MTGLotCostBasis ON tMCL.pkCostBasisLot = dbo.tbl_MTGLotCostBasis.pkCostBasisLot
WHERE        (tMCL.isEnabled = 1)
ORDER BY EstPrice DESC
GO
