/****** Object:  Table [dbo].[tbl_MTGLotCostBasis]    Script Date: 12/8/2024 12:01:49 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[tbl_MTGLotCostBasis](
	[pkCostBasisLot] [int] IDENTITY(1,1) NOT NULL,
	[lotCostBasis] [money] NULL,
	[datePurchased] [datetime] NULL,
	[numberOfCards] [int] NULL,
	[description] [varchar](max) NULL,
 CONSTRAINT [PK_tbl_MTGLotCostBasis] PRIMARY KEY CLUSTERED 
(
	[pkCostBasisLot] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
