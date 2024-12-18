/****** Object:  Table [dbo].[tbl_SealedProductType]    Script Date: 12/8/2024 12:01:49 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[tbl_SealedProductType](
	[pkSealedProductType] [int] IDENTITY(1,1) NOT NULL,
	[sealedProductName] [nvarchar](max) NULL,
	[mtgSet] [nchar](10) NULL,
	[price] [money] NULL,
	[priceAsOfDate] [datetime] NULL,
 CONSTRAINT [PK_tbl_SealedProductType] PRIMARY KEY CLUSTERED 
(
	[pkSealedProductType] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
