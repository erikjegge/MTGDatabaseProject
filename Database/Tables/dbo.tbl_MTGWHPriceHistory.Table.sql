/****** Object:  Table [dbo].[tbl_MTGWHPriceHistory]    Script Date: 12/8/2024 12:01:49 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[tbl_MTGWHPriceHistory](
	[cardID] [varchar](250) NULL,
	[FivePPD] [decimal](5, 4) NULL,
	[FivePVD] [money] NULL,
	[TenPPD] [decimal](5, 4) NULL,
	[TenPVD] [money] NULL,
	[ALLPPD] [decimal](5, 4) NULL,
	[ALL10PVD] [money] NULL
) ON [PRIMARY]
GO
