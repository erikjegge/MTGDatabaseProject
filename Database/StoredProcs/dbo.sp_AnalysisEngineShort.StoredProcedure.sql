/****** Object:  StoredProcedure [dbo].[sp_AnalysisEngineShort]    Script Date: 12/8/2024 12:01:49 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:      Egge, Erik
-- Create Date: 1/25/2023
-- Description: The Analysis Engine
-- =============================================
CREATE PROCEDURE [dbo].[sp_AnalysisEngineShort]
AS
BEGIN

	SELECT cardID
	INTO #temp
	FROM [dbo].[tbl_MTGCardLibrary] 
	WHERE cardID NOT IN (SELECT cardID
						FROM tbl_MTGWHPriceHistory
						GROUP BY cardID)
	GROUP BY cardID 

	DECLARE @CardID VARCHAR(250)

	DECLARE @FirstFivePrice MONEY
	DECLARE @LastFivePrice MONEY
	DECLARE @FivePriceMove decimal(5,4)
	DECLARE @FirstFivePriceDiff MONEY

	DECLARE @FirstTenPrice MONEY
	DECLARE @LastTenPrice MONEY
	DECLARE @TenPriceMove decimal(5,4)
	DECLARE @FirstTenPriceDiff MONEY

	DECLARE @FirstAllPrice MONEY
	DECLARE @LastAllPrice MONEY
	DECLARE @AllPriceMove decimal(5,4)
	DECLARE @AllTimePriceDiff MONEY

	While (Select Count(*) From #temp) > 0
	Begin
		BEGIN TRAN

		SET @CardID = (SELECT TOP 1 CardID FROM #temp)

		-- Get last five readings
		SELECT TOP 5 * 
		INTO #TempLastFive
		FROM tbl_MTGPriceHistory WHERE cardID = @CardID
		ORDER BY pkPriceHistory DESC

		-- Get last five readings
		SELECT TOP 10 *
		INTO #TempLastTen
		FROM tbl_MTGPriceHistory WHERE cardID = @CardID
		ORDER BY pkPriceHistory DESC

		-- Get last five readings
		SELECT *
		INTO #TempAllTime
		FROM tbl_MTGPriceHistory WHERE cardID = @CardID
		ORDER BY pkPriceHistory DESC

		--first 
		SET @FirstFivePrice = (SELECT price FROM #TempLastFive WHERE pkPriceHistory IN (SELECT max(pkPriceHistory) FROM #TempLastFive))
		--last
		SET @LastFivePrice = (SELECT price FROM #TempLastFive WHERE pkPriceHistory IN (SELECT min(pkPriceHistory) FROM #TempLastFive))

		IF @LastFivePrice IS NULL OR @LastFivePrice = 0
			SET @FivePriceMove = 0.00
		ELSE
			SET @FivePriceMove = (@FirstFivePrice - @LastFivePrice) / ABS(@LastFivePrice)

		--SELECT @FivePriceMove
		SET @FirstFivePriceDiff =  @FirstFivePrice - @LastFivePrice
		--SELECT @FirstFivePriceDiff

		--first
		SET @FirstTenPrice = (SELECT price FROM #TempLastTen WHERE pkPriceHistory IN (SELECT max(pkPriceHistory) FROM #TempLastTen))
		--last
		SET @LastTenPrice = (SELECT price FROM #TempLastTen WHERE pkPriceHistory IN (SELECT min(pkPriceHistory) FROM #TempLastTen))

		IF @LastTenPrice IS NULL OR @LastTenPrice = 0
			SET @TenPriceMove = 0.00
		ELSE
			SET @TenPriceMove = (SELECT (@FirstTenPrice - @LastTenPrice) / ABS(@LastTenPrice))

		--SELECT @TenPriceMove
		SET @FirstTenPriceDiff =  @FirstTenPrice - @LastTenPrice
		--SELECT @FirstTenPriceDiff

		--first
		SET @FirstAllPrice = (SELECT price FROM #TempAllTime WHERE pkPriceHistory IN (SELECT max(pkPriceHistory) FROM #TempAllTime))
		--last
		SET @LastAllPrice = (SELECT price FROM #TempAllTime WHERE pkPriceHistory IN (SELECT min(pkPriceHistory) FROM #TempAllTime))

		IF @LastAllPrice IS NULL OR @LastAllPrice = 0
			SET @AllPriceMove = 0.00
		ELSE
			SET @AllPriceMove = (SELECT (@FirstAllPrice - @LastAllPrice) / ABS(@LastAllPrice))

		--SELECT @AllPriceMove
		SET @AllTimePriceDiff = @FirstAllPrice - @LastAllPrice
		--SELECT @AllTimePriceDiff

		INSERT INTO  dbo.tbl_MTGWHPriceHistory
		VALUES (@CardID, @FivePriceMove, @FirstFivePriceDiff, @TenPriceMove, @FirstTenPriceDiff, @AllPriceMove, @AllTimePriceDiff)

		DROP TABLE #TempLastFive
		DROP TABLE #TempLastTen
		DROP TABLE #TempAllTime

		DELETE FROM #Temp WHERE CardID = @CardID

		COMMIT TRAN
	END

	DROP TABLE #temp

	--SELECT * FROM dbo.tbl_MTGWHPriceHistory

END
GO
