/****** Object:  Table [dbo].[tbl_MTGCardLibrary_Legacy]    Script Date: 12/8/2024 12:01:49 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[tbl_MTGCardLibrary_Legacy](
	[pkCard] [int] IDENTITY(1,1) NOT NULL,
	[cardName] [varchar](max) NULL,
	[isEnabled] [bit] NOT NULL,
	[color] [varchar](5) NULL,
	[type] [varchar](250) NULL,
	[set] [varchar](5) NULL,
	[filepath] [varchar](max) NULL,
	[manaCost] [varchar](100) NULL,
	[isFoil] [bit] NULL,
	[boxCode] [int] NULL,
	[cardID] [varchar](250) NULL,
	[pkCostBasisLot] [int] NULL,
 CONSTRAINT [PK_tbl_MTGCardLibrary] PRIMARY KEY CLUSTERED 
(
	[pkCard] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
ALTER TABLE [dbo].[tbl_MTGCardLibrary_Legacy] ADD  DEFAULT ((1)) FOR [isEnabled]
GO
ALTER TABLE [dbo].[tbl_MTGCardLibrary_Legacy] ADD  CONSTRAINT [DF_tbl_MTGCardLibrary_isFoil]  DEFAULT ((0)) FOR [isFoil]
GO
