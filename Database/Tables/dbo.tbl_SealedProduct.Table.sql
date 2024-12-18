/****** Object:  Table [dbo].[tbl_SealedProduct]    Script Date: 12/8/2024 12:01:49 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[tbl_SealedProduct](
	[pkSealedProductID] [int] IDENTITY(1,1) NOT NULL,
	[pkSealedProductType] [int] NULL,
	[pkCostBasisLot] [int] NULL,
	[opened] [bit] NULL,
	[openedDate] [timestamp] NULL,
	[sold] [bit] NULL,
	[soldDate] [datetime] NULL,
	[soldAmount] [money] NULL,
 CONSTRAINT [PK_tbl_SealedProduct] PRIMARY KEY CLUSTERED 
(
	[pkSealedProductID] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
ALTER TABLE [dbo].[tbl_SealedProduct] ADD  CONSTRAINT [DF_tbl_SealedProduct_opened]  DEFAULT ((0)) FOR [opened]
GO
