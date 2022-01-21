/****** Object:  Table [dbo].[tbl_MTGPriceHistory]    Script Date: 1/21/2022 8:27:24 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[tbl_MTGPriceHistory](
	[pkPriceHistory] [int] IDENTITY(1,1) NOT NULL,
	[cardID] [varchar](250) NULL,
	[price] [money] NULL,
	[asOfDate] [datetime] NULL,
	[foilPrice] [money] NULL,
 CONSTRAINT [PK_tbl_MTGPriceHistory] PRIMARY KEY CLUSTERED 
(
	[pkPriceHistory] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
