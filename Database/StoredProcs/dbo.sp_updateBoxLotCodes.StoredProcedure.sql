/****** Object:  StoredProcedure [dbo].[sp_updateBoxLotCodes]    Script Date: 12/8/2024 12:01:49 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:      Egge, Erik
-- Create Date: 10/1/2022
-- Description: Updates the box and lot code to the variables provided then updates cost basis tables
-- =============================================
CREATE PROCEDURE [dbo].[sp_updateBoxLotCodes]
(
    -- Add the parameters for the stored procedure here
    @boxCode int,
    @lotCode int
)
AS
BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
    SET NOCOUNT ON

	--DECLARE @boxCode INT = 23
	--DECLARE @lotCode INT = 5
	
	UPDATE [dbo].[tbl_MTGCardLibrary]
	SET boxCode = @boxCode,
	pkCostBasisLot = @lotCode
	WHERE boxCode IS NULL

	-- UPDATE Card Counts of all lots
	UPDATE tmlcb
	SET tmlcb.numberOfCards = cc.CardCount
	FROM dbo.tbl_MTGLotCostBasis tmlcb
		INNER JOIN (SELECT count(1) as CardCount, pkCostBasisLot FROM [dbo].[tbl_MTGCardLibrary] WHERE pkCostBasisLot IS NOT NULL GROUP BY pkCostBasisLot) AS cc ON tmlcb.pkCostBasisLot = cc.pkCostBasisLot

END
GO
